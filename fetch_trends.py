"""Fetch Google Trends "Trending Now" queries (Taiwan) from SerpApi.

Run manually:  conda activate trends && python fetch_trends.py
               (or double-click run_fetch.bat on Windows)
Scheduled:     Windows Task Scheduler, daily at 06:00 (see install_task.bat).
Reads the API key from config.json next to this script.

Outputs:
  data/trends_YYYY-MM-DD.json  - permanent daily archive
  data/latest.json             - always the newest fetch (watched by TouchDesigner)
  logs/fetch.log               - run log

Each entry in "trends" is an object:
  { "query": str, "search_volume": int, "categories": [str], "trend_breakdown": [str] }
"""

import json
import logging
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

SERPAPI_URL = "https://serpapi.com/search.json"
GEO = "TW"
HOURS = 24          # lookback window: 4, 24, 48, or 168
TIMEOUT_SECONDS = 60


def setup_logging() -> None:
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "fetch.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_api_key() -> str:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        key = json.load(f)["serpapi_api_key"].strip()
    if not key or key == "PASTE_YOUR_KEY_HERE":
        raise ValueError("Set serpapi_api_key in config.json")
    return key


def fetch_trends(api_key: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "engine": "google_trends_trending_now",
        "geo": GEO,
        "hours": HOURS,
        "api_key": api_key,
    })
    with urllib.request.urlopen(f"{SERPAPI_URL}?{params}", timeout=TIMEOUT_SECONDS) as resp:
        payload = json.load(resp)
    if payload.get("error"):
        raise RuntimeError(f"SerpApi error: {payload['error']}")
    return [
        {
            "query": item["query"],
            "search_volume": item.get("search_volume"),
            "categories": [c["name"] for c in item.get("categories", [])],
            "trend_breakdown": item.get("trend_breakdown", []),
        }
        for item in payload.get("trending_searches", [])
    ]


def save(trends: list[dict]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).astimezone()
    doc = {
        "fetched_at": now.isoformat(timespec="seconds"),
        "geo": GEO,
        "count": len(trends),
        "trends": trends,
    }
    text = json.dumps(doc, ensure_ascii=False, indent=2)
    daily_path = DATA_DIR / f"trends_{now:%Y-%m-%d}.json"
    daily_path.write_text(text, encoding="utf-8")
    (DATA_DIR / "latest.json").write_text(text, encoding="utf-8")
    logging.info("Saved %d trends to %s and latest.json", len(trends), daily_path.name)


def main() -> int:
    setup_logging()
    try:
        trends = fetch_trends(load_api_key())
        save(trends)
        return 0
    except Exception:
        # Previous latest.json is left intact on any failure.
        logging.exception("Fetch failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
