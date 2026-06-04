import asyncio
import logging
import re
import time
from typing import Dict, List, Optional, Set

import httpx

from page_tree.core.models import CrawlResult, CrawlSettings
from page_tree.core.robots import RobotsManager
from page_tree.core.scanner import AsyncScanner
from page_tree.core.utils import is_within_boundary, normalize_url

logger = logging.getLogger(__name__)


class AsyncCrawler:
    """クローラーのオーケストレーションを行うクラス。"""

    def __init__(self, settings: CrawlSettings):
        """
        Args:
            settings: クロール設定。
        """
        self.settings = settings
        self.visited: Set[str] = set()
        self.results: List[CrawlResult] = []
        self.queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(settings.concurrency)
        self.last_request_time: Dict[str, float] = {}
        self.robots_manager = RobotsManager(user_agent=settings.user_agent)
        self.root_urls: List[str] = []

        self._include_pattern = (
            re.compile(settings.include_regex) if settings.include_regex else None
        )
        self._exclude_pattern = (
            re.compile(settings.exclude_regex) if settings.exclude_regex else None
        )

    async def run(self, start_urls: List[str]) -> List[CrawlResult]:
        """
        クロールを開始します。

        Args:
            start_urls: クロールを開始するルートURLのリスト。

        Returns:
            クロール結果のリスト。
        """
        self.root_urls = [normalize_url(url) for url in start_urls]
        for url in self.root_urls:
            if self._is_url_allowed(url):
                await self.queue.put((url, 0))

        async with httpx.AsyncClient(
            timeout=self.settings.timeout,
            headers={'User-Agent': self.settings.user_agent},
        ) as client:
            scanner = AsyncScanner(client)

            # 全タスク管理用のワーカー群を作成
            workers = [
                asyncio.create_task(self._worker(scanner, client))
                for _ in range(self.settings.concurrency)
            ]

            # キューが空になるまで待機
            await self.queue.join()

            # ワーカーのキャンセル
            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

        return self.results

    def _is_url_allowed(self, url: str) -> bool:
        """URLがフィルタリング設定に合致するか判定します。"""
        if self._exclude_pattern and self._exclude_pattern.search(url):
            return False
        if self._include_pattern and not self._include_pattern.search(url):
            return False
        return True

    def _is_within_any_root(self, url: str) -> bool:
        """URLがいずれかのルートURLの配下にあるか判定します。"""
        return any(is_within_boundary(url, root) for root in self.root_urls)

    async def _worker(self, scanner: AsyncScanner, client: httpx.AsyncClient) -> None:
        """キューからURLを取り出して処理するワーカー関数。"""
        while True:
            url, depth = await self.queue.get()
            try:
                # 訪問済みチェック
                if url in self.visited:
                    continue

                # 深度制限チェック
                if (
                    self.settings.max_depth is not None
                    and depth > self.settings.max_depth
                ):
                    continue

                # Robots.txt チェック
                if not self.settings.ignore_robots:
                    if not await self.robots_manager.can_fetch(client, url):
                        logger.warning(f'Blocked by robots.txt: {url}')
                        continue

                self.visited.add(url)
                await self._crawl_page(scanner, url, depth)
            except Exception as e:
                logger.error(f'Error crawling {url}: {e}')
            finally:
                self.queue.task_done()

    async def _crawl_page(self, scanner: AsyncScanner, url: str, depth: int) -> None:
        """
        ページをクロールし、新しいURLをキューに追加します。
        """
        # レート制限のための遅延処理
        domain = httpx.URL(url).host
        if self.settings.delay > 0:
            now = time.monotonic()
            last_time = self.last_request_time.get(domain, 0)
            elapsed = now - last_time
            if elapsed < self.settings.delay:
                await asyncio.sleep(self.settings.delay - elapsed)
            self.last_request_time[domain] = time.monotonic()

        logger.info(f'Crawling: {url} (depth: {depth})')
        links = await scanner.extract_links(url)

        for link in links:
            # 正規化
            normalized_link = normalize_url(link, base_url=url)

            # 全ての結果を保持（訪問済みであっても「見つかった」という事実は記録する）
            # ただし、同じページで見つかった同じリンクを重複して記録するかは検討が必要。
            # ここではシンプルに、クロール対象外でも見つかったリンクとして記録する。
            self.results.append(
                CrawlResult(
                    url=normalized_link,
                    found_at=url,
                    status_code=None,  # 訪問先のステータスコードはクロール時に取得
                )
            )

            # 再帰的にクロールするかどうかの判定
            if (
                normalized_link not in self.visited
                and self._is_url_allowed(normalized_link)
                and self._is_within_any_root(normalized_link)
            ):
                await self.queue.put((normalized_link, depth + 1))
