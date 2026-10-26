import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from snapshot_io import atomic_write, preserve_on_error
from run_dashboard import app


class DashboardTests(unittest.TestCase):
    def test_all_page_assets_resolve(self):
        from html.parser import HTMLParser
        class Links(HTMLParser):
            links = None
            def handle_starttag(self, tag, attrs):
                for key, value in attrs:
                    if key in ('src', 'href') and value and not value.startswith(('http', '#', 'data:')):
                        self.links.append(value)
        client = app.test_client()
        for name in ('index.html', 'mes-dashboard.html', 'trade-board.html', 'trading-template.html', 'trading-template-es.html', 'trading-template-zb.html'):
            response = client.get('/' + name)
            self.assertEqual(response.status_code, 200)
            parser = Links(); parser.links = []; parser.feed(response.text)
            response.close()
            for link in parser.links:
                with client.get('/' + link) as asset:
                    self.assertEqual(asset.status_code, 200, link)
        self.assertEqual(client.get('/requirements.txt').status_code, 404)
        self.assertEqual(client.get('/data/../requirements.txt').status_code, 404)

    def test_api_success_and_feed_failure(self):
        client = app.test_client()
        with patch('lavender_dashboard.get_snapshot', return_value={'last_close': 123}):
            self.assertEqual(client.get('/api/snapshot').json['last_close'], 123)
        with patch('lavender_dashboard.get_snapshot', side_effect=RuntimeError('feed unavailable')):
            response = client.get('/api/snapshot')
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json['error'], 'feed unavailable')

    def test_failed_refresh_preserves_original_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            atomic_write(path, json.dumps({'generated_at': 'old', 'last_close': 123}))
            result = preserve_on_error(path, {'generated_at': 'new', 'error': 'feed unavailable'})
            self.assertEqual(result['generated_at'], 'old')
            self.assertEqual(result['last_refresh_attempt'], 'new')
            self.assertEqual(result['last_close'], 123)
            self.assertEqual(result['refresh_error'], 'feed unavailable')

    def test_databento_continuous_symbols(self):
        import mes_levels
        from datetime import datetime, timezone
        from unittest.mock import MagicMock
        import pandas as pd
        fake = MagicMock()
        fake.timeseries.get_range.return_value.to_df.return_value = pd.DataFrame({
            'ts_event': [datetime.now(timezone.utc)], 'open': [100.], 'high': [101.],
            'low': [99.], 'close': [100.], 'volume': [10]})
        with patch.dict('os.environ', {'DATABENTO_API_KEY': 'test'}), patch('databento.Historical', return_value=fake):
            mes_levels.fetch_databento_candles()
            self.assertEqual(fake.timeseries.get_range.call_args.kwargs['stype_in'], 'continuous')

if __name__ == '__main__':
    unittest.main()

class QuoteFeedTests(unittest.TestCase):
    def test_quote_timestamp_and_delayed_label(self):
        from quote_feed import fetch_quote
        response = unittest.mock.Mock()
        response.json.return_value = {'chart': {'result': [{'meta': {
            'regularMarketPrice': 123, 'regularMarketTime': 1700000000}}]}}
        with patch('quote_feed.requests.get', return_value=response):
            name, quote = fetch_quote('ES')
        self.assertEqual(name, 'ES')
        self.assertEqual(quote['last'], 123)
        self.assertTrue(quote['delayed'])
        self.assertEqual(quote['quote_time'], '2023-11-14T22:13:20+00:00')

    def test_quote_failure_is_not_reported_as_success(self):
        with patch('run_dashboard.market_quotes', side_effect=ValueError('upstream failed')):
            response = app.test_client().get('/api/market-quotes')
        self.assertEqual(response.status_code, 503)
        self.assertIn('retained', response.json['error'])
