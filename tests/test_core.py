import datetime as dt
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from action_item_extractor.cli import main
from action_item_extractor.core import extract, parse_due, render_csv, render_markdown

TODAY = dt.date(2026, 3, 4)     # a Wednesday
NOTES = """# Lab meeting 2026-03-04

## Paper
- [ ] @ana send revised Figure 2 to co-authors by Friday
- [x] @bo check reference list
- Discussion about reviewers, no decision.
TODO: Carla will book the confocal by 2026-03-02
- ACTION: renew ethics approval due end of month

## Grant
- [ ] @ana @dan draft budget before 15 March
"""


class DueTests(unittest.TestCase):
    def test_relative_and_absolute(self):
        self.assertEqual(parse_due("Friday", TODAY), dt.date(2026, 3, 6))
        self.assertEqual(parse_due("next Monday", TODAY), dt.date(2026, 3, 16))
        self.assertEqual(parse_due("tomorrow", TODAY), dt.date(2026, 3, 5))
        self.assertEqual(parse_due("15 March", TODAY), dt.date(2026, 3, 15))
        self.assertEqual(parse_due("Jan 10", TODAY), dt.date(2027, 1, 10))
        self.assertEqual(parse_due("end of month", TODAY), dt.date(2026, 3, 31))
        self.assertEqual(parse_due("in 2 weeks", TODAY), dt.date(2026, 3, 18))
        self.assertIsNone(parse_due("soonish", TODAY))


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.items = extract(NOTES, TODAY, "m.md")

    def test_found_items(self):
        self.assertEqual(len(self.items), 5)
        self.assertEqual([i["owner"] for i in self.items], ["ana", "bo", "Carla", "", "ana, dan"])
        self.assertEqual(self.items[1]["done"], True)
        self.assertEqual(self.items[4]["section"], "Grant")
        self.assertEqual(self.items[4]["due"], dt.date(2026, 3, 15))

    def test_rendering(self):
        md = render_markdown(self.items, TODAY)
        self.assertIn("## Carla", md)
        self.assertIn("**OVERDUE**", md)
        self.assertIn("## (unassigned)", md)
        csv_text = render_csv(self.items, TODAY)
        self.assertIn("ana,@ana send revised Figure 2 to co-authors by Friday,2026-03-06,due soon,Paper", csv_text)
        self.assertIn(",renew ethics approval due end of month,2026-03-31,open,Paper", csv_text)

    def test_cli_filters(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "meeting.md")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(NOTES)
            with redirect_stdout(io.StringIO()) as buf, redirect_stderr(io.StringIO()) as err:
                main([os.path.join(d, "*.md"), "--open", "--owner", "ana", "-f", "csv"], today=TODAY)
            self.assertEqual(len(buf.getvalue().strip().splitlines()), 3)
            self.assertIn("2 item(s), 0 overdue", err.getvalue())


if __name__ == "__main__":
    unittest.main()
