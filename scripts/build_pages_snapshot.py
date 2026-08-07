"""Build the static JSON snapshot used by GitHub Pages."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


OUTPUT = Path("data/snapshot.json")


def main() -> None:
    """Write a snapshot payload; keep Pages usable even when the feed is not ready."""
    if not os.environ.get("DATABENTO_API_KEY"):
        os.environ.setdefault("MES_DATA_PROVIDER", "yahoo")

    from mes_levels import get_snapshot

    generated_at_dt = datetime.now(timezone.utc)
    generated_at = generated_at_dt.strftime("%Y-%m-%d %H:%M UTC")
    generated_at_iso = generated_at_dt.isoformat()
    try:
        payload = get_snapshot()
        payload["generated_at"] = generated_at
        payload["generated_at_iso"] = generated_at_iso
    except Exception as exc:
        payload = {
            "error": str(exc),
            "generated_at": generated_at,
            "generated_at_iso": generated_at_iso,
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
