"""Recognizes checkbox tasks, 'TODO/ACTION:' lines, '@owner' mentions and natural-language due dates."""
import csv
import datetime as dt
import io
import re

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

_CHECK = re.compile(r"^\s*[-*+]\s+\[( |x|X)\]\s+(.*)$")
_MARKER = re.compile(r"^\s*(?:[-*+]\s+)?(?:\*\*)?(TODO|ACTION|AI|TASK|FOLLOW[- ]?UP)(?:\*\*)?\s*[:\-]\s*(.*)$", re.I)
_OWNER_AT = re.compile(r"@([A-Za-z][\w.-]*)")
_OWNER_PHRASE = re.compile(r"^([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s+(?:will|to|should|must)\s+", re.U)
_DUE = re.compile(r"\b(?:by|due|before|until|deadline:?)\s+([^,;.()]+?)(?=$|[,;.()]|\s+and\s)", re.I)


def parse_due(text, today):
    """'2026-03-15', '15 March', 'Mar 15', 'Friday', 'next week', 'tomorrow', 'end of month', 'EOD' -> date or None."""
    t = text.strip().lower()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t)
    if m:
        return dt.date(*map(int, m.groups()))
    if t in ("today", "eod", "end of day"):
        return today
    if t == "tomorrow":
        return today + dt.timedelta(days=1)
    if t in ("next week",):
        return today + dt.timedelta(days=7 - today.weekday())
    if t in ("end of week", "eow", "this week"):
        return today + dt.timedelta(days=(4 - today.weekday()) % 7)
    if t in ("end of month", "eom"):
        nxt = (today.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        return nxt - dt.timedelta(days=1)
    m = re.match(r"(?:next |this )?(%s)" % "|".join(WEEKDAYS), t)
    if m:
        delta = (WEEKDAYS.index(m.group(1)) - today.weekday()) % 7 or 7
        if t.startswith("next "):
            delta += 7 if delta < 7 else 0
        return today + dt.timedelta(days=delta)
    m = re.match(r"(\d{1,2})(?:st|nd|rd|th)?\s+([a-z]{3})[a-z]*", t) or re.match(r"([a-z]{3})[a-z]*\s+(\d{1,2})", t)
    if m:
        a, b = m.groups()
        day, mon = (int(a), b) if a.isdigit() else (int(b), a)
        if mon in MONTHS:
            d = dt.date(today.year, MONTHS[mon], day)
            return d if d >= today - dt.timedelta(days=30) else d.replace(year=today.year + 1)
    m = re.match(r"in (\d+) (day|week)s?", t)
    if m:
        return today + dt.timedelta(days=int(m.group(1)) * (7 if m.group(2) == "week" else 1))
    return None


def extract(markdown, today=None, source=""):
    """Return list of dicts: text, owner, due (date or None), done, section, line, source."""
    today = today or dt.date.today()
    items, section = [], ""
    for no, line in enumerate(markdown.splitlines(), 1):
        h = re.match(r"^#{1,6}\s+(.*)$", line)
        if h:
            section = h.group(1).strip()
            continue
        m = _CHECK.match(line)
        done = False
        if m:
            done, text = m.group(1).lower() == "x", m.group(2)
        else:
            m = _MARKER.match(line)
            if not m:
                continue
            text = m.group(2)
        text = text.strip()
        owners = _OWNER_AT.findall(text)
        if not owners:
            op = _OWNER_PHRASE.match(text)
            if op:
                owners = [op.group(1)]
        due = None
        dm = _DUE.search(text)
        if dm:
            due = parse_due(dm.group(1), today)
        items.append({"text": re.sub(r"\s+", " ", text), "owner": ", ".join(owners), "due": due, "done": done,
                      "section": section, "line": no, "source": source})
    return items


def _status(item, today):
    if item["done"]:
        return "done"
    if item["due"] and item["due"] < today:
        return "overdue"
    if item["due"] and (item["due"] - today).days <= 2:
        return "due soon"
    return "open"


def render_markdown(items, today=None, group_by="owner"):
    today = today or dt.date.today()
    groups = {}
    for it in items:
        groups.setdefault(it[group_by] or "(unassigned)", []).append(it)
    out = ["# Action items (%s)" % today.isoformat(), ""]
    for g in sorted(groups):
        out += ["## %s" % g, ""]
        for it in sorted(groups[g], key=lambda i: (i["done"], i["due"] or dt.date.max)):
            st = _status(it, today)
            out.append("- [%s] %s%s%s" % ("x" if it["done"] else " ", it["text"],
                                          " (due %s)" % it["due"].isoformat() if it["due"] else "",
                                          " **%s**" % st.upper() if st in ("overdue", "due soon") else ""))
        out.append("")
    return "\n".join(out)


def render_csv(items, today=None):
    today = today or dt.date.today()
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["owner", "task", "due", "status", "section", "source", "line"])
    for it in items:
        w.writerow([it["owner"], it["text"], it["due"].isoformat() if it["due"] else "", _status(it, today),
                    it["section"], it["source"], it["line"]])
    return buf.getvalue()
