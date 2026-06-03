import pytest
import httpx
import pytest_httpx
from page_tree.core.crawler import AsyncCrawler
from page_tree.core.models import CrawlSettings


@pytest.mark.asyncio
async def test_crawler_depth_limit(httpx_mock: pytest_httpx.HTTPXMock) -> None:
    """再帰深度制限が正しく機能するかテスト。"""
    settings = CrawlSettings(
        max_depth=0,  # 深度0に制限
        concurrency=1,
        user_agent='test-agent',
        timeout=10.0,
        delay=0.0,
        ignore_robots=True,
    )

    # URLの構造: start -> level1
    # level1 にリンクがあっても深度0なのでlevel1は取得されないはず
    httpx_mock.add_response(
        url='http://example.com/start',
        text='<a href="http://example.com/level1">L1</a>',
    )

    crawler = AsyncCrawler(settings)
    visited = await crawler.run(['http://example.com/start'])

    assert 'http://example.com/start' in visited
    assert 'http://example.com/level1' not in visited


@pytest.mark.asyncio
async def test_crawler_rate_limiting(httpx_mock: pytest_httpx.HTTPXMock) -> None:
    """レート制限（delay）が正しく機能するかテスト。"""
    settings = CrawlSettings(
        max_depth=0,
        concurrency=1,
        user_agent='test-agent',
        timeout=10.0,
        delay=0.1,  # 0.1秒の遅延
        ignore_robots=True,
    )

    httpx_mock.add_response(url='http://example.com/1', text='')
    httpx_mock.add_response(url='http://example.com/2', text='')

    import time

    start_time = time.monotonic()

    crawler = AsyncCrawler(settings)
    await crawler.run(['http://example.com/1', 'http://example.com/2'])

    end_time = time.monotonic()

    # 少なくとも0.1秒は経過しているはず
    assert end_time - start_time >= 0.1
