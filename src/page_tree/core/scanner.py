import httpx
from bs4 import BeautifulSoup
from typing import Set
import logging
from page_tree.core.utils import normalize_url

logger = logging.getLogger(__name__)


class AsyncScanner:
    """ページを取得し、リンクを抽出するスキャナー。"""

    def __init__(self, client: httpx.AsyncClient):
        """
        Args:
            client: 非同期HTTPクライアント。
        """
        self.client = client

    async def extract_links(self, url: str) -> Set[str]:
        """
        指定されたURLからリンクを抽出します。

        Args:
            url: リンクを抽出するページのURL。

        Returns:
            抽出されたURLのセット。
        """
        try:
            response = await self.client.get(url, follow_redirects=True)
            response.raise_for_status()

            # HTMLコンテンツタイプ以外は無視
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                logger.debug(f'Skipping non-HTML content: {url} ({content_type})')
                return set()

            soup = BeautifulSoup(response.text, 'html.parser')
            links = set()
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if isinstance(href, list):
                    href = href[0]
                # 相対パスを解決し、正規化する
                normalized_url = normalize_url(str(href), base_url=url)
                links.add(normalized_url)

            return links

        except httpx.HTTPError as e:
            logger.error(f'Failed to fetch {url}: {e}')
            return set()
