# Tasks: 音声ミュートトグル

**Input**: Design documents from `/specs/011-mute-toggle/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: 仕様書でテスト明示的要求なし。手動スモークテストで検証。

**Organization**: Foundational で設定スキーマを整備し、US1（ワンタッチミュート）で全実装、US2（永続化）は US1 の設定保存で自動的に満たされる。

---

## Phase 1: Foundational（設定スキーマ）

**Purpose**: ミュートフラグの永続化基盤を整備する。すべての実装がこれに依存。

- [x] T001 `src/engine/session.py` の `BehaviorSettings` に `is_muted: bool = False` フィールドを追加する
- [x] T002 `src/engine/session.py` の `AppSettings.to_dict()` の `"behavior"` ブロックに `"is_muted": self.behavior.is_muted` を追加する
- [x] T003 `src/engine/session.py` の `AppSettings.from_dict()` の `BehaviorSettings(...)` に `is_muted=b.get("is_muted", False)` を追加する

**Checkpoint**: `AppSettings().to_dict()` に `is_muted` が含まれ、`from_dict()` で読み戻せる

---

## Phase 2: User Story 1 — ワンタッチで全音声をミュートする (Priority: P1) 🎯 MVP

**Goal**: ウィジェットの🔊ボタンをクリックすると通知音・BGMがミュートになり、🔇アイコンに変わる。再クリックで解除。

**Independent Test**: BGM再生中にミュートボタンをクリック → BGMが即停止してアイコンが🔇に変わる。再クリックで🔊に戻る。通知タイミングでも音が鳴らない。

### Implementation for User Story 1

- [x] T004 [US1] `src/ui/timer_widget.py` の `_build_ui()` に `self._mute_btn = self._make_btn("🔊", self._on_mute_click)` を追加し、`btn_layout` の `_pause_btn` と `_skip_btn` の間に挿入する
- [x] T005 [US1] `src/ui/timer_widget.py` の `__init__` に `self.on_mute = lambda: None` を追加し、初期ミュート状態に応じてボタンアイコンを設定する（`if self._settings.behavior.is_muted: self._mute_btn.setText("🔇")`）
- [x] T006 [US1] `src/ui/timer_widget.py` に `_on_mute_click(self)` メソッドと `update_mute_state(self, is_muted: bool)` メソッドを追加する
- [x] T007 [US1] `src/main.py` に `toggle_mute()` 関数を実装する — `settings.behavior.is_muted` をトグルし、ミュートON時は `bgm_svc.stop()`、`settings_svc.save(settings)`、`widget.update_mute_state(...)` を呼ぶ
- [x] T008 [US1] `src/main.py` で `widget.on_mute = toggle_mute` を配線する（他の `widget.on_*` の配線と同じ場所）
- [x] T009 [P] [US1] `src/services/sound_service.py` の `play()` に `if self._settings.behavior.is_muted: return` を追加する（`sound_enabled` チェックの直後）
- [x] T010 [P] [US1] `src/services/bgm_service.py` の `on_phase_changed()` に `if self._settings.behavior.is_muted: return` を追加する（`self.stop()` の直後）

**Checkpoint**: ミュートボタンのON/OFFで通知音・BGMが制御され、アイコンが切り替わる

---

## Phase 3: User Story 2 — ミュート状態を再起動後も保持する (Priority: P2)

**Goal**: ミュートにしたままアプリを終了・再起動してもミュート状態が維持される。

**Independent Test**: ミュートONのまま終了 → 再起動 → ウィジェットのアイコンが🔇で音が鳴らない。

### Implementation for User Story 2

- [x] T011 [US2] Phase 1（T001〜T003）と Phase 2（T007 の `settings_svc.save()`）が完成していれば自動的に動作することを確認する（追加実装なし）

**Checkpoint**: 再起動後もミュート状態が保持されている

---

## Phase 4: Polish

- [x] T012 [P] `python -c "import ast; ast.parse(open('src/ui/timer_widget.py').read())"` など変更5ファイルの構文チェックを実行する
- [ ] T013 手動スモークテスト（ミュートON）: BGM再生中にミュートボタンクリック → BGM即停止 → アイコン🔇 → 通知タイミングで音が鳴らない
- [ ] T014 手動スモークテスト（ミュートOFF）: 🔇クリック → アイコン🔊 → 次フェーズでBGM再生再開
- [ ] T015 手動スモークテスト（永続化）: ミュートONのまま再起動 → 🔇表示 → 音が鳴らない

---

## Dependencies & Execution Order

- **Phase 1**: 依存なし — 即開始
- **Phase 2**: Phase 1 完了後。T004→T005→T006 は同一ファイルのため順次。T007→T008 は順次。T009/T010 は別ファイルのため並列可
- **Phase 3**: Phase 1・2 完了後（確認のみ）
- **Phase 4**: 全フェーズ完了後

### 並列実行

```bash
# Phase 2 内の並列可能グループ:
T009: sound_service.py にミュートガード追加
T010: bgm_service.py にミュートガード追加
# ↑ 別ファイルのため同時実行可
```

---

## Implementation Strategy

### 実装量の見積もり

| ファイル | 追加/変更行数 |
|---|---|
| `session.py` | +3行（フィールド1、to_dict 1、from_dict 1） |
| `timer_widget.py` | +12行（ボタン追加、コールバック、update メソッド） |
| `main.py` | +8行（toggle_mute 関数、配線） |
| `sound_service.py` | +2行（ガード） |
| `bgm_service.py` | +2行（ガード） |
| **合計** | **約27行** |
