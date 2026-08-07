import SwiftUI

/// 一個讀音：實心點 = 主讀音，空心點 = 其他讀音。
struct ReadingRowView: View {
    let reading: Reading
    /// 剛才查的那個詞用的就是這個讀音。
    var isActive: Bool = false
    let isExpanded: Bool
    let onToggle: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                Image(systemName: reading.isPrimary ? "largecircle.fill.circle" : "circle")
                    .font(.caption)
                    .foregroundStyle(reading.isPrimary ? Color.accentColor : Color.secondary)
                    .accessibilityHidden(true)

                CopyableKeys(keys: reading.keys)

                Text(reading.pinyin)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Text(reading.zhuyin)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                // 主讀音不是這個詞用的讀音時，這個標記就是全畫面最重要的資訊
                if isActive {
                    Text("這個詞讀這個")
                        .font(.caption2)
                        .fontWeight(.medium)
                        .padding(.horizontal, 7)
                        .padding(.vertical, 3)
                        .background(Color.accentColor.opacity(0.16), in: .capsule)
                        .foregroundStyle(Color.accentColor)
                }

                Spacer(minLength: 0)

                if !reading.examples.isEmpty && !reading.isPrimary {
                    Button(action: onToggle) {
                        Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(isExpanded ? "收合詞例" : "展開詞例")
                }
            }

            if isExpanded && !reading.examples.isEmpty {
                // 詞例的用途是「這個敲法用在哪」，所以直接橫排，不加標題
                Text(reading.examples.joined(separator: " · "))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .padding(.leading, 26)
            }
        }
        .accessibilityElement(children: .contain)
        .accessibilityLabel(
            "\(reading.isPrimary ? "主讀音" : "其他讀音")，\(reading.pinyin)，\(reading.zhuyin)"
                + (isActive ? "，這個詞讀這個" : "")
        )
    }
}
