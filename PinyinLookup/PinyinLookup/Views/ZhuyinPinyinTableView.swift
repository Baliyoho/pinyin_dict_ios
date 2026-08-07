import SwiftUI
import UIKit

/// 注音 ↔ 拼音對照表。查詢之外的另一半：整體參照，順便把輸入法的拼寫陷阱講清楚。
struct ZhuyinPinyinTableView: View {
    var body: some View {
        List {
            Section {
                ForEach(SpellingTrap.all) { trap in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 8) {
                            Text(trap.rule)
                                .font(.system(.subheadline, design: .monospaced, weight: .semibold))
                            Text(trap.title)
                                .font(.subheadline)
                        }
                        Text(trap.detail)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 2)
                }
            } header: {
                Text("輸入法的拼寫陷阱")
            } footer: {
                Text("這幾條是拼音「寫出來的樣子」跟「敲出來的樣子」不一致的地方，也是這個 App 存在的理由。")
            }

            ForEach(SyllableSection.all) { section in
                Section {
                    LazyVGrid(
                        columns: [GridItem(.adaptive(minimum: 74), spacing: 10)],
                        spacing: 10
                    ) {
                        ForEach(section.pairs) { pair in
                            PairChip(pair: pair)
                        }
                    }
                    .padding(.vertical, 4)
                } header: {
                    Text(section.title)
                } footer: {
                    if let note = section.note {
                        Text(note)
                    }
                }
            }
        }
        .navigationTitle("注音 ↔ 拼音")
        .navigationBarTitleDisplayMode(.inline)
    }
}

private struct PairChip: View {
    let pair: SyllablePair

    var body: some View {
        VStack(spacing: 2) {
            Text(pair.zhuyin)
                .font(.title3)
            Text(pair.pinyin)
                .font(.system(.footnote, design: .monospaced))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 8)
        .background(Color(.secondarySystemGroupedBackground), in: .rect(cornerRadius: 8))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(pair.zhuyin)，拼音 \(pair.pinyin)")
    }
}

struct SyllablePair: Identifiable {
    let zhuyin: String
    let pinyin: String
    var id: String { zhuyin + pinyin }

    init(_ zhuyin: String, _ pinyin: String) {
        self.zhuyin = zhuyin
        self.pinyin = pinyin
    }
}

struct SyllableSection: Identifiable {
    let title: String
    let note: String?
    let pairs: [SyllablePair]
    var id: String { title }

    static let all: [SyllableSection] = [
        SyllableSection(title: "聲母", note: nil, pairs: [
            SyllablePair("ㄅ", "b"), SyllablePair("ㄆ", "p"), SyllablePair("ㄇ", "m"), SyllablePair("ㄈ", "f"),
            SyllablePair("ㄉ", "d"), SyllablePair("ㄊ", "t"), SyllablePair("ㄋ", "n"), SyllablePair("ㄌ", "l"),
            SyllablePair("ㄍ", "g"), SyllablePair("ㄎ", "k"), SyllablePair("ㄏ", "h"),
            SyllablePair("ㄐ", "j"), SyllablePair("ㄑ", "q"), SyllablePair("ㄒ", "x"),
            SyllablePair("ㄓ", "zh"), SyllablePair("ㄔ", "ch"), SyllablePair("ㄕ", "sh"), SyllablePair("ㄖ", "r"),
            SyllablePair("ㄗ", "z"), SyllablePair("ㄘ", "c"), SyllablePair("ㄙ", "s"),
        ]),
        SyllableSection(
            title: "韻母",
            note: "ㄩ 單獨或接在 ㄋ/ㄌ 後面時要敲 v；接在 j/q/x/y 後面則敲 u。",
            pairs: [
                SyllablePair("ㄚ", "a"), SyllablePair("ㄛ", "o"), SyllablePair("ㄜ", "e"), SyllablePair("ㄝ", "ê"),
                SyllablePair("ㄞ", "ai"), SyllablePair("ㄟ", "ei"), SyllablePair("ㄠ", "ao"), SyllablePair("ㄡ", "ou"),
                SyllablePair("ㄢ", "an"), SyllablePair("ㄣ", "en"), SyllablePair("ㄤ", "ang"), SyllablePair("ㄥ", "eng"),
                SyllablePair("ㄦ", "er"),
                SyllablePair("ㄧ", "i"), SyllablePair("ㄨ", "u"), SyllablePair("ㄩ", "ü / v"),
            ]
        ),
        SyllableSection(
            title: "結合韻 ㄧ",
            note: "ㄧㄡ 寫成 iu、ㄧㄢ 的 a 唸得像 ㄝ——寫法跟唸法不一致的地方要記住的是寫法。",
            pairs: [
                SyllablePair("ㄧㄚ", "ia"), SyllablePair("ㄧㄛ", "io"), SyllablePair("ㄧㄝ", "ie"),
                SyllablePair("ㄧㄞ", "iai"), SyllablePair("ㄧㄠ", "iao"), SyllablePair("ㄧㄡ", "iu"),
                SyllablePair("ㄧㄢ", "ian"), SyllablePair("ㄧㄣ", "in"), SyllablePair("ㄧㄤ", "iang"),
                SyllablePair("ㄧㄥ", "ing"), SyllablePair("ㄩㄥ", "iong"),
            ]
        ),
        SyllableSection(
            title: "結合韻 ㄨ",
            note: "ㄨㄟ 寫成 ui、ㄨㄣ 寫成 un、ㄨㄥ 接在聲母後寫成 ong。",
            pairs: [
                SyllablePair("ㄨㄚ", "ua"), SyllablePair("ㄨㄛ", "uo"), SyllablePair("ㄨㄞ", "uai"),
                SyllablePair("ㄨㄟ", "ui"), SyllablePair("ㄨㄢ", "uan"), SyllablePair("ㄨㄣ", "un"),
                SyllablePair("ㄨㄤ", "uang"), SyllablePair("ㄨㄥ", "ong"),
            ]
        ),
        SyllableSection(
            title: "結合韻 ㄩ",
            note: "接在 ㄋ/ㄌ 後面要敲 v：ㄋㄩˇ = nv、ㄌㄩㄝˋ = lve。",
            pairs: [
                SyllablePair("ㄩㄝ", "üe / ve"), SyllablePair("ㄩㄢ", "üan"), SyllablePair("ㄩㄣ", "ün"),
            ]
        ),
        SyllableSection(
            title: "整體認讀音節",
            note: "這些音節照著敲就好，不用拆聲母韻母。ㄓㄔㄕㄖㄗㄘㄙ 單獨成音節時後面補一個 i。",
            pairs: [
                SyllablePair("ㄓ", "zhi"), SyllablePair("ㄔ", "chi"), SyllablePair("ㄕ", "shi"), SyllablePair("ㄖ", "ri"),
                SyllablePair("ㄗ", "zi"), SyllablePair("ㄘ", "ci"), SyllablePair("ㄙ", "si"),
                SyllablePair("ㄧ", "yi"), SyllablePair("ㄨ", "wu"), SyllablePair("ㄩ", "yu"),
                SyllablePair("ㄧㄝ", "ye"), SyllablePair("ㄩㄝ", "yue"), SyllablePair("ㄩㄢ", "yuan"),
                SyllablePair("ㄧㄣ", "yin"), SyllablePair("ㄩㄣ", "yun"), SyllablePair("ㄧㄥ", "ying"),
            ]
        ),
        SyllableSection(title: "聲調", note: "拼音輸入法不打聲調，這欄只是為了看得懂字典。", pairs: [
            SyllablePair("（無）", "1 聲 mā"), SyllablePair("ˊ", "2 聲 má"),
            SyllablePair("ˇ", "3 聲 mǎ"), SyllablePair("ˋ", "4 聲 mà"), SyllablePair("˙", "輕聲 ma"),
        ]),
    ]
}

struct SpellingTrap: Identifiable {
    let rule: String
    let title: String
    let detail: String
    var id: String { rule }

    static let all: [SpellingTrap] = [
        SpellingTrap(rule: "ü → v", title: "ㄩ 敲 v",
             detail: "綠 lǜ 敲 lv、女 nǚ 敲 nv、略 lüè 敲 lve。鍵盤上沒有 ü，一律用 v 代替。"),
        SpellingTrap(rule: "ju ≠ jv", title: "j/q/x/y 後面的 u 其實是 ü",
             detail: "居 jū、去 qù、學 xué、雲 yún 唸的都是 ㄩ，但這幾個聲母後面不可能有真正的 u，"
                 + "所以直接寫 u 也不會搞混——敲 ju 不是 jv。"),
        SpellingTrap(rule: "iu = iou", title: "ㄧㄡ 寫成 iu",
             detail: "六 liù 敲 liu、九 jiǔ 敲 jiu。中間的 o 在拼寫時省掉了。"),
        SpellingTrap(rule: "ui = uei", title: "ㄨㄟ 寫成 ui",
             detail: "對 duì 敲 dui、水 shuǐ 敲 shui。中間的 e 在拼寫時省掉了。"),
        SpellingTrap(rule: "un = uen", title: "ㄨㄣ 寫成 un",
             detail: "論 lùn 敲 lun、春 chūn 敲 chun。"),
        SpellingTrap(rule: "ong = ueng", title: "ㄨㄥ 接聲母寫成 ong",
             detail: "東 dōng 敲 dong；但單獨成音節時寫 weng（翁）。"),
    ]
}
