# -*- coding: utf-8 -*-
"""音節 ↔ 注音 ↔ 輸入法鍵入序列 對照表。

設計原則
--------
用**完整的無調音節對照表**（見 ``SYLLABLE_TO_ZHUYIN``，419 條），而不是逐段
拆解聲母韻母。理由是拼音有一堆縮寫（``iu`` = iou、``ui`` = uei、``un`` = uen、
``ong`` 實為 ueng 的變體），逐段拆解時這些縮寫是主要出錯來源；固定表格則可以
在建置時做 100% 覆蓋率斷言。

音節一律使用 **CC-CEDICT 的拼寫慣例**：
  * ü 寫作 ``u:``（``lu:4`` = 綠、``nu:3`` = 女）
  * 聲調為結尾數字 1–4，**5 = 輕聲**
  * 兒化寫成獨立音節 ``r5``

三種輸出
--------
  * **鍵入序列**（keys）— 拼音輸入法實際要敲的字母：去掉聲調、``u:`` → ``v``
  * **注音**（zhuyin）— 查表 + 聲調符號後綴
  * **帶調拼音**（accented）— ``lu:4`` → ``lǜ``，給人看的
"""

# ---------------------------------------------------------------------------
# 聲調
# ---------------------------------------------------------------------------

#: 注音聲調符號。1 聲不標；5（輕聲）標在**前面**，其餘標在後面。
ZHUYIN_TONE_MARKS = {1: "", 2: "ˊ", 3: "ˇ", 4: "ˋ", 5: "˙"}

#: 輕聲的點放在音節前方（ㄉㄜ˙ 寫作 ˙ㄉㄜ）
ZHUYIN_NEUTRAL_IS_PREFIX = True

#: 帶調拼音用的母音表：index 0–3 對應 1–4 聲。
_ACCENTED_VOWELS = {
    "a": "āáǎà",
    "o": "ōóǒò",
    "e": "ēéěè",
    "i": "īíǐì",
    "u": "ūúǔù",
    "ü": "ǖǘǚǜ",  # ü → ǖǘǚǜ
}

#: 沒有預組合字元的罕見音節，帶調拼音直接列表。
_ACCENTED_IRREGULAR = {
    ("ê", 1): "ê̄", ("ê", 2): "ế",
    ("ê", 3): "ê̌", ("ê", 4): "ề",
    ("m", 1): "m̄", ("m", 2): "ḿ", ("m", 3): "m̌", ("m", 4): "m̀",
    ("n", 1): "n̄", ("n", 2): "ń", ("n", 3): "ň", ("n", 4): "ǹ",
    ("ng", 1): "n̄g", ("ng", 2): "ńg", ("ng", 3): "ňg", ("ng", 4): "ǹg",
    ("hm", 1): "hm", ("hm", 2): "hm", ("hm", 3): "hm", ("hm", 4): "hm",
    ("hng", 1): "hng", ("hng", 2): "hng", ("hng", 3): "hng", ("hng", 4): "hng",
    # 兒化韻尾，沒有母音可標調（實務上永遠是 r5）
    ("r", 1): "r", ("r", 2): "r", ("r", 3): "r", ("r", 4): "r",
}

# ---------------------------------------------------------------------------
# 無調音節 → 注音
# ---------------------------------------------------------------------------

SYLLABLE_TO_ZHUYIN = {
    # --- 零聲母（含 y/w 起頭）------------------------------------------------
    "a": "ㄚ", "ai": "ㄞ", "an": "ㄢ", "ang": "ㄤ", "ao": "ㄠ",
    "e": "ㄜ", "ê": "ㄝ", "ei": "ㄟ", "en": "ㄣ", "eng": "ㄥ", "er": "ㄦ",
    "o": "ㄛ", "ou": "ㄡ",
    "yi": "ㄧ", "ya": "ㄧㄚ", "yo": "ㄧㄛ", "ye": "ㄧㄝ", "yai": "ㄧㄞ",
    "yao": "ㄧㄠ", "you": "ㄧㄡ", "yan": "ㄧㄢ", "yin": "ㄧㄣ",
    "yang": "ㄧㄤ", "ying": "ㄧㄥ",
    "wu": "ㄨ", "wa": "ㄨㄚ", "wo": "ㄨㄛ", "wai": "ㄨㄞ", "wei": "ㄨㄟ",
    "wan": "ㄨㄢ", "wen": "ㄨㄣ", "wang": "ㄨㄤ", "weng": "ㄨㄥ",
    "yu": "ㄩ", "yue": "ㄩㄝ", "yuan": "ㄩㄢ", "yun": "ㄩㄣ", "yong": "ㄩㄥ",

    # --- 成音節輔音／嘆詞（罕見，見 RARE_SYLLABLES）--------------------------
    "m": "ㄇ", "n": "ㄋ", "ng": "ㄫ", "hm": "ㄏㄇ", "hng": "ㄏㄫ",
    "r": "ㄦ",  # 兒化韻尾 r5

    # --- ㄅ b ---------------------------------------------------------------
    "ba": "ㄅㄚ", "bo": "ㄅㄛ", "bai": "ㄅㄞ", "bei": "ㄅㄟ", "bao": "ㄅㄠ",
    "ban": "ㄅㄢ", "ben": "ㄅㄣ", "bang": "ㄅㄤ", "beng": "ㄅㄥ",
    "bi": "ㄅㄧ", "bia": "ㄅㄧㄚ", "bie": "ㄅㄧㄝ", "biao": "ㄅㄧㄠ",
    "bian": "ㄅㄧㄢ", "bin": "ㄅㄧㄣ", "biang": "ㄅㄧㄤ", "bing": "ㄅㄧㄥ",
    "bu": "ㄅㄨ",

    # --- ㄆ p ---------------------------------------------------------------
    "pa": "ㄆㄚ", "po": "ㄆㄛ", "pai": "ㄆㄞ", "pei": "ㄆㄟ", "pao": "ㄆㄠ",
    "pou": "ㄆㄡ", "pan": "ㄆㄢ", "pen": "ㄆㄣ", "pang": "ㄆㄤ", "peng": "ㄆㄥ",
    "pi": "ㄆㄧ", "pie": "ㄆㄧㄝ", "piao": "ㄆㄧㄠ", "pian": "ㄆㄧㄢ",
    "pin": "ㄆㄧㄣ", "ping": "ㄆㄧㄥ", "pu": "ㄆㄨ",

    # --- ㄇ m ---------------------------------------------------------------
    "ma": "ㄇㄚ", "mo": "ㄇㄛ", "me": "ㄇㄜ", "mai": "ㄇㄞ", "mei": "ㄇㄟ",
    "mao": "ㄇㄠ", "mou": "ㄇㄡ", "man": "ㄇㄢ", "men": "ㄇㄣ", "mang": "ㄇㄤ",
    "meng": "ㄇㄥ", "mi": "ㄇㄧ", "mie": "ㄇㄧㄝ", "miao": "ㄇㄧㄠ",
    "miu": "ㄇㄧㄡ", "mian": "ㄇㄧㄢ", "min": "ㄇㄧㄣ", "ming": "ㄇㄧㄥ",
    "mu": "ㄇㄨ",

    # --- ㄈ f ---------------------------------------------------------------
    "fa": "ㄈㄚ", "fo": "ㄈㄛ", "fei": "ㄈㄟ", "fou": "ㄈㄡ", "fan": "ㄈㄢ",
    "fen": "ㄈㄣ", "fang": "ㄈㄤ", "feng": "ㄈㄥ", "fiao": "ㄈㄧㄠ", "fu": "ㄈㄨ",

    # --- ㄉ d ---------------------------------------------------------------
    "da": "ㄉㄚ", "de": "ㄉㄜ", "dai": "ㄉㄞ", "dei": "ㄉㄟ", "dao": "ㄉㄠ",
    "dou": "ㄉㄡ", "dan": "ㄉㄢ", "den": "ㄉㄣ", "dang": "ㄉㄤ", "deng": "ㄉㄥ",
    "di": "ㄉㄧ", "dia": "ㄉㄧㄚ", "die": "ㄉㄧㄝ", "diao": "ㄉㄧㄠ",
    "diu": "ㄉㄧㄡ", "dian": "ㄉㄧㄢ", "ding": "ㄉㄧㄥ",
    "du": "ㄉㄨ", "duo": "ㄉㄨㄛ", "dui": "ㄉㄨㄟ", "duan": "ㄉㄨㄢ",
    "dun": "ㄉㄨㄣ", "dong": "ㄉㄨㄥ",

    # --- ㄊ t ---------------------------------------------------------------
    "ta": "ㄊㄚ", "te": "ㄊㄜ", "tai": "ㄊㄞ", "tei": "ㄊㄟ", "tao": "ㄊㄠ",
    "tou": "ㄊㄡ", "tan": "ㄊㄢ", "tang": "ㄊㄤ", "teng": "ㄊㄥ",
    "ti": "ㄊㄧ", "tie": "ㄊㄧㄝ", "tiao": "ㄊㄧㄠ", "tian": "ㄊㄧㄢ",
    "ting": "ㄊㄧㄥ", "tu": "ㄊㄨ", "tuo": "ㄊㄨㄛ", "tui": "ㄊㄨㄟ",
    "tuan": "ㄊㄨㄢ", "tun": "ㄊㄨㄣ", "tong": "ㄊㄨㄥ",

    # --- ㄋ n ---------------------------------------------------------------
    "na": "ㄋㄚ", "ne": "ㄋㄜ", "nai": "ㄋㄞ", "nei": "ㄋㄟ", "nao": "ㄋㄠ",
    "nou": "ㄋㄡ", "nan": "ㄋㄢ", "nen": "ㄋㄣ", "nang": "ㄋㄤ", "neng": "ㄋㄥ",
    "ni": "ㄋㄧ", "nie": "ㄋㄧㄝ", "niao": "ㄋㄧㄠ", "niu": "ㄋㄧㄡ",
    "nian": "ㄋㄧㄢ", "nin": "ㄋㄧㄣ", "niang": "ㄋㄧㄤ", "ning": "ㄋㄧㄥ",
    "nu": "ㄋㄨ", "nuo": "ㄋㄨㄛ", "nuan": "ㄋㄨㄢ", "nun": "ㄋㄨㄣ",
    "nong": "ㄋㄨㄥ", "nu:": "ㄋㄩ", "nu:e": "ㄋㄩㄝ",

    # --- ㄌ l ---------------------------------------------------------------
    "la": "ㄌㄚ", "lo": "ㄌㄛ", "le": "ㄌㄜ", "lai": "ㄌㄞ", "lei": "ㄌㄟ",
    "lao": "ㄌㄠ", "lou": "ㄌㄡ", "lan": "ㄌㄢ", "lang": "ㄌㄤ", "leng": "ㄌㄥ",
    "li": "ㄌㄧ", "lia": "ㄌㄧㄚ", "lie": "ㄌㄧㄝ", "liao": "ㄌㄧㄠ",
    "liu": "ㄌㄧㄡ", "lian": "ㄌㄧㄢ", "lin": "ㄌㄧㄣ", "liang": "ㄌㄧㄤ",
    "ling": "ㄌㄧㄥ", "lu": "ㄌㄨ", "luo": "ㄌㄨㄛ", "luan": "ㄌㄨㄢ",
    "lun": "ㄌㄨㄣ", "long": "ㄌㄨㄥ", "lu:": "ㄌㄩ", "lu:e": "ㄌㄩㄝ",

    # --- ㄍ g ---------------------------------------------------------------
    "ga": "ㄍㄚ", "ge": "ㄍㄜ", "gai": "ㄍㄞ", "gei": "ㄍㄟ", "gao": "ㄍㄠ",
    "gou": "ㄍㄡ", "gan": "ㄍㄢ", "gen": "ㄍㄣ", "gang": "ㄍㄤ", "geng": "ㄍㄥ",
    "gu": "ㄍㄨ", "gua": "ㄍㄨㄚ", "guo": "ㄍㄨㄛ", "guai": "ㄍㄨㄞ",
    "gui": "ㄍㄨㄟ", "guan": "ㄍㄨㄢ", "gun": "ㄍㄨㄣ", "guang": "ㄍㄨㄤ",
    "gong": "ㄍㄨㄥ",

    # --- ㄎ k ---------------------------------------------------------------
    "ka": "ㄎㄚ", "ke": "ㄎㄜ", "kai": "ㄎㄞ", "kei": "ㄎㄟ", "kao": "ㄎㄠ",
    "kou": "ㄎㄡ", "kan": "ㄎㄢ", "ken": "ㄎㄣ", "kang": "ㄎㄤ", "keng": "ㄎㄥ",
    "ku": "ㄎㄨ", "kua": "ㄎㄨㄚ", "kuo": "ㄎㄨㄛ", "kuai": "ㄎㄨㄞ",
    "kui": "ㄎㄨㄟ", "kuan": "ㄎㄨㄢ", "kun": "ㄎㄨㄣ", "kuang": "ㄎㄨㄤ",
    "kong": "ㄎㄨㄥ",

    # --- ㄏ h ---------------------------------------------------------------
    "ha": "ㄏㄚ", "he": "ㄏㄜ", "hai": "ㄏㄞ", "hei": "ㄏㄟ", "hao": "ㄏㄠ",
    "hou": "ㄏㄡ", "han": "ㄏㄢ", "hen": "ㄏㄣ", "hang": "ㄏㄤ", "heng": "ㄏㄥ",
    "hu": "ㄏㄨ", "hua": "ㄏㄨㄚ", "huo": "ㄏㄨㄛ", "huai": "ㄏㄨㄞ",
    "hui": "ㄏㄨㄟ", "huan": "ㄏㄨㄢ", "hun": "ㄏㄨㄣ", "huang": "ㄏㄨㄤ",
    "hong": "ㄏㄨㄥ",

    # --- ㄐ j（後接 u 一律唸 ü，但輸入法照敲 u）------------------------------
    "ji": "ㄐㄧ", "jia": "ㄐㄧㄚ", "jie": "ㄐㄧㄝ", "jiao": "ㄐㄧㄠ",
    "jiu": "ㄐㄧㄡ", "jian": "ㄐㄧㄢ", "jin": "ㄐㄧㄣ", "jiang": "ㄐㄧㄤ",
    "jing": "ㄐㄧㄥ", "ju": "ㄐㄩ", "jue": "ㄐㄩㄝ", "juan": "ㄐㄩㄢ",
    "jun": "ㄐㄩㄣ", "jiong": "ㄐㄩㄥ",

    # --- ㄑ q ---------------------------------------------------------------
    "qi": "ㄑㄧ", "qia": "ㄑㄧㄚ", "qie": "ㄑㄧㄝ", "qiao": "ㄑㄧㄠ",
    "qiu": "ㄑㄧㄡ", "qian": "ㄑㄧㄢ", "qin": "ㄑㄧㄣ", "qiang": "ㄑㄧㄤ",
    "qing": "ㄑㄧㄥ", "qu": "ㄑㄩ", "que": "ㄑㄩㄝ", "quan": "ㄑㄩㄢ",
    "qun": "ㄑㄩㄣ", "qiong": "ㄑㄩㄥ",

    # --- ㄒ x ---------------------------------------------------------------
    "xi": "ㄒㄧ", "xia": "ㄒㄧㄚ", "xie": "ㄒㄧㄝ", "xiao": "ㄒㄧㄠ",
    "xiu": "ㄒㄧㄡ", "xian": "ㄒㄧㄢ", "xin": "ㄒㄧㄣ", "xiang": "ㄒㄧㄤ",
    "xing": "ㄒㄧㄥ", "xu": "ㄒㄩ", "xue": "ㄒㄩㄝ", "xuan": "ㄒㄩㄢ",
    "xun": "ㄒㄩㄣ", "xiong": "ㄒㄩㄥ",

    # --- ㄓ zh（-i 為空韻，注音不寫韻母）------------------------------------
    "zhi": "ㄓ", "zha": "ㄓㄚ", "zhe": "ㄓㄜ", "zhai": "ㄓㄞ", "zhei": "ㄓㄟ",
    "zhao": "ㄓㄠ", "zhou": "ㄓㄡ", "zhan": "ㄓㄢ", "zhen": "ㄓㄣ",
    "zhang": "ㄓㄤ", "zheng": "ㄓㄥ", "zhu": "ㄓㄨ", "zhua": "ㄓㄨㄚ",
    "zhuo": "ㄓㄨㄛ", "zhuai": "ㄓㄨㄞ", "zhui": "ㄓㄨㄟ", "zhuan": "ㄓㄨㄢ",
    "zhun": "ㄓㄨㄣ", "zhuang": "ㄓㄨㄤ", "zhong": "ㄓㄨㄥ",

    # --- ㄔ ch --------------------------------------------------------------
    "chi": "ㄔ", "cha": "ㄔㄚ", "che": "ㄔㄜ", "chai": "ㄔㄞ", "chao": "ㄔㄠ",
    "chou": "ㄔㄡ", "chan": "ㄔㄢ", "chen": "ㄔㄣ", "chang": "ㄔㄤ",
    "cheng": "ㄔㄥ", "chu": "ㄔㄨ", "chua": "ㄔㄨㄚ", "chuo": "ㄔㄨㄛ",
    "chuai": "ㄔㄨㄞ", "chui": "ㄔㄨㄟ", "chuan": "ㄔㄨㄢ", "chun": "ㄔㄨㄣ",
    "chuang": "ㄔㄨㄤ", "chong": "ㄔㄨㄥ",

    # --- ㄕ sh --------------------------------------------------------------
    "shi": "ㄕ", "sha": "ㄕㄚ", "she": "ㄕㄜ", "shai": "ㄕㄞ", "shei": "ㄕㄟ",
    "shao": "ㄕㄠ", "shou": "ㄕㄡ", "shan": "ㄕㄢ", "shen": "ㄕㄣ",
    "shang": "ㄕㄤ", "sheng": "ㄕㄥ", "shu": "ㄕㄨ", "shua": "ㄕㄨㄚ",
    "shuo": "ㄕㄨㄛ", "shuai": "ㄕㄨㄞ", "shui": "ㄕㄨㄟ", "shuan": "ㄕㄨㄢ",
    "shun": "ㄕㄨㄣ", "shuang": "ㄕㄨㄤ",

    # --- ㄖ r ---------------------------------------------------------------
    "ri": "ㄖ", "re": "ㄖㄜ", "rao": "ㄖㄠ", "rou": "ㄖㄡ", "ran": "ㄖㄢ",
    "ren": "ㄖㄣ", "rang": "ㄖㄤ", "reng": "ㄖㄥ", "ru": "ㄖㄨ", "rua": "ㄖㄨㄚ",
    "ruo": "ㄖㄨㄛ", "rui": "ㄖㄨㄟ", "ruan": "ㄖㄨㄢ", "run": "ㄖㄨㄣ",
    "rong": "ㄖㄨㄥ",

    # --- ㄗ z ---------------------------------------------------------------
    "zi": "ㄗ", "za": "ㄗㄚ", "ze": "ㄗㄜ", "zai": "ㄗㄞ", "zei": "ㄗㄟ",
    "zao": "ㄗㄠ", "zou": "ㄗㄡ", "zan": "ㄗㄢ", "zen": "ㄗㄣ", "zang": "ㄗㄤ",
    "zeng": "ㄗㄥ", "zu": "ㄗㄨ", "zuo": "ㄗㄨㄛ", "zui": "ㄗㄨㄟ",
    "zuan": "ㄗㄨㄢ", "zun": "ㄗㄨㄣ", "zong": "ㄗㄨㄥ",

    # --- ㄘ c ---------------------------------------------------------------
    "ci": "ㄘ", "ca": "ㄘㄚ", "ce": "ㄘㄜ", "cai": "ㄘㄞ", "cei": "ㄘㄟ",
    "cao": "ㄘㄠ", "cou": "ㄘㄡ", "can": "ㄘㄢ", "cen": "ㄘㄣ", "cang": "ㄘㄤ",
    "ceng": "ㄘㄥ", "cu": "ㄘㄨ", "cuo": "ㄘㄨㄛ", "cui": "ㄘㄨㄟ",
    "cuan": "ㄘㄨㄢ", "cun": "ㄘㄨㄣ", "cong": "ㄘㄨㄥ",

    # --- ㄙ s ---------------------------------------------------------------
    "si": "ㄙ", "sa": "ㄙㄚ", "se": "ㄙㄜ", "sai": "ㄙㄞ", "sei": "ㄙㄟ",
    "sao": "ㄙㄠ", "sou": "ㄙㄡ", "san": "ㄙㄢ", "sen": "ㄙㄣ", "sang": "ㄙㄤ",
    "seng": "ㄙㄥ", "su": "ㄙㄨ", "suo": "ㄙㄨㄛ", "sui": "ㄙㄨㄟ",
    "suan": "ㄙㄨㄢ", "sun": "ㄙㄨㄣ", "song": "ㄙㄨㄥ",
}

#: 罕見／非標準音節。管線碰到這些要**發出警告**而不是靜默通過——它們多半不是
#: 拼音輸入法真的敲得出來的東西。
RARE_SYLLABLES = {"ê", "m", "n", "ng", "hm", "hng", "r", "yai", "bia",
                  "biang", "fiao", "cei", "sei", "tei", "den", "rua", "chua"}

#: CC-CEDICT 用 ``xx`` 當「讀音不明」的佔位符，不是音節。
PLACEHOLDER_SYLLABLES = {"xx"}

#: 反查表：注音 → 無調音節。ㄦ 同時是 ``er`` 與兒化 ``r``，取 ``er``。
ZHUYIN_TO_SYLLABLE = {}
for _syl, _zh in SYLLABLE_TO_ZHUYIN.items():
    if _zh not in ZHUYIN_TO_SYLLABLE or _syl in RARE_SYLLABLES:
        if _zh in ZHUYIN_TO_SYLLABLE and _syl in RARE_SYLLABLES:
            continue  # 已有非罕見的音節佔位，別覆蓋
        ZHUYIN_TO_SYLLABLE[_zh] = _syl
del _syl, _zh


class UnknownSyllable(ValueError):
    """音節不在對照表裡。"""


# ---------------------------------------------------------------------------
# 單音節轉換
# ---------------------------------------------------------------------------

def split_tone(syllable):
    """``'lu:4'`` → ``('lu:', 4)``；沒有聲調數字時視為輕聲 5。"""
    s = syllable.strip().lower()
    if s and s[-1].isdigit():
        return s[:-1], int(s[-1])
    return s, 5


def syllable_to_keys(base):
    """無調音節 → 拼音輸入法鍵入序列。

    只有兩條規則：**去掉聲調數字**（呼叫端負責）、``u:`` → ``v``。
    j/q/x/y 後面的 ü 在 CC-CEDICT 裡本來就寫作 ``u``，所以 ``ju1`` → ``ju``
    而不是 ``jv``——這正是這條規則夠用的原因。
    """
    if base not in SYLLABLE_TO_ZHUYIN:
        raise UnknownSyllable(base)
    return base.replace("u:", "v")


def syllable_to_zhuyin(base, tone=5):
    """無調音節 + 聲調 → 注音（含聲調符號）。"""
    if base not in SYLLABLE_TO_ZHUYIN:
        raise UnknownSyllable(base)
    body = SYLLABLE_TO_ZHUYIN[base]
    mark = ZHUYIN_TONE_MARKS.get(tone, "")
    if tone == 5:
        return mark + body if ZHUYIN_NEUTRAL_IS_PREFIX else body + mark
    return body + mark


def syllable_to_accented(base, tone=5):
    """無調音節 + 聲調 → 帶調拼音（``lu:`` + 4 → ``lǜ``）。"""
    if base not in SYLLABLE_TO_ZHUYIN:
        raise UnknownSyllable(base)
    if (base, tone) in _ACCENTED_IRREGULAR:
        return _ACCENTED_IRREGULAR[(base, tone)]
    plain = base.replace("u:", "ü")
    if tone == 5 or tone not in (1, 2, 3, 4):
        return plain
    idx = _accent_position(plain)
    vowel = plain[idx]
    return plain[:idx] + _ACCENTED_VOWELS[vowel][tone - 1] + plain[idx + 1:]


def _accent_position(plain):
    """聲調符號該標在哪個母音上（國語羅馬字標調規則）。

    a 最優先，其次 e/o；``iu`` 標在 u、``ui`` 標在 i（都是「標最後一個」）。
    """
    for v in ("a", "e", "o"):
        i = plain.find(v)
        if i >= 0:
            return i
    for i in range(len(plain) - 1, -1, -1):
        if plain[i] in _ACCENTED_VOWELS:
            return i
    raise UnknownSyllable(plain)


# ---------------------------------------------------------------------------
# 整串轉換（CC-CEDICT 的 "[lu:4 se4]" 這種）
# ---------------------------------------------------------------------------

def split_syllables(pinyin):
    """``'lu:4 se4'`` → ``['lu:4', 'se4']``。順手把標點與空音節濾掉。"""
    return [t for t in pinyin.replace("·", " ").split() if t]


def convert(pinyin):
    """整串 CC-CEDICT 拼音 → ``(keys, zhuyin, accented)`` 三個 list。

    任何一個音節不認得就丟 :class:`UnknownSyllable`，絕不靜默略過。
    """
    keys, zhuyin, accented = [], [], []
    for tok in split_syllables(pinyin):
        base, tone = split_tone(tok)
        keys.append(syllable_to_keys(base))
        zhuyin.append(syllable_to_zhuyin(base, tone))
        accented.append(syllable_to_accented(base, tone))
    return keys, zhuyin, accented


def parse_accented(text):
    """帶調拼音 → ``(無調音節, 聲調)``，例如 ``'lǜ'`` → ``('lu:', 4)``。

    Unihan 的讀音欄位（kMandarin / kXHC1983 …）用的是帶調拼音，這裡把它轉回
    CC-CEDICT 的慣例，好讓兩邊的資料走同一條轉換路徑。
    """
    import unicodedata

    tone = 5
    out = []
    for chunk in unicodedata.normalize("NFD", text.strip().lower()):
        if chunk == "̄":
            tone = 1
        elif chunk == "́":
            tone = 2
        elif chunk == "̌":
            tone = 3
        elif chunk == "̀":
            tone = 4
        elif chunk == "̈":  # ü 的兩點
            if out and out[-1] == "u":
                out[-1] = "u:"
            else:
                raise UnknownSyllable(text)
        elif chunk == "̂":  # ê 的尖帽（欸、誒）
            if out and out[-1] == "e":
                out[-1] = "ê"
            else:
                raise UnknownSyllable(text)
        elif unicodedata.combining(chunk):
            raise UnknownSyllable(text)
        else:
            out.append(chunk)
    base = "".join(out)
    # Unihan 偶爾寫 ü 而非 u:，也偶爾用 v
    base = base.replace("ü", "u:").replace("v", "u:")
    if base not in SYLLABLE_TO_ZHUYIN:
        raise UnknownSyllable(text)
    return base, tone


def zhuyin_to_keys(zhuyin_syllable):
    """注音（可含聲調符號）→ 鍵入序列。給 App 的注音查詢用。"""
    z = zhuyin_syllable.strip()
    z = z.lstrip("˙").rstrip("ˊˇˋ˙")
    if z not in ZHUYIN_TO_SYLLABLE:
        raise UnknownSyllable(zhuyin_syllable)
    return syllable_to_keys(ZHUYIN_TO_SYLLABLE[z])
