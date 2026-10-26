"""Atomic publishing keeps browsers from reading a half-written snapshot."""
import json
import os
from pathlib import Path
import tempfile


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as file:
        temp = Path(file.name)
        file.write(text)
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def preserve_on_error(path, payload):
    """Keep the true time of the last usable data, recording the failed update."""
    if payload.get('error') and Path(path).exists():
        try:
            previous = json.loads(Path(path).read_text())
            if not previous.get('error'):
                previous['refresh_error'] = payload['error']
                previous['last_refresh_attempt'] = payload['generated_at']
                return previous
        except (ValueError, OSError):
            pass
    return payload
