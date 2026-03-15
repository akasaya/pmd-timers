# Tasks: フェーズ別BGM再生

**Input**: Design documents from `/specs/008-phase-bgm/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 `python -m pytest tests/ -v` を実行し全テストがパスする状態を確認する

---

## Phase 2: Foundational

**⚠️ CRITICAL**: US1〜US4 の全タスクはこのフェーズの完了を前提とする

- [X] T002 `src/engine/session.py` の `AppSettings` に `BgmSettings` dataclass を追加する：`work_bgm_path: str = ""`、`work_bgm_enabled: bool = False`、`work_bgm_volume: float = 0.5`、`break_bgm_path: str = ""`、`break_bgm_enabled: bool = False`、`break_bgm_volume: float = 0.5`、および `to_dict` / `from_dict` のシリアライズ対応（キー: `"bgm"`）

**Checkpoint**: `AppSettings` に bgm フィールドが追加されシリアライズ確認済み

---

## Phase 3: User Story 1 - 作業中BGMの自動ループ再生 (Priority: P1) 🎯 MVP

**Goal**: 作業フェーズ開始時に BGM が自動ループ再生され、フェーズ終了・一時停止で停止する

**Independent Test**: 作業用 WAV を設定し、タイマー開始→ループ再生確認、終了→停止確認

- [X] T003 [US1] `src/services/bgm_service.py` を新規作成する：`QSoundEffect` を try/except でオプションインポートし、`_effect_work` と `_effect_break` の2インスタンスを持つ `BgmService(QObject)` クラスを実装する。`on_phase_changed(phase: Phase)` で WORKING → work BGM ループ再生（setLoopCount(-1)）、SHORT_BREAK/LONG_BREAK → break BGM ループ再生、PAUSED/IDLE → 全停止。`stop()` と `reload()` メソッドも実装する
- [X] T004 [US1] `src/main.py` を修正する：`BgmService(settings, app)` を初期化し、`engine.phase_changed` シグナルに `lambda phase_val, idx: bgm_svc.on_phase_changed(Phase(phase_val))` を接続する
- [X] T005 [US1] `src/main.py` の `open_settings` 関数を修正する：設定保存後に `bgm_svc.reload()` を呼び出す

**Checkpoint**: 作業用BGMファイルを設定してタイマーを開始するとループ再生され、終了・一時停止で停止することを確認

---

## Phase 4: User Story 2 - 休憩中BGMの自動ループ再生 (Priority: P2)

**Goal**: 休憩フェーズ（SHORT_BREAK / LONG_BREAK）で休憩用BGMがループ再生される

**Independent Test**: 休憩用WAVを設定し、スキップで休憩フェーズへ進めてループ再生確認

- [X] T006 [US2] `src/services/bgm_service.py` の `on_phase_changed` に SHORT_BREAK / LONG_BREAK フェーズのハンドリングが既に含まれていることを確認し、必要であれば休憩用 `_effect_break` の `setSource` / `setLoopCount` / `setVolume` 処理を追加・修正する（T003 で同時実装されている場合は確認のみ）

**Checkpoint**: 休憩フェーズ時に休憩用BGMが再生され、作業フェーズ切り替え時に正しく入れ替わることを確認

---

## Phase 5: User Story 3 - BGM音量の調整 (Priority: P2)

**Goal**: 作業用・休憩用それぞれ独立した音量スライダーで 0〜100% を設定できる

**Independent Test**: 音量スライダーを 0% にして BGM を再生し、音が出ないことを確認

- [X] T007 [US3] `src/services/bgm_service.py` の `_play(effect, path, volume)` ヘルパーに `effect.setVolume(volume)` を追加し、`reload()` 時も `settings.bgm.work_bgm_volume` / `break_bgm_volume` を `setVolume` に反映する

**Checkpoint**: 音量スライダーを変更して保存後、BGM の音量が反映されることを確認

---

## Phase 6: User Story 4 - 設定ダイアログからのBGM管理 (Priority: P2)

**Goal**: 設定ダイアログで作業用・休憩用BGMのファイル選択・音量・有効/無効・プレビューが操作できる

**Independent Test**: 設定ダイアログを開き、ファイル選択→音量調整→プレビュー→保存が一連で動作することを確認

- [X] T008 [US4] `src/ui/settings_dialog.py` に「BGM設定」`QGroupBox` を追加する。作業中BGMセクション：ファイル名ラベル・「参照」ボタン（`_browse_work_bgm`）・プレビューボタン（`_preview_work_bgm`）・音量スライダー（0〜100、`_work_volume_label` 連動）・「作業中BGMを有効にする」チェックボックス。休憩中BGMセクション：同様の構成（`break` 変数名）
- [X] T009 [US4] `src/ui/settings_dialog.py` の `_apply()` に `bgm` 設定の保存を追加する：`work_bgm_path`、`work_bgm_enabled`、`work_bgm_volume`（スライダー値 / 100.0）、`break_*` も同様
- [X] T010 [US4] `src/ui/settings_dialog.py` の `_reset()` に BGM 設定リセットを追加する：全フィールドをデフォルト値（パス空・無効・音量50%）に戻し UI を更新する

**Checkpoint**: 設定ダイアログで BGM ファイル選択→プレビュー→保存→タイマー開始で正しい BGM が流れることを確認

---

## Phase 7: Polish & 動作確認

- [X] T011 `python -m pytest tests/ -v` を実行し全テストがパスすることを確認する
- [X] T012 `tests/unit/test_bgm_service.py` を新規作成する：`work_bgm_enabled=False` で BGM が再生されないこと、`on_phase_changed(Phase.WORKING)` で `_effect_work.play()` が呼ばれること、`on_phase_changed(Phase.PAUSED)` で `stop()` が呼ばれること、`reload()` で `_load_sources()` が呼ばれることを確認する

---

## Dependencies & Execution Order

```
T001（既存テスト確認）
  ↓
T002（BgmSettings追加）
  ↓
T003（BgmService新規）→ T004（main.py接続）→ T005（reload連携）   ← US1
  ↓（並行可）
T006（休憩BGM確認）                                                  ← US2
  ↓（並行可）
T007（音量設定）                                                      ← US3
  ↓（並行可）
T008 → T009 → T010（設定ダイアログUI）                               ← US4
  ↓
T011（全テスト） → T012（BGMサービス単体テスト）
```

- T003〜T005（US1）と T008〜T010（US4）は別ファイルのため並行可能
- T006・T007 は T003 完了後に別ファイルで並行可能

---

## Implementation Strategy

### MVP（US1のみ: 作業BGMループ）

T001 → T002 → T003 → T004 → T005 → T011

### Full（全機能）

T001 → T002 → T003〜T005（作業BGM） → T006（休憩BGM） → T007（音量） → T008〜T010（設定UI） → T011 → T012
