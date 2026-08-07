import SwiftUI
import UIKit

/// 主畫面。單一畫面、開啟即聚焦、逐字即時顯示結果、沒有搜尋按鈕。
struct SearchView: View {
    @State private var model: SearchViewModel
    @FocusState private var isInputFocused: Bool

    private let store: DictionaryStore

    init(store: DictionaryStore) {
        self.store = store
        _model = State(initialValue: SearchViewModel(store: store))
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                inputField
                Divider()
                results
            }
            .background(Color(.systemGroupedBackground))
            .navigationTitle("查拼音")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItemGroup(placement: .topBarTrailing) {
                    NavigationLink {
                        ZhuyinPinyinTableView()
                    } label: {
                        Label("對照表", systemImage: "tablecells")
                    }
                    NavigationLink {
                        AboutView(store: store)
                    } label: {
                        Label("關於", systemImage: "info.circle")
                    }
                }
            }
            .onAppear { isInputFocused = true }
            .onChange(of: model.input) { _, _ in model.refresh() }
        }
    }

    private var inputField: some View {
        HStack(spacing: 10) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(.secondary)

            // 用系統注音鍵盤直接打字，所以不做任何自動修正或首字母大寫
            TextField("漢字、注音或拼音", text: $model.input)
                .font(.title3)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .submitLabel(.done)
                .focused($isInputFocused)

            if !model.input.isEmpty {
                Button {
                    model.clear()
                    isInputFocused = true
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(.tertiary)
                }
                .buttonStyle(.plain)
                .accessibilityLabel("清除")
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color(.systemBackground))
    }

    @ViewBuilder
    private var results: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 12) {
                if let header = model.result.header {
                    PhraseHeaderView(header: header)
                }
                if let notice = model.result.notice {
                    Text(notice)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 4)
                }
                ForEach(model.result.chars) { entry in
                    CharCardView(
                        entry: entry,
                        activeZhuyin: model.result.phraseReadings[entry.ch] ?? []
                    )
                }
                if model.result.isEmpty && model.result.notice == nil {
                    emptyState
                }
            }
            .padding(16)
        }
        .scrollDismissesKeyboard(.interactively)
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("一般字典告訴你「綠 = lǜ」，但拼音輸入法要敲的是 **lv**。這個 App 補的就是這段落差。")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            VStack(alignment: .leading, spacing: 8) {
                hint("綠色", "打漢字 — 查整串怎麼敲")
                hint("ㄌㄩˋ", "打注音 — 列出這個讀音的字")
                hint("lv", "打拼音 — 反查敲這串的字")
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color(.secondarySystemGroupedBackground), in: .rect(cornerRadius: 14))
        .padding(.top, 40)
    }

    private func hint(_ example: String, _ description: String) -> some View {
        Button {
            model.input = example
        } label: {
            HStack(spacing: 10) {
                Text(example)
                    .font(.body.weight(.medium))
                    .frame(width: 64, alignment: .leading)
                Text(description)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                Spacer(minLength: 0)
            }
            .contentShape(.rect)
        }
        .buttonStyle(.plain)
    }
}
