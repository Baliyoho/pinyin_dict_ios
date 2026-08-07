import SwiftUI
import UIKit

/// 整串的鍵入序列——畫面上最大、最醒目的東西。
///
/// 你查「綠色」，真正想知道的是「敲 lv se」。帶調拼音與注音是輔助，字小一號。
struct PhraseHeaderView: View {
    let header: PhraseHeader

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(header.text)
                .font(.title3)
                .foregroundStyle(.secondary)

            CopyableKeys(keys: header.keys, prominent: true)

            HStack(spacing: 8) {
                Text(header.pinyin)
                Text("·").foregroundStyle(.tertiary)
                Text(header.zhuyin)
            }
            .font(.subheadline)
            .foregroundStyle(.secondary)

            if !header.isExactWord {
                Label(
                    "詞庫裡沒有這個詞，上面是逐字取主讀音拼出來的。碰到多音字不一定對，"
                        + "以下面的單字卡為準。",
                    systemImage: "exclamationmark.triangle"
                )
                .font(.caption)
                .foregroundStyle(.orange)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color(.secondarySystemGroupedBackground), in: .rect(cornerRadius: 14))
    }
}
