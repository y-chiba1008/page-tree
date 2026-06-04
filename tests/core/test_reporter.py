import json
from page_tree.core.models import CrawlResult
from page_tree.core.reporter import Reporter


def test_reporter_to_text_flat() -> None:
    results = [
        CrawlResult(url='http://example.com/a', found_at='http://example.com/', status_code=200),
        CrawlResult(url='http://example.com/b', found_at='http://example.com/', status_code=200),
        CrawlResult(url='http://example.com/a', found_at='http://example.com/page1', status_code=200),
    ]
    reporter = Reporter(results)
    text = reporter.to_text(grouped=False)
    
    # 重複が排除され、ソートされていること
    assert text == 'http://example.com/a\nhttp://example.com/b'


def test_reporter_to_text_grouped() -> None:
    results = [
        CrawlResult(url='http://example.com/a', found_at='http://example.com/', status_code=200),
        CrawlResult(url='http://example.com/b', found_at='http://example.com/', status_code=200),
        CrawlResult(url='http://example.com/a', found_at='http://example.com/page1', status_code=200),
    ]
    reporter = Reporter(results)
    text = reporter.to_text(grouped=True)
    
    assert 'Source: http://example.com/' in text
    assert '  - http://example.com/a' in text
    assert '  - http://example.com/b' in text
    assert 'Source: http://example.com/page1' in text


def test_reporter_to_json_flat() -> None:
    results = [
        CrawlResult(url='http://example.com/a', found_at='http://example.com/', status_code=200),
    ]
    reporter = Reporter(results)
    data = json.loads(reporter.to_json(grouped=False))
    
    assert len(data) == 1
    assert data[0]['url'] == 'http://example.com/a'


def test_reporter_to_json_grouped() -> None:
    results = [
        CrawlResult(url='http://example.com/a', found_at='http://example.com/', status_code=200),
        CrawlResult(url='http://example.com/a', found_at='http://example.com/page1', status_code=200),
    ]
    reporter = Reporter(results)
    data = json.loads(reporter.to_json(grouped=True))
    
    assert len(data) == 2
    assert data[0]['source'] == 'http://example.com/'
    assert data[0]['links'] == ['http://example.com/a']


def test_reporter_to_csv() -> None:
    results = [
        CrawlResult(url='http://example.com/a', found_at='http://example.com/', status_code=200),
    ]
    reporter = Reporter(results)
    csv_text = reporter.to_csv()
    
    assert 'url,found_at,status_code,error' in csv_text
    assert 'http://example.com/a,http://example.com/,200,' in csv_text
