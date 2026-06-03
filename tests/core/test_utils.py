import pytest
from page_tree.core.utils import normalize_url, is_within_boundary


@pytest.mark.parametrize(
    ('url', 'base', 'expected'),
    [
        ('https://example.com/path/', None, 'https://example.com/path'),
        ('https://example.com/path/#fragment', None, 'https://example.com/path'),
        ('/relative', 'https://example.com/', 'https://example.com/relative'),
    ],
    ids=['trailing_slash', 'fragment', 'relative_url'],
)
def test_normalize_url(url, base, expected):
    """
    URLが適切に正規化されることをテストします。
    """
    assert normalize_url(url, base) == expected


@pytest.mark.parametrize(
    ('url', 'root', 'expected'),
    [
        ('https://example.com/base/path', 'https://example.com/base', True),
        ('https://example.com/other', 'https://example.com/base', False),
    ],
    ids=['within_boundary', 'outside_boundary'],
)
def test_is_within_boundary(url, root, expected):
    """
    URLが境界内にあるか判定されることをテストします。
    """
    assert is_within_boundary(url, root) is expected
