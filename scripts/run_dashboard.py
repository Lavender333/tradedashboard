"""Serve every dashboard page and refresh published data every fifteen minutes."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from flask import abort, jsonify, send_from_directory
from quote_feed import market_quotes
from lavender_dashboard import app

app.view_functions['index'] = lambda: send_from_directory(ROOT, 'index.html', max_age=0)

PAGES = {'index.html', 'trading-template.html', 'trading-template-es.html',
         'trading-template-zb.html', 'market-selector.js', 'market-data-client.js', 'mes-dashboard.html', 'trade-board.html'}

@app.route('/<name>')
def page(name):
    if name not in PAGES:
        abort(404)
    return send_from_directory(ROOT, name, max_age=0)

@app.route('/assets/<path:name>')
def assets(name):
    return send_from_directory(ROOT / 'assets', name)

@app.route('/data/<name>')
def data(name):
    if not name.endswith(('.json', '.js')):
        abort(404)
    response = send_from_directory(ROOT / 'data', name, max_age=0)
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/api/market-quotes')
def quotes():
    try:
        response = jsonify(market_quotes())
    except Exception:
        response = jsonify({'error': 'Yahoo quotes unavailable; published calculation data retained'})
        response.status_code = 503
    response.headers['Cache-Control'] = 'no-store'
    return response


def refresh_forever():
    while True:
        for script in ('build_pages_snapshot.py', 'build_template_snapshot.py'):
            try:
                subprocess.run([sys.executable, str(ROOT / 'scripts' / script)], cwd=ROOT,
                               check=True, timeout=300)
            except (subprocess.SubprocessError, OSError) as exc:
                app.logger.error('Snapshot update failed: %s', exc)
        time.sleep(900)

if __name__ == '__main__':
    threading.Thread(target=refresh_forever, daemon=True).start()
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '8000')), debug=False)
