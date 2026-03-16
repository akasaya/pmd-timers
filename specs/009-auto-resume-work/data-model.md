# Data Model: 休憩後の作業タイマー自動スタート設定

**Branch**: `009-auto-resume-work`
**Date**: 2026-03-16

## 既存エンティティ（変更なし）

### BehaviorSettings (`src/engine/session.py:106`)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `auto_start_next_session` | `bool` | `False` | 休憩終了後に作業タイマーを自動スタートするか |

**状態遷移**: このフラグが `True` のとき、`TimerEngine._advance_phase()` は SHORT_BREAK/LONG_BREAK 完了後に自動で `_begin_work_session()` を呼び出す。`False` のときは `Phase.IDLE` に遷移してユーザー操作待ちになる。

### AppSettings (`src/engine/session.py:149`)

`BehaviorSettings` を `behavior` フィールドとして含む。`to_dict()` / `from_dict()` により JSON 設定ファイルへの永続化と読み込みが実装済み。

## スキーマ変更

**なし** — 既存の `BehaviorSettings.auto_start_next_session` フィールドとその永続化処理はすでに完成している。

## UIバインディング（新規追加対象）

| UIウィジェット | 対応する設定フィールド | 操作 |
|---|---|---|
| `_auto_start_check: QCheckBox` | `settings.behavior.auto_start_next_session` | 読み取り: `setChecked(...)` / 書き込み: `isChecked()` |
