"""Build the static JSON snapshot used by GitHub Pages."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mes_levels import get_snapshot


OUTPUT = Path("data/snapshot.json")


def main() -> None:
    """Write a snapshot payload; keep Pages usable even when the feed is not ready."""
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    try:
        payload = get_snapshot()
        payload["generated_at"] = generated_at
    except Exception as exc:
        payload = {
            "error": str(exc),
            "generated_at": generated_at,
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
