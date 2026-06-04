import csv
import json
from dataclasses import asdict
from io import StringIO
from typing import List

from page_tree.core.models import CrawlResult


class Reporter:
    """
    クロール結果を整形して出力するクラス。
    """

    def __init__(self, results: List[CrawlResult]):
        """
        Args:
            results: クロール結果のリスト。
        """
        self.results = results

    def to_text(self, grouped: bool = False) -> str:
        """
        結果をテキスト形式に変換します。

        Args:
            grouped: ページごとにグループ化するかどうか。
        """
        if not self.results:
            return 'No links found.'

        if not grouped:
            return '\n'.join(sorted({r.url for r in self.results}))

        # グループ化
        groups: dict[str, set[str]] = {}
        for r in self.results:
            if r.found_at not in groups:
                groups[r.found_at] = set()
            groups[r.found_at].add(r.url)

        output = []
        for found_at in sorted(groups.keys()):
            output.append(f'Source: {found_at}')
            for url in sorted(groups[found_at]):
                output.append(f'  - {url}')
            output.append('')

        return '\n'.join(output).strip()

    def to_json(self, grouped: bool = False) -> str:
        """
        結果をJSON形式に変換します。

        Args:
            grouped: ページごとにグループ化するかどうか。
        """
        if not grouped:
            # 重複を排除してURLのリストにするか、詳細を保持するか。
            # ここでは詳細（CrawlResult全体）をリストで返す。
            data = [asdict(r) for r in self.results]
        else:
            groups: dict[str, list[str]] = {}
            for r in self.results:
                if r.found_at not in groups:
                    groups[r.found_at] = []
                groups[r.found_at].append(r.url)
            data = [
                {'source': k, 'links': sorted(list(set(v)))}
                for k, v in sorted(groups.items())
            ]

        return json.dumps(data, indent=2, ensure_ascii=False)

    def to_csv(self) -> str:
        """
        結果をCSV形式に変換します（フラット形式のみサポート）。
        """
        output = StringIO()
        writer = csv.DictWriter(
            output, fieldnames=['url', 'found_at', 'status_code', 'error']
        )
        writer.writeheader()
        for r in self.results:
            writer.writerow(asdict(r))
        return output.getvalue()
