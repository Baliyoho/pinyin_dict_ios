import Foundation
import Observation

/// 主畫面的狀態。
///
/// 輸入一改就立刻重查——查詢是本機 SQLite，單次不到 1 毫秒，不需要 debounce，
/// 也就沒有「打完再按搜尋」這回事。改動由 View 的 `onChange` 驅動，而不是
/// 屬性觀察器：`@Observable` 會把儲存屬性改寫成計算屬性，跟 `didSet` 混用是
/// 自找麻煩。
@Observable
final class SearchViewModel {
    var input: String = ""

    private(set) var result: SearchResult = .none

    private let store: DictionaryStore

    init(store: DictionaryStore) {
        self.store = store
    }

    func clear() {
        input = ""
        refresh()
    }

    func refresh() {
        switch QueryClassifier.classify(input) {
        case .empty:
            result = .none
        case let .han(text):
            result = lookUpHan(text)
        case let .zhuyin(zhuyin):
            result = lookUpZhuyin(zhuyin)
        case let .latin(keys):
            result = lookUpLatin(keys)
        }
    }

    // MARK: - 漢字

    private func lookUpHan(_ text: String) -> SearchResult {
        let entries = store.charEntries(in: text)
        guard !entries.isEmpty else {
            return SearchResult(notice: "字典裡沒有「\(text)」。這本字典收 CJK 基本區的兩萬多字。")
        }
        let word = text.count > 1 ? store.word(text) : nil
        return SearchResult(
            header: header(for: text, entries: entries, word: word),
            chars: entries,
            phraseReadings: word.map { phraseReadings(for: text, word: $0) } ?? [:]
        )
    }

    /// 把詞條的注音逐位對回每個字，得出「這個字在這個詞裡讀什麼」。
    ///
    /// 字數與音節數對不上時（少數詞條會這樣）就整個放棄——寧可不標，也不要標錯。
    private func phraseReadings(for text: String, word: WordEntry) -> [String: Set<String>] {
        let syllables = word.zhuyin.split(separator: " ").map(String.init)
        guard syllables.count == text.count else { return [:] }
        var readings: [String: Set<String>] = [:]
        for (character, zhuyin) in zip(text, syllables) {
            readings[String(character), default: []].insert(zhuyin)
        }
        return readings
    }

    /// 整串怎麼敲。
    ///
    /// 優先查詞庫——詞庫知道「銀行」的行讀 háng。查不到才逐字取主讀音拼起來，
    /// 但那對多音字可能拼錯，所以會標記成非精確結果讓畫面提醒使用者。
    private func header(
        for text: String, entries: [CharEntry], word: WordEntry?
    ) -> PhraseHeader? {
        guard text.count > 1 else { return nil }

        if let word {
            return PhraseHeader(
                text: text,
                keys: word.keys,
                pinyin: word.pinyin,
                zhuyin: word.zhuyin,
                isExactWord: true
            )
        }

        // charEntries 會把重複的字去掉，所以要回頭照原文的順序逐字對回去
        let byCharacter = Dictionary(
            entries.map { ($0.ch, $0) }, uniquingKeysWith: { first, _ in first }
        )
        var keys: [String] = []
        var pinyin: [String] = []
        var zhuyin: [String] = []
        for character in text {
            guard let reading = byCharacter[String(character)]?.primary else {
                return nil
            }
            keys.append(reading.keys)
            pinyin.append(reading.pinyin)
            zhuyin.append(reading.zhuyin)
        }
        return PhraseHeader(
            text: text,
            keys: keys.joined(separator: " "),
            pinyin: pinyin.joined(),
            zhuyin: zhuyin.joined(separator: " "),
            isExactWord: false
        )
    }

    // MARK: - 反查

    private func lookUpLatin(_ keys: String) -> SearchResult {
        let entries = store.chars(matchingKeys: keys)
        if !entries.isEmpty {
            return SearchResult(chars: entries, notice: "敲「\(keys)」的字")
        }
        let candidates = store.keysStartingWith(keys)
        if candidates.isEmpty {
            return SearchResult(notice: "沒有「\(keys)」這個敲法。")
        }
        return SearchResult(
            notice: "還沒打完？以「\(keys)」開頭的敲法："
                + candidates.joined(separator: "、")
        )
    }

    private func lookUpZhuyin(_ zhuyin: String) -> SearchResult {
        let entries = store.chars(matchingZhuyin: zhuyin)
        guard !entries.isEmpty else {
            return SearchResult(notice: "沒有讀「\(zhuyin)」的字。")
        }
        let hasTone = zhuyin.unicodeScalars.contains(where: QueryClassifier.isTone)
        return SearchResult(
            chars: entries,
            notice: hasTone ? "讀「\(zhuyin)」的字" : "讀「\(zhuyin)」的字（不分聲調）"
        )
    }
}
