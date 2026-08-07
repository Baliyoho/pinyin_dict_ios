import Foundation

/// 字典查詢 API。所有 SQL 都集中在這裡，View 只拿到 model。
final class DictionaryStore {
    /// 清單型查詢（打拼音或注音）最多回幾個字。多了看不完，也拖慢逐字即時查詢。
    private static let listLimit = 40
    /// 每個讀音顯示幾個詞例。
    private static let examplesPerReading = 3

    private let database: Database

    init(database: Database) {
        self.database = database
    }

    /// 開啟打包在 app bundle 裡的 `dict.sqlite`。
    convenience init(bundle: Bundle = .main) throws {
        guard let path = bundle.path(forResource: "dict", ofType: "sqlite") else {
            throw Database.Failure.cannotOpen(
                path: "dict.sqlite", message: "字典檔不在 app bundle 裡"
            )
        }
        try self.init(database: Database(path: path))
    }

    // MARK: - 詞

    /// 整串詞查詢。繁簡都吃。
    ///
    /// 詞庫在繁簡相同時把 `simp` 存成空字串，所以比對 `trad` 那一邊一定會命中，
    /// 不需要 COALESCE。
    func word(_ text: String) -> WordEntry? {
        let sql = """
            SELECT trad, simp, pinyin, keys, zhuyin
            FROM words WHERE trad = ?1 OR simp = ?1
            ORDER BY freq DESC LIMIT 1
            """
        return (try? database.query(sql, [text]) { row in
            WordEntry(
                trad: row.string(0),
                simp: row.optionalString(1) ?? row.string(0),
                pinyin: row.string(2),
                keys: row.string(3),
                zhuyin: row.string(4)
            )
        })?.first
    }

    // MARK: - 字

    func charEntry(_ ch: String) -> CharEntry? {
        let sql = "SELECT strokes, radical, variant FROM chars WHERE ch = ?1"
        guard let row = (try? database.query(sql, [ch], transform: { row in
            (row.optionalInt(0), row.optionalString(1), row.optionalString(2))
        }))?.first else { return nil }

        return CharEntry(
            ch: ch,
            strokes: row.0,
            radical: row.1,
            variant: row.2,
            readings: readings(for: ch)
        )
    }

    /// 逐字拆解一串漢字。重複的字只查一次。
    func charEntries(in text: String) -> [CharEntry] {
        var seen = Set<String>()
        return text.compactMap { character in
            let ch = String(character)
            guard seen.insert(ch).inserted else { return nil }
            return charEntry(ch)
        }
    }

    private func readings(for ch: String) -> [Reading] {
        let examples = examplesByReading(for: ch)
        let sql = """
            SELECT pinyin, keys, zhuyin, freq, rank
            FROM readings WHERE ch = ?1 ORDER BY rank
            """
        return (try? database.query(sql, [ch]) { row in
            let pinyin = row.string(0)
            let keys = row.string(1)
            return Reading(
                pinyin: pinyin,
                keys: keys,
                zhuyin: row.string(2),
                freq: row.int(3),
                rank: row.int(4),
                examples: Array(
                    (examples[ReadingKey(keys: keys, pinyin: pinyin)] ?? [])
                        .prefix(Self.examplesPerReading)
                )
            )
        }) ?? []
    }

    private struct ReadingKey: Hashable {
        let keys: String
        let pinyin: String
    }

    /// 一次撈完一個字的所有詞例再分組，避免每個讀音各發一次查詢。
    ///
    /// 分組要連**帶調拼音**一起比，不能只比 keys：和 hé 與 和 hè 敲起來都是
    /// `he`，只比 keys 會把「和平」算成 hè 的例子。
    private func examplesByReading(for ch: String) -> [ReadingKey: [String]] {
        let sql = """
            SELECT reading_keys, reading_pinyin, word
            FROM char_word_examples WHERE ch = ?1
            ORDER BY freq DESC, rowid
            """
        let rows = (try? database.query(sql, [ch]) { row in
            (ReadingKey(keys: row.string(0), pinyin: row.string(1)), row.string(2))
        }) ?? []

        var grouped: [ReadingKey: [String]] = [:]
        for (key, word) in rows {
            grouped[key, default: []].append(word)
        }
        return grouped
    }

    // MARK: - 反查

    /// 用鍵入序列反查（打 `lv` 找出所有這樣敲的字）。
    func chars(matchingKeys keys: String) -> [CharEntry] {
        let sql = """
            SELECT DISTINCT r.ch FROM readings r JOIN chars c ON c.ch = r.ch
            WHERE r.keys = ?1 ORDER BY c.word_count DESC LIMIT \(Self.listLimit)
            """
        return charEntries(fromCharacterQuery: sql, [keys])
    }

    /// 用注音反查。沒打聲調就把五個聲調全找出來——省得還要先想清楚是幾聲。
    func chars(matchingZhuyin zhuyin: String) -> [CharEntry] {
        let hasTone = zhuyin.contains { "ˊˇˋ˙".contains($0) }
        let sql = hasTone
            ? """
              SELECT DISTINCT r.ch FROM readings r JOIN chars c ON c.ch = r.ch
              WHERE r.zhuyin = ?1 ORDER BY c.word_count DESC LIMIT \(Self.listLimit)
              """
            : """
              SELECT DISTINCT r.ch FROM readings r JOIN chars c ON c.ch = r.ch
              WHERE r.zhuyin IN (?1, ?1 || 'ˊ', ?1 || 'ˇ', ?1 || 'ˋ', '˙' || ?1)
              ORDER BY c.word_count DESC LIMIT \(Self.listLimit)
              """
        return charEntries(fromCharacterQuery: sql, [zhuyin])
    }

    private func charEntries(
        fromCharacterQuery sql: String, _ parameters: [String]
    ) -> [CharEntry] {
        let characters = (try? database.query(sql, parameters) { $0.string(0) }) ?? []
        return characters.compactMap(charEntry)
    }

    // MARK: - 統計

    struct Stats {
        let chars: Int
        let words: Int
    }

    /// 給「關於」頁用的實際筆數——講得出數字，才知道查不到時是資料沒收還是查錯了。
    func stats() -> Stats {
        func count(_ table: String) -> Int {
            (try? database.query("SELECT COUNT(*) FROM \(table)") { $0.int(0) })?
                .first ?? 0
        }
        return Stats(chars: count("chars"), words: count("words"))
    }

    /// 打到一半時，有沒有以這幾個字母開頭的鍵入序列。用來給「還沒打完」的提示。
    func keysStartingWith(_ prefix: String, limit: Int = 6) -> [String] {
        let sql = """
            SELECT DISTINCT keys FROM readings WHERE keys LIKE ?1 || '%'
            ORDER BY LENGTH(keys), keys LIMIT \(limit)
            """
        return (try? database.query(sql, [prefix]) { $0.string(0) }) ?? []
    }
}
