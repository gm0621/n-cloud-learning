from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
home = (ROOT / "index.html").read_text(encoding="utf-8")
curriculum = (ROOT / "curriculum/index.html").read_text(encoding="utf-8")
styles = (ROOT / "assets/styles.css").read_text(encoding="utf-8")

# Homepage is a short decision surface, not a second 18-lesson catalog.
assert 'class="entry-choice-grid"' in home
assert len(re.findall(r'class="entry-choice-card', home)) == 4
for marker in (
    "第一次來，從基礎開始",
    "日常維運與事件調查",
    "SE／導入與 Backend",
    "NPSC／NPEC 考照",
    "不知道怎麼選？先走共同基礎",
):
    assert marker in home, f"home missing entry marker: {marker}"
assert 'class="course-grid"' not in home, "homepage still duplicates the long lesson catalog"
assert home.index('class="entry-choice-grid"') < home.index('id="series-preview"')

# Role choices appear before the complete catalog.
assert curriculum.index('id="role-paths"') < curriculum.index('id="series"')
for path_id in ("path-foundation", "path-operations", "path-se", "path-certification"):
    assert f'id="{path_id}"' in curriculum, path_id
assert len(re.findall(r'class="role-path-card', curriculum)) == 4
assert '<ol aria-label="共同基礎學習順序"><li>系列一</li><li>第 1～12 課</li></ol>' in curriculum
assert '<li>系列二</li>' not in curriculum.split('aria-label="共同基礎學習順序"', 1)[1].split('</ol>', 1)[0]
for route_marker in (
    "系列一 基礎", "系列二 實機", "系列三 正規化",
    "系列四 監控", "系列五 事件", "系列六 POC",
    "系列七 NPSC", "系列八 NPEC", "系列九 Backend",
):
    assert route_marker in curriculum, route_marker
assert 'data-series-deeplink' in curriculum
assert 'series.open = series === target' in curriculum

# Every series and lesson has a designed, fully clickable overview component.
for number in range(1, 10):
    assert f'id="series-{number}"' in curriculum, f"series-{number}"
series_bodies = re.findall(r'<div class="series-body">(.*?)</div>', curriculum, re.S)
assert len(series_bodies) == 9, len(series_bodies)
lesson_links = []
for body in series_bodies:
    lesson_links.extend(re.findall(r'<li><a href="\.\./day(\d{2})/">([^<]+)</a></li>', body))
assert len(lesson_links) == 88, len(lesson_links)
assert {int(number) for number, _ in lesson_links} == set(range(1, 89))
for expected_start in (1, 13, 25, 35, 45, 55, 65, 73, 81):
    assert f'<ol start="{expected_start}">' in curriculum, expected_start

# Links look and behave like cards while retaining strong keyboard affordance.
for marker in (
    ".entry-choice-card{",
    ".role-path-card{",
    ".series-body li a{",
    "text-decoration:none",
    ".series-body li a:hover",
    ".series-body li a:focus-visible",
):
    assert marker in styles, f"styles missing: {marker}"
assert ".lesson-header nav a:not(:first-of-type){display:none}" in styles
assert ".lesson-header nav a:not(:last-of-type){display:none}" not in styles

# All 88 lesson targets remain valid and return to the same real curriculum.
for number in range(1, 89):
    lesson_path = ROOT / f"day{number:02d}/index.html"
    assert lesson_path.exists(), number
    lesson_html = lesson_path.read_text(encoding="utf-8")
    assert 'href="../curriculum/">完整路線</a>' in lesson_html, f"day{number:02d} header route"
    assert re.search(r'href="\.\./curriculum/">(?:← )?回完整課程地圖</a>', lesson_html), f"day{number:02d} footer route"

print(
    "ENTRY_EXPERIENCE_CONTRACT_PASS "
    "entry_choices=4 role_paths=4 series=9 lesson_cards=88"
)
