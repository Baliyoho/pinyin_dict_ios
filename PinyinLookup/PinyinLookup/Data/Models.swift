import Foundation

/// 一個字的一種讀音。
///
/// 三個欄位對應三種需求：`keys` 是拼音輸入法真正要敲的字母（這個 App 的重點），
/// `pinyin` 是字典上看得懂的帶調拼音，`zhuyin` 是你本來就會的注音。
struct Reading: Identifiable, Hashable {
    /// 帶調拼音，例如 `lǜ`。
    let pinyin: String
    /// 輸入法鍵入序列，例如 `lv`。**這是第一級資訊。**
    let keys: String
    /// 注音，例如 `ㄌㄩˋ`。
    let zhuyin: String
    /// 這個讀音出現在多少 CC-CEDICT 詞條裡。用來排序，數字本身不顯示。
    let freq: Int
    /// 0 = 主讀音。
    let rank: Int
    /// 示範這個讀音的詞，例如 `["綠色", "綠豆", "常綠"]`。
    let examples: [String]

    var isPrimary: Bool { rank == 0 }
    var id: String { "\(pinyin)|\(keys)" }
}

/// 一個漢字，連同它所有的讀音。
struct CharEntry: Identifiable, Hashable {
    let ch: String
    let strokes: Int?
    let radical: String?
    /// 對應的繁體或簡體，沒有就是 nil。
    let variant: String?
    /// 依 rank 排序，第一個是主讀音。
    let readings: [Reading]

    var id: String { ch }
    /// 多音字——這個 App 最有價值、也最容易出錯的地方。
    var isPolyphonic: Bool { readings.count > 1 }
    var primary: Reading? { readings.first }
}

/// 詞庫裡的一筆詞條。
struct WordEntry: Hashable {
    let trad: String
    let simp: String
    /// 整串帶調拼音，例如 `lǜsè`。
    let pinyin: String
    /// 整串鍵入序列，音節間以空白分隔，例如 `lv se`。
    let keys: String
    /// 整串注音，例如 `ㄌㄩˋ ㄙㄜˋ`。
    let zhuyin: String
}

/// 畫面最上方那張「整串怎麼敲」的卡片。
struct PhraseHeader: Hashable {
    let text: String
    let keys: String
    let pinyin: String
    let zhuyin: String
    /// 讀音是查詞庫來的（可信），還是逐字拼出來的（多音字可能拼錯）。
    ///
    /// 這個差別要讓使用者看得見：逐字拼的時候每個字都取主讀音，碰到多音字就
    /// 有機會給錯，此時下面的單字卡才是真正該看的東西。
    let isExactWord: Bool
}

/// 一次查詢的結果。
struct SearchResult {
    var header: PhraseHeader?
    var chars: [CharEntry] = []
    /// 這串詞裡，每個字實際讀的是哪個音（以注音當識別碼，因為它把聲調也帶上了）。
    ///
    /// 「銀行」的行讀 háng，不是它自己的主讀音 xíng。少了這個對應，單字卡會用
    /// ● 標著 xíng，等於在使用者剛查完 yin hang 之後告訴他行要敲 xing。
    var phraseReadings: [String: Set<String>] = [:]
    /// 給使用者的一句說明（查無資料、或這批字是怎麼來的）。
    var notice: String?

    var isEmpty: Bool { header == nil && chars.isEmpty }

    static let none = SearchResult()
}
