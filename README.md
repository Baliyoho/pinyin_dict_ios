# 拼音字典

輸入漢字，查出對應的**拼音輸入**——也就是在拼音鍵盤上實際要打的字母。
純網頁版，加到 iPhone 主畫面後可以完全離線使用。

## 功能

只回答一件事：這些字在 iOS 拼音鍵盤上要按哪些字母。不顯示聲調符號。

- 輸入單字或整句漢字，直接給出要打的字母（`銀行` → `yinhang`）
- 依詞組挑打法：`銀行` 打 `hang`、`重新開始` 打 `chong`，不會逐字亂猜
- 逐字對照卡：漢字配上要打的字母；點一下可看該字的其他拼法（罕用的會標示出來）
- 只差聲調的讀音會合併——`好` hǎo/hào 打起來都是 `hao`，就不會被標成「多種打法」
- `ü` 會提醒在鍵盤上要打 `v`（`綠` → 打 `lv`）
- 一鍵複製整串字母
- 最近查詢記錄，存在手機本機
- 繁體、簡體都能查

## 在 iPhone 上安裝

1. 用 Safari 開啟網址
2. 點下方的「分享」→「加入主畫面」
3. **第一次開啟時保持連線幾秒**，等右上角顯示「已可離線使用」

之後開飛航模式也能查。字典（約 5 MB）會存在手機上，不會再連網。

## 離線是怎麼做的

`public/sw.js` 這個 Service Worker 在安裝時就把整個 App 和兩份字典檔一次寫進裝置的 Cache Storage，
之後所有請求都優先讀快取。右上角的狀態顯示會在資料真的存好之後才變成「已可離線使用」。

因為是快取優先，**每次部署前都要重新產生 Service Worker 的版本編號**，否則已安裝的手機不會更新：

```bash
npm run stamp        # 依內容雜湊改寫 sw.js 的 VERSION
```

## 部署到 Cloudflare

### 方式一：接 GitHub（推薦，推上去就自動部署）

Cloudflare 主控台 → Workers & Pages → Create → Pages → Connect to Git，選這個 repo，然後：

| 設定 | 值 |
| --- | --- |
| Framework preset | None |
| Build command | 留空 |
| Build output directory | `public` |

`public/` 裡已經是可以直接上線的靜態檔案，不需要建置步驟。

### 方式二：用 Wrangler 從本機推

```bash
npm install
npx wrangler login
npm run deploy       # 等同 npm run stamp && wrangler deploy
```

## 重新產生字典資料

只有在要更新字音來源時才需要跑：

```bash
pip install pypinyin pillow
curl -o cedict.zip https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip
unzip cedict.zip -d cedict

npm run data -- cedict/cedict_ts.u8   # 產生 public/data/*
npm run icons                          # 產生 public/icons/*
npm run stamp                          # 更新 sw.js 版本
```

## 本機預覽

```bash
npm run serve        # http://localhost:8788
```

Service Worker 需要 `https` 或 `localhost` 才會註冊，用 IP 連會沒有離線功能。

## 專案結構

```
public/            直接上線的靜態網站
  index.html
  app.js           查詢、斷詞、拼音轉字母
  styles.css
  sw.js            離線快取
  manifest.webmanifest
  data/            chars.txt（4 萬多字）、words.txt（20 萬多詞）
tools/             產生資料、圖示、版本編號的腳本
```

## 讀音標準說明

字音來自 pypinyin 與 CC-CEDICT，採大陸普通話標準。這正好是 iOS 拼音鍵盤依循的標準，
所以拿來查「要打什麼字母」是準的；但若要對照臺灣教育部審定音，會有少數字不同。

## 資料來源

- [pypinyin](https://github.com/mozillazg/python-pinyin) — 單字讀音
- [CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict) — 詞彙讀音，授權 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

`public/data/` 內的字典檔衍生自 CC-CEDICT，同樣以 CC BY-SA 4.0 釋出。
