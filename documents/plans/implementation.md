# 実装プラン: page-tree

## フェーズ 1: 基盤構築 (page_tree.core)
- [ ] **データモデルの定義 (`core/models.py`)**:
    - `CrawlResult`: 見つかったリンクとメタデータを保持。
    - `CrawlSettings`: CLIからの設定値を保持。
- [ ] **Robots.txt ハンドラ (`core/robots.py`)**:
    - `robots.txt` の非同期取得。
    - `urllib.robotparser.RobotFileParser` のラッパー実装。
- [ ] **URL ユーティリティ (`core/utils.py`)**:
    - 正規化（フラグメントの削除、適切な末尾スラッシュの処理など）。
    - 境界チェック（URLがルート配下にあるかどうかの判定）。

## フェーズ 2: コアロジック (page_tree.core)
- [ ] **スキャナー (`core/scanner.py`)**:
    - `httpx.AsyncClient` を使用した `AsyncScanner` クラス。
    - ページを取得し `BeautifulSoup` でリンクを抽出するメソッド。
    - HTML以外のコンテンツタイプを無視する処理。
- [ ] **クローラー (`core/crawler.py`)**:
    - `asyncio.Queue` を使用した `AsyncCrawler` クラス。
    - 訪問済みURLの `set` 管理。
    - セマフォによる並列数制御。
    - 再帰深度のトラッキング。
    - URLフィルタリング（前方一致、正規表現）。

## フェーズ 3: CLI と出力
- [ ] **リポーター (`core/reporter.py`)**:
    - テキスト、JSON、CSV形式への整形。
    - フラット出力とグループ化出力のサポート。
- [ ] **CLI エントリポイント (`cli/main.py`)**:
    - すべてのオプションを備えた `click` コマンドの定義。
    - `--output` 未指定時の標準出力処理。
    - ログ出力や進捗表示（Richなど）の設定。

## フェーズ 4: 統合とテスト
- [ ] `src/page_tree/__init__.py` を更新し、`page_tree.cli.main.main` を呼び出すように設定。
- [ ] **テストスイートの作成**:
    - フィルタリングと正規化のユニットテスト。
    - スキャナーとクローラーのHTTPモックテスト。
    - ローカルWebサーバーを用いた統合テスト。

## 検証ステップ
1. [ ] `pytest` で全テストを実行。
2. [ ] 既知のサイト（ローカルのドキュメントサーバーなど）に対して手動テスト。
3. [ ] 特定のDisallowルールを持つサイトに対して `robots.txt` の遵守を確認。
4. [ ] 並列数と深度制限が正しく機能することを確認。
