from urllib.parse import urlparse, urljoin, urlunparse
from typing import Optional


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    URLを正規化します（フラグメント削除、末尾スラッシュの整理など）。

    Args:
        url: 正規化対象のURL。
        base_url: ベースとなるURL。

    Returns:
        正規化されたURL。
    """
    if base_url:
        url = urljoin(base_url, url)

    parsed = urlparse(url)

    # フラグメントを削除
    path = parsed.path
    if path.endswith('/') and len(path) > 1:
        path = path.rstrip('/')

    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, '')
    )


def is_within_boundary(url: str, root_url: str) -> bool:
    """
    URLがルートURLの境界内にあるかを判定します。

    Args:
        url: 判定対象のURL。
        root_url: ルートとなるURL。

    Returns:
        境界内の場合は True。
    """
    return url.startswith(root_url)
