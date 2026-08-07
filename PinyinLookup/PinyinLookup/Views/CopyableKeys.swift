import SwiftUI
import UIKit

/// 鍵入序列 + 點一下複製。
///
/// 這是整個 App 唯一要記住的互動：看到那串字母，點它，貼到別的地方去。
/// 字母之間拉開字距，是為了讓人一眼看出「這是要一個一個敲的鍵」，而不是一個詞。
struct CopyableKeys: View {
    let keys: String
    /// 整串詞的鍵入序列用大字；單一讀音用小字。
    var prominent: Bool = false

    @State private var justCopied = false

    var body: some View {
        Button(action: copy) {
            HStack(spacing: 10) {
                Text(keys)
                    .font(.system(
                        prominent ? .largeTitle : .body,
                        design: .monospaced,
                        weight: prominent ? .semibold : .medium
                    ))
                    .tracking(prominent ? 6 : 2)
                    .foregroundStyle(.primary)
                    .lineLimit(1)
                    .minimumScaleFactor(0.5)

                Image(systemName: justCopied ? "checkmark.circle.fill" : "doc.on.doc")
                    .font(prominent ? .body : .caption)
                    .foregroundStyle(justCopied ? Color.green : Color.secondary)
                    .accessibilityHidden(true)
            }
            .contentShape(.rect)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(justCopied ? "已複製" : "複製鍵入序列 \(spelledOut)")
    }

    /// VoiceOver 要逐字母唸，不然 "lv" 會被唸成一個字。
    private var spelledOut: String {
        keys.map(String.init).joined(separator: " ")
    }

    /// 標成 MainActor，裡面的 Task 才會留在主執行緒上——它要改 @State。
    @MainActor
    private func copy() {
        UIPasteboard.general.string = keys
        UIImpactFeedbackGenerator(style: .light).impactOccurred()
        justCopied = true
        Task {
            try? await Task.sleep(for: .seconds(1.2))
            justCopied = false
        }
    }
}
