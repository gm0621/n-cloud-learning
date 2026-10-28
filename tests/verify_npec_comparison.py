from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "npec-comparison" / "index.html"

assert PAGE.exists(), "missing npec comparison page"
html = PAGE.read_text(encoding="utf-8")

required_markers = [
    "我的答案，和同事的實機示範一樣嗎？",
    "解題邏輯多數相同；實作完成度不能混為一談。",
    "最重要的修正：第 6 題",
    "Syslog＋情資比對＋Hit Count",
    "這不是官方答案表",
    "填過表單",
    "未儲存的表單示範",
]
for marker in required_markers:
    assert marker in html, f"missing content marker: {marker}"

for number in range(4, 15):
    assert f'id="q{number}"' in html, f"missing q{number} anchor"
    assert f"Q{number:02d}" in html, f"missing Q{number:02d} label"

assert len(re.findall(r'<details class="question" id="q(?:[4-9]|1[0-4])"', html)) == 11
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

print("NPEC_COMPARISON_PASS questions=11 private_source_hidden=true homepage_link=true readme_link=true")
