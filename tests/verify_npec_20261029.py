#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "npec-20261029" / "index.html"
assert PAGE.exists(), "missing NPEC 2026-10-29 page"
html = PAGE.read_text(encoding="utf-8")

parser = HTMLParser()
parser.feed(html)
parser.close()

assert '<html lang="zh-Hant">' in html
assert '<meta name="viewport"' in html
assert '@media(max-width:640px)' in html
assert '@media print' in html
assert 'N-Reporter Login' in html
assert '實機狀態' in html

ids = [int(x) for x in re.findall(r'<details class="question" id="q(\d+)"', html)]
assert ids == list(range(1, 15)), ids
assert html.count('class="question"') == 14

for n in range(1, 15):
    block = html.split(f'id="q{n}"', 1)[1].split('</details>', 1)[0]
    for marker in ('完整題目', '逐步設定', '驗收', '常見錯誤'):
        assert marker in block, (n, marker)
    steps = re.search(r'<ol class="steps">(.*?)</ol>', block, re.S)
    assert steps and steps.group(1).count('<li>') >= 8, (n, 'insufficient steps')

required = (
    'ncloud-7.0.027.img',
    '3.10.0-1160.119.1.el7.x86_64',
    '192.168.11.109:514/UDP',
    'Facility 19',
    '18:00～隔日 08:00',
    'Cisco Firepower',
    'https://www.npartner.com',
    '210.71.213,0/24',
    '公司檔案伺服器讀取資料排名',
    '外部IP對主機網段資料下載',
    'https://192.168.11.121',
    '重要服務網站',
    '外對內重要服務port 連線監控',
    '外對內重要服務port 連線告警',
    '上班時間瀏覽社群網站與影音平台',
    'administrator',
    '192.168.11.115',
    '!Home AND Blacklist',
    '最近 30 分鐘',
    'cfg.npdb',
)
for marker in required:
    assert marker in html, marker

# Prevent stale values from the discarded, mismatched draft.
for forbidden in (
    'np_kernel.npz',
    '192.168.11.190',
    'mis@npartner.com',
    'administrator、admin、root、sa、superadmin',
    'Ipcam_1',
    '打卡機_1',
    '情資IP連線排名',
    '資安監控儀表板',
    '[組別]_cfg.npdb',
    '[REDACTED]',
    'password=',
    'passwd=',
):
    assert forbidden not in html, forbidden

assert '全部展開' in html and '全部收合' in html
assert 'location.hash' in html
assert 'href="npec-20261029/"' in (ROOT / 'index.html').read_text(encoding='utf-8')
assert 'npec-20261029/' in (ROOT / 'README.md').read_text(encoding='utf-8')
print('NPEC_20261029_PASS questions=14 detailed_steps=pass responsive=pass print=pass sensitive_scan=pass')
