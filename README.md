# Daily Google Trends to TouchDesigner

Fetches Taiwan's Google Trends "Trending Now" queries (~150–200 strings) from
SerpApi every day at 06:00, stores them as JSON, and displays them in
TouchDesigner.

```
Windows Task Scheduler (06:00 daily)
        │
        ▼
fetch_trends.py ──► SerpApi (engine=google_trends_trending_now, geo=TW)
        │
        ├──► data/trends_YYYY-MM-DD.json   (permanent daily archive)
        └──► data/latest.json              (watched by TouchDesigner)
                        │
                        ▼
        TouchDesigner: trends_loader script ─► Table DAT ─► Text TOP
```

## Requirements

- Windows 10/11
- Python 3.9+ on PATH (standard library only, no pip installs)
- A [SerpApi](https://serpapi.com/) API key
- TouchDesigner

## Setup

1. Copy `config.example.json` to `config.json` and paste your SerpApi key:

   ```json
   { "serpapi_api_key": "your_real_key" }
   ```

   `config.json` is git-ignored, so the key never gets committed.

2. Test the fetcher manually:

   ```
   python fetch_trends.py
   ```

   On success it creates `data/latest.json` and `data/trends_YYYY-MM-DD.json`,
   and logs to `logs/fetch.log`. On failure it logs the error and leaves the
   previous `latest.json` untouched.

3. Register the daily 06:00 task by double-clicking `install_task.bat`
   (or running it in a terminal). It also enables "run as soon as possible
   after a missed start", so the fetch still happens if the PC was off or
   asleep at 06:00.

   Verify: `schtasks /Query /TN "TrendsFetch"`
   Remove:  `schtasks /Delete /TN "TrendsFetch" /F`

## Output format

`data/latest.json` (and each daily archive) looks like:

```json
{
  "fetched_at": "2026-09-09T06:00:04+08:00",
  "geo": "TW",
  "count": 159,
  "trends": [
    {
      "query": "trend string",
      "search_volume": 20000,
      "categories": ["Entertainment"],
      "trend_breakdown": ["related query 1", "related query 2"]
    }
  ]
}
```

Notes: `search_volume` is a rough bucket (e.g. 20K+, 50K+), not an exact
number; `categories` and `trend_breakdown` may be empty for some trends.

To change the region or lookback window, edit `GEO` / `HOURS` at the top of
`fetch_trends.py` (`hours` accepts 4, 24, 48, or 168).

## Virtual room ("The screen going on and off")

`td/build_virtual_room.py` builds the whole installation network
programmatically (a virtual room with a floor screen that pulses on/off,
showing one trending query at a time, and a light that brightens the room
with each pulse).

1. Open TouchDesigner, then the Textport (Alt+T).
2. Run (adjust the path):

   ```python
   exec(open(r"C:\path\to\td\build_virtual_room.py", encoding="utf-8").read())
   ```

3. It creates `/project1/virtual_room` with sample trends. To load the real
   daily data, paste `td/trends_loader.py` into a Text DAT **inside**
   `/project1/virtual_room` (so it finds `trends_table` next to it), edit its
   `LATEST_JSON` path, and run it — plus the Timer CHOP described below for
   daily refresh.
4. Fullscreen `/project1/virtual_room/OUT` on the real screen via a Window COMP.

Tunables at the top of the script: room dimensions (`ROOM_W/H/D`), screen
size, and `PULSE_PERIOD` (seconds per on/off cycle). The network is safe to
rebuild: re-running the script replaces `/project1/virtual_room`.

## TouchDesigner wiring

Build this small network once in your project:

1. **Text DAT** named `trends_loader` — paste the contents of
   `td/trends_loader.py` into it, then edit the `LATEST_JSON` path at the top
   to the absolute path of `data\latest.json` on this machine.
2. **Table DAT** named `trends_table` — the script fills it with one row per
   trend, columns `query`, `search_volume`, `categories`, `trend_breakdown`
   (multiple values joined with `; `). Use this table to drive whatever visual
   you want: text instancing, particles, sizing by search volume, etc.
3. **Text TOP** named `trends_text` — the script writes all trend queries into
   it (newline-separated) for an immediate visible display. Increase the TOP
   resolution and font size to taste.
4. **Timer CHOP** named `timer1` — set Length to 60 seconds, turn on Loop,
   and click Start. In its callbacks DAT add:

   ```python
   def onDone(timerOp, segment, interrupt):
       op('trends_loader').run()
       return
   ```

   This re-reads `latest.json` every 60 seconds, so the display updates by
   itself after each morning's fetch. You can also run
   `op('trends_loader').run()` once manually (right-click the Text DAT >
   Run Script) to load immediately.

The loader is safe to run repeatedly: if the JSON file is missing or being
written at that moment, it keeps the previous contents on screen.

## Files

| File | Purpose |
| --- | --- |
| `fetch_trends.py` | Daily fetcher (SerpApi -> JSON) |
| `config.example.json` | Template for `config.json` (API key) |
| `install_task.bat` | Registers the 06:00 Windows scheduled task |
| `td/trends_loader.py` | Script to paste into a TouchDesigner Text DAT |
| `data/` | Generated JSON (git-ignored) |
| `logs/fetch.log` | Fetch log (git-ignored) |
