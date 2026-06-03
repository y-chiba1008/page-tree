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

            # キューからURLを順次処理する
            while not self.queue.empty():
                url, depth = await self.queue.get()

                # 訪問済みチェック
                if url in self.visited:
                    self.queue.task_done()
                    continue

                # 深度制限チェック
                if (
                    self.settings.max_depth is not None
                    and depth > self.settings.max_depth
                ):
                    self.queue.task_done()
                    continue

                self.visited.add(url)

                # スキャン実行（各URLごとに処理）
                await self._crawl_page(scanner, url, depth)

                self.queue.task_done()

        return self.visited

    async def _crawl_page(self, scanner: AsyncScanner, url: str, depth: int) -> None:
        """
        ページをクロールし、新しいURLをキューに追加します。

        Args:
            scanner: スキャナー。
            url: クロールするURL。
            depth: 現在の再帰深度。
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

        async with self.semaphore:
            logger.info(f'Crawling: {url} (depth: {depth})')
            links = await scanner.extract_links(url)
            for link in links:
                if link not in self.visited:
                    # TODO: robots.txt のチェックが必要
                    # TODO: ルート配下かどうかのチェックを強化（start_urlsのドメインなど）
                    await self.queue.put((link, depth + 1))
