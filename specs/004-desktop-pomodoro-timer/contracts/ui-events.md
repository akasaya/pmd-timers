# UI Contract: タイマーイベントとシグナル

**Feature Branch**: `004-desktop-pomodoro-timer`
**Date**: 2026-03-15

アプリ内のコンポーネント間で交わされるイベント契約を定義します。
実装言語・フレームワークに依存しない論理インターフェースです。

---

## ユーザー操作イベント（UI → TimerEngine）

| イベント名 | パラメータ | 説明 |
|-----------|-----------|------|
| `cmd_start` | なし | タイマー開始（IDLE → WORKING） |
| `cmd_pause` | なし | タイマー一時停止 |
| `cmd_resume` | なし | 一時停止から再開 |
| `cmd_reset` | なし | タイマーリセット（任意の状態 → IDLE） |
| `cmd_skip` | なし | 現在フェーズをスキップして次へ |
| `cmd_open_settings` | なし | 設定画面を開く |
| `cmd_quit` | なし | アプリ終了 |
| `cmd_sleep_resume` | `action: "resume" \| "reset"` | スリープ復帰ダイアログの応答 |

---

## タイマー状態変化イベント（TimerEngine → UI）

| イベント名 | ペイロード | 説明 |
|-----------|-----------|------|
| `timer_tick` | `remaining_sec: int` | 毎秒の残り時間更新 |
| `phase_changed` | `new_phase: PhaseEnum, session_index: int` | フェーズ遷移発生 |
| `session_completed` | `session: TimerSession` | セッション1件完了 |
| `daily_count_updated` | `count: int` | 当日完了セッション数更新 |
| `sleep_detected` | `elapsed_sec: int` | スリープから復帰し判断が必要 |
| `settings_changed` | `new_settings: AppSettings` | 設定が変更された |

---

## 通知契約（TimerEngine → NotificationService）

| トリガー | 通知タイトル | 通知本文 |
|---------|------------|---------|
| WORKING → SHORT_BREAK | 「作業完了！」 | 「5分間休憩しましょう 🎉」 |
| WORKING → LONG_BREAK | 「4セッション達成！」 | 「15分間しっかり休憩を ✨」 |
| SHORT_BREAK → WORKING | 「休憩終了」 | 「次のセッションを始めましょう」 |
| LONG_BREAK → WORKING | 「長休憩終了」 | 「リフレッシュできましたか？」 |

---

## 設定保存契約（SettingsService）

| 操作 | 入力 | 出力 | エラー条件 |
|------|------|------|----------|
| `load_settings()` | なし | `AppSettings` | ファイル不存在時はデフォルト返却 |
| `save_settings(settings)` | `AppSettings` | なし | バリデーション失敗時は例外 |
| `reset_to_defaults()` | なし | `AppSettings` | なし |

---

## ウィンドウ位置契約（WindowManager）

| 操作 | 説明 |
|------|------|
| `get_default_position()` | 画面右上隅から16px内側の座標を返す |
| `clamp_to_screen(x, y)` | 座標がスクリーン外に出ないように補正して返す |
| `save_position(x, y)` | 設定ファイルにウィンドウ位置を保存 |
| `restore_position()` | 保存済み位置を返す（未保存時はデフォルト） |
