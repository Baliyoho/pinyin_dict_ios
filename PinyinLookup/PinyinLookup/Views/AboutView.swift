import SwiftUI

/// 資料來源標註。
///
/// 純自用不散布其實沒有標註義務，但兩份資料都是別人無償維護出來的，寫上去
/// 幾乎零成本。順便把「這本字典收了什麼、沒收什麼」講清楚，查不到時才知道原因。
struct AboutView: View {
    let store: DictionaryStore

    /// COUNT(*) 要掃一整張表，別讓它跟著每次重繪跑。
    @State private var stats: DictionaryStore.Stats?

    var body: some View {
        List {
            Section("這是什麼") {
                Text("一般字典告訴你「綠 = lǜ」，但拼音輸入法實際上要敲 lv——不打聲調，ü 敲成 v。"
                     + "這個 App 把那段落差算好，讓你用注音鍵盤打出漢字，直接得到拼音輸入法的鍵入序列。")
                .font(.subheadline)
            }

            Section("字典內容") {
                LabeledContent("單字", value: stats.map { "\($0.chars.formatted()) 字" } ?? "—")
                LabeledContent("詞條", value: stats.map { "\($0.words.formatted()) 筆" } ?? "—")
                LabeledContent("收字範圍", value: "U+4E00–U+9FFF")
                Text("100% 離線，沒有廣告，沒有網路連線。")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Section {
                source(
                    name: "Unihan Database",
                    detail: "讀音、筆畫、部首、繁簡對應",
                    license: "Unicode License",
                    url: "https://www.unicode.org/Public/UNIDATA/Unihan.zip"
                )
                source(
                    name: "CC-CEDICT",
                    detail: "詞語拼音、多音字詞例",
                    license: "CC BY-SA 4.0",
                    url: "https://www.mdbg.net/chinese/dictionary?page=cedict"
                )
            } header: {
                Text("資料來源")
            } footer: {
                Text("兩份資料都由社群無償維護，本 App 未修改其內容，僅重新編排。")
            }

            Section("已知限制") {
                bullet("讀音排序依 CC-CEDICT 的詞條數，不是台灣教育部的審定音，"
                       + "少數字的主讀音可能跟你學的不一樣。")
                bullet("兒化音（花兒）沒有收進逐字對齊，以免把 r 誤算成一個字的讀音。")
                bullet("詞庫查不到的詞會逐字取主讀音拼起來，多音字可能拼錯，畫面上會標示。")
            }
        }
        .navigationTitle("關於")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if stats == nil { stats = store.stats() }
        }
    }

    private func source(name: String, detail: String, license: String, url: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(name).font(.body.weight(.medium))
            Text(detail).font(.caption).foregroundStyle(.secondary)
            Text(license).font(.caption2).foregroundStyle(.tertiary)
            if let link = URL(string: url) {
                Link(url, destination: link)
                    .font(.caption2)
            }
        }
        .padding(.vertical, 2)
    }

    private func bullet(_ text: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text("·")
            Text(text)
        }
        .font(.caption)
        .foregroundStyle(.secondary)
    }
}
