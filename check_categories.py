#!/usr/bin/env python3
"""
Kontrola nových kategorií po importu produktů.

Použití:
  python3 check_categories.py snapshot   # Uloží aktuální stav kategorií
  python3 check_categories.py check      # Porovná feed se snapshotem
"""

import argparse
import json
import os
import sys
from datetime import datetime

import requests
from lxml import etree

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

FEED_URL = (
    "https://www.celiakshop.sk/export/categories.xml"
    "?partnerId=3&patternId=-31"
    "&hash=d52ef530583656c220f639affe3ac0ecf34341538327595ea93017441c44bdf1"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_DIR = os.path.join(SCRIPT_DIR, "snapshots")
LATEST_SNAPSHOT = os.path.join(SNAPSHOT_DIR, "latest.json")


def _color(text, color):
    if HAS_COLOR:
        return f"{color}{text}{Style.RESET_ALL}"
    return text


def ok(text):
    return _color(text, Fore.GREEN)


def err(text):
    return _color(text, Fore.RED)


def warn(text):
    return _color(text, Fore.YELLOW)


def bold(text):
    if HAS_COLOR:
        return f"{Style.BRIGHT}{text}{Style.RESET_ALL}"
    return text


def fetch_categories(url: str) -> dict:
    """Stáhne XML feed a vrátí dict {id: {id, parent_id, title, index_name, visible}}."""
    print(f"Stahuji feed: {url[:60]}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(err(f"Chyba při stahování feedu: {e}"), file=sys.stderr)
        sys.exit(1)

    try:
        root = etree.fromstring(response.content)
    except etree.XMLSyntaxError as e:
        print(err(f"Chyba při parsování XML: {e}"), file=sys.stderr)
        sys.exit(1)

    categories = {}
    for cat in root.findall("CATEGORY"):
        cat_id = cat.findtext("ID", "").strip()
        if not cat_id:
            continue
        categories[cat_id] = {
            "id": cat_id,
            "parent_id": cat.findtext("PARENT_ID", "").strip(),
            "title": cat.findtext("TITLE", "").strip(),
            "index_name": cat.findtext("INDEX_NAME", "").strip(),
            "visible": cat.findtext("VISIBLE", "").strip(),
        }

    print(f"Načteno {len(categories)} kategorií.")
    return categories


def save_snapshot(categories: dict):
    """Uloží snapshot do latest.json a do zálohy s časovým razítkem."""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_path = os.path.join(SNAPSHOT_DIR, f"snapshot_{timestamp}.json")

    payload = {
        "timestamp": timestamp,
        "count": len(categories),
        "categories": categories,
    }

    with open(LATEST_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(ok(f"✓ Snapshot uložen: {LATEST_SNAPSHOT}"))
    print(f"  Záloha:           {backup_path}")
    print(f"  Kategorií:        {len(categories)}")


def load_snapshot() -> dict:
    """Načte poslední snapshot. Ukončí program, pokud neexistuje."""
    if not os.path.exists(LATEST_SNAPSHOT):
        print(err("Snapshot nenalezen. Nejdřív spusť: python3 check_categories.py snapshot"), file=sys.stderr)
        sys.exit(1)

    with open(LATEST_SNAPSHOT, encoding="utf-8") as f:
        payload = json.load(f)

    print(f"Snapshot z: {payload.get('timestamp', '?')} ({payload.get('count', '?')} kategorií)")
    return payload["categories"]


def compare(before: dict, after: dict, verbose: bool = False):
    """Porovná dva snapshoty a vypíše rozdíly."""
    before_ids = set(before.keys())
    after_ids = set(after.keys())

    added = after_ids - before_ids
    removed = before_ids - after_ids

    print()
    print(bold("=" * 50))
    print(bold("VÝSLEDEK KONTROLY"))
    print(bold("=" * 50))

    if not added and not removed:
        print(ok("✅ OK – žádné nové ani smazané kategorie."))
    else:
        if added:
            print(warn(f"\n⚠️  NOVÉ KATEGORIE ({len(added)}):"))
            for cat_id in sorted(added, key=int):
                cat = after[cat_id]
                parent_title = before.get(cat["parent_id"], after.get(cat["parent_id"], {})).get("title", cat["parent_id"])
                visible = "viditelná" if cat["visible"] == "1" else "skrytá"
                print(f"  {ok('+')} ID {cat_id:>6}  {bold(cat['title'])}  (parent: {parent_title}, {visible})")

        if removed:
            print(warn(f"\n⚠️  SMAZANÉ KATEGORIE ({len(removed)}):"))
            for cat_id in sorted(removed, key=int):
                cat = before[cat_id]
                print(f"  {err('-')} ID {cat_id:>6}  {bold(cat['title'])}")

    if verbose:
        print(f"\n{bold('Všechny kategorie po importu')} ({len(after)}):")
        for cat_id in sorted(after.keys(), key=int):
            cat = after[cat_id]
            marker = ok("  + ") if cat_id in added else "    "
            print(f"{marker}ID {cat_id:>6}  {cat['title']}")


def cmd_snapshot():
    categories = fetch_categories(FEED_URL)
    save_snapshot(categories)


def cmd_check(verbose: bool = False):
    before = load_snapshot()
    after = fetch_categories(FEED_URL)
    compare(before, after, verbose=verbose)


def main():
    parser = argparse.ArgumentParser(
        description="Kontrola nových kategorií po importu produktů."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("snapshot", help="Uloží aktuální stav kategorií")

    check_parser = subparsers.add_parser("check", help="Porovná feed se snapshotem")
    check_parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Zobrazí i seznam všech kategorií"
    )

    args = parser.parse_args()

    if args.command == "snapshot":
        cmd_snapshot()
    elif args.command == "check":
        cmd_check(verbose=args.verbose)


if __name__ == "__main__":
    main()
