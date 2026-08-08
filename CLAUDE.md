# 注音查拼音字典 — 專案脈絡

自用的 iOS 離線字典。核心價值：一般字典說「綠 = lǜ」，但拼音輸入法要敲 **`lv`**，
這個 App 補的就是那段落差。所以**鍵入序列是第一級資訊**，帶調拼音與注音是輔助。

完整說明見 `README.md`。

## 目前狀態（重要）

資料管線**已驗證**：`tools/test_conversions.py` 17 項全過，`tools/build_dict.py`
健檢全過，`dict.sqlite` 已產出並 commit（16 MB，20,924 字／123,769 詞條）。

Swift **從未經過編譯器**。前一個工作階段跑在 Linux 容器裡，沒有 Xcode 也沒有
swiftc，所以整個 App 是寫完後用兩種間接方式驗證的：

- `project.pbxproj` 用自寫的 ASCII plist parser 檢查過解析與物件參照完整性
- `DictionaryStore` + `QueryClassifier` + `SearchViewModel` 的邏輯逐句移植成
  Python，對真的 `dict.sqlite` 跑過各種案例，確認 SQL、排序與 fallback 都正確

**所以第一件事是把它 build 起來，修掉編譯錯誤。**

## 建置與執行

```sh
open PinyinLookup/PinyinLookup.xcodeproj   # Xcode 16+（用了 objectVersion 77 的同步資料夾）
```

模擬器跑起來後的驗收案例：

| 輸入 | 應該看到 |
|---|---|
| `綠色` | 標題 `lv se`／lǜsè／ㄌㄩˋ ㄙㄜˋ；綠的兩個讀音各帶詞例 |
| `銀行` | 標題 `yin hang`；行的 **háng** 那列標「這個詞讀這個」（主讀音是 xíng） |
| `長大` | 長的 **zhǎng** 那列被標記 |
| `謝謝` | xièxie，同一張卡的兩個讀音**都**被標記（同字不同調） |
| `lv` | 率、綠、律…（不是 lu 的字） |
| `lü` | 同上，ü 會正規化成 v |
| `ㄌㄩˋ` | 同上；打 `ㄌㄩ` 不分聲調也要有結果 |
| `zh` | 「還沒打完？以 zh 開頭的敲法：zha、zhe…」 |
| `綠貓` | 逐字拼出來，並顯示「詞庫沒有這個詞」的橘色警告 |

## 第一次 build 特別要留意的地方

這幾處是沒編譯器可驗證時我挑出來的風險點，出錯的話多半在這裡：

1. **`import SQLite3` 的連結**（`Data/Database.swift`）。理論上 SDK 的 module map
   會自動連 libsqlite3；若出現 undefined symbol，在 target 的 Frameworks 加
   `libsqlite3.tbd`，或設 `OTHER_LDFLAGS = -lsqlite3`。
2. **`dict.sqlite` 有沒有真的進 bundle**。用的是 Xcode 16 的同步資料夾群組，資源
   應該會自動進 Resources build phase。App 啟動時若顯示「字典檔載入失敗」就是
   沒進去——去 Build Phases → Copy Bundle Resources 確認。
3. **`@Observable`**（`Search/SearchViewModel.swift`）。刻意沒用 `didSet`，改由
   `SearchView` 的 `onChange` 驅動。若要改動這裡，別把 `didSet` 加回去。
4. **memberwise init 與 `@State private`**。`CopyableKeys`、`CharCardView`、
   `AboutView` 都是 `let` 屬性配 `@State private var`，跨檔案建構。這是標準
   SwiftUI 寫法，但沒編譯驗證過；真的報錯就補一個明確的 `init`。
5. **iOS 17 API**：`ContentUnavailableView`、`.rect(cornerRadius:)`、
   `onChange(of:_:)` 的雙參數版本。deployment target 是 17.0，不要往下調。

## 慣例

- **零第三方依賴**。用系統內建的 libsqlite3，免費 Apple ID 簽名時少一個變數。
- 註解用繁體中文，寫「為什麼」而不是「做了什麼」。
- SQL 全部集中在 `DictionaryStore`，View 只拿 model。
- 資料管線只用 Python 標準庫。改了 `tools/` 就要跑
  `python3 tools/test_conversions.py`。

## 上機（免費 Apple ID）

Signing & Capabilities → Team 選 Personal Team，Bundle ID 已是
`com.baliyoho.pinyinlookup`。憑證 7 天過期，接上電腦重新 Run 即可續期。
