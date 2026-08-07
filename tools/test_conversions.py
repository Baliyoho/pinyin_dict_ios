#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""轉換正確性測試。

    python3 tools/test_conversions.py

分三類：
  * **全量覆蓋** — CC-CEDICT 裡每一個不重複音節都必須轉得出鍵入序列與注音，
    覆蓋率必須 100%；轉不出來的要被列出來，不准靜默略過。
  * **已知案例回歸** — 規格裡點名的那幾個坑（綠／路／女／居／略／六／對）。
  * **多音字對齊** — 逐位對齊真的有把「某字在某詞裡讀什麼」算對。

覆蓋率測試需要 CC-CEDICT；沒有網路又沒有快取時會直接 skip 而不是假裝通過。
"""

import os
import re
import sys
import unittest
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import build_dict
import zhuyin_table as zt

#: CC-CEDICT 用來表示「讀音不明」的佔位符，不是音節。
PLACEHOLDERS = zt.PLACEHOLDER_SYLLABLES

#: CC-CEDICT 有幾個舊式「合體度量衡字」，一個字配兩個音節卻寫成一串
#: （兛 = ``qian1ke4`` = 千克）。它們是資料慣例，不是音節。
CONTRACTIONS = {
    "bai3ke", "bai3mi", "bai3wa", "fen1ke", "fen1wa", "hao2ke", "hao2wa",
    "li2ke", "li3wa", "qian1ke", "qian1wa", "shi2ke", "shi2wa",
}

HAN = re.compile(r"^[一-鿿]+$")

_cedict_cache = None


def load_cedict():
    """讀 CC-CEDICT；抓不到就回 None（測試會 skip）。"""
    global _cedict_cache
    if _cedict_cache is None:
        try:
            _cedict_cache = build_dict.parse_cedict(
                build_dict.fetch_cedict(), lambda *a: None
            )
        except Exception as exc:  # 沒網路也沒快取
            print(f"（取不到 CC-CEDICT，覆蓋率測試會被略過：{exc}）")
            _cedict_cache = []
    return _cedict_cache


class TestKeys(unittest.TestCase):
    """拼音 → 輸入法鍵入序列。這是整個 App 的核心價值。"""

    CASES = [
        ("lu:4", "lv", "綠 — ü 敲成 v，這正是字典不會告訴你的事"),
        ("lu4", "lu", "路 — 真正的 u，不變"),
        ("nu:3", "nv", "女"),
        ("ju1", "ju", "居 — j/q/x/y 後只有 ü，CC-CEDICT 已寫成 u，不是 jv"),
        ("lu:e4", "lve", "略"),
        ("liu4", "liu", "六 — iou 的縮寫，輸入法照敲"),
        ("dui4", "dui", "對 — uei 的縮寫"),
        ("qu4", "qu", "去"),
        ("xue2", "xue", "學"),
        ("nu:e4", "nve", "虐"),
        ("jun1", "jun", "軍 — 唸 ㄐㄩㄣ 但敲 jun"),
        ("weng1", "weng", "翁"),
        ("zhi1", "zhi", "之"),
    ]

    def test_known_cases(self):
        for token, expected, why in self.CASES:
            with self.subTest(token=token):
                base, _ = zt.split_tone(token)
                self.assertEqual(zt.syllable_to_keys(base), expected, why)

    def test_keys_never_contain_tone_or_colon(self):
        for base in zt.SYLLABLE_TO_ZHUYIN:
            keys = zt.syllable_to_keys(base)
            self.assertRegex(keys, r"^[a-zê]+$", f"{base} → {keys}")


class TestZhuyin(unittest.TestCase):
    CASES = [
        ("lu:4", "ㄌㄩˋ", "綠"),
        ("lu4", "ㄌㄨˋ", "路"),
        ("nu:3", "ㄋㄩˇ", "女"),
        ("ju1", "ㄐㄩ", "居 — 一聲不標符號"),
        ("lu:e4", "ㄌㄩㄝˋ", "略"),
        ("liu4", "ㄌㄧㄡˋ", "六 — iu 其實是 ㄧㄡ"),
        ("dui4", "ㄉㄨㄟˋ", "對 — ui 其實是 ㄨㄟ"),
        ("jun1", "ㄐㄩㄣ", "軍"),
        ("weng1", "ㄨㄥ", "翁"),
        ("de5", "˙ㄉㄜ", "的 — 輕聲的點在前面"),
        ("se4", "ㄙㄜˋ", "色"),
        ("er2", "ㄦˊ", "兒"),
        ("zhi1", "ㄓ", "之 — 空韻不寫韻母"),
    ]

    def test_known_cases(self):
        for token, expected, why in self.CASES:
            with self.subTest(token=token):
                base, tone = zt.split_tone(token)
                self.assertEqual(zt.syllable_to_zhuyin(base, tone), expected, why)

    def test_roundtrip_zhuyin_to_keys(self):
        """注音查詢要能反查回同一組鍵入序列。"""
        for base in zt.SYLLABLE_TO_ZHUYIN:
            if base in zt.RARE_SYLLABLES:
                continue
            zhuyin = zt.syllable_to_zhuyin(base, 4)
            self.assertEqual(zt.zhuyin_to_keys(zhuyin), zt.syllable_to_keys(base), base)

    def test_no_duplicate_zhuyin(self):
        """一個注音串不該對應到兩個常用音節，否則反查會變曖昧。"""
        counts = Counter(
            z for s, z in zt.SYLLABLE_TO_ZHUYIN.items() if s not in zt.RARE_SYLLABLES
        )
        self.assertEqual([z for z, n in counts.items() if n > 1], [])


class TestAccented(unittest.TestCase):
    CASES = [
        ("lu:4", "lǜ"), ("lu4", "lù"), ("nu:3", "nǚ"), ("ju1", "jū"),
        ("lu:e4", "lüè"), ("liu4", "liù"), ("dui4", "duì"), ("de5", "de"),
        ("hao3", "hǎo"), ("xue2", "xué"), ("er2", "ér"), ("gui4", "guì"),
        ("jiu3", "jiǔ"), ("zhuang1", "zhuāng"),
    ]

    def test_known_cases(self):
        for token, expected in self.CASES:
            with self.subTest(token=token):
                base, tone = zt.split_tone(token)
                self.assertEqual(zt.syllable_to_accented(base, tone), expected)

    def test_parse_accented_roundtrip(self):
        """Unihan 的帶調拼音要能解析回 CC-CEDICT 的寫法。"""
        for base in zt.SYLLABLE_TO_ZHUYIN:
            if base in zt.RARE_SYLLABLES:
                continue
            for tone in (1, 2, 3, 4, 5):
                text = zt.syllable_to_accented(base, tone)
                got_base, got_tone = zt.parse_accented(text)
                self.assertEqual((got_base, got_tone), (base, tone), text)


class TestPhrase(unittest.TestCase):
    def test_lu_se(self):
        keys, zhuyin, accented = zt.convert("lu:4 se4")
        self.assertEqual(keys, ["lv", "se"])
        self.assertEqual(zhuyin, ["ㄌㄩˋ", "ㄙㄜˋ"])
        self.assertEqual(accented, ["lǜ", "sè"])

    def test_unknown_syllable_raises(self):
        """轉不出來要炸掉，不准靜默通過。"""
        with self.assertRaises(zt.UnknownSyllable):
            zt.convert("zzz1")


class TestCedictCoverage(unittest.TestCase):
    """全量覆蓋：CC-CEDICT 的每一個音節都要轉得出來。"""

    def setUp(self):
        self.entries = load_cedict()
        if not self.entries:
            self.skipTest("取不到 CC-CEDICT")

    def _syllable_universe(self):
        """漢字詞條裡出現的所有無調音節（排除佔位符與合體度量衡字）。"""
        universe = Counter()
        for entry in self.entries:
            if not (HAN.match(entry.trad) or HAN.match(entry.simp)):
                continue  # 含拉丁字母的詞條（打call、AA制）不是漢語音節
            for token in entry.syllables:
                base, _ = zt.split_tone(token)
                if base in PLACEHOLDERS or base in CONTRACTIONS:
                    continue
                universe[base] += 1
        return universe

    def test_full_coverage(self):
        universe = self._syllable_universe()
        missing = sorted(s for s in universe if s not in zt.SYLLABLE_TO_ZHUYIN)
        self.assertEqual(
            missing, [],
            f"對照表沒收到 {len(missing)} 個音節（共 {len(universe)} 個）：{missing}",
        )
        for base in universe:
            zt.syllable_to_keys(base)
            zt.syllable_to_zhuyin(base, 1)
            zt.syllable_to_accented(base, 1)
        print(f"\n  音節覆蓋率 100%：{len(universe)} 個不重複音節")

    def test_universe_size_is_sane(self):
        """音節數大幅變動代表資料或篩選條件出事了，要有人看一眼。"""
        n = len(self._syllable_universe())
        self.assertTrue(400 <= n <= 440, f"不重複音節數 {n}，預期 400–440")

    def test_placeholders_are_accounted_for(self):
        """佔位符與合體字必須真的存在，否則這兩張例外清單已經過期。"""
        seen = {zt.split_tone(t)[0] for e in self.entries for t in e.syllables}
        self.assertTrue(PLACEHOLDERS & seen, "xx 佔位符不見了，例外清單該清掉")
        self.assertTrue(CONTRACTIONS & seen, "合體度量衡字不見了，例外清單該清掉")


class TestAlignment(unittest.TestCase):
    """多音字逐位對齊 — 這是決定讀音排序的關鍵，也最容易錯。"""

    @classmethod
    def setUpClass(cls):
        entries = load_cedict()
        cls.freq = None
        if entries:
            cls.freq, cls.examples, _, cls.stats = build_dict.align(
                entries, lambda *a: None
            )

    def setUp(self):
        if self.freq is None:
            self.skipTest("取不到 CC-CEDICT")

    def _readings(self, ch):
        return {
            (base, tone): n
            for (c, base, tone), n in self.freq.items() if c == ch
        }

    def test_polyphone_readings_present(self):
        cases = [
            ("行", {("hang", 2), ("xing", 2)}, "銀行 hang2 / 行走 xing2"),
            ("長", {("zhang", 3), ("chang", 2)}, "長大 zhang3 / 長短 chang2"),
            ("綠", {("lu:", 4), ("lu", 4)}, "綠色 lv / 綠林 lu"),
        ]
        for ch, expected, why in cases:
            with self.subTest(ch=ch):
                self.assertTrue(expected <= set(self._readings(ch)), why)

    def test_lv_beats_lu_for_green(self):
        readings = self._readings("綠")
        self.assertGreater(readings[("lu:", 4)], readings[("lu", 4)],
                           "綠 的主讀音該是 lv（lu:4），詞條數要多於 lu4")

    def test_examples_demonstrate_the_reading(self):
        """綠色要示範 lv，綠林要示範 lu。"""
        lv_words = {e.trad for e in self.examples[("綠", "lv", "lǜ")]}
        lu_words = {e.trad for e in self.examples[("綠", "lu", "lù")]}
        self.assertIn("綠色", lv_words)
        self.assertIn("綠林", lu_words)
        self.assertNotIn("綠林", lv_words)

    def test_examples_are_tone_aware(self):
        """和 hé 與 和 hè 敲起來都是 he，詞例不准混在一起。"""
        he2 = {e.trad for e in self.examples[("和", "he", "hé")]}
        he4 = {e.trad for e in self.examples[("和", "he", "hè")]}
        self.assertIn("和平", he2)
        self.assertIn("應和", he4)
        self.assertNotIn("和平", he4)

    def test_erhua_and_mismatches_excluded(self):
        self.assertGreater(self.stats["erhua"], 0, "應該有兒化詞條被排除")
        self.assertGreater(self.stats["aligned"], 100000, "對齊的詞條太少")


if __name__ == "__main__":
    unittest.main(verbosity=2)
