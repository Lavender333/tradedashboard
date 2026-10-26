"""Stop publication if builders failed, even when they retained an old snapshot."""
from datetime import datetime, timezone
import json
from pathlib import Path


def check(directory=Path('data')):
    now = datetime.now(timezone.utc)
    for name in ('snapshot.json', 'template-snapshot.json', 'market-quotes.json'):
        payload = json.loads((directory / name).read_text())
        if payload.get('error') or payload.get('refresh_error'):
            raise RuntimeError(f'{name}: data refresh failed')
        generated = datetime.fromisoformat(payload['generated_at'].replace(' UTC', '+00:00').replace('Z', '+00:00'))
        age = (now - generated).total_seconds()
        if not -60 <= age <= 1800:
            raise RuntimeError(f'{name}: publication timestamp is not current')
        if name != 'snapshot.json':
            for instrument in ('ES', 'ZB'):
                item = payload['instruments'][instrument]
                if not isinstance(item.get('last'), (float, int)) or item['last'] <= 0:
                    raise RuntimeError(f'{name}: {instrument} has no price')
    print('All three market data files are ready to publish.')


if __name__ == '__main__':
    check()
