#!/usr/bin/env python3
"""Generate static N-Cloud lesson pages 19–88 from reviewed structured content."""
from __future__ import annotations
from dataclasses import dataclass
from html import escape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

@dataclass(frozen=True)
class Lesson:
    number: int
    title: str
    series: str
    gate: str
    location: str
    objective: str
    evidence: str
    boundary: str
    deliverable: str
    steps: tuple[str, str, str, str]


@dataclass(frozen=True)
class Case:
    number: int
    input: str
    question: str
    correct: str
    wrong: tuple[str, str]
    rubric: tuple[str, str, str]


SPECS_TEXT = r"""
19|TopN 與 TopN × TopN|系列二｜N-Cloud 實機操作|G1／G2|報表 → Top N；細項名稱依 UI 版本與角色核對|從已驗證的查詢找出最高來源，再展開目的或服務，說清楚排名維度與指標|相同時間窗與範圍下可重現兩層排名，並能解釋第一層與第二層母體|排名高只代表所選指標較高，不等於惡意、異常或根因|一份雙層 TopN 判讀卡|定義要回答的問題;固定時間、設備與資料類型;選維度與 Bytes、Sessions 或事件數;展開第二維並核對原始事件
20|報表與排程輸出|系列二｜N-Cloud 實機操作|G1／G2；排程外送為 G3|報表；排程、收件者與外送通道須另行授權|把查詢轉成有期間、時區、欄位、格式與接收目的的測試報表|輸出檔可開啟，期間、時區、欄位與筆數能回到來源查詢核對|產生檔案不代表內容正確；正式排程與外送可能造成資料外洩或郵件風暴|報表驗收紀錄與清理步驟|先保存可重現查詢;指定期間、時區與欄位;只產生一次性 LAB 輸出;逐項比對查詢與檔案
21|Dashboard 元件|系列二｜N-Cloud 實機操作|G2|Dashboard → Dashboard 列表；元件種類依版本核對|建立三個各自回答明確問題的元件，不把所有指標塞在同一張圖|每個元件都有問題、資料來源、時間窗、單位與可追查入口，手機與投影均可讀|漂亮不等於可行動；不同時間窗、單位或母體不能直接並排比較|三格值班 Dashboard 規格與畫面驗收|先寫三個值班問題;為每題選趨勢、排行或狀態;統一時間與單位;用窄版和投影檢查可讀性
22|SNMP 設備檢視|系列二｜N-Cloud 實機操作|G1|設備管理 → 設備資產樹狀圖；效能監控 → 效能監控列表|用 CPU、記憶體、介面利用率、errors、discards 與 Counter 趨勢判讀設備健康|同一設備與介面在連續時間窗的趨勢、增量與狀態可被再次查得|單點高值、Counter 累積值或 Admin Down 不能直接當成故障結論|設備健康判讀表|確認設備與介面唯一識別;辨認 Gauge、Counter 與狀態值;計算期間增量並對齊時間;回查 Syslog 或拓撲補證據
23|PM：Ping／Web／Port|系列二｜N-Cloud 實機操作|G2；正式探測與外部目標為 G3|效能監控 → 效能監控列表；建立入口依版本與權限核對|分辨 Ping、Port 與 Web 測試各自能證明的範圍，在 LAB 建立可清理測試|三種測試都有明確目標、頻率、逾時、結果與刪除紀錄，且能解釋彼此差異|Ping 成功不代表應用正常；Port 開啟不代表交易成功；Web 成功也不代表所有使用者路徑正常|三種 PM 測試比較表|定義使用者症狀與量測點;依證明範圍選 Ping、Port 或 Web;以 Gimmy-LAB 前綴建立最小測試;觀察結果後刪除並確認無殘留
24|值班人員綜合實作|系列二｜N-Cloud 實機操作|G1；必要的個人物件限 G2|事件、報表、設備管理、效能監控與 Dashboard|在限定時間內完成事件查詢、TopN、設備健康與服務品質摘要|交付包含時間線、跨資料證據、限制、值班結論與下一步，另一人可重現|限時不代表可以跳過範圍、時區、權限或證據界線|一頁值班摘要與五分鐘口頭交接|先做五分鐘 Triage;依假設選事件與 TopN;核對 SNMP 與 PM;寫出事實、限制與下一步
25|Syslog Facility、Severity 與格式|系列三｜資料接入與正規化|G0／G2|設備管理 → 自定義資料格式；實際 parser 入口依版本核對|拆解 PRI、header、message、Facility 與 Severity，不把設備等級直接當成業務風險|去識別樣本可被逐欄標示，計算出的 Facility／Severity 與原文一致|Severity 是設備送出的分類，不是事件真實影響或處置優先序|Syslog 解碼工作紙|保留原始樣本與編碼;拆 PRI、header、message;計算 Facility 與 Severity;再用資產與行為評估風險
26|Windows Event 與 NXLog|系列三｜資料接入與正規化|G0／G2；正式主機設定為 G3|文件與 LAB；接收端入口依版本核對|畫出 NXLog input、route、output 到接收端的資料旅程，使用去識別樣本驗證|測試事件在來源與接收端都有對應 ID、時間與內容，且能定位中斷節點|不得把真實帳號、主機名稱或安全紀錄放入公開教材；正式 Agent 變更需核准|Windows 事件接入驗證表|選一筆去識別測試事件;畫 input、route、output;對齊來源與接收時間;逐段驗證服務、網路與格式
27|應用程式與多行 Log|系列三｜資料接入與正規化|G0／G2|設備管理 → 自定義資料格式；來源輪替設定屬另一 Gate|處理時間格式、多行堆疊、編碼與輪替，避免一件事件被切成多筆或多件黏成一筆|正常、跨行、異常字元與輪替樣本的事件邊界都符合測試預期|只用單行成功樣本無法證明 parser 能承受例外與版本漂移|多行 Log 測試集|蒐集正常與錯誤堆疊樣本;定義事件起始與續行規則;加入編碼與輪替案例;比較事件數與原文邊界
28|Tag-Value 正規化|系列三｜資料接入與正規化|G0／G2|設備管理 → 自定義資料格式|將 key=value 型紀錄解析成至少五個穩定、可搜尋且有型別語意的欄位|正案例與缺值、重複 key、含空白值案例均有預期輸出，原文可回查|看到等號不代表格式永遠穩定；重複 key、跳脫字元與空值要先定義|Tag-Value 欄位字典與測試表|盤點分隔符與跳脫規則;建立欄位字典與型別;先跑固定正案例;再跑缺值、重複與未知 key
29|Delimiter 正規化|系列三｜資料接入與正規化|G0／G2|設備管理 → 自定義資料格式|為固定欄位順序的紀錄定義分隔、缺欄位、多分隔符與格式漂移策略|每個樣本的欄位數、位置、空值與溢出處理都有明確預期|Delimiter parser 最怕來源版本改欄位順序；不得只驗證一筆漂亮樣本|Delimiter 版本化測試矩陣|確認分隔符與引用規則;編號每個欄位位置;加入缺欄與多分隔案例;以版本標記 schema 變更
30|CEF 與 Label 關係|系列三｜資料接入與正規化|G0／G2|自定義資料格式或 CEF parser；入口依版本核對|正確配對 CEF header、extension 與 cs1／cs1Label 等自訂欄位的語意|每個自訂值都有對應 Label，缺 Label 或型別不符會被測試發現|cs1 只是槽位，沒有 cs1Label 就不能自行猜測業務語意|CEF 欄位配對表|拆開 CEF header 七欄;解析 extension key-value;配對值欄與 Label 欄;測試缺 Label、跳脫與重複欄位
31|時間、時區與事件時間|系列三｜資料接入與正規化|G0／G2|事件查詢與 parser 測試；系統時區設定為 G3|分辨事件時間、接收時間與處理時間，修正時區、年份與延遲造成的錯位|已知樣本在指定時區顯示正確，三種時間可被保留並計算延遲|直接改系統時間或時區會影響整站；本課只在 LAB 樣本與 parser 層驗證|時間欄位對照與偏移診斷表|記錄原文時間與時區;分開事件、接收、處理時間;以已知時間算偏移;測試跨日、夏令與缺年份案例
32|Parser 測試與失敗診斷|系列三｜資料接入與正規化|G0／G2|設備管理 → 自定義資料格式；正式套用為 G3|建立正常、缺值、異常字元與版本差異測試組，從 RAW 到欄位逐段定位|測試集可重跑，通過與失敗案例都有預期值、差異與修正紀錄|修到單一樣本成功不算完成；parser 變更可能讓舊格式回歸|Parser 回歸測試包|凍結去識別原始樣本;寫欄位級預期結果;同跑正反與版本案例;修正後全組回歸並保留差異
33|N-Probe／External Receiver 概念|系列三｜資料接入與正規化|G0／G1；部署與網路變更為 G3|系統資訊可檢視元件狀態；拓撲與設定入口依方案核對|依資料來源、網段、容量與故障域選擇收集位置，畫出端到端資料流|架構圖包含來源、傳輸、接收、處理、儲存、監控與失效影響|元件名稱相近不代表角色相同；不得未核對版本就給固定安裝步驟|資料接入架構圖|列出來源與協定;標示跨網段與信任邊界;估算事件量與緩衝;設計健康檢查與失效路徑
34|新資料源 Onboarding 實作|系列三｜資料接入與正規化|G0／G2；正式接入為 G3|文件、樣本與 LAB parser|從樣本、欄位字典、測試、查詢到交接，完成可重現的新資料源接入包|另一位工程師可用接入包重跑樣本、看懂欄位、查到事件並知道 rollback|沒有擁有者、版本、敏感資料處理與回復方式的 parser 不可交付|新資料源 Onboarding 包|定義需求與擁有者;凍結去識別樣本和欄位字典;建立 parser 與回歸測試;完成查詢驗收、文件與回復
35|基準線與門檻設計|系列四｜監控、告警與自動化|G1／G2|報表、智慧分析或效能監控；規則入口依版本核對|用歷史分布與業務時段定義平常範圍，再設計門檻、持續時間與恢復|門檻有資料期間、分群、例外、命中率與誤報評估，不是拍腦袋單點值|平均值會掩蓋尖峰；不同日型、資產與指標不可混成一條門檻|基準線與門檻設計卡|選指標與分群;取足夠歷史期間;比較分位數與日型;以回放估算命中與誤報
36|分時監控|系列四｜監控、告警與自動化|G2；正式通知為 G3|報表 → 分時監控報表；規則建立入口依版本核對|建立 LAB 規則並解釋時間窗、次數、持續時間、恢復與觀察期|用已知事件回放可預測何時觸發、何時恢復，清理後無殘留|只設閾值不設持續與恢復，容易造成抖動與告警風暴|分時監控狀態機|畫出正常、等待、告警、恢復;設定時間窗與最少命中;加入恢復與冷卻;用 LAB 資料回放後刪除
37|分時 TopN|系列四｜監控、告警與自動化|G2；通知為 G3|報表 → 分時監控報表／Top N；細項依版本核對|針對來源、目的或服務建立排名監控，分清維度、指標、母體與比較基準|每個命中可回到同一時間窗的 TopN 與原始資料，排名變化可被解釋|排名第一不一定超標；小母體中的第一名也可能非常小|分時 TopN 規格與回放結果|定義母體與排名維度;選 Bytes、Sessions 或事件數;設定與歷史比較方式;回放命中並核對原始資料
38|去重、抑制與告警風暴|系列四｜監控、告警與自動化|G0／G2|告警樣版或監控規則；正式值班策略為 G3|用重複事件案例設計聚合 key、抑制、重新通知與恢復摘要|相同根因的事件被合理合併，不同設備或影響不會被錯誤吞掉|抑制太強會漏告警，太弱會造成風暴；必須記錄被抑制數量|告警風暴前後對照表|選擇穩定聚合 key;定義抑制窗與上限;保留首告、計數與恢復;以相似和不同事件做正反測試
39|通知群組與測試訊息|系列四｜監控、告警與自動化|G3|系統管理 → 通報設定；只能在逐項授權後操作|設計 LAB 通知群組與測試訊息，核對收件者、內容、時區、連結與停止方式|核准的測試接收者只收到一則可辨識測試訊息，系統有發送與接收證據|未授權不得新增正式收件者或發送；測試失控時須立即停止並清理|通知 Gate 檢查表|確認核准人與測試通道;建立最小收件群組;發送一次帶 LAB 標記的訊息;核對兩端紀錄後刪除
40|第三方通知整合|系列四｜監控、告警與自動化|G3|通報設定與第三方測試端點；實際供應商依核准方案|以測試端點驗證 Email、Teams、LINE 或 Telegram payload、重試與敏感資料邊界|測試端收到預期欄位，失敗與重試可觀察，secret 未出現在教材或 log|Webhook URL、token 與 signing secret 等認證材料不得貼入頁面、Repo、截圖或聊天紀錄|第三方通知資料契約|定義最小 payload 與遮罩;使用專用測試端點;驗證成功、失敗與重試;撤銷測試 secret 並清理
41|轉發與減量轉發|系列四｜監控、告警與自動化|G3|系統管理或資料轉發相關設定；實際入口依版本核對|比較正規化、RAW DATA、原始設備 IP 與減量條件，設計不丟關鍵證據的轉發|測試接收端筆數、欄位、來源、延遲與丟棄規則可和來源端對帳|過度減量會破壞調查證據；轉發也可能擴散敏感資料與流量|轉發前後對帳表|列出必留與可省欄位;定義 filter 與資料邊界;用去識別樣本送測試端;對帳筆數、欄位與失敗路徑
42|自動執行安全設計|系列四｜監控、告警與自動化|G3|N-Robot／自動化設計；本課不連正式執行端|設計 dry-run、白名單、人工核准、上限、逾時、審計與 rollback|模擬執行可顯示將做什麼、對誰、何時停止，失敗可回復且有紀錄|告警正確不代表自動動作安全；錯誤目標或重試迴圈可能放大事故|自動化安全控制矩陣|先定義禁止動作與白名單;建立 dry-run 與人工核准;設定頻率、上限與逾時;演練失敗、停止與 rollback
43|情資 IP、黑名單與聯防|系列四｜監控、告警與自動化|G1／G2；封鎖與聯防為 G3|智慧聯防／N-Robot；入口與能力依授權版本核對|先觀察命中，再結合情資信心、資產角色與行為證據評估，不直接封鎖|每個命中都有來源、更新時間、信心、歷史活動、誤判檢查與處置 Gate|IP 會共享、重用或被 CDN／VPN 使用；單一清單命中不是惡意證明|情資命中判讀與 Gate 表|記錄情資來源與新鮮度;查歷史與資產角色;比較支持和反對證據;先告警觀察再決定是否送審
44|監控工程 Capstone|系列四｜監控、告警與自動化|G2；外送與自動處置為 G3|以 LAB 查詢、規則、測試通道與 Runbook 完成|從需求到基準線、規則、回放、通知設計、Runbook 與清理完成整組交付|另一人可重跑測試、預測觸發與恢復、找到擁有者並執行停用或 rollback|沒有測試與停止方式的監控不是完成，只是把風險移到值班人員|監控工程交付包|把需求寫成可觀察條件;建立基準與 LAB 規則;回放正反案例;完成通知 Gate、Runbook 與清理
45|事件分級與 Triage|系列五｜事件調查與維運情境|G0／G1|事件查詢與值班工作紙|在五分鐘內確認症狀、影響、時間、資產、資料來源與升級條件|Triage 紀錄能說明已知、未知、優先級理由與下一個最小查詢|嚴重度標籤不等於業務影響；先確認範圍與關鍵服務|五分鐘 Triage 卡|確認誰受影響與何時開始;辨識關鍵資產和服務;選第一個最有區辨力的資料源;設定更新與升級時點
46|VPN 登入異常|系列五｜事件調查與維運情境|G0／G1|事件查詢；必要時搭配操作歷程與 Flow|串聯失敗、成功、來源、帳號、設備與設定異動，提出可驗證假設|時間線可分辨單一使用者、來源集中、全域認證或設定變更，且保留限制|多次失敗可能是輸入錯誤、服務異常或攻擊；不能只憑次數定性|VPN 登入事件時間線|固定事件與接收時間;依帳號、來源與設備分群;找成功、失敗與變更對照;列出鎖定、RADIUS 與情資待查項
47|頻寬異常與 Top Talker|系列五｜事件調查與維運情境|G0／G1|Flow 查詢、Top N、設備用途與排程紀錄|用 Flow、資產用途、排程與基準判斷高流量是否合理|高流量的來源、目的、服務、期間、Bytes 與業務用途可被交叉核對|Top Talker 只是排名；備份、更新與惡意外傳都可能長得很大|頻寬異常判讀表|確認壅塞時間與介面;找同窗 Top Talker;核對資產用途和排程;比較基準並提出限速或深查方向
48|設備介面不穩|系列五｜事件調查與維運情境|G0／G1|設備資產樹、效能監控、Syslog 與拓撲|用 Admin／Oper、errors、discards、flap Syslog 與對端狀態定位層次|介面兩端、時間線、Counter 增量與設定狀態能互相對上|Counter 累積值不可直接比較；Admin Down 可能是預期設定|介面不穩證據鏈|確認正確介面與對端;計算錯誤和丟棄增量;對齊 link up/down 事件;區分實體、壅塞、設定與監控問題
49|網站慢與 SLA|系列五｜事件調查與維運情境|G0／G1|效能監控、SNMP、事件與應用紀錄|交叉比對 Ping、Port、Web、SNMP 與應用事件，定位慢在網路、連線或交易|不同量測點的延遲、遺失、狀態碼與資源趨勢在同一時間線比較|單一監測點不能代表所有使用者；平均回應時間也會掩蓋長尾|網站慢調查時間線|確認使用者路徑與量測點;分層查 Ping、Port、Web;核對主機與介面健康;加入應用錯誤和變更紀錄
50|Windows／NAS 檔案稽核|系列五｜事件調查與維運情境|G0／G1|事件查詢；欄位名稱依來源與 parser 核對|解讀 5145、4656、4663 等事件，回答誰、從哪裡、對哪個檔案做了什麼|事件 ID、帳號、主機、share、object、access mask 與結果可回到 RAW 核對|單一 Event ID 不一定等於成功存取；需看 Handle、AccessMask 與關聯事件|檔案存取證據表|確認稽核來源與事件 ID;串聯帳號、來源與物件;解讀 access mask 和結果;標記缺少的刪除、權限或成功證據
51|AD、使用者與 IP 關聯|系列五｜事件調查與維運情境|G0／G1|事件查詢、IP 名稱解析與資產資料|建立帳號、來源 IP、設備、登入工作階段與時間的可追溯證據鏈|每個關聯都有來源、有效時間與信心，遇到 DHCP／NAT／共享帳號會標示限制|名稱解析與 IP 對應會隨時間變動；現在的對應不代表事件當時|身分與資產關聯圖|固定調查時間;找登入與 DHCP／資產證據;建立帳號、IP、主機關聯;標記 NAT、共享與時間有效性
52|情資命中與誤判|系列五｜事件調查與維運情境|G0／G1|智慧分析、事件與情資來源紀錄|將情資分數、來源新鮮度、歷史活動、資產角色與實際行為分開判讀|結論列出支持、反對、限制與下一個驗證，不以單一命中直接升級|舊情資、共享 IP、掃描器與 CDN 都可能造成誤判|情資命中分析表|確認來源、分數與更新時間;查事件前後活動;核對資產與業務角色;依證據決定忽略、監看或升級
53|調查報告與交接|系列五｜事件調查與維運情境|G0／G1|調查工作紙與核准的匯出結果|寫出事實、假設、限制、影響、時間線、下一步與證據保存方式|接班者能依查詢條件與證據索引重現結論，知道哪些仍未證實|報告不得混淆事件時間與撰寫時間，也不能貼出不必要敏感資料|一頁調查報告|先寫影響與時間範圍;分開事實、假設與限制;引用可重現證據;指定下一步、負責角色與更新時間
54|跨資料事件 Capstone|系列五｜事件調查與維運情境|G0／G1|事件、Flow、SNMP、PM 與調查工作紙|在限時內完成查詢、交叉驗證、結論簡報與同儕質詢|交付有替代假設、反證、證據鏈、限制與可執行下一步|限時結論仍須保留不確定性；不得為求完整而編造缺失資料|跨資料調查簡報|五分鐘定義事件;二十分鐘建立多假設;三十分鐘交叉驗證;十五分鐘交付與接受質詢
55|需求訪談與問題定義|系列六｜SE、POC 與客戶導入|G0|訪談工作紙，不進行系統變更|把「想要監控」改寫成資料、範圍、期間、輸出與驗收問題|需求句能被轉成可觀察成功條件，並記錄擁有者、限制與非目標|不要把產品功能清單當需求，也不要在未確認資料可得前承諾結果|需求與驗收問題清單|追問業務情境與決策;確認來源、範圍和保存;定義輸出與時效;寫成可測試成功條件與非目標
56|產品、元件與資料流選擇|系列六｜SE、POC 與客戶導入|G0／G1|架構工作紙；系統資訊只做唯讀核對|依來源、協定、網段、容量與使用者需求選擇 N-Cloud、N-Reporter、N-Probe、Receiver 等角色|架構圖每個元件都有輸入、輸出、責任、健康檢查與失效影響|產品名稱不能取代責任描述；實際版本與授權能力需另核對|元件責任與資料流圖|列出資料來源和消費者;標示協定與信任邊界;分配收集、處理、儲存與查詢責任;檢查單點與監控
57|License 與 Sizing 基礎|系列六｜SE、POC 與客戶導入|G0|官方文件、版本資料與估算工作紙|依 Device、Server Service、SNMP、Flow、PM、Domain 等計量維度做案例估算|每個數字都有來源日期、單位、假設、餘裕與需官方確認項目|授權規則可能依版本與方案改變；教材不取代正式報價或官方文件|License／Sizing 假設表|分類來源與服務;套用當期官方計量單位;估事件量、保存與成長;加入餘裕並列待確認項
58|拓撲、HA 與故障域|系列六｜SE、POC 與客戶導入|G0|架構圖與故障演練工作紙|畫出元件、網段、入口、儲存、備援、管理面與單點故障|每個關鍵元件失效時，資料收集、查詢、告警與復原影響都能說明|畫兩台不等於 HA；還要核對狀態同步、切換、資料一致性與操作責任|拓撲與故障域矩陣|畫正常資料與管理路徑;圈出共享依賴與單點;逐元件模擬失效;定義偵測、切換、復原與驗證
59|POC 計畫與成功條件|系列六｜SE、POC 與客戶導入|G0／G2|POC 計畫、LAB 與清理清單|定義範圍、樣本、日程、責任、成功條件、退出條件與資料清理|每個成功條件都有步驟、預期、證據、負責人與截止時間|POC 不等於無限制試用；沒有退出與清理會留下資料和責任風險|POC 計畫書|鎖定三到五個核心情境;準備資料與環境;定義逐項驗收證據;安排結束、歸還、刪除與決策
60|初始設定與資料接入|系列六｜SE、POC 與客戶導入|G2；網路、帳號與正式來源為 G3|LAB 快速設定、設備管理與事件查詢；入口依版本核對|完成來源到接收、解析、儲存與查詢的最小可驗證資料流|每一段都有時間、狀態、樣本與查詢證據，失敗可指出斷點|一次接很多來源會放大排錯；先用單一去識別樣本完成 tracer bullet|最小資料流驗收包|確認 Gate 與回復;接一個最小來源;逐段驗證接收、解析與儲存;以查詢和 RAW 對帳後清理
61|效能、容量與保存策略|系列六｜SE、POC 與客戶導入|G0／G1|系統資訊、報表與容量工作紙|估算事件量、Flow、保存期間、成長、尖峰與查詢負載，記錄假設|模型可由來源數、每日量、壓縮假設與保存天數重算，並有實測校正點|平均每日量不足以代表尖峰；壓縮率與索引成本不能用猜測當承諾|容量模型與校正計畫|蒐集平均與尖峰樣本;按資料類型分開估算;加入保存、索引與成長;用 POC 實測校正並留餘裕
62|驗收、UAT 與缺陷管理|系列六｜SE、POC 與客戶導入|G0／G1／G2|UAT 工作紙與核准 LAB|把需求轉成可重現步驟、前置條件、預期、實際、證據與缺陷狀態|不同測試者可重現結果，失敗有嚴重度、擁有者、修復版本與重測證據|「看起來正常」不是驗收；缺陷關閉必須有修復與重測證據|UAT 與缺陷追蹤表|從需求建立測試 ID;寫前置、步驟與預期;保存實際結果和證據;分級、修復、重測並取得簽認
63|Runbook、交接與教育訓練|系列六｜SE、POC 與客戶導入|G0／G1|Runbook、聯絡表與演練工作紙|產出日常操作、告警處理、備份、升級聯絡與禁止事項，讓接手者可執行|新接手者能在不口頭提示下完成一項日常檢查與一項告警演練|Runbook 不是功能手冊複製；必須包含現場責任、例外、停止與升級條件|可演練 Runbook|列出角色與聯絡順序;寫日常與事件步驟;加入預期、失敗與停止條件;由非作者演練並修正
64|客戶導入 Capstone|系列六｜SE、POC 與客戶導入|G0／G2；正式變更為 G3|文件包與核准 LAB tracer bullet|完成需求、架構、Sizing、POC、驗收、Runbook 與交接的整體提案|文件彼此一致，成功條件有證據，風險、假設、責任與未決項透明|簡報漂亮不能取代可驗證資料流、驗收結果與退出方案|客戶導入交付包|整理需求與非目標;完成架構與容量假設;跑最小 POC 與 UAT;交付 Runbook、風險、決策與清理
65|N-Partner 產品線與定位|系列七｜NPSC 證照準備|G0|當期官方公開文件與產品比較表|為客戶情境選合適產品角色並排除不適用選項|每個選擇都以需求、資料流與當期官方定位說明，不靠名稱猜測|產品線、版本與政策會變；每次考前必須重新核對官方資料|產品情境比較表|辨識情境需求;列出候選產品責任;用資料來源與輸出排除;標記需以官方版本再確認的項目
66|架構、元件與核心技術|系列七｜NPSC 證照準備|G0|官方公開範圍與架構題工作紙|比較 N-Cloud、N-Reporter、N-Probe、External Receiver 的責任與資料流|能從來源、處理、儲存、分析與遠端接收情境選元件並說明錯項|不背縮寫配對；題目改寫後仍要靠責任與資料流判斷|元件責任速查圖|先畫來源到使用者;定位收集、處理、儲存與分析;加入遠端和故障情境;逐一解釋不適用選項
67|Syslog、Flow、SNMP、PM 高頻觀念|系列七｜NPSC 證照準備|G0|情境題與四類資料比較表|用情境快速選資料來源，並說明其他三種為何不能直接回答|每題包含正確來源、可證明範圍、不能證明範圍與補充資料|不要把「可協助」誤寫成「單獨證明」；尤其 Flow 沒有完整內容、Ping 不等於應用|四類資料情境題組|抓題目要回答的名詞;選最直接的資料來源;排除只能旁證的選項;補上驗證限制
68|常用操作、Dashboard 與稽核|系列七｜NPSC 證照準備|G0／G1|事件查詢、Top N、Dashboard、操作歷程與名稱解析|完成查詢、排行、Dashboard 與使用者／IP 關聯題組，辨識操作目的|能把每個情境配到功能類型與證據，而不是死背選單字樣|UI 路徑可能依版本和角色改變；考前以官方當期環境為準|常用操作情境地圖|先判斷查詢、呈現或稽核目的;選時間和範圍;指定輸出證據;說明版本與權限限制
69|License 計算專題|系列七｜NPSC 證照準備|G0|當期官方 License 規則與計算工作紙|完成 Device、Server Service、SNMP、Flow、PM、Domain 案例並寫出假設|算式逐項標示計量單位、去重方式、版本日期與官方待確認項|不得從缺少選項的題綱猜標準答案，也不能沿用過期授權規則|License 計算題組|圈出所有計量名詞;依當期規則分類;逐項列算式與去重;做反算和邊界案例檢查
70|採購、保固與 MA|系列七｜NPSC 證照準備|G0|當期官方政策、合約與案例工作紙|用案例分辨採購、保固、維護與服務責任，建立考前更新清單|每個答案標示適用產品、日期、條款來源與需詢問窗口|商務政策變動快；教材只教核對方法，不宣稱永久期限或價格|政策核對卡|辨識案例是產品、保固或服務;查當期官方條款;分開標準與例外;記錄日期、來源與升級窗口
71|NPSC 模擬考一|系列七｜NPSC 證照準備|G0|依當期官方公開題數與時間設定；不使用真實考題|進行等比例概念模擬，建立錯題分類與信心標記|作答後能把錯誤分成觀念、題幹、計算、版本與時間管理|未校驗的 NPSC.txt 只有題綱，不能當答案來源；模擬題為能力練習|第一次模擬與錯題簿|核對當期公開規則;限時作答並標信心;依能力類別檢討;排出兩項補強優先序
72|NPSC 模擬考二與補強|系列七｜NPSC 證照準備|G0|第二套能力模擬與考前檢查表|更換情境第二次限時模擬，驗證補強是否有效並完成考前清單|弱項正確率、作答時間與過度自信題都有前後比較|只重做相同題目會記答案而非補能力；需更換情境與數字|第二次模擬與考前清單|以新情境重新測弱項;比較正確率與時間;複習低信心高風險題;完成版本、證件與應試清單
73|NPEC 能力地圖與限時策略|系列八｜NPEC／專家實機準備|G0|依官方公開能力與自建模擬任務|把任務拆成讀題、規劃、實作、驗證、排錯與交付，分配限時預算|每階段有時間盒、完成證據、停止條件與保底交付|題數、配分與能力範圍必須以當期可追溯的官方公開來源複核；無來源時維持 UNKNOWN|限時作戰板|先圈交付與限制;安排依賴和風險;預留驗證與排錯;設定超時降級與最後交付
74|需求轉架構與 License|系列八｜NPEC／專家實機準備|G0|限時架構與估算工作紙|在限時內完成元件、拓撲、容量、License、風險與驗收設計|架構圖與算式可追溯需求，假設與待官方確認項目清楚|缺資料時要寫假設與詢問，不可為了作答編造環境數字|限時架構包|擷取來源、量與服務需求;畫最小資料流和故障域;列 License 與容量算式;補驗收、風險與問題清單
75|設備納管、名稱解析與查詢|系列八｜NPEC／專家實機準備|G2；正式設備與網路為 G3|設備管理、名稱解析、事件查詢；依 LAB 版本核對|在 LAB 完成最小資料流、名稱解析與查詢，保留每段驗證證據|設備、資料接收、解析、名稱顯示與查詢結果都有可回復紀錄|納管會影響 License、輪詢與資料量；只操作核准 LAB 物件|設備納管 tracer bullet|確認 Gate、License 與回復;建立 Gimmy-LAB 設備或模擬來源;驗證收資料與名稱;查詢後刪除並確認無殘留
76|正規化與異常樣本修正|系列八｜NPEC／專家實機準備|G0／G2|自定義資料格式與 parser 測試|在限時內建立 parser，處理缺欄、編碼、異常字元與格式版本|正反案例全部重跑，欄位字典、差異與回復版本齊全|不能只修考題中的一筆；需避免新規則破壞既有格式|限時 parser 測試包|先保留原始樣本與預期;做最小正常 parser;加入三種異常案例;全組回歸並提交限制
77|TopN、監控、通知與 Dashboard|系列八｜NPEC／專家實機準備|G2；通知為 G3|Top N、監控、Dashboard 與核准測試通道|將資料轉成排行、監控與展示，使用測試通道驗證完整證據鏈|Dashboard 可追到查詢，告警可由回放觸發，通知只到核准測試端|展示、告警與通知是不同契約；任何一段成功都不代表全鏈完成|監控展示 tracer bullet|先做可重現查詢與 TopN;建立最小 LAB 規則;把狀態放入 Dashboard;經 Gate 發一則測試通知並清理
78|故障注入與系統化排錯|系列八｜NPEC／專家實機準備|G0／G2；不得破壞正式資料流|模擬環境與已知故障卡|處理資料未進來、時間錯誤、權限、查詢與通知失敗，依層次排錯|每個故障都有症狀、假設、最小測試、修正、回歸與根因紀錄|故障注入必須可逆且有停止條件；不得關閉正式服務來製造案例|故障排錯紀錄|先保存健康基準;一次注入一個可逆故障;由外到內縮小斷點;修復後重跑端到端 smoke
79|三小時整合模擬一|系列八｜NPEC／專家實機準備|G0／G2；所有 G3 步驟以設計替代|自建情境一與核准 LAB|完整執行需求、設定、查詢、Dashboard、排錯與說明，留下時間紀錄|三小時內有可驗證核心流程、風險清單、失敗證據與口頭說明|模擬題不是官方真題；以能力與證據品質評分，不猜官方配分|整合模擬一交付包|二十分鐘讀題規劃;九十分鐘做 tracer bullet;四十分鐘補功能與排錯;三十分鐘驗證、清理與簡報
80|三小時整合模擬二|系列八｜NPEC／專家實機準備|G0／G2；所有 G3 步驟以設計替代|更換來源、限制與故障的自建情境二|以不同情境重做，依第一次錯誤模式調整順序、時間與保底策略|第二次交付在核心完成率、回歸證據與時間分配上可量化改善|不要重用第一次答案；情境、數字、故障與資料格式都要更換|整合模擬二與改善報告|先回顧第一次三大失誤;用新情境重新規劃;保留驗證和清理時間;比較兩次證據與完成率
81|Backend 導覽與系統資訊|系列九｜Backend、維護與升級|G1|系統管理 → 領域資訊；其他 Backend 入口依部署與權限核對|找到 UI 版本、Kernel、角色、服務、容量與健康證據，不做變更|環境卡清楚分開 UI、Kernel、節點、時區、License 與觀察時間|版本字串彼此不可混稱；沒有權限看到的項目要標 UNKNOWN|Backend 環境卡|確認環境與角色;分開記錄 UI 與 Kernel;查看服務、資源與資料狀態;標示未知、證據時間與禁止事項
82|備份範圍與還原點|系列九｜Backend、維護與升級|G1／G2；正式備份與還原為 G3|備份設計、唯讀清單與核准 LAB 還原測試|建立設定、資料、憑證、secret、License 與文件的備份清單，驗證可讀性|每個備份有擁有者、範圍、時間、位置、加密、保留與還原測試結果|看到備份檔不代表可還原；secret 不得寫入教材、Repo 或驗收摘要|備份目錄與還原證據|盤點需保護資產;定義一致性與還原點;驗證檔案、權限和 checksum;在隔離 LAB 做還原抽測
83|資料庫、儲存與保存容量|系列九｜Backend、維護與升級|G1；清理與策略變更為 G3|系統資訊、容量監控與資料庫唯讀觀察|觀察容量趨勢、保存策略、成長率與查詢影響，設定預警設計|模型包含可用容量、每日成長、尖峰、保留、索引與預計耗盡日|直接刪資料或改 retention 是高風險；本課只做唯讀觀察與方案|容量趨勢與預警計畫|記錄容量與觀察時間;按資料類型估每日成長;計算不同保留情境;提出門檻、擴充與核准清理方案
84|服務、Log 與健康檢查|系列九｜Backend、維護與升級|G1；重啟與設定變更為 G3|系統資訊、服務狀態與系統紀錄；命令依部署文件核對|從服務狀態、系統紀錄、端點與資料流定位問題層次|健康檢查同時包含程序、依賴、端口、寫入、查詢與時間戳|程序存在不代表功能健康；不得看到紅燈就直接重啟|分層健康檢查表|先看使用者症狀與最近變更;檢查服務和依賴;驗證資料進、處理、存、查;提出最小修復與回復 Gate
85|版本矩陣、Kernel 與相容性|系列九｜Backend、維護與升級|G1|系統資訊、官方 release note 與相容性矩陣|區分 UI、Kernel、OS、資料庫與元件版本，不因版本號相近就混用套件或路徑|版本矩陣標示現況、目標、支援來源、依賴與禁止組合|相近版本號不代表套件可互換；未取得官方相容證據即為 UNKNOWN|版本與相容性矩陣|盤點所有元件版本;對照當期官方文件;標示升級順序與阻塞;凍結核准套件與 checksum
86|Checksum、變更計畫與 Gate|系列九｜Backend、維護與升級|G1／G2；執行正式變更為 G3|變更單、套件清單與隔離驗證環境|核對檔案 checksum、備份、窗口、風險、回復、核准與通訊計畫|執行前 checksum 與核准清單一致，任何 UNKNOWN 都會阻止 Gate 放行|檔名相同不代表內容相同；checksum 接受後需凍結，不可臨時替換|變更 Gate 套件|確認需求、範圍與擁有者;驗證來源、簽章與 checksum;完成備份、回復和溝通;逐 Gate 記錄 go／no-go
87|LAB 升級計畫與驗證設計|系列九｜Backend、維護與升級|G3（本課 plan-only；實際執行須另案核准）|隔離 LAB 升級計畫，不操作未授權服務|規劃並評估升級前、中、後 checkpoint 與代表性功能 smoke；未核准前不得執行|計畫須定義版本、服務、收資料、查詢、Dashboard、權限與排程的前後證據欄，不能宣稱已完成升級|本課只有 plan-only 成果；未知版本、備份、rollback 或核准任一項即停止，不得執行 LAB 或正式環境升級|LAB 升級計畫與評估報告|凍結版本矩陣與 checksum 計畫;設計備份與回復點驗證;規劃逐 Gate checkpoint 與紀錄欄;設計功能 smoke、接受或 rollback 決策
88|回復與災難演練|系列九｜Backend、維護與升級|G3（本課 plan-only；實際執行須另經核准）|隔離 LAB／災難演練計畫，不操作未授權正式服務|依故障情境規劃 rollback 或 restore 演練，評估 RTO、RPO、缺口與改善；未核准前不得執行|計畫須要求還原後驗證資料完整、權限、查詢、告警與交接；不能宣稱已完成實際復原|本課只有 plan-only 成果；沒有範圍、核准、回復與觀察者時不得執行 rollback、restore 或正式環境操作|災難演練計畫與評估報告|宣告情境、RTO、RPO 與成功條件;規劃隔離故障及 rollback 或 restore 決策;列出資料與核心功能驗證矩陣;安排時間紀錄、缺口追蹤與改善責任
"""

SERIES_RANGE = {
    range(19, 25): ("SERIES 2 · HANDS-ON", "實機操作"),
    range(25, 35): ("SERIES 3 · NORMALIZATION", "資料接入與正規化"),
    range(35, 45): ("SERIES 4 · MONITORING", "監控、告警與自動化"),
    range(45, 55): ("SERIES 5 · INVESTIGATION", "事件調查與維運情境"),
    range(55, 65): ("SERIES 6 · DELIVERY", "SE、POC 與客戶導入"),
    range(65, 73): ("SERIES 7 · NPSC", "NPSC 證照準備"),
    range(73, 81): ("SERIES 8 · NPEC", "NPEC／專家實機準備"),
    range(81, 89): ("SERIES 9 · BACKEND", "Backend、維護與升級"),
}


def parse_specs() -> list[Lesson]:
    lessons = []
    for raw in SPECS_TEXT.strip().splitlines():
        parts = [part.strip() for part in raw.split("|")]
        if len(parts) != 10:
            raise ValueError(f"Expected 10 columns, got {len(parts)}: {raw}")
        number, title, series, gate, location, objective, evidence, boundary, deliverable, steps = parts
        step_items = tuple(part.strip() for part in steps.split(";"))
        if len(step_items) != 4:
            raise ValueError(f"Expected four steps for lesson {number}")
        lessons.append(Lesson(int(number), title, series, gate, location, objective, evidence, boundary, deliverable, step_items))
    if [item.number for item in lessons] != list(range(19, 89)):
        raise ValueError("Lesson numbers must be continuous from 19 to 88")
    return lessons


def load_cases() -> dict[int, Case]:
    path = ROOT / "content" / "lesson_cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("lesson_cases.json must contain a list")
    cases: dict[int, Case] = {}
    for raw in payload:
        if not isinstance(raw, dict):
            raise ValueError("Each lesson case must be an object")
        number = raw.get("n")
        wrong = raw.get("wrong")
        rubric = raw.get("rubric")
        if not isinstance(number, int) or not isinstance(wrong, list) or not isinstance(rubric, list):
            raise ValueError(f"Invalid case schema: {raw}")
        if len(wrong) != 2 or len(rubric) != 3 or not all(isinstance(value, str) and value.strip() for value in [raw.get("input"), raw.get("question"), raw.get("correct"), *wrong, *rubric]):
            raise ValueError(f"Invalid case content for lesson {number}")
        cases[number] = Case(number, raw["input"], raw["question"], raw["correct"], tuple(wrong), tuple(rubric))
    if sorted(cases) != list(range(19, 89)):
        raise ValueError("Case numbers must be continuous from 19 to 88")
    return cases


def load_lesson_packs() -> dict[int, dict]:
    """Load the lesson-specific teaching, lab, assessment, and source packs."""
    path = ROOT / "content" / "lesson_packs.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("lesson_packs.json must contain a list")
    packs: dict[int, dict] = {}
    for raw in payload:
        if not isinstance(raw, dict) or not isinstance(raw.get("n"), int):
            raise ValueError(f"Invalid lesson pack: {raw}")
        number = raw["n"]
        if number in packs:
            raise ValueError(f"Duplicate lesson pack: {number}")
        packs[number] = raw
    if sorted(packs) != list(range(19, 89)):
        raise ValueError("Lesson pack numbers must be continuous from 19 to 88")
    return packs


def gate_guidance(item: Lesson) -> str:
    if item.number in {87, 88}:
        return "本課為 plan-only，只規劃逐項核准、隔離 LAB、可驗證備份、維護窗口、停止條件與 rollback owner；未核准前不得執行。實際 G3 動作須另案核准並依受控程序執行，本課不予放行。禁止在正式環境演練。"
    if item.number in {39, 40, 41}:
        return "只有具逐項核准且使用隔離測試收件匣或端點時，才可執行一次本課 G3 測試；否則只完成 plan／dry-run。禁止正式收件者、正式資料與無上限重試。"
    if item.gate.startswith("G3"):
        return "本課只完成 G3 的 plan、dry-run、審核、停止與 rollback 演練，不連正式執行端；任何實際作用都需要另一張逐項核准 Gate。"
    return "先用 G0／G1 建立證據，再依核准進 G2；任何外送、正式來源、自動執行、升級、重啟或回復都停在 G3 Gate 前。"


def zh_number(number: int) -> str:
    digits = "零一二三四五六七八九"
    if number < 10:
        return digits[number]
    tens, ones = divmod(number, 10)
    prefix = "十" if tens == 1 else digits[tens] + "十"
    return prefix + (digits[ones] if ones else "")


def series_label(number: int) -> tuple[str, str]:
    for numbers, labels in SERIES_RANGE.items():
        if number in numbers:
            return labels
    raise KeyError(number)


def lesson_html(item: Lesson, all_lessons: list[Lesson], cases: dict[int, Case] | None = None, packs: dict[int, dict] | None = None) -> str:
    n = item.number
    case = (cases or load_cases())[n]
    pack = (packs or load_lesson_packs())[n]
    zh = zh_number(n)
    eyebrow, series_short = series_label(n)
    prev_href = f"../day{n-1:02d}/"
    next_href = f"../day{n+1:02d}/" if n < 88 else "../curriculum/"
    next_label = f"第{zh_number(n+1)}課" if n < 88 else "完成 88 課路線"
    next_title = all_lessons[n-18].title if n < 88 else "依角色選路線，持續用證據工作"
    prerequisites = "".join(f"<li>{escape(value)}</li>" for value in pack["prerequisites"])
    concepts = "".join(
        f'<article><span>{escape(concept["term"])}</span><h3>{escape(concept["explanation"])}</h3><p><b>別混淆：</b>{escape(concept["confusion"])}</p></article>'
        for concept in pack["concepts"]
    )
    guided_steps = "".join(
        f'<article><span>{index}</span><h3>{escape(step["action"])}</h3><p><b>輸入：</b>{escape(step["input"])}</p><p><b>預期：</b>{escape(step["expected"])}</p><p><b>證據：</b>{escape(step["evidence"])}</p><p><b>失敗：</b>{escape(step["failure"])}</p></article>'
        for index, step in enumerate(pack["guided_steps"], 1)
    )
    fixture = pack["fixture"]
    fixture_headers = "".join(f'<th scope="col">{escape(value)}</th>' for value in fixture["columns"])
    fixture_rows = "".join(
        "<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in row) + "</tr>"
        for row in fixture["rows"]
    )
    task = pack["independent_task"]
    task_constraints = "".join(f"<li>{escape(value)}</li>" for value in task["constraints"])
    artifact_fields = "".join(f"<li>{escape(value)}</li>" for value in task["artifact_fields"])
    acceptance_rows = "".join(
        f'<tr><td>{escape(item["criterion"])}</td><td>{escape(item["pass"])}</td><td>{escape(item["fail"])}</td><td>{item["points"]}</td></tr>'
        for item in pack["acceptance"]
    )
    troubleshooting = "".join(
        f'<article><h3>{escape(item["symptom"])}</h3><p><b>最小檢查：</b>{escape(item["check"])}</p><p><b>預期：</b>{escape(item["expected"])}</p><p><b>修正：</b>{escape(item["fix"])}</p><p><b>停止／升級：</b>{escape(item["stop"])}</p></article>'
        for item in pack["troubleshooting"]
    )
    sources = "".join(
        '<li>'
        + (f'<a href="{escape(source["url"], quote=True)}" rel="noopener noreferrer">{escape(source["title"])}</a>' if source["url"] else f'<strong>{escape(source["title"])}</strong>')
        + f'｜{escape(source["status"])}｜複核：{escape(source["reviewed"])}｜適用：{escape(source["applies"])}</li>'
        for source in pack["sources"]
    )
    worksheet_fields = "".join(
        f'<label for="notes-artifact-{index}"><span>{escape(label)}</span><small>依 fixture 與驗收表填寫；未知項必須明示。</small><textarea id="notes-artifact-{index}" data-notes="artifact-{index}" rows="6" placeholder="填寫：{escape(label)}"></textarea></label>'
        for index, label in enumerate(task["artifact_fields"], 1)
    )
    reference_answer = "".join(f"<li>{escape(value)}</li>" for value in task["reference_answer"])
    checkpoint_correct = pack["acceptance"][0]["pass"]
    checkpoint_wrong = (pack["acceptance"][0]["fail"], pack["acceptance"][1]["fail"])
    case_choices = [
        ("case-wrong-a", escape(case.wrong[0])),
        ("case-correct", escape(case.correct)),
        ("case-wrong-b", escape(case.wrong[1])),
    ]
    case_choices = case_choices[n % 3:] + case_choices[:n % 3]
    case_options = "".join(f'<button type="button" data-choice="{choice}">{label}</button>' for choice, label in case_choices)
    artifact_choices = [
        ("artifact-fail-a", escape(checkpoint_wrong[0])),
        ("artifact-pass", escape(checkpoint_correct)),
        ("artifact-fail-b", escape(checkpoint_wrong[1])),
    ]
    artifact_offset = (n + 1) % 3
    artifact_choices = artifact_choices[artifact_offset:] + artifact_choices[:artifact_offset]
    artifact_options = "".join(f'<button type="button" data-choice="{choice}">{label}</button>' for choice, label in artifact_choices)
    safe_location = escape(item.location)
    objective = escape(item.objective)
    evidence = escape(item.evidence)
    boundary = escape(item.boundary)
    deliverable = escape(item.deliverable)
    gate = escape(item.gate)
    case_input = escape(case.input)
    case_question = escape(case.question)
    case_correct = escape(case.correct)
    case_wrong = tuple(escape(value) for value in case.wrong)
    rubric = "".join(f"<li>{escape(value)}</li>" for value in case.rubric)
    safety = escape(gate_guidance(item))
    goal_action = "依四步流程完成計畫與評估" if n in {87, 88} else "依四步流程完成實作"
    next_kicker = "下一課" if n < 88 else "完成路線"
    next_copy = f"{series_short}路線會把本課成果帶進下一個可驗收工作。" if n < 88 else "回到完整路線，依角色複習、重做 Capstone 或安排實機 Gate。"
    return f'''<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="第{zh}課：{escape(item.title)}，含目的、證據、實作、驗收與排錯"><title>第{zh}課｜{escape(item.title)}</title><link rel="stylesheet" href="../assets/styles.css"><script src="../assets/lesson-practice.js" defer></script></head>
<body data-lesson="lesson{n:02d}" data-lesson-name="第{zh}課"><a class="skip-link" href="#main">跳到主要內容</a><header class="site-header lesson-header"><a class="brand" href="../"><span class="brand-mark">N</span><span>N-Cloud Learning</span></a><nav aria-label="課程導覽"><a href="../curriculum/">完整路線</a><a href="{prev_href}">第{zh_number(n-1)}課</a><span>第{zh}課</span></nav></header>
<main id="main"><section class="lesson-hero wrap"><div><p class="eyebrow">{eyebrow} · LESSON {n:02d}</p><h1>{escape(item.title)}<br><em>做出能被核對的成果</em></h1><p class="hero-copy">{objective}</p></div><aside class="goal-card" aria-label="本課學習目標"><span>本課目標</span><ol><li>先說明目的與證據界線</li><li>{goal_action}</li><li>交付「{deliverable}」並能排錯</li></ol><small>建議時間：約 70–90 分鐘｜{gate}</small></aside></section>
<div class="lesson-layout wrap"><aside class="lesson-nav" aria-label="本課章節"><p>本課章節</p><a href="#purpose">01 目的與成果</a><a href="#concepts">02 先備與概念</a><a href="#location">03 位置與界線</a><a href="#fixture">04 練習資料</a><a href="#guided">05 逐步跟做</a><a href="#practice-one">06 判讀檢查</a><a href="#practice-two">07 獨立任務</a><a href="#worksheet">08 產物工作紙</a><a href="#acceptance">09 100 分驗收</a><a href="#troubleshoot">10 專屬排錯</a><a href="#sources">11 來源與版本</a><a href="#debrief">12 教師版</a><a href="#complete">13 完成紀錄</a></aside><article class="lesson-content">
<section id="purpose" class="lesson-section"><p class="section-index">01</p><h2>先確定這課要解決什麼</h2><div class="metric-grid"><article><span>Question</span><strong>核心問題</strong><small>{objective}</small></article><article><span>Artifact</span><strong>{deliverable}</strong><small>不是只看畫面，而是留下可交接成果</small></article><article><span>Evidence</span><strong>可重現</strong><small>{evidence}</small></article><article><span>Boundary</span><strong>不超過證據</strong><small>{boundary}</small></article></div></section>
<section id="concepts" class="lesson-section"><p class="section-index">02</p><h2>先備能力與三個本課概念</h2><div class="acceptance-box"><b>開始前先確認</b><ul>{prerequisites}</ul></div><div class="metric-grid lesson-concepts">{concepts}</div></section>
<section id="location" class="lesson-section"><p class="section-index">03</p><h2>位置、版本與安全 Gate</h2><div class="formula-card"><span>候選入口｜必須以實機版本與角色核對</span><strong>{safe_location}</strong><p>教材只固定工作目的與驗收證據，不把未核對的子選單、按鈕或欄位畫成真實 UI。</p></div><div class="lab-card"><span>{gate}</span><h3>操作邊界</h3><ol><li>G0 可用去識別樣本反覆練習。</li><li>G1 只查詢、檢視與核准匯出。</li><li>G2 僅在核准 LAB 建立可清理物件。</li><li>任何外送、正式來源、自動執行、升級或服務變更均須逐項 G3 Gate。</li></ol></div></section>
<section id="fixture" class="lesson-section"><p class="section-index">04</p><h2>{escape(fixture["title"])}</h2><div class="record-sample lesson-case"><span>本課 fixture｜去識別／文件保留範圍</span><p>{case_input}</p><small>資料供本課計算、判讀與故障練習，不代表正式產品輸出。</small></div><div class="breakpoint-table-wrap" tabindex="0" aria-label="可左右捲動：第{zh}課練習資料"><table class="breakpoint-table"><caption>{escape(fixture["title"])}｜教學模擬資料</caption><thead><tr>{fixture_headers}</tr></thead><tbody>{fixture_rows}</tbody></table></div></section>
<section id="guided" class="lesson-section"><p class="section-index">05</p><h2>跟著做：每一步都有預期與失敗訊號</h2><div class="stage-list deep-steps">{guided_steps}</div><p class="data-note"><b>停止條件：</b>環境、角色、版本、影響範圍、回復方式或核准任一項不清楚，就停在觀察與設計。</p></section>
<section id="practice-one" class="lesson-section practice-section"><p class="section-index">06</p><p class="practice-label">觀念檢查 · 約 10 分鐘</p><h2>用 fixture 判讀案例</h2><div class="quiz-card" data-quiz="case-{n}" data-correct="case-correct" data-explain="可核對答案：{case_correct}" data-hint="回到 fixture，分開已知、未知、證據界線與 Gate。"><h3>{case_question}</h3><div class="quiz-options">{case_options}</div><p class="quiz-status" data-quiz-status>尚未答對</p><div class="feedback" data-feedback hidden></div></div><div class="acceptance-box"><b>案例檢查點</b><ul>{rubric}</ul></div></section>
<section id="practice-two" class="lesson-section practice-section"><p class="section-index">07</p><p class="practice-label">獨立任務 · 約 25 分鐘</p><h2>{escape(task["brief"])}</h2><div class="compare-grid"><article><h3>限制</h3><ul>{task_constraints}</ul></article><article><h3>必交欄位</h3><ul>{artifact_fields}</ul></article></div><div class="quiz-card" data-quiz="artifact-{n}" data-correct="artifact-pass" data-explain="通過條件：{escape(checkpoint_correct)}" data-hint="用下方 100 分驗收表判斷，不以完成按鈕取代產物。"><h3>針對「{escape(task["brief"])}」，哪個描述達到第一項通過條件？</h3><div class="quiz-options">{artifact_options}</div><p class="quiz-status" data-quiz-status>尚未答對</p><div class="feedback" data-feedback hidden></div></div></section>
<section id="worksheet" class="lesson-section worksheet-section"><p class="section-index">08</p><p class="practice-label">產物工作紙 · 約 20 分鐘</p><h2>填妥本課交付物</h2><p class="lead">每一欄都對應本課必交產物；內容只保存在這個瀏覽器並可列印。請勿填入帳密、token、認證材料或客戶識別。</p><div class="worksheet-grid">{worksheet_fields}</div><p class="worksheet-status" data-notes-status role="status">工作紙 0 / {len(task["artifact_fields"])} 欄已填</p></section>
<section id="acceptance" class="lesson-section"><p class="section-index">09</p><h2>完成條件：100 分驗收表</h2><div class="breakpoint-table-wrap" tabindex="0" aria-label="可左右捲動：本課量化驗收表"><table class="breakpoint-table"><caption>本課產物驗收｜總分 100，70 分通過；任一安全 Gate 違反仍不通過</caption><thead><tr><th scope="col">項目</th><th scope="col">通過</th><th scope="col">不通過</th><th scope="col">分數</th></tr></thead><tbody>{acceptance_rows}</tbody></table></div></section>
<section id="troubleshoot" class="lesson-section"><p class="section-index">10</p><h2>本課專屬排錯</h2><div class="troubleshoot-grid">{troubleshooting}</div></section>
<section id="sources" class="lesson-section"><p class="section-index">11</p><h2>來源、版本與複核狀態</h2><ul class="source-list">{sources}</ul><p class="data-note"><b>來源 Gate：</b>標示 CONTROLLED_SOURCE_REQUIRED 的產品能力、路徑、授權或政策，在取得當期受控來源前一律是 UNKNOWN，不作為正式操作或報價依據。</p></section>
<section id="debrief" class="lesson-section"><p class="section-index">12</p><h2>教師版與錯項解析</h2><div class="key-point"><b>案例答案</b><p>{case_correct}</p></div><div class="compare-grid"><article><h3>錯項一</h3><p>{case_wrong[0]}</p></article><article><h3>錯項二</h3><p>{case_wrong[1]}</p></article></div><details class="reference-answer"><summary>完成獨立任務後再展開參考成果</summary><ul>{reference_answer}</ul></details><div class="key-point"><b>安全界線</b><p>{safety}</p></div></section>
<section id="complete" class="lesson-section"><p class="section-index">13</p><h2>完成第{zh}課學習紀錄</h2><p class="lead">兩題答對、產物工作紙 {len(task["artifact_fields"])} 欄完成，並確認三項能力；本頁完成不等於實機認證通過。</p><label class="check-row"><input type="checkbox" data-progress="purpose"><span>我能說明本課目的、位置與安全 Gate</span></label><label class="check-row"><input type="checkbox" data-progress="evidence"><span>我能依 100 分表驗收「{deliverable}」</span></label><label class="check-row"><input type="checkbox" data-progress="boundary"><span>我知道本課證據不能證明什麼，以及何時停止</span></label><div class="progress-row"><span id="progress-text">0 / 3</span><div class="progress-track" role="progressbar" aria-label="本課自評進度" aria-valuemin="0" aria-valuemax="3" aria-valuenow="0"><i id="progress-bar"></i></div></div><button class="button primary" id="finish-button" type="button">完成第{zh}課</button><p id="completion-message" class="completion-message" role="status"></p><div class="next-lesson-note"><span>{next_kicker}</span><strong>{escape(next_title)}</strong><p>{escape(next_copy)}</p><a class="text-link" href="{next_href}">{next_label} →</a></div></section>
</article></div></main><footer><div class="wrap"><a href="{prev_href}">← 第{zh_number(n-1)}課</a><a href="../curriculum/">回完整課程地圖</a><a href="{next_href}">{next_label} →</a></div></footer></body></html>
'''


def update_curriculum_links(lessons: list[Lesson]) -> None:
    """Replace each advanced-series list with canonical linked lesson titles."""
    path = ROOT / "curriculum" / "index.html"
    html = path.read_text(encoding="utf-8")
    foundation = [
        (1, "N-Cloud 在做什麼"),
        (2, "資料如何進入 N-Cloud"),
        (3, "Syslog 欄位與事件"),
        (4, "Flow 與通聯分析"),
        (5, "SNMP 與設備健康"),
        (6, "PM、SLA 與服務品質"),
        (7, "時間範圍與搜尋條件"),
        (8, "TopN、報表與 Dashboard"),
        (9, "門檻、規則與告警"),
        (10, "故障排查方法"),
        (11, "資安事件調查"),
        (12, "綜合事件調查"),
    ]
    early = [
        (13, "LAB 安全、版本與角色權限"),
        (14, "系統資訊與設備樹"),
        (15, "事件查詢入門"),
        (16, "RAW DATA 與欄位"),
        (17, "IP 名稱解析與 CSV"),
        (18, "儲存查詢與欄位版面"),
    ]
    groups = {
        "系列一 · 01～12": foundation,
        "系列二 · 13～24": early + [(item.number, item.title) for item in lessons if 19 <= item.number <= 24],
        "系列三 · 25～34": [(item.number, item.title) for item in lessons if 25 <= item.number <= 34],
        "系列四 · 35～44": [(item.number, item.title) for item in lessons if 35 <= item.number <= 44],
        "系列五 · 45～54": [(item.number, item.title) for item in lessons if 45 <= item.number <= 54],
        "系列六 · 55～64": [(item.number, item.title) for item in lessons if 55 <= item.number <= 64],
        "系列七 · 65～72": [(item.number, item.title) for item in lessons if 65 <= item.number <= 72],
        "系列八 · 73～80": [(item.number, item.title) for item in lessons if 73 <= item.number <= 80],
        "系列九 · 81～88": [(item.number, item.title) for item in lessons if 81 <= item.number <= 88],
    }
    for label, items in groups.items():
        links = f'<ol start="{items[0][0]}">' + "".join(
            f'<li><a href="../day{number:02d}/">{escape(title)}</a></li>'
            for number, title in items
        ) + "</ol>"
        pattern = rf'(<details[^>]*><summary><span>{re.escape(label)}</span>.*?<div class="series-body"><p>.*?</p>)<ol(?: start="\d+")?>.*?</ol>(</div></details>)'
        html, count = re.subn(pattern, rf"\1{links}\2", html, count=1, flags=re.DOTALL)
        if count != 1:
            raise ValueError(f"Could not update curriculum group: {label}")
    path.write_text(html, encoding="utf-8")


def main() -> None:
    lessons = parse_specs()
    cases = load_cases()
    packs = load_lesson_packs()
    for item in lessons:
        path = ROOT / f"day{item.number:02d}" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(lesson_html(item, lessons, cases, packs), encoding="utf-8")
    update_curriculum_links(lessons)
    curriculum = (ROOT / "curriculum" / "index.html").read_text(encoding="utf-8")
    targets = set(re.findall(r'href="\.\./day(\d{2})/"', curriculum))
    print(f"BUILT_LESSONS count={len(lessons)} first={lessons[0].number} last={lessons[-1].number} curriculum_unique_targets={len(targets)}")


if __name__ == "__main__":
    main()
