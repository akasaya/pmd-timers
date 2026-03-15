# Tasks: UIバグ修正 - 透明度・ホバー・文字視認性・Windows統計

**Input**: Design documents from `/specs/006-fix-ui-bugs/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, contracts/ ✓

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

**Purpose**: 作業ブランチ確認のみ（既存プロジェクト、新規ファイル作成不要）

- [X] T001 現在のブランチが `006-fix-ui-bugs` であることを確認し、テストが全パスする状態を確認する (`python -m pytest tests/ -v`)

---

## Phase 2: Foundational（なし）

この修正は独立した4ファイルへの変更のみ。共通基盤の変更は不要。

---

## Phase 3: User Story 1 - 透明度設定の直感的な動作 (Priority: P1) 🎯 MVP

**Goal**: 設定ダイアログのラベルを「透明度」→「不透明度」に修正し、数値が大きいほど見やすくなることをUIで明示する

**Independent Test**: 設定ダイアログを開き、スライダーラベルが「不透明度」と表示され、100%設定でウィジェットが完全にくっきり見えることを確認

- [X] T002 [US1] `src/ui/settings_dialog.py` の透明度スライダーのラベルを「不透明度（表示の濃さ）」に変更し、スライダー下に「100%=くっきり / 20%=うっすら」の説明テキストを追加する

**Checkpoint**: 設定ダイアログを開いてラベルが「不透明度」に変わっていることを確認

---

## Phase 4: User Story 2 - ホバーボタンの安定した操作 (Priority: P1)

**Goal**: `leaveEvent` にデバウンスタイマーを追加し、子ウィジェット間のマウス移動でボタンが消えないようにする

**Independent Test**: ウィジェット上にマウスを乗せ、ボタンをクリックできることを確認（ガタつきなし）

- [X] T003 [US2] `src/ui/timer_widget.py` の `__init__` に `QTimer` (シングルショット、150ms) を追加し、`leaveEvent` でタイマー起動、タイムアウト時に `underMouse()` が `False` の場合のみフェードアウトを実行するよう修正する（`enterEvent` 時はタイマーをキャンセルする）

**Checkpoint**: ウィジェット上でマウスを動かし、ボタンがガタつかずクリックできることを確認

---

## Phase 5: User Story 3 - 文字の視認性向上 (Priority: P2)

**Goal**: フレームレス透明ウィンドウの背景に半透明ダークパネルを追加し、明るい壁紙でも文字が読める

**Independent Test**: 白い壁紙の上でウィジェットのタイマー数字が読めることを確認

- [X] T004 [US3] `src/ui/timer_widget.py` の `_build_ui` メソッドで、メインコンテナウィジェットに `objectName("container")` を設定し、スタイルシートに `QWidget#container { background: rgba(20, 20, 20, 180); border-radius: 8px; }` を適用する（T003完了後）

**Checkpoint**: 白い背景でウィジェットを表示し、タイマー数字・ラベルが明確に読めることを確認

---

## Phase 6: User Story 4 - Windows環境での統計ダッシュボード表示 (Priority: P2)

**Goal**: PyQt6-Qt6-Charts非インストール環境でもダッシュボードにテキスト形式の日別統計を表示する

**Independent Test**: `CHARTS_AVAILABLE=False` の状態でダッシュボードを開き、テキスト形式のデータが表示されることを確認

- [X] T005 [P] [US4] `src/ui/charts/session_bar_chart.py` のフォールバック表示を強化する：`CHARTS_AVAILABLE=False` 時に `QGridLayout` を使って日付・テキスト棒グラフ（`█` 文字）・数値を表示する `_build_text_chart(daily_counts)` メソッドを実装し、データが0件の場合は「まだ記録がありません」メッセージを表示する

**Checkpoint**: PyQt6-Qt6-Charts未インストール環境（またはCHARTS_AVAILABLEをFalseに設定）でダッシュボードを開き、テキスト棒グラフが表示されることを確認

---

## Phase 7: Polish & 動作確認

- [X] T006 `python -m pytest tests/ -v` を実行し、全テストがパスすることを確認する
- [ ] T007 `quickstart.md` の4シナリオを手動で確認し、全バグが修正されていることを検証する

---

## Dependencies & Execution Order

- **T001**: 最初に実行（現状確認）
- **T002**: T001完了後（`settings_dialog.py`のみ変更、独立）
- **T003**: T001完了後（`timer_widget.py`変更）
- **T004**: T003完了後（同じ`timer_widget.py`を変更するため逐次）
- **T005**: T001完了後（`session_bar_chart.py`のみ変更、T002・T003と並行可）
- **T006, T007**: 全実装完了後

### 並行実行可能

T002・T003・T005 は別ファイルのため並行実装可能：

```
T001 完了後:
  ├─ T002 (settings_dialog.py)  ─→ 完了
  ├─ T003 (timer_widget.py)     ─→ T004 (timer_widget.py)
  └─ T005 (session_bar_chart.py) ─→ 完了
全完了後 → T006 → T007
```

---

## Implementation Strategy

### MVP First (US1 + US2 = P1バグ修正のみ)

1. T001: 現状確認
2. T002: 透明度ラベル修正
3. T003: ホバーデバウンス修正
4. T006: テスト確認
5. **STOP and VALIDATE**: P1バグ2件が修正されていることを確認

### Full Fix（全4バグ）

1. T001 → T002, T003, T005（並行） → T004 → T006 → T007
