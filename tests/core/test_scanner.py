import httpx
import pytest
import pytest_httpx
from page_tree.core.scanner import AsyncScanner


@pytest.mark.asyncio
async def test_extract_links(httpx_mock: pytest_httpx.HTTPXMock) -> None:
    """AsyncScanner.extract_links が正しくリンクを抽出できるかテスト。"""
    url = 'http://example.com'
    html = """
    <html>
        <body>
            <a href="http://example.com/page1">Page 1</a>
            <a href="/page2">Page 2</a>
        </body>
    </html>
    """
    httpx_mock.add_response(
        url=url,
        text=html,
        headers={'Content-Type': 'text/html'},
    )

    async with httpx.AsyncClient() as client:
        scanner = AsyncScanner(client)
        links = await scanner.extract_links(url)

    assert 'http://example.com/page1' in links
    assert 'http://example.com/page2' in links
    assert len(links) == 2


@pytest.mark.asyncio
async def test_extract_links_non_html(httpx_mock: pytest_httpx.HTTPXMock) -> None:
    """HTML以外が返された場合に空のセットを返すかテスト。"""
    url = 'http://example.com/image.png'
    httpx_mock.add_response(
        url=url,
        content=b'fake-image-data',
        headers={'Content-Type': 'image/png'},
    )

    async with httpx.AsyncClient() as client:
        scanner = AsyncScanner(client)
        links = await scanner.extract_links(url)

    assert links == set()
