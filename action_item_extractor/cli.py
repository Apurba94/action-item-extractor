"""Command-line interface for action-item-extractor."""
import argparse
import datetime as dt
import glob
import os
import sys

from .core import extract, render_csv, render_markdown


def main(argv=None, today=None):
    ap = argparse.ArgumentParser(prog="action-item-extractor", description="Collect action items from meeting notes.")
    ap.add_argument("notes", nargs="+", help="Markdown files or globs (e.g. 'meetings/*.md')")
    ap.add_argument("-f", "--format", choices=["markdown", "csv"], default="markdown")
    ap.add_argument("--open", action="store_true", help="hide completed items")
    ap.add_argument("--owner", help="only items for this owner")
    ap.add_argument("--group-by", choices=["owner", "section", "source"], default="owner")
    ap.add_argument("-o", "--output")
    args = ap.parse_args(argv)
    today = today or dt.date.today()
    items = []
    for pat in args.notes:
        for p in sorted(glob.glob(pat)) or [pat]:
            with open(p, encoding="utf-8") as fh:
                items += extract(fh.read(), today, os.path.basename(p))
    if args.open:
        items = [i for i in items if not i["done"]]
    if args.owner:
        items = [i for i in items if args.owner.lower() in i["owner"].lower()]
    out = render_csv(items, today) if args.format == "csv" else render_markdown(items, today, args.group_by)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
    else:
        sys.stdout.write(out)
    overdue = sum(1 for i in items if not i["done"] and i["due"] and i["due"] < today)
    print("%d item(s), %d overdue" % (len(items), overdue), file=sys.stderr)
    return 0
