from pathlib import Path
from html.parser import HTMLParser
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "npec-comparison" / "index.html"

assert PAGE.exists(), "missing npec comparison page"
html = PAGE.read_text(encoding="utf-8")

# Basic HTML tokenization catches malformed tags and broken quoting.
parser = HTMLParser()
parser.feed(html)
parser.close()

required_markers = [
    "我的答案，和同事的實機示範一樣嗎？",
    "解題邏輯多數相同；實作完成度不能混為一談。",
    "最重要的修正：第 6 題",
    "Syslog＋情資比對＋Hit Count",
    "這不是官方答案表",
    "填過表單",
    "未儲存的表單示範",
    "第 4～14 題逐題設定手冊",
    "位置 → 欄位對照 → 逐步設定 → 驗收 → 常見錯誤",
]
for marker in required_markers:
    assert marker in html, f"missing content marker: {marker}"

question_blocks = {}
for number in range(4, 15):
    assert f'id="q{number}"' in html, f"missing q{number} anchor"
    assert f"Q{number:02d}" in html, f"missing Q{number:02d} label"
    match = re.search(
        rf'<details class="question" id="q{number}".*?</details>', html, re.S
    )
    assert match, f"missing q{number} details block"
    block = match.group(0)
    question_blocks[number] = block
    assert block.count('class="manual"') == 1, f"q{number} missing manual"
    assert block.count('class="route"') == 1, f"q{number} missing route"
    assert block.count('class="steps"') == 1, f"q{number} missing steps"
    assert "<h4>驗收</h4>" in block, f"q{number} missing acceptance section"
    assert "<h4>常見錯誤</h4>" in block, f"q{number} missing pitfalls section"
    steps = re.search(r'<ol class="steps">(.*?)</ol>', block, re.S)
    assert steps and steps.group(1).count("<li>") >= 7, f"q{number} needs >=7 steps"

assert len(question_blocks) == 11
assert html.count('class="manual"') == 11
assert html.count('class="route"') == 11
assert html.count('class="steps"') == 11
assert html.count("<h4>驗收</h4>") == 11
assert html.count("<h4>常見錯誤</h4>") == 11

route_markers = [
    "系統管理 → IP 名稱解析 → IP 名稱解析列表",
    "報表 → 分時監控報表 → 訂製分時監控報表",
    "報表 → Top N → Top N 報表",
    "事件 → 事件查詢",
    "設備管理 → 設備資產樹狀圖",
    "Dashboard → 列表 → 新增",
]
for marker in route_markers:
    assert marker in html, f"missing menu route: {marker}"

assert "192.168.11.100" in html
assert "192.168.11.110" in html
assert "https://192.168.11.121" in html
assert "23、22、3389、1433、389" in html
assert "[REDACTED]" not in html
assert "192.168.6.100" not in html
assert "community" not in html.lower()

home = (ROOT / "index.html").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
assert 'href="npec-comparison/"' in home, "home missing npec comparison link"
assert "npec-comparison/" in readme, "README missing npec comparison link"

print(
    "NPEC_COMPARISON_PASS questions=11 manuals=11 min_steps=7 "
    "acceptance=11 pitfalls=11 private_source_hidden=true"
)
