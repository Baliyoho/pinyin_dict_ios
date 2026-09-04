#!/usr/bin/env python3
"""Build the offline dictionary files shipped with the web app.

Sources
  * pypinyin  - per-character readings, ordered by how common the reading is
  * CC-CEDICT - word readings, keyed by both traditional and simplified forms

Both are emitted as numbered ASCII pinyin (zhong1, lv4). The browser renders
tone marks and keyboard keystrokes from that single form.
"""
import re
import sys
import unicodedata
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "data"

TONE_VOWELS = {}
for base, marked in (
    ("a", "āáǎà"), ("o", "ōóǒò"), ("e", "ēéěè"),
    ("i", "īíǐì"), ("u", "ūúǔù"), ("v", "ǖǘǚǜ"),
    ("n", "ńňǹ"), ("m", "ḿ"),
):
    for tone, ch in enumerate(marked, start=1):
        TONE_VOWELS[ch] = (base, tone)
TONE_VOWELS["ü"] = ("v", 0)
TONE_VOWELS["ê"] = ("e", 0)


def marked_to_numbered(syllable):
    """'zhōng' -> 'zhong1', 'lǜ' -> 'lv4', 'de' -> 'de5'."""
    out, tone = [], 5
    for ch in syllable:
        if ch in TONE_VOWELS:
            base, t = TONE_VOWELS[ch]
            out.append(base)
            if t:
                tone = t
        else:
            out.append(ch)
    text = "".join(out)
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text + str(tone)


VALID = re.compile(r"^[a-z:]+[1-5]$")
CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿\U00020000-\U0003ffff]")


def clean_cedict_syllable(syllable):
    """'Ni3' -> 'ni3', 'lu:4' -> 'lv4'. Returns None for junk like 'xx5'."""
    s = syllable.lower().replace("u:", "v")
    if not VALID.match(s):
        return None
    return s


def load_chars():
    sys.path.insert(0, "/tmp/pp/x")
    from pypinyin.pinyin_dict import pinyin_dict

    chars = OrderedDict()
    for code, readings in pinyin_dict.items():
        ch = chr(code)
        if not CJK.match(ch):
            continue
        seen = []
        for reading in readings.split(","):
            numbered = marked_to_numbered(reading.strip())
            if VALID.match(numbered) and numbered not in seen:
                seen.append(numbered)
        if seen:
            chars[ch] = seen
    return chars


def load_cedict(path, chars):
    """Word readings from CC-CEDICT, indexed under traditional and simplified."""
    words = OrderedDict()
    line_re = re.compile(r"^(\S+)\s+(\S+)\s+\[([^]]*)\]")
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            m = line_re.match(line)
            if not m:
                continue
            trad, simp, raw = m.groups()
            syllables = [clean_cedict_syllable(s) for s in raw.split()]
            if not syllables or any(s is None for s in syllables):
                continue
            reading = " ".join(syllables)
            for headword in (trad, simp):
                # One syllable per character, or the reading can't be aligned.
                if len(headword) != len(syllables) or not CJK.search(headword):
                    continue
                if any(not CJK.match(c) for c in headword):
                    continue
                readings = words.setdefault(headword, [])
                if reading not in readings and len(readings) < 3:
                    readings.append(reading)
    # Single characters live in chars.txt; keep words.txt to actual words.
    for key in [k for k in words if len(k) < 2]:
        merge_single(chars, key, words.pop(key))
    return words


def merge_single(chars, ch, readings):
    """Add a CC-CEDICT reading for a character pypinyin doesn't know about."""
    existing = chars.setdefault(ch, [])
    for reading in readings:
        if reading not in existing:
            existing.append(reading)


def load_pypinyin_phrases(words):
    """Fill gaps CC-CEDICT misses (mostly simplified colloquialisms)."""
    from pypinyin.phrases_dict import phrases_dict

    added = 0
    for phrase, per_char in phrases_dict.items():
        if phrase in words or not all(CJK.match(c) for c in phrase):
            continue
        if len(phrase) != len(per_char):
            continue
        syllables = [marked_to_numbered(group[0]) for group in per_char]
        if any(not VALID.match(s) for s in syllables):
            continue
        words[phrase] = [" ".join(syllables)]
        added += 1
    return added


def mark_rare(chars, words):
    """Flag readings no word in the dictionary actually uses.

    pypinyin lists literary and variant readings (開 also has qiān), which turns
    almost every character into a 多音字 unless the rare ones are marked.
    """
    usage = defaultdict(Counter)
    for word, readings in words.items():
        for ch, syllable in zip(word, readings[0].split(" ")):
            usage[ch][syllable] += 1

    for ch, readings in chars.items():
        attested = [r for r in readings if usage[ch][r]]
        if not attested:
            attested = readings[:1]      # nothing to go on: trust pypinyin's first
        chars[ch] = [r if r in attested else "~" + r for r in readings]


def write(path, rows):
    with path.open("w", encoding="utf-8") as fh:
        for key, values in rows.items():
            fh.write(key + "\t" + "|".join(values) + "\n")
    return path.stat().st_size


def main():
    cedict = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/cedict/cedict_ts.u8")
    OUT.mkdir(parents=True, exist_ok=True)

    chars = load_chars()
    words = load_cedict(cedict, chars)
    added = load_pypinyin_phrases(words)
    mark_rare(chars, words)

    # Longest word decides the segmenter's lookahead window.
    max_len = max(len(w) for w in words)
    (OUT / "meta.json").write_text(
        '{"chars":%d,"words":%d,"maxWordLength":%d}\n' % (len(chars), len(words), max_len),
        encoding="utf-8",
    )
    kb = lambda n: "%.1f MB" % (n / 1048576)
    print("chars:", len(chars), kb(write(OUT / "chars.txt", chars)))
    print("words:", len(words), "(+%d from pypinyin)" % added, kb(write(OUT / "words.txt", words)))
    print("max word length:", max_len)


if __name__ == "__main__":
    main()
