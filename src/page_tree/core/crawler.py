import asyncio
import httpx
import logging
import time
from typing import Set, Dict
from page_tree.core.scanner import AsyncScanner
from page_tree.core.models import CrawlSettings

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
        self.queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(settings.concurrency)
        self.last_request_time: Dict[str, float] = {}

    async def run(self, start_urls: list[str]) -> Set[str]:
        """
        クロールを開始します。

        Args:
            start_urls: 開始点となるURLリスト。

        Returns:
            収集したすべてのURLのセット。
        """
        for url in start_urls:
            # (url, depth)
            await self.queue.put((url, 0))

        async with httpx.AsyncClient(
            timeout=self.settings.timeout,
            headers={'User-Agent': self.settings.user_agent},
        ) as client:
            scanner = AsyncScanner(client)

            # 全タスク管理用のワーカー群を作成
            workers = [
                asyncio.create_task(self._worker(scanner))
                for _ in range(self.settings.concurrency)
            ]

            # キューが空になるまで待機
            await self.queue.join()

            # ワーカーのキャンセル
            for worker in workers:
                worker.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

        return self.visited

    async def _worker(self, scanner: AsyncScanner) -> None:
        """キューからURLを取り出して処理するワーカー関数。"""
        while True:
            url, depth = await self.queue.get()
            try:
                # 訪問済みチェック
                if url not in self.visited:
                    # 深度制限チェック
                    if (
                        self.settings.max_depth is not None
                        and depth > self.settings.max_depth
                    ):
                        continue

                    self.visited.add(url)
                    await self._crawl_page(scanner, url, depth)
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
            if link not in self.visited:
                # TODO: robots.txt のチェックが必要
                # TODO: ルート配下かどうかのチェックを強化
                await self.queue.put((link, depth + 1))
