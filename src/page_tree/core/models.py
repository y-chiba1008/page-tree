from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CrawlSettings:
    """
    クロールの設定値を保持するデータクラス。
    """

    max_depth: Optional[int]
    concurrency: int
    user_agent: str
    timeout: float
    delay: float
    ignore_robots: bool


@dataclass(frozen=True)
class CrawlResult:
    """
    クロールの結果を保持するデータクラス。
    """

    url: str
    found_at: str
    status_code: Optional[int]
    error: Optional[str] = None
