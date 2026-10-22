#!/usr/bin/env python3
"""Focused structural, content, navigation, and safety contract for lessons 19–88."""
from __future__ import annotations

from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
import importlib.util
import json
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
PACKS = module.load_lesson_packs()
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
        self.notes = 0
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
        if data.get("data-notes") is not None:
            self.notes += 1
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


def options_for(html: str, choice: str) -> str:
    match = re.search(
        rf'<button[^>]*data-choice="{re.escape(choice)}"[^>]*>(.*?)</button>',
        html,
        flags=re.DOTALL,
    )
    assert match is not None, f"missing option {choice}"
    return unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def option_position(html: str, choice: str) -> int:
    for block in re.findall(r'<div class="quiz-options">(.*?)</div>', html, flags=re.S):
        choices = re.findall(r'data-choice="([^"]+)"', block)
        if choice in choices:
            return choices.index(choice)
    raise AssertionError(f"missing option position for {choice}")


def strings_in(value):
    if isinstance(value, str):
        if value:
            yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings_in(item)


def verify_pack(number: int, pack: dict) -> None:
    assert pack["n"] == number
    assert len(pack["prerequisites"]) == 3
    assert all(len(value) >= 8 for value in pack["prerequisites"])
    assert len(pack["concepts"]) >= 3
    assert all(set(item) == {"term", "explanation", "confusion"} for item in pack["concepts"])
    assert all(len(item["explanation"]) >= 20 and len(item["confusion"]) >= 12 for item in pack["concepts"])
    fixture = pack["fixture"]
    assert len(fixture["title"]) >= 8
    assert len(fixture["columns"]) >= 3
    assert len(fixture["rows"]) >= (10 if number in {24, 34, 44, 54, 64, 71, 72, 79, 80} else 4)
    assert all(len(row) == len(fixture["columns"]) for row in fixture["rows"])
    assert len(pack["guided_steps"]) == 4
    assert all(set(step) == {"action", "input", "expected", "evidence", "failure"} for step in pack["guided_steps"])
    assert all(all(len(str(step[key])) >= 10 for key in step) for step in pack["guided_steps"])
    task = pack["independent_task"]
    assert len(task["brief"]) >= 18
    assert len(task["constraints"]) >= 3
    assert len(task["artifact_fields"]) >= 4
    assert len(set(task["artifact_fields"])) == len(task["artifact_fields"])
    assert len(task["reference_answer"]) >= 3
    assert len(pack["acceptance"]) == 3
    assert all(set(item) == {"criterion", "pass", "fail", "points"} for item in pack["acceptance"])
    assert sum(item["points"] for item in pack["acceptance"]) == 100
    assert len(pack["troubleshooting"]) >= 3
    assert all(set(item) == {"symptom", "check", "expected", "fix", "stop"} for item in pack["troubleshooting"])
    assert pack["sources"]
    assert all(set(item) == {"title", "url", "status", "reviewed", "applies"} for item in pack["sources"])
    for source in pack["sources"]:
        assert source["status"] in {"VERIFIED_OFFICIAL_PUBLIC", "CONTROLLED_SOURCE_REQUIRED"}
        if source["status"] == "CONTROLLED_SOURCE_REQUIRED":
            assert source["url"] == "" and source["reviewed"] == "UNKNOWN"
        else:
            assert source["url"].startswith("https://") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["reviewed"])


assert sorted(PACKS) == list(range(19, 89))
for lesson_number, lesson_pack in PACKS.items():
    verify_pack(lesson_number, lesson_pack)
assert len({pack["independent_task"]["brief"] for pack in PACKS.values()}) == 70
assert len({pack["fixture"]["title"] for pack in PACKS.values()}) == 70
assert len({tuple(item["term"] for item in pack["concepts"]) for pack in PACKS.values()}) == 70
assert len({tuple(item["symptom"] for item in pack["troubleshooting"]) for pack in PACKS.values()}) == 70
for number in range(65, 89):
    for item in PACKS[number]["troubleshooting"]:
        assert not item["symptom"].endswith("未得到預期結果"), f"lesson {number} retains generated troubleshooting symptom"
        assert "定位第一個差異，只修正該課資料或計算口徑後重新核對" not in item["fix"], f"lesson {number} retains generated troubleshooting fix"


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
    assert "案例檢查點" in html, f"{name} missing case checkpoint"
    pack = PACKS[number]
    for marker in strings_in(pack):
        assert escape(marker, quote=True) in html or escape(marker) in html, f"{name} missing deep-pack content: {marker}"

    assert parser.sections == 13, (name, parser.sections)
    assert parser.quizzes == 2, (name, parser.quizzes)
    assert parser.progress == 3, (name, parser.progress)
    expected_notes = len(pack["independent_task"]["artifact_fields"])
    assert parser.notes == expected_notes, (name, parser.notes, expected_notes)
    assert f"工作紙 0 / {expected_notes} 欄已填" in html, name
    assert f"產物工作紙 {expected_notes} 欄完成" in html, name
    assert len(parser.ids) == len(set(parser.ids)), f"duplicate id in {name}"
    assert "../assets/lesson-practice.js" in parser.scripts, name
    assert any("教學模擬" in caption for caption in parser.captions), name
    assert any("總分 100" in caption for caption in parser.captions), name
    assert parser.table_headers == len(pack["fixture"]["columns"]) + 4, (name, parser.table_headers)
    assert parser.scoped_headers == parser.table_headers, f"unscoped table header in {name}"

    for marker in ("完成條件", "產物工作紙", "100 分驗收表", "本課專屬排錯", "來源、版本與複核狀態", "教師版", "停止條件", "候選入口", "不代表正式產品輸出", "UNKNOWN", "G3 Gate"):
        assert marker in html, f"{name} missing marker {marker}"
    assert item.gate in html, f"{name} missing gate {item.gate}"
    assert "帳密、token、認證材料或客戶識別" in html, f"{name} missing privacy boundary"
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
        options = dict(
            (choice, unescape(re.sub(r"<[^>]+>", "", label)).strip())
            for choice, label in re.findall(r'<button[^>]*data-choice="([^"]+)"[^>]*>(.*?)</button>', options_html, flags=re.DOTALL)
        )
        choices = set(options)
        assert answer in choices, f"{name} quiz answer {answer} missing from its own choices"
    assert options_for(html, "case-correct") == case.correct, f"{name} case answer text drift"
    assert options_for(html, "artifact-pass") == pack["acceptance"][0]["pass"], f"{name} artifact checkpoint drift"

    if number in {87, 88}:
        assert "逐項核准、隔離 LAB" in html and "禁止在正式環境演練" in html, name
        if number == 87:
            assert "plan-only" in html and "未核准前不得執行" in html, name
            assert "依四步流程完成計畫與評估" in html, name
            assert "LAB 升級計畫與評估報告" in html, name
            assert "完成升級前、中、後檢查" not in html, name
            assert "LAB 升級證據包" not in html, name
        if number == 88:
            assert "plan-only" in html and "未核准前不得執行" in html, name
            assert "依四步流程完成計畫與評估" in html, name
            assert "依故障情境執行 rollback 或 restore" not in html, name
    elif number in {39, 40, 41}:
        assert "隔離測試收件匣或端點" in html and "否則只完成 plan／dry-run" in html, name
    elif item.gate.startswith("G3"):
        assert "只完成 G3 的 plan、dry-run" in html, name
    assert ".111" not in html, f"{name} leaks an environment shorthand"

    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, html), f"{name} contains sensitive pattern {pattern}"
    return option_position(html, "case-correct"), option_position(html, "artifact-pass")


case_answer_positions = set()
artifact_answer_positions = set()
for lesson in LESSONS:
    case_position, artifact_position = verify_lesson(lesson)
    case_answer_positions.add(case_position)
    artifact_answer_positions.add(artifact_position)
assert case_answer_positions == {0, 1, 2}, case_answer_positions
assert artifact_answer_positions == {0, 1, 2}, artifact_answer_positions

assert len(LESSONS) == 70
assert [item.number for item in LESSONS] == list(range(19, 89))

constraint_signatures = {
    tuple(pack["independent_task"]["constraints"])
    for pack in PACKS.values()
}
acceptance_signatures = {
    tuple((item["criterion"], item["pass"], item["fail"]) for item in pack["acceptance"])
    for pack in PACKS.values()
}
assert len(constraint_signatures) == 70, "independent constraints must be materially unique per lesson"
assert len(acceptance_signatures) == 70, "acceptance criteria must be materially unique per lesson"
for number, pack in PACKS.items():
    actions = " ".join(step["action"] for step in pack["guided_steps"])
    for generic in (
        "依資料流處理第",
        "執行正例、反例與邊界檢查",
        "封裝交付並套用停止與清理 Gate",
    ):
        assert generic not in actions, f"lesson {number} retains generic guided-step template: {generic}"

for number, required_terms in {
    40: ("Webhook 機制", "Webhook URL", "token", "signing secret", "憑證"),
    41: ("Backpressure", "重複事件", "順序語意", "迴圈預防"),
    42: ("Canary", "冪等", "並行", "爆炸半徑"),
    49: ("SLI", "SLO", "SLA", "可用性", "P95"),
    50: ("5145", "4656", "4663"),
    54: ("Flow", "重傳", "UNKNOWN"),
}.items():
    lesson_blob = json.dumps(PACKS[number], ensure_ascii=False)
    for term in required_terms:
        assert term in lesson_blob, f"lesson {number} missing required technical boundary: {term}"

curriculum = (ROOT / "curriculum" / "index.html").read_text(encoding="utf-8")
detail_blocks = re.findall(r"<details[^>]*>.*?</details>", curriculum, flags=re.DOTALL)
series_targets = [
    int(number)
    for block in detail_blocks
    for number in re.findall(r'href="\.\./day(\d{2})/"', block)
]
assert series_targets == list(range(1, 89)), f"curriculum series order mismatch: {series_targets}"
assert len(set(series_targets)) == 88
assert "全部已有可學頁面" in curriculum

curriculum_md = (ROOT / "CURRICULUM.md").read_text(encoding="utf-8")
for marker in (
    "LAB 升級計畫與驗證設計",
    "本課只完成 plan-only 升級計畫與評估",
    "本課只完成 plan-only rollback／restore 演練計畫與評估",
):
    assert marker in curriculum_md, f"curriculum markdown missing plan-only marker: {marker}"
for stale in (
    "只在 LAB 演練，完成升級前／中／後檢查與功能 smoke",
    "依故障情境執行 rollback／restore",
):
    assert stale not in curriculum_md, f"curriculum markdown retains unsafe execution language: {stale}"

home = (ROOT / "index.html").read_text(encoding="utf-8")
for marker in ("88 課全數可學", "完整 9 系列、88 課已可學習", 'href="curriculum/"'):
    assert marker in home, f"home missing {marker}"

day18 = (ROOT / "day18" / "index.html").read_text(encoding="utf-8")
assert 'href="../day19/"' in day18, "day18 must continue to day19"

practice_js = (ROOT / "assets" / "lesson-practice.js").read_text(encoding="utf-8")
assert ".innerHTML" not in practice_js
for marker in ("isPlainObject", "aria-live", "aria-pressed", "notesKey", "[data-notes]", "工作紙", "completionKey", "revokeCompletionIfInvalid", "beforeprint", "prefers-reduced-motion"):
    haystack = practice_js if marker != "prefers-reduced-motion" else (ROOT / "assets" / "styles.css").read_text(encoding="utf-8")
    assert marker in haystack, f"shared contract missing {marker}"

for source in (*sorted(ROOT.glob("day*/index.html")), GENERATOR, ROOT / "content" / "lesson_cases.json", ROOT / "content" / "lesson_packs.json"):
    source_text = source.read_text(encoding="utf-8")
    assert ".111" not in source_text, f"{source} contains an environment shorthand"
    for pattern in SENSITIVE_PATTERNS:
        assert not re.search(pattern, source_text), f"{source} contains sensitive pattern {pattern}"

total_notes = sum(len(pack["independent_task"]["artifact_fields"]) for pack in PACKS.values())
print(f"LESSONS_19_88_CONTRACT_PASS lessons=70 deep_packs=70 sections=910 quizzes=140 notes={total_notes} progress=210 curriculum_unique_targets=88 safety_gate=true")
