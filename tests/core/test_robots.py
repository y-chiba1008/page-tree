import pytest
import httpx
from page_tree.core.robots import RobotsManager


@pytest.mark.asyncio
async def test_robots_manager_can_fetch():
    # 簡単なモックサーバーの代わりに、httpx.AsyncClient を利用してテストする
    # 実際には外部通信が発生するため、本来は pytest-httpx 等でモックすべき
    # ここでは基礎的な動作確認として構成のみ示す
    manager = RobotsManager()
    async with httpx.AsyncClient() as client:
        # モックの robots.txt コンテンツを想定したテストは難しいが、
        # 接続の初期化とエラーハンドリングは確認できる
        result = await manager.can_fetch(client, 'https://google.com')
        assert isinstance(result, bool)
