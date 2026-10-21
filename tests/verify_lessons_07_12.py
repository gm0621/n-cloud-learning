#!/usr/bin/env python3
"""Focused structural contract for N-Cloud lessons 07–12."""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class LessonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.sections = 0
        self.quizzes = 0
        self.progress = 0
        self.links = []
        self.scripts = []
        self.captions = []
        self.table_headers = 0
        self.scoped_headers = 0
        self._caption = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get("id"):
            self.ids.append(data["id"])
        classes = str(data.get("class") or "").split()
        if tag == "section" and "lesson-section" in classes:
            self.sections += 1
        if data.get("data-quiz") is not None:
            self.quizzes += 1
        if data.get("data-progress") is not None:
            self.progress += 1
        if tag == "a" and data.get("href"):
            self.links.append(data["href"])
        if tag == "script" and data.get("src"):
            self.scripts.append(data["src"])
        if tag == "caption":
            self._caption = True
        if tag == "th":
            self.table_headers += 1
            if data.get("scope") == "col":
                self.scoped_headers += 1

    def handle_endtag(self, tag):
        if tag == "caption":
            self._caption = False

    def handle_data(self, data):
        if self._caption:
            self.captions.append(data.strip())


def verify_lesson(number: int):
    name = f"day{number:02d}"
    path = ROOT / name / "index.html"
    assert path.exists(), f"missing {path}"
    html = path.read_text(encoding="utf-8")
    parser = LessonParser()
    parser.feed(html)
    assert f'data-lesson="lesson{number:02d}"' in html
    assert f'data-lesson-name="第{number_zh(number)}課"' in html
    assert parser.sections >= 7, (name, parser.sections)
    assert parser.quizzes >= 2, (name, parser.quizzes)
    assert parser.progress == 3, (name, parser.progress)
    assert len(parser.ids) == len(set(parser.ids)), f"duplicate id in {name}"
    assert "../assets/lesson-practice.js" in parser.scripts
    assert any("教學模擬" in caption for caption in parser.captions), name
    assert parser.table_headers > 0, f"{name} missing table headers"
    assert parser.scoped_headers == parser.table_headers, f"{name} unscoped table header"
    assert "完成條件" in html and "排錯" in html and "詳解" in html
    assert f"../day{number-1:02d}/" in parser.links
    if number < 12:
        assert f"../day{number+1:02d}/" in parser.links
    for href in parser.links:
        if href.startswith("#"):
            assert href[1:] in parser.ids, (name, href)


def number_zh(number: int) -> str:
    words = {7: "七", 8: "八", 9: "九", 10: "十", 11: "十一", 12: "十二"}
    return words[number]


for lesson in range(7, 13):
    verify_lesson(lesson)

home = (ROOT / "index.html").read_text(encoding="utf-8")
for lesson in range(7, 13):
    assert f'href="day{lesson:02d}/"' in home, f"home missing day{lesson:02d} link"

day06 = (ROOT / "day06" / "index.html").read_text(encoding="utf-8")
assert 'href="../day07/"' in day06, "day06 must continue to day07"

day09 = (ROOT / "day09" / "index.html").read_text(encoding="utf-8")
assert "26 封信" not in day09, "day09 must not claim an unsupported exact notification count"

day12 = (ROOT / "day12" / "index.html").read_text(encoding="utf-8")
assert "18.4 GB" not in day12, "day12 traffic must remain physically possible on the stated 100 Mbps WAN"

js = (ROOT / "assets" / "lesson-practice.js").read_text(encoding="utf-8")
assert "function completionReady()" in js
assert "boxes.every(box=>box.checked)&&quizIds.every(id=>solved[id])&&notes.every(field=>field.value.trim())" in js
assert "revokeCompletionIfInvalid()" in js
assert "aria-valuenow" in js
assert not re.search(r"\bTODO\b", "\n".join((ROOT / f"day{n:02d}" / "index.html").read_text() for n in range(7, 13)))
print("LESSONS_07_12_CONTRACT_PASS lessons=6 min_sections=7 min_quizzes=2 progress=3")
