# UI Contract: ウィジェット表示・ダッシュボードイベント

**Feature Branch**: `005-compact-stats-dashboard`
**Date**: 2026-03-15

004 の `contracts/ui-events.md` を拡張する。

---

## ウィジェット表示イベント（WidgetDisplayManager）

| イベント名 | トリガー | 処理 |
|-----------|---------|------|
| `widget_enter` | マウスがウィジェット領域に入る | 操作ボタンをフェードイン（150ms） |
| `widget_leave` | マウスがウィジェット領域から出る | 操作ボタンをフェードアウト（150ms） |
| `widget_drag_start` | ウィジェット上でマウスボタン押下 | ドラッグ開始座標を記録 |
| `widget_drag_end` | マウスボタンを離す | 新しい位置を `SettingsService` に保存 |
| `opacity_changed` | `opacity` 設定値変更 | `QWidget.setWindowOpacity()` を即座に適用 |

---

## ダッシュボードイベント（DashboardWindow → DashboardViewModel）

| イベント名 | パラメータ | 説明 |
|-----------|-----------|------|
| `dashboard_open` | なし | ダッシュボードを開く（モーダルレス） |
| `dashboard_close` | なし | ダッシュボードを閉じる |
| `period_changed` | `period: PeriodEnum` | 期間フィルター切り替え（TODAY/THIS_WEEK/THIS_MONTH） |
| `date_selected` | `date: str` | 特定日のセッション詳細を表示 |
| `stats_refresh` | なし | タイマーエンジンからの自動更新トリガー |

---

## タイマーエンジン → ダッシュボード間イベント

| イベント名 | ペイロード | 説明 |
|-----------|-----------|------|
| `session_recorded` | `session: TimerSession` | セッション完了/中断時に統計更新を要求 |

**接続方式:**
- ダッシュボードが開いている場合: `session_recorded` シグナルを受信して `stats_refresh` を発火
- ダッシュボードが閉じている場合: シグナルは無視（次回開時に最新データを読み込む）

---

## HistoryService API（内部コントラクト）

| 操作 | 入力 | 出力 | 説明 |
|------|------|------|------|
| `record_session(session)` | `TimerSession` | なし | セッションを当日の DailyRecord に追記・保存 |
| `load_daily(date)` | `str` (date) | `DailyRecord \| None` | 指定日の記録を読み込む |
| `load_period(start, end)` | `str, str` | `list[DailyRecord]` | 期間内の全記録を読み込む |
| `get_streak()` | なし | `int` | 現在の連続達成日数を返す |
| `cleanup(keep_days=90)` | `int` | `int` (削除件数) | 古いファイルを削除する |

---

## DashboardViewModel API（内部コントラクト）

| 操作 | 入力 | 出力 |
|------|------|------|
| `get_today_stats()` | なし | `TodayStats` |
| `get_period_stats(period)` | `PeriodEnum` | `PeriodStats` |
| `get_session_detail(date)` | `str` | `list[TimerSession]` |
| `refresh()` | なし | なし（内部キャッシュをクリアして再読み込み） |
