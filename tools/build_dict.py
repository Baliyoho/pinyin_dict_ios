#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""資料管線：Unihan + CC-CEDICT → ``dict.sqlite``。

純標準庫（urllib / zipfile / sqlite3 / re / unicodedata），Mac 端跑一次即可。

    python3 tools/build_dict.py                    # 產出預設路徑的 dict.sqlite
    python3 tools/build_dict.py --with-definitions # 額外打包英文釋義（DB 會變大）

流程
----
1. 下載並解壓 Unihan.zip / CC-CEDICT，解析出筆畫、部首、繁簡對應、字頻與讀音。
2. 解析 CC-CEDICT，逐位對齊漢字與音節，得出「某字在某詞裡讀什麼」。
3. 由對齊結果算出每個讀音的詞條數（= 讀音頻率），決定多音字卡片的排序。
4. 統一轉出鍵入序列（``lv``）與注音（``ㄌㄩˋ``）。
5. 寫入 SQLite、建索引、VACUUM，最後跑健檢。
"""

import argparse
import os
import re
import sqlite3
import sys
import unicodedata
import urllib.request
import zipfile
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import zhuyin_table as zt

# ---------------------------------------------------------------------------
# 常數
# ---------------------------------------------------------------------------

UNIHAN_URL = "https://www.unicode.org/Public/UNIDATA/Unihan.zip"
CEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.zip"

#: 只收 CJK 統一漢字基本區，約 21k 字。控制 DB 體積用。
CJK_START, CJK_END = 0x4E00, 0x9FFF

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE = os.path.join(HERE, ".cache")
DEFAULT_OUT = os.path.join(
    os.path.dirname(HERE), "PinyinLookup", "PinyinLookup", "Resources", "dict.sqlite"
)

#: 每個「字 + 讀音」最多留幾個詞例（App 顯示 3 個，多留一點給日後調整）
EXAMPLES_PER_READING = 6

CEDICT_LINE = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]*)\]\s+/(.*)/\s*$")
UNIHAN_FIELDS = {
    "Unihan_Readings.txt": {
        "kMandarin", "kHanyuPinyin", "kTGHZ2013", "kXHC1983", "kHanyuPinlu",
    },
    "Unihan_IRGSources.txt": {"kTotalStrokes", "kRSUnicode"},
    "Unihan_RadicalStrokeCounts.txt": {"kRSUnicode"},
    "Unihan_Variants.txt": {"kSimplifiedVariant", "kTraditionalVariant"},
}


def log(msg):
    print(msg, flush=True)


def is_cjk(ch):
    return CJK_START <= ord(ch) <= CJK_END


def all_cjk(s):
    return bool(s) and all(is_cjk(c) for c in s)


# ---------------------------------------------------------------------------
# 下載
# ---------------------------------------------------------------------------

def fetch(url, dest):
    """下載到 *dest*，已存在且非空就直接用快取。"""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        log(f"  cached  {os.path.basename(dest)} ({os.path.getsize(dest):,} bytes)")
        return dest
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    log(f"  fetching {url}")
    tmp = dest + ".part"
    with urllib.request.urlopen(url, timeout=300) as resp, open(tmp, "wb") as fh:
        expected = resp.headers.get("Content-Length")
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            fh.write(chunk)
    got = os.path.getsize(tmp)
    if expected is not None and got != int(expected):
        os.remove(tmp)
        raise IOError(f"下載不完整：{url} 收到 {got}，應為 {expected}")
    os.replace(tmp, dest)
    log(f"  saved   {os.path.basename(dest)} ({got:,} bytes)")
    return dest


def fetch_cedict(cache_dir=DEFAULT_CACHE):
    """回傳 CC-CEDICT 的原始文字（測試也會用到）。"""
    path = fetch(CEDICT_URL, os.path.join(cache_dir, "cedict.zip"))
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.endswith(".u8"))
        return z.read(name).decode("utf-8")


def fetch_unihan(cache_dir=DEFAULT_CACHE):
    return fetch(UNIHAN_URL, os.path.join(cache_dir, "Unihan.zip"))


# ---------------------------------------------------------------------------
# Unihan
# ---------------------------------------------------------------------------

def parse_unihan(zip_path, warn):
    """讀出每個字的讀音、筆畫、部首、繁簡對應與字頻。"""
    raw = defaultdict(dict)
    with zipfile.ZipFile(zip_path) as z:
        present = set(z.namelist())
        for fname, wanted in UNIHAN_FIELDS.items():
            if fname not in present:
                warn("unihan-file", f"{fname} 不在 Unihan.zip 裡，略過")
                continue
            for line in z.read(fname).decode("utf-8").splitlines():
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) < 3 or parts[1] not in wanted:
                    continue
                cp = int(parts[0][2:], 16)
                if not (CJK_START <= cp <= CJK_END):
                    continue
                # kRSUnicode 可能同時出現在兩個檔案，先到先得即可
                raw[cp].setdefault(parts[1], parts[2])

    chars = {}
    for cp, fields in raw.items():
        ch = chr(cp)
        chars[ch] = {
            "cp": cp,
            "strokes": _first_int(fields.get("kTotalStrokes")),
            "radical": _radical_char(fields.get("kRSUnicode"), warn),
            "variant": _variant(fields, warn),
            "pinlu": _pinlu(fields.get("kHanyuPinlu")),
            "readings": _unihan_readings(ch, fields, warn),
        }
    return chars


def _first_int(value):
    if not value:
        return None
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def _radical_char(value, warn):
    """``'120.8'`` / ``"120'.8"`` → ``'糸'``。

    康熙部首區 U+2F00–U+2FD5 依序就是 1–214 號部首；NFKC 會把 ⽷ 正規化成
    一般漢字 糸，正好省下一張 214 筆的硬編碼表。
    """
    if not value:
        return None
    m = re.match(r"(\d+)", value)
    if not m:
        return None
    num = int(m.group(1))
    if not 1 <= num <= 214:
        warn("radical", f"部首編號超出範圍：{value}")
        return None
    return unicodedata.normalize("NFKC", chr(0x2F00 + num - 1))


def _variant(fields, warn):
    for key in ("kSimplifiedVariant", "kTraditionalVariant"):
        value = fields.get(key)
        if not value:
            continue
        for token in value.split():
            token = token.split("<")[0]
            if not token.startswith("U+"):
                continue
            cp = int(token[2:], 16)
            if CJK_START <= cp <= CJK_END:
                return chr(cp)
    return None


def _pinlu(value):
    """``'lǜ(220)'`` → 220。用作「這個字有多常用」的代理值。"""
    if not value:
        return 0
    return sum(int(n) for n in re.findall(r"\((\d+)\)", value))


def _unihan_readings(ch, fields, warn):
    """回傳 ``[(base, tone, source)]``，依 Unihan 的排序（第一個 = 主讀音）。"""
    out = []
    seen = set()

    def add(text, source):
        text = text.strip()
        if not text:
            return
        try:
            base, tone = zt.parse_accented(text)
        except zt.UnknownSyllable:
            warn("unihan-reading", f"{ch} 的讀音無法解析：{text!r}（{source}）")
            return
        if (base, tone) not in seen:
            seen.add((base, tone))
            out.append((base, tone, source))

    for token in (fields.get("kMandarin") or "").split():
        add(token, "kMandarin")
    for key in ("kTGHZ2013", "kXHC1983", "kHanyuPinyin"):
        for token in (fields.get(key) or "").split():
            # 格式是 位置:讀音,讀音
            body = token.split(":", 1)[-1]
            for reading in body.split(","):
                add(reading, key)
    for token in re.findall(r"([^\s(]+)\(\d+\)", fields.get("kHanyuPinlu") or ""):
        add(token, "kHanyuPinlu")
    return out


# ---------------------------------------------------------------------------
# CC-CEDICT
# ---------------------------------------------------------------------------

class Entry:
    __slots__ = ("trad", "simp", "syllables", "definitions")

    def __init__(self, trad, simp, syllables, definitions):
        self.trad = trad
        self.simp = simp
        self.syllables = syllables
        self.definitions = definitions


def parse_cedict(text, warn):
    entries, skipped = [], Counter()
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        m = CEDICT_LINE.match(line)
        if not m:
            skipped["malformed"] += 1
            continue
        trad, simp, pinyin, defs = m.groups()
        syllables = [s.lower() for s in zt.split_syllables(pinyin)]
        entries.append(Entry(trad, simp, syllables, defs.split("/")))
    if skipped:
        warn("cedict", f"略過無法解析的行：{dict(skipped)}")
    return entries


def convert_entry(entry, warn):
    """把一筆詞條的音節轉成 (keys, zhuyin, accented)；有任何一個轉不出就回 None。"""
    keys, zhuyin, accented = [], [], []
    for token in entry.syllables:
        base, tone = zt.split_tone(token)
        if base in zt.PLACEHOLDER_SYLLABLES:
            return None
        try:
            keys.append(zt.syllable_to_keys(base))
            zhuyin.append(zt.syllable_to_zhuyin(base, tone))
            accented.append(zt.syllable_to_accented(base, tone))
        except zt.UnknownSyllable:
            warn("syllable", f"{entry.trad} 的音節不在對照表：{token!r}")
            return None
    return keys, zhuyin, accented


# ---------------------------------------------------------------------------
# 逐位對齊
# ---------------------------------------------------------------------------

def align(entries, warn):
    """逐位對齊漢字與音節，得出字級讀音、讀音頻率與詞例。

    排除：含非漢字的詞條、含兒化 ``r5`` 的詞條、字數與音節數不符的詞條。
    """
    reading_freq = Counter()          # (ch, base, tone) -> 詞條數
    examples = defaultdict(list)      # (ch, keys) -> [entry]
    char_word_count = Counter()       # ch -> 出現在多少詞條
    stats = Counter()

    for entry in entries:
        for form in {entry.trad, entry.simp}:
            for ch in set(form):
                if is_cjk(ch):
                    char_word_count[ch] += 1

        if "r" in [zt.split_tone(s)[0] for s in entry.syllables]:
            stats["erhua"] += 1
            continue
        forms = [f for f in (entry.trad, entry.simp) if all_cjk(f)]
        if not forms:
            stats["non_han"] += 1
            continue
        if any(len(f) != len(entry.syllables) for f in forms):
            stats["length_mismatch"] += 1
            continue

        converted = convert_entry(entry, warn)
        if converted is None:
            stats["unconvertible"] += 1
            continue
        keys = converted[0]

        stats["aligned"] += 1
        for form in forms:
            for ch, token, key in zip(form, entry.syllables, keys):
                base, tone = zt.split_tone(token)
                reading_freq[(ch, base, tone)] += 1
                # 詞例要綁到**帶調**的讀音，不能只綁鍵入序列：和 hé 與 和 hè
                # 敲起來都是 he，但「不和」示範的是 hé，「應和」才是 hè。
                examples[(ch, key, zt.syllable_to_accented(base, tone))].append(entry)
    return reading_freq, examples, char_word_count, stats


def word_frequency(entries):
    """詞頻代理值：這個詞被幾筆 CC-CEDICT 詞條包含。

    CC-CEDICT 本身沒有詞頻，但常用詞會不斷出現在別的詞條裡（綠色 出現在
    綠色食品、綠色和平…），罕用詞則不會。這比「組成字有多常用」準得多——
    水綠 的兩個字都很常見，可是沒人會拿它當例子。
    """
    counts = Counter()
    for entry in entries:
        for form in {entry.trad, entry.simp}:
            if not all_cjk(form):
                continue
            for length in range(2, min(len(form), 4) + 1):
                for i in range(len(form) - length + 1):
                    counts[form[i:i + length]] += 1
    return counts


# ---------------------------------------------------------------------------
# 組裝
# ---------------------------------------------------------------------------

def build_readings(chars, reading_freq, warn):
    """每個字的讀音清單，依詞條數排序（rank 0 = 主讀音）。

    來源優先序：CC-CEDICT 對齊出來的讀音（有頻率，最可靠）擺前面；Unihan 的
    讀音補上 CC-CEDICT 沒收到的字，並保留 kMandarin 作為 tie-break 的依據。
    """
    by_char = defaultdict(dict)   # ch -> (base, tone) -> freq
    for (ch, base, tone), freq in reading_freq.items():
        by_char[ch][(base, tone)] = freq

    rows = []
    for ch, info in chars.items():
        readings = dict(by_char.get(ch, {}))
        unihan_order = {}
        for i, (base, tone, source) in enumerate(info["readings"]):
            unihan_order.setdefault((base, tone), i)
            # 沒有 CC-CEDICT 資料的字，至少給它 Unihan 的讀音
            if not readings and source == "kMandarin":
                readings[(base, tone)] = 0
        if not readings:
            for base, tone, _ in info["readings"]:
                readings[(base, tone)] = 0
        if not readings:
            continue

        ordered = sorted(
            readings.items(),
            key=lambda kv: (-kv[1], unihan_order.get(kv[0], 999), kv[0][0], kv[0][1]),
        )
        for rank, ((base, tone), freq) in enumerate(ordered):
            try:
                rows.append((
                    ch,
                    zt.syllable_to_accented(base, tone),
                    zt.syllable_to_keys(base),
                    zt.syllable_to_zhuyin(base, tone),
                    freq,
                    rank,
                ))
            except zt.UnknownSyllable:
                warn("reading", f"{ch} 的讀音轉不出來：{base}{tone}")
    return rows


class Commonality:
    """字有多常用。

    首選 Unihan 的 ``kHanyuPinlu``（真實語料頻次，但只涵蓋約 2,500 個常用字），
    涵蓋不到的字退回「出現在多少 CC-CEDICT 詞條」。兩者當成 tuple 依序比較，
    所以常用字永遠排在罕用字前面，罕用字之間也還有個穩定的順序。
    """

    def __init__(self, chars, char_word_count):
        self.pinlu = {ch: info["pinlu"] for ch, info in chars.items()}
        self.word_count = char_word_count

    def of(self, ch):
        return (self.pinlu.get(ch, 0), self.word_count.get(ch, 0))

    def word(self, form):
        """整個詞的常用度：取最弱的那個字——一個詞要常見，每個字都得常見。"""
        return min((self.of(ch) for ch in form), default=(0, 0))

    def word_excluding(self, form, ch):
        """排除指定字之後的常用度。

        挑詞例時，被查的字在每個候選詞裡都一樣，把它算進去只會讓分數全部撞在
        一起（綠色／品綠／洗綠 會同分），所以要把它剔掉再比。
        """
        rest = [c for c in form if c != ch]
        return self.word(rest) if rest else self.of(ch)


def build_words(entries, word_freq, warn):
    rows, index = [], {}
    for entry in entries:
        if not (all_cjk(entry.trad) or all_cjk(entry.simp)):
            continue
        converted = convert_entry(entry, warn)
        if converted is None:
            continue
        keys, zhuyin, accented = converted
        score = max(word_freq.get(entry.trad, 0), word_freq.get(entry.simp, 0))
        rows.append((
            entry.trad,
            # 繁簡相同時 simp 存空字串，省下約 38% 的重複文字與索引；查詢用
            # `trad=? OR simp=?` 依然打得中，因為 trad 那邊一定會命中。
            "" if entry.simp == entry.trad else entry.simp,
            "".join(accented), " ".join(keys), " ".join(zhuyin),
            score,
            "; ".join(d for d in entry.definitions if d),
        ))
        index[id(entry)] = rows[-1]
    return rows, index


def build_examples(examples, word_rows_by_entry, word_freq, common, warn):
    """每個「字 + 讀音」挑幾個最能示範這個敲法的詞。

    排序依據，由重到輕：雙字詞優先（最好認）→ 詞頻高的優先 → 其餘的字越常用
    越好 → 被查的字在詞首優先 → 短的優先。單字詞會被剔掉，它示範不了什麼。
    """
    rows = []
    for (ch, keys, pinyin), entries in sorted(examples.items()):
        scored = []
        for entry in entries:
            row = word_rows_by_entry.get(id(entry))
            if row is None:
                continue
            word = row[0] if all_cjk(row[0]) else (row[1] or row[0])
            if len(word) < 2:
                continue
            scored.append((
                0 if len(word) == 2 else 1,
                -word_freq.get(word, 0),
                tuple(-v for v in common.word_excluding(word, ch)),
                0 if word[0] == ch else 1,
                len(word),
                word,
                row[3],
            ))
        scored.sort()
        seen = set()
        for _, negfreq, _, _, _, word, word_keys in scored:
            if word in seen:
                continue
            seen.add(word)
            rows.append((ch, keys, pinyin, word, word_keys, -negfreq))
            if len(seen) >= EXAMPLES_PER_READING:
                break
    return rows


# ---------------------------------------------------------------------------
# SQLite
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE chars (
  ch TEXT PRIMARY KEY,
  cp INTEGER,
  strokes INTEGER,
  radical TEXT,
  variant TEXT,
  word_count INTEGER
);

CREATE TABLE readings (
  ch TEXT, pinyin TEXT,
  keys TEXT,
  zhuyin TEXT,
  freq INTEGER,
  rank INTEGER
);
CREATE INDEX idx_readings_ch ON readings(ch);
CREATE INDEX idx_readings_keys ON readings(keys);
CREATE INDEX idx_readings_zhuyin ON readings(zhuyin);

CREATE TABLE words (
  trad TEXT, simp TEXT,
  pinyin TEXT, keys TEXT, zhuyin TEXT,
  freq INTEGER
);
CREATE INDEX idx_words_trad ON words(trad);
CREATE INDEX idx_words_simp ON words(simp);

-- reading_pinyin 是規格之外多加的一欄。少了它，和 hé 與 和 hè 會共用同一批
-- 詞例（兩者的 keys 都是 he），等於把「不和」標成 hè 的例子——這個 App 最不
-- 該錯的就是多音字，所以寧可多存一欄帶調拼音把讀音釘死。
CREATE TABLE char_word_examples (
  ch TEXT, reading_keys TEXT, reading_pinyin TEXT,
  word TEXT, word_keys TEXT,
  freq INTEGER
);
CREATE INDEX idx_cwe ON char_word_examples(ch, reading_keys);

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
"""


def write_db(path, char_rows, reading_rows, word_rows, example_rows,
             with_definitions, meta):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    if with_definitions:
        conn.execute("ALTER TABLE words ADD COLUMN defs TEXT")

    conn.executemany("INSERT INTO chars VALUES (?,?,?,?,?,?)", char_rows)
    conn.executemany("INSERT INTO readings VALUES (?,?,?,?,?,?)", reading_rows)
    if with_definitions:
        conn.executemany("INSERT INTO words VALUES (?,?,?,?,?,?,?)", word_rows)
    else:
        conn.executemany(
            "INSERT INTO words VALUES (?,?,?,?,?,?)", [r[:6] for r in word_rows]
        )
    conn.executemany("INSERT INTO char_word_examples VALUES (?,?,?,?,?,?)", example_rows)
    conn.executemany("INSERT INTO meta VALUES (?,?)", sorted(meta.items()))
    conn.commit()
    conn.execute("VACUUM")
    conn.close()


# ---------------------------------------------------------------------------
# 健檢
# ---------------------------------------------------------------------------

def health_check(path):
    """建置後 DB 健檢。回傳 (ok, [訊息])。"""
    conn = sqlite3.connect(path)
    q = lambda sql: conn.execute(sql).fetchone()[0]
    messages, ok = [], True

    def check(label, value, predicate, expectation):
        nonlocal ok
        good = predicate(value)
        ok = ok and good
        messages.append(f"  [{'ok ' if good else 'FAIL'}] {label}: {value:,} ({expectation})")

    check("chars", q("SELECT COUNT(*) FROM chars"), lambda n: 20000 <= n <= 22000, "≈21k")
    check("words", q("SELECT COUNT(*) FROM words"), lambda n: 115000 <= n <= 130000, "≈124k")
    check("readings", q("SELECT COUNT(*) FROM readings"), lambda n: n > 20000, ">20k")
    check("examples", q("SELECT COUNT(*) FROM char_word_examples"), lambda n: n > 40000, ">40k")
    check("readings.keys 空值",
          q("SELECT COUNT(*) FROM readings WHERE keys IS NULL OR keys=''"),
          lambda n: n == 0, "必須為 0")
    check("readings.zhuyin 空值",
          q("SELECT COUNT(*) FROM readings WHERE zhuyin IS NULL OR zhuyin=''"),
          lambda n: n == 0, "必須為 0")
    check("words.keys 空值",
          q("SELECT COUNT(*) FROM words WHERE keys IS NULL OR keys=''"),
          lambda n: n == 0, "必須為 0")
    check("每個字都有主讀音",
          q("SELECT COUNT(*) FROM chars c WHERE NOT EXISTS "
            "(SELECT 1 FROM readings r WHERE r.ch=c.ch AND r.rank=0)"),
          lambda n: n == 0, "必須為 0")

    # 已知案例
    for ch, expected in (("綠", "lv"), ("路", "lu"), ("女", "nv"), ("居", "ju"),
                         ("略", "lve"), ("六", "liu"), ("對", "dui")):
        got = conn.execute(
            "SELECT keys FROM readings WHERE ch=? ORDER BY rank LIMIT 1", (ch,)
        ).fetchone()
        good = got is not None and got[0] == expected
        ok = ok and good
        messages.append(f"  [{'ok ' if good else 'FAIL'}] {ch} 主讀音 keys = "
                        f"{got[0] if got else None!r}（應為 {expected}）")

    # 多音字詞例必須綁對讀音——這是 App 最容易誤導人的地方。
    # 只斷言「不能出現另一個讀音的詞」與「至少有幾個詞例」；至於哪個詞排第一，
    # 那是詞頻排序的事，不該寫死在健檢裡。
    for ch, pinyin, must_not in (
        ("綠", "lǜ", "綠林"),
        ("綠", "lù", "綠色"),
        ("行", "háng", "行走"),
        ("行", "xíng", "銀行"),
        ("長", "zhǎng", "長短"),
        ("長", "cháng", "長大"),
        ("和", "hè", "和平"),
    ):
        words = {
            r[0] for r in conn.execute(
                "SELECT word FROM char_word_examples WHERE ch=? AND reading_pinyin=?",
                (ch, pinyin),
            )
        }
        good = len(words) >= 3 and must_not not in words
        ok = ok and good
        messages.append(f"  [{'ok ' if good else 'FAIL'}] {ch} {pinyin} 有 {len(words)} "
                        f"個詞例且不含 {must_not}（那是別的讀音）")

    conn.close()
    return ok, messages


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(description="建置注音查拼音字典的 SQLite 資料庫")
    ap.add_argument("--out", default=DEFAULT_OUT, help="輸出的 dict.sqlite 路徑")
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE, help="原始資料快取目錄")
    ap.add_argument("--with-definitions", action="store_true",
                    help="一併打包 CC-CEDICT 英文釋義（DB 會大不少）")
    args = ap.parse_args(argv)

    warnings = defaultdict(list)

    def warn(kind, msg):
        warnings[kind].append(msg)

    log("1/5 下載原始資料")
    unihan_zip = fetch_unihan(args.cache_dir)
    cedict_text = fetch_cedict(args.cache_dir)

    log("2/5 解析 Unihan")
    chars = parse_unihan(unihan_zip, warn)
    log(f"  {len(chars):,} 個字（U+4E00–U+9FFF）")

    log("3/5 解析 CC-CEDICT 並逐位對齊")
    entries = parse_cedict(cedict_text, warn)
    log(f"  {len(entries):,} 筆詞條")
    reading_freq, examples, char_word_count, stats = align(entries, warn)
    log(f"  對齊 {stats['aligned']:,} 筆；排除 兒化 {stats['erhua']:,}／"
        f"非漢字 {stats['non_han']:,}／字數不符 {stats['length_mismatch']:,}／"
        f"音節不明 {stats['unconvertible']:,}")

    log("4/5 組裝資料列")
    common = Commonality(chars, char_word_count)
    word_freq = word_frequency(entries)
    reading_rows = build_readings(chars, reading_freq, warn)
    # 一個讀音都湊不出來的字（合體度量衡字、罕用異體字）留著也查不出東西，剔掉。
    has_reading = {row[0] for row in reading_rows}
    dropped = sorted(set(chars) - has_reading)
    if dropped:
        warn("no-reading", f"{len(dropped)} 個字沒有任何讀音，不收進 DB："
                           f"{''.join(dropped[:20])}…")
    char_rows = [
        (ch, info["cp"], info["strokes"], info["radical"], info["variant"],
         char_word_count.get(ch, 0))
        for ch, info in sorted(chars.items()) if ch in has_reading
    ]
    word_rows, word_index = build_words(entries, word_freq, warn)
    example_rows = build_examples(examples, word_index, word_freq, common, warn)
    log(f"  chars {len(char_rows):,}／readings {len(reading_rows):,}／"
        f"words {len(word_rows):,}／examples {len(example_rows):,}")

    log("5/5 寫入 SQLite")
    meta = {
        "schema_version": "1",
        "source_unihan": UNIHAN_URL,
        "source_cedict": CEDICT_URL,
        "cedict_entries": str(len(entries)),
        "with_definitions": "1" if args.with_definitions else "0",
    }
    write_db(args.out, char_rows, reading_rows, word_rows, example_rows,
             args.with_definitions, meta)
    size = os.path.getsize(args.out)
    log(f"  {args.out}（{size / 1024 / 1024:.1f} MB）")

    if warnings:
        log("\n警告（不靜默略過，全部列出前 10 條）：")
        for kind, msgs in sorted(warnings.items()):
            log(f"  {kind}: {len(msgs)} 條")
            for msg in msgs[:10]:
                log(f"    - {msg}")

    log("\n健檢：")
    ok, messages = health_check(args.out)
    for msg in messages:
        log(msg)
    if not ok:
        log("\n健檢未通過。")
        return 1
    log("\n健檢通過。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
