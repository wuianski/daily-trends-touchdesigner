"""TouchDesigner loader for the daily Google Trends JSON.

How to use inside TouchDesigner (see README.md for full wiring steps):
  1. Paste this whole script into a Text DAT named 'trends_loader'.
  2. Edit LATEST_JSON below to the absolute path of data/latest.json.
  3. Create a Table DAT named 'trends_table' and a Text TOP named 'trends_text'.
  4. Trigger op('trends_loader').run() periodically (e.g. Timer CHOP callback)
     to re-read the file. Running it once on project start also works.

The script is safe to run repeatedly: if the JSON file is missing or
mid-write, it leaves the previous table/text contents unchanged.
"""

import json

# --- EDIT THIS PATH (absolute path to data/latest.json on the Windows machine)
LATEST_JSON = r"C:\path\to\code\data\latest.json"

TABLE_DAT = 'trends_table'   # one row per trend, columns: query / search_volume / categories / trend_breakdown
TEXT_TOP = 'trends_text'     # simple visible display of all trend queries


def load_trends():
    print('trends_loader: LATEST_JSON =', LATEST_JSON)
    try:
        with open(LATEST_JSON, encoding='utf-8') as f:
            doc = json.load(f)
        trends = doc.get('trends', [])
        print('trends_loader: file OK, count={}, fetched_at={}'.format(
            len(trends), doc.get('fetched_at', '')))
        if trends:
            first = trends[0]
            print('trends_loader: first query =', first.get('query') if isinstance(first, dict) else first)
        return trends, doc.get('fetched_at', '')
    except Exception as e:
        print('trends_loader: could not read {}: {}'.format(LATEST_JSON, e))
        return None, None


def update_ops(trends, fetched_at):
    table = op(TABLE_DAT)
    if table is None:
        print('trends_loader: missing DAT', TABLE_DAT, '- put this script inside /project1/virtual_room')
        return
    table.clear()
    table.appendRow(['query', 'search_volume', 'categories', 'trend_breakdown'])
    for t in trends:
        if isinstance(t, dict):
            table.appendRow([
                t.get('query', ''),
                t.get('search_volume') or 0,
                '; '.join(t.get('categories', [])),
                '; '.join(t.get('trend_breakdown', [])),
            ])
        else:
            table.appendRow([str(t), 0, '', ''])
    print('trends_loader: {} now has {} data rows (plus header)'.format(
        table.path, table.numRows - 1))

    text_top = op(TEXT_TOP)
    if text_top is not None:
        text_top.par.text = '\n'.join(
            (t.get('query', '') if isinstance(t, dict) else str(t)) for t in trends
        )


trends, fetched_at = load_trends()
if trends is not None:
    update_ops(trends, fetched_at)
