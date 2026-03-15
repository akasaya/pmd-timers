# Data Model: デスクトップ常駐ポモドーロタイマー

**Feature Branch**: `004-desktop-pomodoro-timer`
**Date**: 2026-03-15
**Phase**: Phase 1 - Design

---

## エンティティ一覧

### 1. TimerSession（タイマーセッション）

1回のポモドーロセッション（作業または休憩）を表す。

| フィールド | 型 | 説明 | バリデーション |
|-----------|-----|------|--------------|
| `id` | str (UUID4) | セッション識別子 | 自動生成 |
| `type` | Enum | `WORK` / `SHORT_BREAK` / `LONG_BREAK` | 必須 |
| `date` | str (ISO8601 date) | セッションが属する日付 | `YYYY-MM-DD` |
| `start_time` | str (ISO8601) | 開始時刻 | 必須 |
| `end_time` | str (ISO8601) \| None | 終了時刻（未完了時は null） | - |
| `scheduled_duration_sec` | int | 予定秒数 | 1〜5400（90分） |
| `actual_duration_sec` | int | 実際の経過秒数 | 0〜scheduled_duration_sec |
| `status` | Enum | `COMPLETED` / `INTERRUPTED` / `SKIPPED` | 必須 |
| `session_index` | int | サイクル内の作業セッション番号（1始まり） | 1〜sessions_before_long_break |
| `cycle_number` | int | その日の何サイクル目か | 1以上 |

**状態遷移:**
```
(開始) → COMPLETED  （自然に時間が来た）
       → INTERRUPTED （ユーザーが手動中断）
       → SKIPPED     （ユーザーがスキップ操作）
```

---

### 2. TimerState（タイマー実行状態）

アプリのメモリ上に保持するリアルタイム状態。永続化はしない（再起動時に IDLE から再スタート）。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `phase` | Enum | `IDLE` / `WORKING` / `SHORT_BREAK` / `LONG_BREAK` / `PAUSED` |
| `pre_pause_phase` | Enum \| None | PAUSED 前のフェーズ（再開時に使用） |
| `remaining_sec` | int | 残り秒数 |
| `current_session_index` | int | 現在の作業セッション番号（1〜N） |
| `daily_completed_count` | int | 当日完了した作業セッション数 |
| `is_sleep_paused` | bool | スリープによる自動一時停止かどうか |
| `sleep_start_time` | datetime \| None | スリープ開始時刻 |

**状態遷移（フル）:**
```
IDLE      → WORKING
WORKING   → PAUSED, SHORT_BREAK, LONG_BREAK, IDLE（リセット）
SHORT_BREAK → PAUSED, WORKING, IDLE（リセット）
LONG_BREAK  → PAUSED, WORKING, IDLE（リセット）
PAUSED    → pre_pause_phase（再開）, IDLE（中断）
```

---

### 3. AppSettings（アプリ設定）

ユーザーが設定した永続化データ。`settings.json` に保存。

**timers サブグループ:**

| フィールド | 型 | デフォルト | 範囲 |
|-----------|-----|----------|------|
| `work_duration_min` | int | 25 | 5〜90 |
| `short_break_min` | int | 5 | 1〜30 |
| `long_break_min` | int | 15 | 5〜60 |
| `sessions_before_long_break` | int | 4 | 2〜10 |

**behavior サブグループ:**

| フィールド | 型 | デフォルト |
|-----------|-----|----------|
| `auto_start_next_session` | bool | false |

**notifications サブグループ:**

| フィールド | 型 | デフォルト |
|-----------|-----|----------|
| `sound_enabled` | bool | true |
| `desktop_notification_enabled` | bool | true |

**ui サブグループ:**

| フィールド | 型 | デフォルト |
|-----------|-----|----------|
| `always_on_top` | bool | true |
| `window_opacity` | float | 0.95 | （0.5〜1.0）|
| `window_x` | int \| None | null（右上デフォルト） |
| `window_y` | int \| None | null（右上デフォルト） |
| `window_width` | int | 200 |
| `window_height` | int | 120 |

---

### 4. DailyRecord（日次記録）

当日の集計データ。セッション完了のたびに更新し `history.json` に保存。

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `date` | str (ISO8601 date) | 記録対象日 |
| `work_sessions_completed` | int | 完了した作業セッション数 |
| `work_sessions_interrupted` | int | 中断した作業セッション数 |
| `total_work_time_sec` | int | 累計作業秒数 |
| `total_break_time_sec` | int | 累計休憩秒数 |
| `long_breaks_taken` | int | 長休憩の回数 |

---

## ファイル保存構造

```
%APPDATA%\pmd-timers\       (Windows)
~/.config/pmd-timers/        (その他)
├── settings.json             # AppSettings
└── history/
    └── 2026-03-15.json       # DailyRecord + sessions[]（日付ごと）
```

---

## バリデーションルール

| ルール | 詳細 |
|-------|------|
| 作業時間の最小値 | 5分（これ以下は Pomodoro の意味をなさない） |
| 休憩時間の最小値 | 1分 |
| `sessions_before_long_break` | 2〜10（1は長休憩がなくなるため除外） |
| `window_opacity` | 0.5〜1.0（0.5未満は操作できなくなる） |
| セッション記録の保持期間 | 90日間（古いファイルは自動削除） |
