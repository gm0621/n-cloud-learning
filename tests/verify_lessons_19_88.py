#!/usr/bin/env python3
"""Focused structural, content, navigation, and safety contract for lessons 19–88."""
from __future__ import annotations

from html import escape
from html.parser import HTMLParser
from pathlib import Path
import importlib.util
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "build_lessons.py"
spec = importlib.util.spec_from_file_location("build_lessons", GENERATOR)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load generator: {GENERATOR}")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
LESSONS = module.parse_specs()
CASES = module.load_cases()
SENSITIVE_PATTERNS = [
    r"(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}",
    r"192\.168\.\d{1,3}\.\d{1,3}",
    r"(?i)(password|passwd|token|api[_ -]?key)\s*[:=]\s*[^\s<]+",
    r"(?i)authorization\s*:\s*(?:bearer|basic)\s+\S+",
    r"(?i)bearer\s+[a-z0-9._~-]{16,}",
    r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"https://(?:hooks|webhook)\.[^\s<]+",
]


class LessonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.captions: list[str] = []
        self.sections = 0
        self.quizzes = 0
        self.progress = 0
        self.table_headers = 0
        self.scoped_headers = 0
        self._caption = False

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        element_id = data.get("id")
        if isinstance(element_id, str):
            self.ids.append(element_id)
        classes = str(data.get("class") or "").split()
        if tag == "section" and "lesson-section" in classes:
            self.sections += 1
        if data.get("data-quiz") is not None:
            self.quizzes += 1
        if data.get("data-progress") is not None:
            self.progress += 1
        href = data.get("href")
        if tag == "a" and isinstance(href, str):
            self.links.append(href)
        src = data.get("src")
        if tag == "script" and isinstance(src, str):
            self.scripts.append(src)
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
        if self._caption and data.strip():
            self.captions.append(data.strip())


def verify_lesson(item):
    number = item.number
    name = f"day{number:02d}"
    path = ROOT / name / "index.html"
    assert path.exists(), f"missing {path}"
    html = path.read_text(encoding="utf-8")
    parser = LessonParser()
    parser.feed(html)

    assert f'data-lesson="lesson{number:02d}"' in html, name
    assert f'data-lesson-name="第{module.zh_number(number)}課"' in html, name
    assert item.title in html, f"{name} missing canonical title {item.title}"
    assert item.objective in html, f"{name} missing objective"
    assert item.evidence in html, f"{name} missing evidence"
    assert item.boundary in html, f"{name} missing boundary"
    assert item.deliverable in html, f"{name} missing deliverable"
    case = CASES[number]
    for marker in (case.input, case.question, case.correct, *case.wrong, *case.rubric):
        assert escape(marker) in html, f"{name} missing case-specific content: {marker}"
    assert 'class="record-sample lesson-case"' in html, f"{name} missing concrete lesson case"
    assert "案例驗收 rubric" in html, f"{name} missing case rubric"

    assert parser.sections == 9, (name, parser.sections)
    assert parser.quizzes == 2, (name, parser.quizzes)
    assert parser.progress == 3, (name, parser.progress)
    assert len(parser.ids) == len(set(parser.ids)), f"duplicate id in {name}"
    assert "../assets/lesson-practice.js" in parser.scripts, name
    assert any("教學模擬" in caption for caption in parser.captions), name
    assert parser.table_headers == 3, (name, parser.table_headers)
    assert parser.scoped_headers == parser.table_headers, f"unscoped table header in {name}"

    for marker in ("完成條件", "排錯", "詳解", "停止條件", "候選入口", "不代表真實 N-Cloud", "UNKNOWN", "G3 Gate"):
        assert marker in html, f"{name} missing marker {marker}"
    assert item.gate in html, f"{name} missing gate {item.gate}"
    assert "帳密或客戶識別" in html, f"{name} missing privacy boundary"
    assert "TODO" not in html, name

    assert f"../day{number-1:02d}/" in parser.links, f"{name} missing previous lesson"
    expected_next = f"../day{number+1:02d}/" if number < 88 else "../curriculum/"
    assert expected_next in parser.links, f"{name} missing next lesson"
    for href in parser.links:
        if href.startswith("#"):
            assert href[1:] in parser.ids, (name, href)

    quiz_blocks = re.findall(
        r'<div class="quiz-card"[^>]*data-correct="([^"]+)"[^>]*>.*?<div class="quiz-options">(.*?)</div><p class="quiz-status"',
        html,
        flags=re.DOTALL,
    )
    assert len(quiz_blocks) == 2, (name, len(quiz_blocks))
    for answer, options_html in quiz_blocks:
        choices = set(re.findall(r'data-choice="([^"]+)"', options_html))
        assert answer in choices, f"{name} quiz answer {answer} missing from its own choices"

    if number in {87, 88}:
        assert "逐項核准、隔離 LAB" in html and "禁止在正式環境演練" in html, name
    elif number in {39, 40, 41}:
        assert "隔離測試收件匣或端點" in html and "否則只完成 plan／dry-run" in html, name
    elif item.gate.startswith("G3"):
        assert "只完成 G3 的 plan、dry-run" in html, name
    assert ".111" not in html, f"{name} leaks an environment shorthand"

    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, html), f"{name} contains sensitive pattern {pattern}"


for lesson in LESSONS:
    verify_lesson(lesson)

assert len(LESSONS) == 70
assert [item.number for item in LESSONS] == list(range(19, 89))

curriculum = (ROOT / "curriculum" / "index.html").read_text(encoding="utf-8")
detail_blocks = re.findall(r"<details(?: open)?>.*?</details>", curriculum, flags=re.DOTALL)
series_targets = [
    int(number)
    for block in detail_blocks
    for number in re.findall(r'href="\.\./day(\d{2})/"', block)
]
assert series_targets == list(range(1, 89)), f"curriculum series order mismatch: {series_targets}"
assert len(set(series_targets)) == 88
assert "全部已有可學頁面" in curriculum

home = (ROOT / "index.html").read_text(encoding="utf-8")
for marker in ("88 課全數可學", "完整 9 系列、88 課已可學習", 'href="curriculum/"'):
    assert marker in home, f"home missing {marker}"

day18 = (ROOT / "day18" / "index.html").read_text(encoding="utf-8")
assert 'href="../day19/"' in day18, "day18 must continue to day19"

practice_js = (ROOT / "assets" / "lesson-practice.js").read_text(encoding="utf-8")
assert ".innerHTML" not in practice_js
for marker in ("isPlainObject", "aria-live", "aria-pressed", "prefers-reduced-motion"):
    haystack = practice_js if marker != "prefers-reduced-motion" else (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
    assert marker in haystack, f"shared contract missing {marker}"

for source in (GENERATOR, ROOT / "content" / "lesson_cases.json"):
    source_text = source.read_text(encoding="utf-8")
    assert ".111" not in source_text, f"{source} contains an environment shorthand"
    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, source_text), f"{source} contains sensitive pattern {pattern}"

print("LESSONS_19_88_CONTRACT_PASS lessons=70 case_lessons=70 sections=630 quizzes=140 progress=210 curriculum_unique_targets=88 safety_gate=true")
