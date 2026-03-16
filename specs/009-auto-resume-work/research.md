# Research: 休憩後の作業タイマー自動スタート設定

**Branch**: `009-auto-resume-work`
**Date**: 2026-03-16

## 調査サマリー

本フィーチャーは純粋なUIフィーチャーであり、バックエンドのすべてのロジックがすでに実装済みであることが確認された。

---

## 発見事項

### 1. バックエンドの実装状況

**Decision**: 追加の実装は不要。バックエンドはすでに完成している。

**Rationale**:
- `src/engine/session.py:107` — `BehaviorSettings.auto_start_next_session: bool = False`
- `src/engine/session.py:150–239` — `AppSettings.to_dict()` / `from_dict()` で永続化済み
- `src/engine/timer_engine.py:123–128` — 休憩フェーズ完了時に `auto_start_next_session` フラグを参照して分岐するロジックが存在

**Alternatives considered**: N/A（実装済み）

---

### 2. 設定ダイアログのUIパターン

**Decision**: `SettingsDialog` の「ウィジェット設定」グループに `QCheckBox` として追加する。

**Rationale**:
- 既存の `_hover_check`（ホバー時のみ表示）・`_ontop_check`（常に最前面）と同じ `QCheckBox` パターンを使用
- `_apply()` で `self._settings.behavior.auto_start_next_session = self._auto_start_check.isChecked()` と配線するだけ
- `_reset()` で `False`（デフォルト値）にリセット

**Alternatives considered**:
- 「タイマー設定」グループへの追加: タイマー時間設定と性質が異なるため不採用。動作設定として「ウィジェット設定」グループが適切。
- 独立したグループボックス「動作設定」の新設: 1項目のみのためオーバーエンジニアリング。

---

### 3. 既存テストの確認

**Decision**: 既存の `timer_engine` テストが `auto_start_next_session` をカバーしているか確認が必要。

**Rationale**: エンジン側のロジックはすでに動作しているが、UIダイアログの `_apply()` / `_reset()` に対するユニットテストを追加することで安全性を担保する。

---

## 結論

実装スコープは `src/ui/settings_dialog.py` の1ファイルのみ:

1. `__init__` 内で `self._auto_start_check = QCheckBox(...)` を初期化
2. `_build_ui()` の「ウィジェット設定」フォームに行を追加
3. `_apply()` で値をセット
4. `_reset()` でデフォルト値にリセット

バックエンド変更・設定スキーマ変更・新規ファイル作成は不要。
