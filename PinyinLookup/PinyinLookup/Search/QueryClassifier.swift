import Foundation

/// 使用者到底打了什麼。
enum Query: Equatable {
    case empty
    /// 漢字，例如 `綠色`。
    case han(String)
    /// 注音符號（可含聲調），例如 `ㄌㄩˋ`。
    case zhuyin(String)
    /// 拉丁字母，例如 `lv`。已正規化成鍵入序列的寫法。
    case latin(String)
}

/// 依字元範圍自動判斷輸入類型，不需要模式切換按鈕。
///
/// 判斷順序是漢字 → 注音 → 拉丁字母。混打時以先出現的類型為準，這樣「用注音
/// 鍵盤打字打到一半」的中間狀態（ㄌㄩ 還沒選字）也能即時給出結果。
enum QueryClassifier {
    /// U+4E00–U+9FFF，CJK 基本區。字典只收這個範圍。
    static func isHan(_ scalar: Unicode.Scalar) -> Bool {
        (0x4E00...0x9FFF).contains(scalar.value)
    }

    /// U+3105–U+312F（ㄅ–ㄦ）加上四個聲調符號。
    static func isZhuyin(_ scalar: Unicode.Scalar) -> Bool {
        (0x3105...0x312F).contains(scalar.value) || isTone(scalar)
    }

    /// ˊ ˇ ˋ ˙
    static func isTone(_ scalar: Unicode.Scalar) -> Bool {
        [0x02CA, 0x02C7, 0x02CB, 0x02D9].contains(scalar.value)
    }

    static func classify(_ raw: String) -> Query {
        let text = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return .empty }

        let han = String(text.unicodeScalars.filter(isHan).map(Character.init))
        if !han.isEmpty { return .han(han) }

        // 聲調符號單獨出現不算注音（例如只打了一個 ˋ）
        let zhuyin = String(text.unicodeScalars.filter(isZhuyin).map(Character.init))
        if zhuyin.unicodeScalars.contains(where: { !isTone($0) }) {
            return .zhuyin(zhuyin)
        }

        let latin = normalizeKeys(text)
        return latin.isEmpty ? .empty : .latin(latin)
    }

    /// 把使用者打的拉丁字母正規化成資料庫裡的鍵入序列寫法。
    ///
    /// 同時接受 `lv` 與 `lü`——知道 ü 唸法的人會很自然地打 `lü`，但輸入法實際
    /// 要敲的是 `lv`，這正是這個 App 要弭平的落差，所以兩種都認。
    static func normalizeKeys(_ text: String) -> String {
        var out = ""
        for character in text.lowercased() {
            switch character {
            case "ü", "ǖ", "ǘ", "ǚ", "ǜ":
                out.append("v")
            case "a"..."z":
                out.append(character)
            default:
                break  // 數字、聲調、空白一律略過
            }
        }
        return out
    }
}
