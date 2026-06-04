import httpx
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse


class RobotsManager:
    """
    robots.txt の取得と解析を行うクラス。
    """

    def __init__(self, user_agent: str = 'page-tree'):
        self.user_agent = user_agent
        self.parsers: dict[str, RobotFileParser] = {}

    async def _fetch_robots(
        self, client: httpx.AsyncClient, domain: str
    ) -> RobotFileParser:
        """
        指定されたドメインの robots.txt を非同期で取得します。
        """
        robots_url = f'{domain}/robots.txt'
        parser = RobotFileParser()

        try:
            response = await client.get(robots_url, follow_redirects=True)
            if response.status_code == 200:
                parser.parse(response.text.splitlines())
            else:
                # 404などの場合は全て許可とみなす
                parser.parse([])
        except httpx.HTTPError:
            # エラー時も全て許可とみなす
            parser.parse([])

        return parser

    async def can_fetch(self, client: httpx.AsyncClient, url: str) -> bool:
        """
        URLへのアクセスが許可されているか判定します。
        """
        parsed = urlparse(url)
        domain = f'{parsed.scheme}://{parsed.netloc}'

        if domain not in self.parsers:
            self.parsers[domain] = await self._fetch_robots(client, domain)

        return self.parsers[domain].can_fetch(self.user_agent, url)
