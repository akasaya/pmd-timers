# Tasks: 休憩後の作業タイマー自動スタート設定

**Input**: Design documents from `/specs/009-auto-resume-work/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: テストは仕様書で明示的に要求されていないため省略（既存エンジンロジックのテストは別途）

**Organization**: 変更対象は `src/ui/settings_dialog.py` 1ファイルのみ。フェーズ構成はシンプルに保つ。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2）
- ファイルパスを含める

---

## Phase 1: 準備確認（Setup）

**Purpose**: 実装前に既存コードの状態を確認し、変更箇所を特定する

- [x] T001 `src/ui/settings_dialog.py` を読んで `_build_ui()`・`_apply()`・`_reset()` の既存パターンを確認し、チェックボックス追加位置を特定する
- [x] T002 `src/engine/session.py` で `BehaviorSettings.auto_start_next_session: bool = False` が存在することを確認する

**Checkpoint**: 変更対象のファイルと3箇所の追加位置が確認できた状態

---

## Phase 2: 基盤確認（Foundational）

**Purpose**: バックエンドロジックが正常に機能していることを確認する

**⚠️ 確認のみ・コード変更なし**

- [x] T003 `src/engine/timer_engine.py:123` で `auto_start_next_session` フラグの分岐ロジックが存在することを確認する
- [x] T004 `src/main.py:71` で `engine.update_settings(new_settings)` が設定ダイアログの OK 後に呼ばれていることを確認する（US2の即時反映はこれで担保済み）

**Checkpoint**: バックエンド実装確認完了 → UI追加のみで機能が完成することが確認できた

---

## Phase 3: User Story 1 - 設定画面でオート再開を有効にする (Priority: P1) 🎯 MVP

**Goal**: 設定ダイアログに「休憩終了後に次の作業を自動スタート」チェックボックスを追加し、保存・読み込みを配線する

**Independent Test**: 設定ダイアログを開き、チェックをオンにして OK → アプリを再起動 → 設定ダイアログを開いてチェックがオンのままか確認。また休憩タイマーを短くして自動スタートが発火するか確認。

### Implementation for User Story 1

- [x] T005 [US1] `src/ui/settings_dialog.py` の `_build_ui()` 内「ウィジェット設定」グループ（`ui_form`）に `self._auto_start_check = QCheckBox("休憩終了後に次の作業を自動スタート")` を追加し、`self._settings.behavior.auto_start_next_session` で初期化する（`_notify_desktop_check` の addRow の直前に配置）
- [x] T006 [US1] `src/ui/settings_dialog.py` の `_apply()` に `self._settings.behavior.auto_start_next_session = self._auto_start_check.isChecked()` を追加する（BGM設定の書き込み行の後、`self.accept()` の前）
- [x] T007 [US1] `src/ui/settings_dialog.py` の `_reset()` に `self._auto_start_check.setChecked(defaults.behavior.auto_start_next_session)` を追加する（BGM reset ブロックの後）

**Checkpoint**: T005〜T007 完了後、設定ダイアログでチェックのオン/オフが保存・読み込みできる

---

## Phase 4: User Story 2 - 設定変更の即時反映 (Priority: P2)

**Goal**: 実行中のセッションがある状態でオート再開設定を変更したとき、次のフェーズ遷移から反映されることを確認する

**Independent Test**: 作業タイマー実行中に設定ダイアログでオート再開をオンにして OK → 休憩タイマーが終わったとき自動で作業タイマーが始まる。

### Implementation for User Story 2

- [x] T008 [US2] `src/main.py:66-74` の `open_settings()` を読んで `engine.update_settings(new_settings)` が既に呼ばれていること（即時反映が自動で実現されていること）を確認し、追加実装が不要であることを文書化する（コード変更なし）

**Checkpoint**: US2 は既存の `engine.update_settings()` の仕組みで自動的に満たされることが確認できた

---

## Phase 5: Polish & 動作確認

**Purpose**: 実装の整合性確認と手動検証

- [x] T009 [P] `ruff check src/ui/settings_dialog.py` を実行してリントエラーがないことを確認する（ruff未インストールのため Python 構文チェックで代替、Syntax OK）
- [ ] T010 手動スモークテスト: アプリを起動 → 設定ダイアログを開く → 「休憩終了後に次の作業を自動スタート」チェックボックスが表示される → オンにして OK → 設定ファイルに `auto_start_next_session: true` が保存されている → アプリ再起動後も設定が保持されている
- [ ] T011 手動スモークテスト（自動スタートON）: 作業時間を1分に短縮して設定 → オート再開をオン → タイマー開始 → 作業タイマー終了後に休憩タイマーが始まり → 休憩タイマー終了後に自動で作業タイマーが始まる
- [ ] T012 手動スモークテスト（自動スタートOFF）: オート再開をオフに戻す → 休憩タイマー終了後はIDLE状態で停止する

---

## Dependencies & Execution Order

### フェーズ依存関係

- **Phase 1（準備確認）**: 依存なし、即開始可能
- **Phase 2（基盤確認）**: Phase 1 完了後（並列実行も可）
- **Phase 3（US1 実装）**: Phase 1・2 完了後 — T005→T006→T007 の順番で実行（同一ファイルのため順次）
- **Phase 4（US2 確認）**: Phase 3 完了後（確認のみ）
- **Phase 5（Polish）**: Phase 3・4 完了後

### 並列実行の機会

- T001・T002 は並列実行可（異なるファイルの読み取り）
- T003・T004 は並列実行可
- T009 は他の T010〜T012 と並列実行可
- T005・T006・T007 は同一ファイルへの変更のため順次実行

---

## Parallel Example: User Story 1

```bash
# Phase 1 - 並列確認:
Task: "T001 settings_dialog.py の既存パターンを確認"
Task: "T002 BehaviorSettings の存在確認"

# Phase 3 - 順次実装（同一ファイル）:
T005 → T006 → T007
```

---

## Implementation Strategy

### MVP First (User Story 1 のみ)

1. Phase 1・2（確認）を完了
2. Phase 3 の T005→T006→T007 を実装（3行追加）
3. **STOP and VALIDATE**: 設定ダイアログでチェックボックスが動作することを確認
4. Phase 4・5 でリント・手動テスト

### 実装量の見積もり

- 変更ファイル: `src/ui/settings_dialog.py` のみ
- 追加行数: 約5〜6行（`_build_ui()` 2行、`_apply()` 1行、`_reset()` 1行）
- 新規ファイル: なし
- バックエンド変更: なし

---

## Notes

- [P] タスク = 異なるファイル、依存なし
- [Story] ラベルでユーザーストーリーとのトレーサビリティを確保
- T005〜T007 は同一ファイル（`settings_dialog.py`）への変更なので並列不可
- US2 は既存コードで自動的に満たされるため追加実装不要
- `_reset()` でのリセット値は `defaults.behavior.auto_start_next_session`（`AppSettings()` のデフォルト = `False`）
