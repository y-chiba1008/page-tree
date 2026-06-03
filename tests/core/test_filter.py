import httpx
import pytest
import pytest_httpx

from page_tree.core.crawler import AsyncCrawler
from page_tree.core.models import CrawlSettings


@pytest.mark.asyncio
async def test_crawler_url_filtering(httpx_mock: pytest_httpx.HTTPXMock) -> None:
    """URLフィルタリング機能（include/exclude）のテスト。"""
    settings = CrawlSettings(
        max_depth=2,
        concurrency=1,
        user_agent='test-agent',
        timeout=10.0,
        delay=0.0,
        ignore_robots=True,
        include_regex=r'example\.com',  # すべてマッチする
        exclude_regex=r'example\.com/exclude',  # exclude フィルタ
    )

    # 構造: start -> include_page (OK)
    #               -> exclude_page (NG)
    httpx_mock.add_response(
        url='http://example.com/start',
        text='<a href="http://example.com/include">Include</a> <a href="http://example.com/exclude">Exclude</a>',
        headers={'Content-Type': 'text/html'},
    )
    # include_page は取得される
    httpx_mock.add_response(
        url='http://example.com/include',
        text='<a href="http://example.com/other">Other</a>',
        headers={'Content-Type': 'text/html'},
    )
    # exclude_page は取得されない想定
    httpx_mock.add_response(
        url='http://example.com/exclude',
        text='',
        headers={'Content-Type': 'text/html'},
        is_optional=True,
    )
    # 他のページも登録してモック漏れを防ぐ
    httpx_mock.add_response(
        url='http://example.com/other',
        text='',
        headers={'Content-Type': 'text/html'},
    )

    crawler = AsyncCrawler(settings)
    visited = await crawler.run(['http://example.com/start'])

    assert 'http://example.com/start' in visited
    assert 'http://example.com/include' in visited
    assert 'http://example.com/exclude' not in visited
    assert 'http://example.com/other' in visited
