import SwiftUI

@main
struct PinyinLookupApp: App {
    var body: some Scene {
        WindowGroup {
            RootView()
        }
    }
}

/// 開字典檔。開不起來就把原因講清楚——空白畫面最難查。
struct RootView: View {
    @State private var store: Result<DictionaryStore, Error> = Result {
        try DictionaryStore()
    }

    var body: some View {
        switch store {
        case let .success(store):
            SearchView(store: store)
        case let .failure(error):
            ContentUnavailableView {
                Label("字典檔載入失敗", systemImage: "exclamationmark.triangle")
            } description: {
                Text(error.localizedDescription)
                    .font(.footnote)
                    .monospaced()
            }
        }
    }
}
