import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import click
from rich.console import Console
from rich.logging import RichHandler

from page_tree.core.crawler import AsyncCrawler
from page_tree.core.models import CrawlSettings
from page_tree.core.reporter import Reporter

# Rich コンソールの初期化
console = Console()


def setup_logging(verbose: bool) -> None:
    """
    ロギングの設定を行います。
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s',
        datefmt='[%X]',
        handlers=[RichHandler(rich_tracebacks=True, console=console)],
    )


@click.command()
@click.argument('root_urls', nargs=-1, required=True)
@click.option(
    '-d',
    '--max-depth',
    type=int,
    default=None,
    help='最大再帰深度（デフォルト: 無制限）',
)
@click.option(
    '-c', '--concurrency', type=int, default=5, help='同時リクエスト数（デフォルト: 5）'
)
@click.option(
    '-o', '--output', type=click.Path(path_type=Path), help='結果を保存するファイルパス'
)
@click.option(
    '-f',
    '--format',
    'output_format',
    type=click.Choice(['text', 'json', 'csv']),
    default='text',
    help='出力形式（デフォルト: text）',
)
@click.option(
    '-u', '--user-agent', default='page-tree/0.1.0', help='カスタムUser-Agent文字列'
)
@click.option(
    '-t',
    '--timeout',
    type=float,
    default=10.0,
    help='リクエストのタイムアウト秒数（デフォルト: 10.0）',
)
@click.option(
    '--delay',
    type=float,
    default=0.0,
    help='同一ドメインへのリクエスト間の最小遅延時間',
)
@click.option('--ignore-robots', is_flag=True, help='robots.txt を無視する')
@click.option(
    '--include', 'include_regex', help='収集・クロール対象に含めるURLの正規表現'
)
@click.option('--exclude', 'exclude_regex', help='除外するURLの正規表現')
@click.option(
    '--grouped',
    is_flag=True,
    help='リンクを「どのページで見つかったか」でグループ化して出力',
)
@click.option('-v', '--verbose', is_flag=True, help='詳細なログを表示')
def main(
    root_urls: Tuple[str, ...],
    max_depth: Optional[int],
    concurrency: int,
    output: Optional[Path],
    output_format: str,
    user_agent: str,
    timeout: float,
    delay: float,
    ignore_robots: bool,
    include_regex: Optional[str],
    exclude_regex: Optional[str],
    grouped: bool,
    verbose: bool,
) -> None:
    """
    ROOT_URLS から開始して再帰的にリンクを収集します。
    """
    setup_logging(verbose)

    settings = CrawlSettings(
        max_depth=max_depth,
        concurrency=concurrency,
        user_agent=user_agent,
        timeout=timeout,
        delay=delay,
        ignore_robots=ignore_robots,
        include_regex=include_regex,
        exclude_regex=exclude_regex,
    )

    crawler = AsyncCrawler(settings)

    with console.status('[bold green]Crawling...') as status:
        try:
            results = asyncio.run(crawler.run(list(root_urls)))
        except Exception as e:
            console.print(f'[bold red]Error during crawling:[/bold red] {e}')
            sys.exit(1)

    reporter = Reporter(results)

    # 出力内容の生成
    if output_format == 'text':
        content = reporter.to_text(grouped=grouped)
    elif output_format == 'json':
        content = reporter.to_json(grouped=grouped)
    else:  # csv
        content = reporter.to_csv()

    # 出力
    if output:
        try:
            output.write_text(content, encoding='utf-8')
            console.print(f'[bold green]Results saved to:[/bold green] {output}')
        except Exception as e:
            console.print(f'[bold red]Error saving results to {output}:[/bold red] {e}')
            sys.exit(1)
    else:
        # 標準出力
        console.print(content)


if __name__ == '__main__':
    main()
