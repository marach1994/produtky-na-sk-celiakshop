#!/usr/bin/env python3
"""
Zkontroluje CZ feed a pokud najde produkty se sezónní defaultCategory
(Vánoce / Velikonoce / Prázdniny), napíše alert do Freelo úkolu 30581159.

Použití:
  python3 check_seasonal.py          # stáhne feed z URL
  python3 check_seasonal.py feed.csv # zpracuje lokální soubor
"""

import csv
import ssl
import sys
import urllib.request
import urllib.error
from io import StringIO

SOURCE_URL = (
    "https://www.celiakshop.cz/export/products.csv"
    "?patternId=61&partnerId=3"
    "&hash=95ecec03380b553c399e5a1b4a7e17d1598be40e1649a612d4cb1777adfc6429"
)

FREELO_TASK_ID = 30581159
FREELO_USER    = os.environ.get("FREELO_USER", "adamkelbl0@gmail.com")
FREELO_TOKEN   = os.environ.get("FREELO_TOKEN", "")

SEASONAL_KEYWORDS = ["Vánoce", "Velikonoce", "Prázdniny"]


def fetch_url(url: str) -> bytes:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(url, context=ctx) as resp:
        return resp.read()


def find_seasonal_products(content: str) -> list[dict]:
    reader = csv.DictReader(StringIO(content), delimiter=";")
    hits = []
    for row in reader:
        category = row.get("defaultCategory", "")
        if any(kw.lower() in category.lower() for kw in SEASONAL_KEYWORDS):
            hits.append({"code": row.get("code", ""), "name": row.get("name", ""), "category": category})
    return hits


def post_freelo_comment(message: str) -> None:
    import json
    import base64

    url = f"https://api.freelo.io/v1/task/{FREELO_TASK_ID}/comments"
    credentials = base64.b64encode(f"{FREELO_USER}:{FREELO_TOKEN}".encode()).decode()
    body = json.dumps({"content": message}).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("Content-Type", "application/json")

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, context=ctx) as resp:
        resp.read()


def build_message(hits: list[dict]) -> str:
    lines = [
        f"⚠️ Sezónní kategorie ve feedu – {len(hits)} produktů",
        "",
        "Následující produkty mají jako defaultCategory sezónní kategorii:",
        "",
    ]
    for p in hits:
        lines.append(f"• {p['code']} — {p['name']} ({p['category']})")
    return "<br>".join(lines)


def main():
    if len(sys.argv) >= 2:
        with open(sys.argv[1], encoding="utf-8-sig") as f:
            content = f.read()
    else:
        print("Stahuji CZ feed...", file=sys.stderr)
        content = fetch_url(SOURCE_URL).decode("utf-8-sig")

    hits = find_seasonal_products(content)

    if not hits:
        print("OK – žádné sezónní kategorie nenalezeny.", file=sys.stderr)
        sys.exit(0)

    print(f"NALEZENO {len(hits)} produktů se sezónní kategorií:", file=sys.stderr)
    for p in hits:
        print(f"  {p['code']:<15} {p['category']}", file=sys.stderr)

    print("Posílám alert do Freelo...", file=sys.stderr)
    try:
        post_freelo_comment(build_message(hits))
        print("Alert odeslán.", file=sys.stderr)
    except urllib.error.URLError as e:
        print(f"Chyba při odesílání do Freelo: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
