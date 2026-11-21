"""Generate a standalone comparison from two live AUREN /risk responses."""
import argparse
import json
import math
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen

API = "https://auren-api-8yrq.onrender.com/risk"
METRICS = [
    ("Largest position", ("concentration", "top_weight"), "share"),
    ("Effective assets", ("concentration", "effective_assets"), "number"),
    ("Volatility", ("volatility",), "share"),
    ("Max drawdown", ("max_drawdown",), "share"),
    ("AUREN score", ("score",), "number"),
]


def snapshot(share):
    weights = {"BTC-USD": share, "ETH-USD": 100 - share}
    body = {"weights": weights}
    req = Request(API, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urlopen(req, timeout=60) as response:
        result = json.load(response)
    if not isinstance(result, dict) or not isinstance(result.get("concentration"), dict):
        raise ValueError("Unexpected risk response")
    return {"request": body, "received_utc": datetime.now(timezone.utc).isoformat(),
            "response": result}


def value(record, path):
    field = record["response"]
    for key in path:
        field = field.get(key) if isinstance(field, dict) else None
    return field if type(field) in (float, int) and math.isfinite(field) else None


def render(records):
    rows = []
    for label, path, unit in METRICS:
        a, b = (value(r, path) for r in records)
        def show(x):
            if x is None:
                return "Unavailable"
            return f"{x:.1%}" if unit == "share" else f"{x:.2f}"
        delta = "Unavailable" if a is None or b is None else (
            f"{100*(b-a):+.1f} pp" if unit == "share" else f"{b-a:+.2f}")
        rows.append(f"<tr><th scope=row>{label}</th><td>{show(a)}</td><td>{show(b)}</td><td>{delta}</td></tr>")
    names = []
    for r in records:
        w = r["request"]["weights"]
        names.append(f'{w["BTC-USD"]}/{w["ETH-USD"]}')
    return f"""<!doctype html><html lang=en><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Weight Lens | BTC and ETH</title>
<style>*{{box-sizing:border-box}}body{{font:16px/1.55 system-ui;color:#132923;background:#f6faf8;margin:0}}
main{{max-width:790px;margin:auto;padding:8vh 18px}}h1{{font-size:2.7rem;margin:0}}
header{{border-top:5px solid #167259;padding-top:20px}}small{{color:#495956}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}td,th{{padding:12px 6px;text-align:right;border-bottom:1px solid #ccd9d4}}
th:first-child{{text-align:left}}thead{{background:#133d32;color:white}}a{{color:#086246}}
@media(max-width:480px){{td,th{{font-size:13px;padding:8px 3px}}}}</style>
<main><header><small>AUREN / PUBLIC API STUDY</small><h1>Weight Lens</h1>
<p>Same two assets, different weights. Compare synthetic BTC/ETH portfolios on the same API, side by side.</p></header>
<table><thead><tr><th>Risk metric</th><th>{names[0]}</th><th>{names[1]}</th><th>Change</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<p>Change is the second result minus the first; pp means percentage points. A less negative drawdown is a smaller historical loss. More balanced weights alone do not guarantee lower volatility.</p>
<p><a href="evidence.json">Inspect both requests and responses</a></p>
<small>Snapshot: {escape(records[-1]["received_utc"])}. Separate sequential calls, not an atomic market snapshot. Analytics only; no trades.</small></main></html>"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--btc", nargs=2, type=int, default=[80, 50], metavar=("BASE", "COMPARE"))
    p.add_argument("--out", type=Path, default=Path("docs"))
    args = p.parse_args()
    if not all(0 < n < 100 for n in args.btc):
        p.error("BTC shares must be integers between 1 and 99")
    records = [snapshot(n) for n in args.btc]
    report = render(records)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "index.html").write_text(report, encoding="utf-8")
    (args.out / "evidence.json").write_text(json.dumps({"endpoint": API, "calls": records}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        sys.exit(f"Report not generated: {exc}")
