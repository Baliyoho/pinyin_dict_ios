import Foundation
import SQLite3

/// `sqlite3` C API 的薄封裝。
///
/// 用系統內建的 libsqlite3（`import SQLite3` 會透過 SDK 的 module map 自動連結），
/// 不引入任何第三方套件——免費 Apple ID 簽名時，少一個變數就少一個出錯的地方。
///
/// DB 唯讀，直接從 app bundle 開啟，不複製到 Documents。
final class Database {
    enum Failure: Error, LocalizedError {
        case cannotOpen(path: String, message: String)
        case cannotPrepare(sql: String, message: String)

        var errorDescription: String? {
            switch self {
            case let .cannotOpen(path, message):
                return "打不開字典檔 \(path)：\(message)"
            case let .cannotPrepare(sql, message):
                return "SQL 準備失敗：\(message)\n\(sql)"
            }
        }
    }

    /// sqlite 需要知道綁進去的字串能不能沿用。`-1` 是 `SQLITE_TRANSIENT`，
    /// 代表「請自己複製一份」——Swift 的 String 只在呼叫期間保證有效，所以一定
    /// 要用這個，不能用 STATIC。
    private static let transient = unsafeBitCast(
        -1, to: sqlite3_destructor_type.self
    )

    private var handle: OpaquePointer?

    init(path: String) throws {
        var opened: OpaquePointer?
        let flags = SQLITE_OPEN_READONLY | SQLITE_OPEN_NOMUTEX
        let status = sqlite3_open_v2(path, &opened, flags, nil)
        guard status == SQLITE_OK, let opened else {
            let message = opened.map { String(cString: sqlite3_errmsg($0)) }
                ?? "sqlite3_open_v2 回傳 \(status)"
            sqlite3_close(opened)
            throw Failure.cannotOpen(path: path, message: message)
        }
        handle = opened
    }

    deinit {
        sqlite3_close(handle)
    }

    /// 一列查詢結果。只在 `query` 的 transform 區塊內有效。
    struct Row {
        fileprivate let statement: OpaquePointer

        func string(_ index: Int32) -> String {
            guard let text = sqlite3_column_text(statement, index) else { return "" }
            return String(cString: text)
        }

        /// 空字串一律當成「沒有值」——詞庫在繁簡相同時會把 simp 存成空字串。
        func optionalString(_ index: Int32) -> String? {
            let value = string(index)
            return value.isEmpty ? nil : value
        }

        func int(_ index: Int32) -> Int {
            Int(sqlite3_column_int64(statement, index))
        }

        func optionalInt(_ index: Int32) -> Int? {
            sqlite3_column_type(statement, index) == SQLITE_NULL ? nil : int(index)
        }
    }

    /// 跑一句 SQL，把每一列交給 `transform`。參數一律以字串綁定。
    func query<T>(
        _ sql: String,
        _ parameters: [String] = [],
        transform: (Row) -> T
    ) throws -> [T] {
        var statement: OpaquePointer?
        guard sqlite3_prepare_v2(handle, sql, -1, &statement, nil) == SQLITE_OK,
              let statement
        else {
            let message = handle.map { String(cString: sqlite3_errmsg($0)) } ?? "unknown"
            sqlite3_finalize(statement)
            throw Failure.cannotPrepare(sql: sql, message: message)
        }
        defer { sqlite3_finalize(statement) }

        for (offset, parameter) in parameters.enumerated() {
            sqlite3_bind_text(
                statement, Int32(offset + 1), parameter, -1, Self.transient
            )
        }

        var rows: [T] = []
        while sqlite3_step(statement) == SQLITE_ROW {
            rows.append(transform(Row(statement: statement)))
        }
        return rows
    }
}
