#!/usr/bin/env python3
"""Contract for de-identified NPEC historical-document alignment."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = json.loads((ROOT / "content" / "lesson_packs.json").read_text(encoding="utf-8"))
BY_N = {item["n"]: item for item in PACKS}


def flattened(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def require_historical_source(lesson: int) -> None:
    sources = BY_N[lesson]["sources"]
    matches = [s for s in sources if s["status"] == "USER_PROVIDED_HISTORICAL"]
    assert len(matches) == 1, f"lesson {lesson}: expected one historical source marker"
    marker = flattened(matches[0])
    assert "不代表當期官方考綱" in marker
    assert "不公開原題" in marker


# Lesson 73: historical exam contract, clearly bounded and non-official-current.
lesson73 = flattened(BY_N[73])
for marker in ["14 題", "180 分鐘", "至少 10 題", "先保底再回頭", "第 85～86 課", "第 87 課"]:
    assert marker in lesson73, f"lesson 73 missing {marker}"
assert "不代表當期官方考綱" in lesson73
assert "至少 10 題完成且通過驗收" in lesson73
assert "阻塞證據另列且不得計入十題完成門檻" in lesson73
assert "完成題有驗收證據；阻塞題另列" in lesson73
for forbidden in ["完成或明確阻塞", "完成／阻塞", "完成 10 項或留下可核阻塞"]:
    assert forbidden not in lesson73, f"lesson 73 must not count blockers toward the completion floor: {forbidden}"
require_historical_source(73)

# Lesson 77: retention/download chain is a first-class, no-exfiltration exercise.
lesson77 = flattened(BY_N[77])
for marker in ["事件保存條件", "單次下載", "下載對帳", "不建立排程", "不外送"]:
    assert marker in lesson77, f"lesson 77 missing {marker}"
require_historical_source(77)

# Lessons 79/80: two distinct 14-task simulations with a 10-task floor.
fixtures: dict[int, list[list[object]]] = {}
for lesson in (79, 80):
    pack = BY_N[lesson]
    rows = pack["fixture"]["rows"]
    fixtures[lesson] = rows
    assert len(rows) == 14, f"lesson {lesson}: expected 14 task rows, got {len(rows)}"
    task_ids = [str(row[0]) for row in rows]
    assert task_ids == [f"T{i:02d}" for i in range(1, 15)], task_ids
    text = flattened(pack)
    for marker in ["14 項", "至少完成 10 項", "交卷設定匯出", "匯出檔可讀回驗", "清理檢查"]:
        assert marker in text, f"lesson {lesson} missing {marker}"
    assert "至少 10 項各有設定、結果、回查與清理證據" in text
    assert "阻塞項另列且不得計入十項完成門檻" in text
    for forbidden in ["完成或明確阻塞", "完成／阻塞", "完成 10 項或留下可核阻塞"]:
        assert forbidden not in text, f"lesson {lesson} must not count blockers toward the completion floor: {forbidden}"
    require_historical_source(lesson)

assert fixtures[79] != fixtures[80], "the two simulations must use different task sets"

# Generated pages must expose the same public learning contract after rebuild.
for lesson in (73, 77, 79, 80):
    html = (ROOT / f"day{lesson:02d}" / "index.html").read_text(encoding="utf-8")
    assert "USER_PROVIDED_HISTORICAL" in html, f"day {lesson}: historical source not rendered"
    assert "不代表當期官方考綱" in html

day73_html = (ROOT / "day73" / "index.html").read_text(encoding="utf-8")
assert "至少 10 題完成且通過驗收" in day73_html
assert "阻塞證據另列且不得計入十題完成門檻" in day73_html
assert "完成題有驗收證據；阻塞題另列" in day73_html

for lesson in (79, 80):
    html = (ROOT / f"day{lesson:02d}" / "index.html").read_text(encoding="utf-8")
    assert "14 項" in html
    assert "至少完成 10 項" in html
    assert "交卷設定匯出" in html
    assert "至少 10 項各有設定、結果、回查與清理證據" in html
    assert "阻塞項另列且不得計入十項完成門檻" in html

for lesson in (73, 79, 80):
    html = (ROOT / f"day{lesson:02d}" / "index.html").read_text(encoding="utf-8")
    for forbidden in ["完成或明確阻塞", "完成／阻塞", "完成 10 項或留下可核阻塞"]:
        assert forbidden not in html, f"day {lesson} renders an invalid completion-floor phrase: {forbidden}"

print("NPEC_HISTORICAL_ALIGNMENT_PASS lessons=4 simulations=2 tasks=28 floor=10 safety=plan-only")
