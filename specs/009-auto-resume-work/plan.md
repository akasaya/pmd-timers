# Implementation Plan: 休憩後の作業タイマー自動スタート設定

**Branch**: `009-auto-resume-work` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/009-auto-resume-work/spec.md`

## Summary

設定ダイアログに「休憩終了後に次の作業タイマーを自動スタートする」チェックボックスを追加する。
バックエンドの `BehaviorSettings.auto_start_next_session` フラグとその永続化、エンジンの分岐ロジックはすでに実装済みのため、UIへの配線のみが実装対象。

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: PyQt6 6.7+（QCheckBox, QFormLayout）
**Storage**: JSON設定ファイル（既存スキーマ変更なし）
**Testing**: pytest
**Target Platform**: Windows/Linux デスクトップ（WSL2含む）
**Project Type**: Desktop app
**Performance Goals**: N/A（UIトグル1つの追加）
**Constraints**: 既存のUIパターン（`QCheckBox` + `QFormLayout`）に従うこと
**Scale/Scope**: 1ファイル変更（`settings_dialog.py`）

## Constitution Check

Constitutionファイルがテンプレートのみのため、プロジェクト固有の制約なし。

既存コードパターンとの整合性チェック:
- [x] 既存 `QCheckBox` パターンを踏襲（`_hover_check`, `_ontop_check` と同様）
- [x] `_apply()` / `_reset()` の既存パターンを踏襲
- [x] 新規ファイル・新規クラス・新規サービスを作成しない（YAGNI）
- [x] バックエンドに手を加えない

## Project Structure

### Documentation (this feature)

```text
specs/009-auto-resume-work/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── ui/
    └── settings_dialog.py   # 唯一の変更対象

tests/
└── test_settings_dialog.py  # UIバインディングのユニットテスト追加（既存 or 新規）
```

**Structure Decision**: 単一プロジェクト構成。変更は `settings_dialog.py` 1ファイルのみ。

## Implementation Design

### 変更箇所: `src/ui/settings_dialog.py`

#### 1. `_build_ui()` — ウィジェット設定グループへの追加

`_notify_desktop_check` の行の直前（`ui_form.addRow(self._notify_desktop_check)` の前）に追加:

```python
self._auto_start_check = QCheckBox("休憩終了後に次の作業を自動スタート")
self._auto_start_check.setChecked(self._settings.behavior.auto_start_next_session)
ui_form.addRow(self._auto_start_check)
```

#### 2. `_apply()` — 設定への書き込み

```python
self._settings.behavior.auto_start_next_session = self._auto_start_check.isChecked()
```

#### 3. `_reset()` — デフォルト値へのリセット

```python
self._auto_start_check.setChecked(defaults.behavior.auto_start_next_session)  # False
```

### 変更箇所の配置方針

- **グループ**: 「ウィジェット設定」（`ui_group`）に含める
  - 「タイマー設定」はタイマー時間に特化しているため不採用
  - 「動作設定」の独立グループ新設は1項目のためオーバーエンジニアリング
- **位置**: `_notify_desktop_check`（デスクトップ通知）の直前
  - 通知系の設定とまとめて動作設定として認識しやすい

## Testing Strategy

`_apply()` / `_reset()` のバインディングを確認するユニットテスト:

1. チェックをオンにして `_apply()` → `settings.behavior.auto_start_next_session == True`
2. チェックをオフにして `_apply()` → `settings.behavior.auto_start_next_session == False`
3. `_reset()` → `_auto_start_check.isChecked() == False`（デフォルト）
4. ダイアログ初期化時、設定が `True` の場合チェックが入っている
