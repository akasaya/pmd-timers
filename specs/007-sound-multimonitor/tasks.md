# Tasks: 通知音改善とマルチモニター対応

**Input**: Design documents from `/specs/007-sound-multimonitor/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, contracts/ ✓

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 `assets/sounds/` ディレクトリが存在し `notification.wav`（CC0）が配置済みであることを確認する
- [X] T002 `python -m pytest tests/ -v` を実行し全テストがパスする状態を確認する（29テスト）

---

## Phase 2: Foundational

- [X] T003 `src/engine/session.py` の `NotificationSettings` データクラスに `custom_sound_path: str = ""` フィールドを追加し、`to_dict` / `from_dict` のシリアライズに対応させる（空文字はデフォルト音を意味する）

---

## Phase 3: User Story 1 - デフォルト通知音の再生 (Priority: P1) 🎯 MVP

**Goal**: セッション終了時に `assets/sounds/notification.wav` を再生する。5秒超で自動停止。

**Independent Test**: タイマーを短縮して完了させ、音が鳴ることを確認できる。

- [X] T004 [US1] `src/services/sound_service.py` を新規作成する：`QSoundEffect` + `QTimer`（5秒タイムアウト）を使い、`play()` メソッドで `sound_enabled` を確認してから再生する。`custom_sound_path` が有効なら優先、無効なら `assets/sounds/notification.wav` にフォールバックする
- [X] T005 [US1] `src/services/notification_service.py` を修正する：`NotificationService.__init__` に `sound_service: SoundService | None = None` 引数を追加し、`notify_phase_change` から `self._sound_service.play()` を呼び出す
- [X] T006 [US1] `src/main.py` を修正する：`SoundService` を初期化し、`NotificationService` に渡す

**Checkpoint**: タイマーを1分に設定して完了させ、音が鳴ることを確認

---

## Phase 4: User Story 2 - カスタム通知音の設定 (Priority: P2)

**Goal**: 設定ダイアログからWAVファイルを選択・プレビューし、次回以降そのファイルが使われる。

**Independent Test**: 設定でカスタムWAVを選択・保存し、セッション終了時にそのファイルが再生される。

- [X] T007 [US2] `src/ui/settings_dialog.py` を修正する：通知グループに「通知音ファイル」行を追加（現在のファイル名ラベル + 「参照」ボタン + 「プレビュー」ボタン）。WAVが5秒超の場合に `⚠ 5秒でカットされます` ラベルを表示する。プレビュー再生には `SoundService` を一時使用する
- [X] T008 [US2] `src/ui/settings_dialog.py` の `_apply()` に `custom_sound_path` の保存を追加し、`_reset()` でも空文字にリセットされるようにする
- [X] T009 [US2] `src/main.py` を修正する：設定保存後に `sound_service.reload()` を呼び出して音声ファイルを再ロードする（`SoundService` に `reload()` メソッドを追加）

**Checkpoint**: 設定でカスタムWAVを選択→プレビュー→保存し、セッション終了で正しい音が鳴ることを確認

---

## Phase 5: User Story 3 - マルチモニター対応 (Priority: P2)

**Goal**: `_clamp_to_screen` を全スクリーン対応に変更し、どのディスプレイにもドラッグできる。

**Independent Test**: サブディスプレイにドラッグ移動し、再起動後も位置が復元される（マルチモニター環境のみ）。

- [X] T010 [P] [US3] `src/ui/timer_widget.py` の `_clamp_to_screen` を修正する：`QApplication.primaryScreen()` の代わりに `QApplication.screens()` で全スクリーンの `united(availableGeometry())` を仮想矩形として使用する
- [X] T011 [P] [US3] `src/ui/timer_widget.py` の `_restore_position` を修正する：保存座標が全ディスプレイ仮想矩形外の場合、`primaryScreen` の右上にリセットする（画面外への消失を防ぐ）

**Checkpoint**: シングルモニターで既存動作が変わらないことを確認（マルチモニター実機確認はquickstart.md参照）

---

## Phase 6: Polish & 動作確認

- [X] T012 `python -m pytest tests/ -v` を実行し全テストがパスすることを確認する
- [X] T013 `src/services/sound_service.py` の単体テスト `tests/unit/test_sound_service.py` を作成する：`sound_enabled=False` で再生しないこと、`custom_sound_path` が無効のときデフォルト音にフォールバックすることを確認する

---

## Dependencies & Execution Order

```
T001 → T002 → T003（Foundational）
         ↓
T004（SoundService新規）→ T005（NotificationService修正）→ T006（main.py）
         ↓（並行可）
T007 → T008 → T009（設定UI）
         ↓（並行可）
T010, T011（マルチモニター、別ファイル）
         ↓
T012 → T013
```

- T010・T011 は `timer_widget.py` 内なので逐次
- T004〜T006 と T010〜T011 は別ファイルのため並行可能

---

## Implementation Strategy

### MVP (P1のみ: デフォルト音)

T001 → T002 → T003 → T004 → T005 → T006 → T012

### Full (全機能)

T001 → T002 → T003 → T004〜T006（音声基盤）→ T007〜T009（カスタム音UI）→ T010〜T011（マルチモニター）→ T012 → T013
