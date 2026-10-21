#!/usr/bin/env python3
"""Focused structural and safety contract for N-Cloud lessons 13–18."""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOPICS = {
    13: "LAB 安全、版本與角色權限",
    14: "系統資訊與設備樹",
    15: "事件查詢入門",
    16: "RAW DATA 與欄位",
    17: "IP 名稱解析與 CSV",
    18: "儲存查詢與欄位版面",
}
ZH = {13: "十三", 14: "十四", 15: "十五", 16: "十六", 17: "十七", 18: "十八"}


class LessonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.scripts, self.captions = [], [], [], []
        self.sections = self.quizzes = self.progress = 0
        self.table_headers = self.scoped_headers = 0
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
    assert f'data-lesson-name="第{ZH[number]}課"' in html
    assert TOPICS[number] in html, f"{name} missing canonical topic"
    assert parser.sections >= 7, (name, parser.sections)
    assert parser.quizzes >= 2, (name, parser.quizzes)
    assert parser.progress == 3, (name, parser.progress)
    assert len(parser.ids) == len(set(parser.ids)), f"duplicate id in {name}"
    assert "../assets/lesson-practice.js" in parser.scripts
    assert any("教學模擬" in caption for caption in parser.captions), name
    assert parser.table_headers > 0, f"{name} missing table headers"
    assert parser.scoped_headers == parser.table_headers, f"{name} unscoped table header"
    assert "完成條件" in html and "排錯" in html and "詳解" in html
    assert "不代表真實 N-Cloud" in html, f"{name} missing simulation boundary"
    assert any(gate in html for gate in ("G1", "G2", "G3")), f"{name} missing safety gate"
    assert f"../day{number-1:02d}/" in parser.links
    if number < 18:
        assert f"../day{number+1:02d}/" in parser.links
    for href in parser.links:
        if href.startswith("#"):
            assert href[1:] in parser.ids, (name, href)
    correct = re.findall(r'data-correct="([^"]+)"', html)
    choices = set(re.findall(r'data-choice="([^"]+)"', html))
    assert all(answer in choices for answer in correct), f"{name} invalid quiz answer"


for lesson in range(13, 19):
    verify_lesson(lesson)

home = (ROOT / "index.html").read_text(encoding="utf-8")
for lesson in range(13, 19):
    assert f'href="day{lesson:02d}/"' in home, f"home missing day{lesson:02d} link"

day12 = (ROOT / "day12" / "index.html").read_text(encoding="utf-8")
assert 'href="../day13/"' in day12, "day12 must continue to day13"

all_html = "\n".join((ROOT / f"day{n:02d}" / "index.html").read_text() for n in range(13, 19))
assert not re.search(r"\bTODO\b", all_html)
assert "正式環境直接修改" not in all_html
print("LESSONS_13_18_CONTRACT_PASS lessons=6 min_sections=7 min_quizzes=2 progress=3 safety_gate=true")
