# action-item-extractor

**Turn a folder of meeting notes into one to-do list per person: checkbox tasks, `TODO:` and
`ACTION:` lines, `@owner` mentions and due dates like "by Friday" or "before 15 March".**

Part of the *Research Automation Toolkit*: 100 open tools for daily research work.

## Why

Lab meetings, supervision sessions and collaboration calls produce action items that live in
scattered notes and are forgotten by next week. Collecting them automatically, with owners and due
dates, makes follow-up the default and gives every meeting a quick "what did we promise?" review.

## Features

- Recognizes `- [ ] task`, `- [x] done`, `TODO:`, `ACTION:`, `AI:`, `TASK:`, `FOLLOW-UP:` lines
- Owners from `@mentions` (several allowed) or phrases like "Carla will ..."
- Due dates: ISO dates, "15 March", "Mar 15", weekdays, "next Monday", "tomorrow", "end of week/month",
  "in 2 weeks" (relative to today)
- Status: open, due soon, overdue, done; grouped by owner, section or source file
- Markdown or CSV output; filters `--open` and `--owner`; many files and globs at once

## Usage

```bash
pip install .
action-item-extractor "meetings/2026-*.md" --open
action-item-extractor notes.md --owner ana -f csv -o ana_tasks.csv
action-item-extractor meetings/*.md --group-by source
```

## Testing

```bash
python -m unittest discover -s tests -t .
```

## License

MIT (c) JANIN A APURBA
