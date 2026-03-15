# Data Model: コンパクトタイマーウィジェットと統計ダッシュボード

**Feature Branch**: `005-compact-stats-dashboard`
**Date**: 2026-03-15
**Phase**: Phase 1 - Design

> **注記**: 本フィーチャーは 004-desktop-pomodoro-timer のデータモデルを継承・拡張する。
> 共通エンティティ（TimerSession, AppSettings の基本部分）は 004/data-model.md を参照。

---

## 新規エンティティ / 拡張エンティティ

### 1. WidgetDisplaySettings（ウィジェット表示設定）

`AppSettings.ui` サブグループに追加するフィールド群。

| フィールド | 型 | デフォルト | 範囲 | 説明 |
|-----------|-----|----------|------|------|
| `window_opacity` | float | 0.95 | 0.2〜1.0 | ウィジェットの不透明度 |
| `hover_reveal_buttons` | bool | true | - | ホバー時のみ操作ボタンを表示するか |
| `animation_duration_ms` | int | 150 | 50〜500 | ホバーアニメーション時間（ms） |
| `window_x` | int \| None | null | - | X座標（null = 右上デフォルト） |
| `window_y` | int \| None | null | - | Y座標（null = 右上デフォルト） |
| `window_width` | int | 200 | 120〜400 | ウィジェット幅（px） |
| `window_height` | int | 80 | 60〜200 | ウィジェット高さ（px） |

---

### 2. DailyRecord（日次統計記録）

日付ごとのJSONファイル（`history/YYYY-MM-DD.json`）に永続化される集計データ。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | str (ISO8601 date) | 記録対象日 |
| `work_sessions_completed` | int | 完了した作業セッション数 |
| `work_sessions_interrupted` | int | 中断した作業セッション数 |
| `short_breaks_completed` | int | 完了した短休憩回数 |
| `long_breaks_completed` | int | 完了した長休憩回数 |
| `total_work_sec` | int | 累計作業時間（秒） |
| `total_break_sec` | int | 累計休憩時間（秒） |
| `sessions` | list[TimerSession] | その日の全セッション詳細 |

**永続化フォーマット例 (`history/2026-03-15.json`):**
```json
{
  "date": "2026-03-15",
  "work_sessions_completed": 4,
  "work_sessions_interrupted": 1,
  "short_breaks_completed": 3,
  "long_breaks_completed": 1,
  "total_work_sec": 5700,
  "total_break_sec": 900,
  "sessions": [
    {
      "id": "abc123",
      "type": "WORK",
      "start_time": "2026-03-15T09:00:00",
      "end_time": "2026-03-15T09:25:00",
      "status": "COMPLETED",
      "session_index": 1,
      "cycle_number": 1
    }
  ]
}
```

---

### 3. DashboardViewModel（ダッシュボード表示用集計）

永続データから計算するビューモデル。ファイルに保存しない（オンデマンド計算）。

#### 3-1. TodayStats（当日サマリー）

| フィールド | 型 | 計算元 |
|-----------|-----|-------|
| `date` | str | 当日の DailyRecord.date |
| `completed_count` | int | DailyRecord.work_sessions_completed |
| `interrupted_count` | int | DailyRecord.work_sessions_interrupted |
| `total_work_time_str` | str | total_work_sec を "H時間M分" 形式に変換 |
| `short_breaks` | int | DailyRecord.short_breaks_completed |
| `long_breaks` | int | DailyRecord.long_breaks_completed |
| `current_streak_days` | int | 後述のストリーク計算 |

#### 3-2. PeriodStats（期間集計）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `period` | Enum | `TODAY` / `THIS_WEEK` / `THIS_MONTH` |
| `start_date` | str | 集計期間の開始日 |
| `end_date` | str | 集計期間の終了日 |
| `daily_counts` | list[DailyCount] | 日別完了セッション数のリスト（グラフ用） |
| `total_completed` | int | 期間合計完了セッション数 |
| `total_work_sec` | int | 期間合計作業時間（秒） |
| `best_day_date` | str \| None | 最多セッション数の日付 |
| `best_day_count` | int | 最多セッション数 |

#### 3-3. DailyCount（グラフ用日別カウント）

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | str | 日付 (`YYYY-MM-DD`) |
| `label` | str | グラフ軸ラベル（"3/15" 形式） |
| `count` | int | その日の完了作業セッション数 |

---

## ストリーク計算アルゴリズム

```
streak = 0
today = 今日の日付
for day in [today, today-1, today-2, ...] （最大90日):
    record = load_daily_record(day)
    if record が存在しない or record.work_sessions_completed == 0:
        break
    streak += 1
return streak
```

---

## バリデーションルール

| ルール | 詳細 |
|-------|------|
| `window_opacity` | 0.2〜1.0（0.2未満は視認性が低すぎる） |
| `window_width` | 120〜400（120px未満だと残り時間が切れる） |
| `window_height` | 60〜200 |
| DailyRecord の保持期間 | 90日（古いファイルは `HistoryService.cleanup()` で削除） |
| セッション詳細のタイムスタンプ | start_time <= end_time |
