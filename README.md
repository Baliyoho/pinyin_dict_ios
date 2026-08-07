# 注音查拼音字典（iOS，自用）

你會注音，也用注音輸入法打字。看到一個漢字，你知道它怎麼唸，但不知道在**拼音
輸入法**裡要敲哪幾個字母。

一般字典告訴你「綠 = lǜ」。拼音輸入法實際上要敲的是 **`lv`**——不打聲調，ü 敲成 v。
這中間的落差就是這個 App 要解決的問題，所以**「輸入法鍵入序列」是第一級資訊**，
帶調拼音與注音是輔助。

100% 離線、零廣告、開啟即用的單畫面查詢工具。

```
┌─────────────────────────────┐
│  綠色                        │
│  l v   s e            [複製] │  ← 整串鍵入序列，最大最醒目
│  lǜsè · ㄌㄩˋ ㄙㄜˋ           │
└─────────────────────────────┘

  綠   [多音字 2 讀]
  ● lv    lǜ   ㄌㄩˋ    [複製]
    綠色 · 綠豆 · 常綠
  ○ lu    lù   ㄌㄨˋ    [複製]
    綠林 · 綠園 · 鴨綠江
  14 畫 · 部首 糸 · 另作 绿
```

三種輸入自動判斷，不用切模式：**漢字**（綠色）、**注音**（ㄌㄩˋ）、**拼音**（lv，
也吃 lü）。

## 專案結構

```
tools/
  zhuyin_table.py      419 條無調音節的固定對照表 + 三種轉換
  build_dict.py        資料管線：Unihan + CC-CEDICT → dict.sqlite
  test_conversions.py  轉換正確性測試（17 項）
PinyinLookup/
  PinyinLookup.xcodeproj
  PinyinLookup/
    Data/              Database（sqlite3 薄封裝）／DictionaryStore（查詢 API）／Models
    Search/            QueryClassifier（判斷輸入類型）／SearchViewModel
    Views/             SearchView 與各結果卡片、對照表頁、關於頁
    Resources/dict.sqlite
```

SwiftUI，iOS 17+，**零第三方依賴**——用系統內建的 libsqlite3，免費簽名時少一個變數。
DB 唯讀，直接從 app bundle 開啟，不複製到 Documents。

## 上機（免費 Apple ID）

1. `open PinyinLookup/PinyinLookup.xcodeproj`
2. 選 PinyinLookup target → Signing & Capabilities → Team 選你的 Apple ID
   （Personal Team）。Bundle ID 已預設為 `com.baliyoho.pinyinlookup`，被佔用時改一個。
3. iPhone 13 接上、選為執行目標、Run。
4. iPhone 上：設定 → 一般 → VPN 與裝置管理 → 信任該開發者。

**憑證 7 天後過期**，過期後接上電腦重新 Run 一次即可續期，資料與設定不會遺失。
若確定長期使用，再考慮 $99/年 開發者帳號換成一年效期。

先在模擬器跑一遍再上實機。驗收查詢：`綠色`、`銀行`、`長大`、`lv`、`ㄌㄩˋ`。

## 重建字典

`dict.sqlite`（16 MB）已經 commit 進 repo，clone 下來直接就能 build。要重建的話：

```sh
python3 tools/test_conversions.py     # 先確認轉換邏輯正確
python3 tools/build_dict.py           # 下載原始資料 → dict.sqlite → 健檢
python3 tools/build_dict.py --with-definitions   # 額外打包英文釋義
```

純標準庫，不用裝任何東西。原始資料快取在 `tools/.cache/`（已 gitignore）。
管線最後會跑健檢：字數、詞數、`keys` 欄無空值、以及綠／路／女／居／略／六／對
這些已知案例的鍵入序列。

## 幾個值得知道的設計判斷

**`u:` → `v` 這條規則為什麼夠用。** CC-CEDICT 只在 `lu:`/`nu:` 這種會歧義的地方標
冒號；j/q/x/y 後面只可能是 ü，所以本來就寫成 `u`。因此 `ju1` → `ju` 而不是 `jv`。

**詞例綁的是帶調讀音，不是鍵入序列。** 和 hé 與 和 hè 敲起來都是 `he`，只綁 keys
會把「和平」標成 hè 的例子。為此在 `char_word_examples` 多加一欄 `reading_pinyin`
（規格的 schema 之外唯一的增補）。

**詞頻用「這個詞被幾筆詞條包含」當代理值。** CC-CEDICT 沒有詞頻。改用組成字的字頻
會選出「水綠」這種每個字都常見、卻沒人拿來當例子的詞；而常用詞會不斷出現在別的
詞條裡（綠色 出現在綠色食品、綠色和平…），這個訊號準得多。

**查到的詞會標出每個字在這個詞裡讀哪個音。** 查「銀行」時，行的主讀音是 xíng，但
這個詞讀 háng——單字卡會把 háng 那列標成「這個詞讀這個」。少了這個，App 會在使用者
剛查完 `yin hang` 之後用 ● 告訴他行要敲 xing。

**詞庫查不到的詞會逐字取主讀音拼起來，並明講那是推測。** 多音字有機會拼錯，畫面上
會標示，要使用者以下面的單字卡為準。

## 資料來源

| 來源 | 用途 | 授權 |
|---|---|---|
| [Unihan Database](https://www.unicode.org/Public/UNIDATA/Unihan.zip) | 讀音、筆畫、部首、繁簡對應 | Unicode License |
| [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cedict) | 詞語拼音、多音字詞例 | CC BY-SA 4.0 |

收錄 20,924 字（CJK 基本區 U+4E00–U+9FFF 中有讀音的）、123,769 筆詞條。
出處同時標在 App 的「關於」頁。
