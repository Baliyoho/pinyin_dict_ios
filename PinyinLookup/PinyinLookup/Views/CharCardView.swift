import SwiftUI
import UIKit

/// 單字卡：一個字、它所有的讀音、以及筆畫部首。
///
/// 多音字給明顯的標記——這是這個 App 最有價值、也最容易誤導人的地方。
struct CharCardView: View {
    let entry: CharEntry
    /// 這個字在剛才查的那串詞裡讀什麼（注音）。空的代表不是詞查詢。
    var activeZhuyin: Set<String> = []

    /// 主讀音預設展開，其他讀音摺疊但看得見。
    @State private var expanded: Set<Reading.ID> = []

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .center, spacing: 12) {
                Text(entry.ch)
                    .font(.system(size: 46))

                if entry.isPolyphonic {
                    Text("多音字 \(entry.readings.count) 讀")
                        .font(.caption2)
                        .fontWeight(.medium)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color.orange.opacity(0.18), in: .capsule)
                        .foregroundStyle(.orange)
                }

                Spacer(minLength: 0)
            }

            VStack(alignment: .leading, spacing: 10) {
                ForEach(entry.readings) { reading in
                    ReadingRowView(
                        reading: reading,
                        isActive: activeZhuyin.contains(reading.zhuyin),
                        isExpanded: isExpanded(reading)
                    ) {
                        toggle(reading)
                    }
                }
            }

            if let footnote {
                Text(footnote)
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color(.secondarySystemGroupedBackground), in: .rect(cornerRadius: 14))
    }

    /// 主讀音、以及剛才查的詞用到的讀音，一律先展開；其餘的等使用者點。
    private func isExpanded(_ reading: Reading) -> Bool {
        reading.isPrimary
            || activeZhuyin.contains(reading.zhuyin)
            || expanded.contains(reading.id)
    }

    private func toggle(_ reading: Reading) {
        if expanded.contains(reading.id) {
            expanded.remove(reading.id)
        } else {
            expanded.insert(reading.id)
        }
    }

    private var footnote: String? {
        var parts: [String] = []
        if let strokes = entry.strokes { parts.append("\(strokes) 畫") }
        if let radical = entry.radical { parts.append("部首 \(radical)") }
        if let variant = entry.variant { parts.append("另作 \(variant)") }
        return parts.isEmpty ? nil : parts.joined(separator: " · ")
    }
}
