# Tasks: コンパクトタイマーウィジェットと統計ダッシュボード

**Input**: Design documents from `/specs/005-compact-stats-dashboard/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/ui-events.md, research.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1〜US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup（共通インフラ追加）

**Purpose**: 005 が必要とする新しいディレクトリと依存ライブラリを追加する

- [x] T001 `requirements.txt` に `PyQt6-Qt6-Charts>=6.7.0` を追記する
- [x] T002 [P] `src/ui/charts/` ディレクトリを作成し `__init__.py` を配置する（`src/ui/charts/__init__.py`）
- [x] T003 [P] `tests/unit/` および `tests/integration/` ディレクトリが存在しない場合は作成し `__init__.py` を配置する

---

## Phase 2: Foundational（全ストーリー共通の基盤）

**Purpose**: 全ユーザーストーリーが依存するデータモデルとサービスの基盤を実装する

**⚠️ CRITICAL**: このフェーズが完了するまでユーザーストーリーの実装を開始しないこと

- [x] T004 `AppSettings` の `ui` サブグループに `WidgetDisplaySettings` フィールド（`window_opacity`, `hover_reveal_buttons`, `animation_duration_ms`, `window_x`, `window_y`, `window_width`, `window_height`）を追加する（`src/engine/session.py` または `src/services/settings_service.py`）
- [x] T005 [P] `DailyRecord` データクラスを追加する（`date`, `work_sessions_completed`, `work_sessions_interrupted`, `short_breaks_completed`, `long_breaks_completed`, `total_work_sec`, `total_break_sec`, `sessions`）（`src/engine/session.py`）
- [x] T006 `HistoryService` に以下のメソッドを追加・実装する：`record_session(session: TimerSession)`, `load_daily(date: str) -> DailyRecord | None`, `load_period(start: str, end: str) -> list[DailyRecord]`, `get_streak() -> int`, `cleanup(keep_days=90) -> int`（`src/services/history_service.py`）
- [x] T007 `TimerEngine` の `session_completed` シグナルを `HistoryService.record_session()` に接続する（`src/main.py` またはアプリ初期化コード）

**Checkpoint**: `HistoryService.record_session()` を呼び出してデータが `history/YYYY-MM-DD.json` に保存されることを確認する

---

## Phase 3: User Story 1 - コンパクトウィジェット（ホバーUI・ドラッグ移動） (Priority: P1) 🎯 MVP

**Goal**: タイマーウィジェットが画面の5%以下に収まり、ホバー時のみ操作ボタンを表示し、ドラッグで移動・位置永続化できる

**Independent Test**: アプリを起動してウィジェットを表示し、（1）ホバーでボタンが現れること、（2）ドラッグで移動できること、（3）再起動後も位置が保持されること、（4）ウィジェット外のクリックが背後のアプリに届くことを確認する

### Implementation for User Story 1

- [x] T008 [US1] `TimerWidget` に `QGraphicsOpacityEffect` を使ったボタンコンテナを追加し、`enterEvent` / `leaveEvent` で `QPropertyAnimation`（150ms フェード）によるホバーUI を実装する（`src/ui/timer_widget.py`）
- [x] T009 [US1] `TimerWidget` のウィジェットサイズをデフォルト 200×80px に設定し、画面の5%以下に収まることを確認する（`src/ui/timer_widget.py`）
- [x] T010 [US1] `mousePressEvent` / `mouseMoveEvent` / `mouseReleaseEvent` を実装してウィジェットのドラッグ移動を実現する。移動完了時（`mouseReleaseEvent`）に `SettingsService.save_settings()` で座標を永続化する（`src/ui/timer_widget.py`）
- [x] T011 [US1] 起動時に `SettingsService.load_settings()` から `window_x`, `window_y` を読み込み、null の場合は画面右上隅（16px オフセット）にデフォルト配置するロジックを実装する（`src/ui/timer_widget.py`）
- [x] T012 [US1] ウィジェットに `Qt.WindowType.Tool` フラグを追加してタスクバーへの表示を抑制し、ウィジェット外クリックが背後のウィンドウに届くことを確認する（`src/ui/timer_widget.py`）

**Checkpoint**: アプリを起動してUS1の独立テストを実行し全て通過すること

---

## Phase 4: User Story 2 - 統計ダッシュボード（当日記録・グラフ表示） (Priority: P1)

**Goal**: タイマーを数セッション動かした後にダッシュボードを開くと、当日の完了セッション数・累計作業時間・休憩回数がグラフ付きで表示され、セッション完了時にリアルタイムで更新される

**Independent Test**: 3セッション完了後にダッシュボードを開き、完了数=3・累計作業時間が正確・グラフに3本の棒が表示されることを確認する

### Implementation for User Story 2

- [x] T013 [P] [US2] `DashboardViewModel` クラスを実装する：`get_today_stats() -> TodayStats`, `get_period_stats(period: PeriodEnum) -> PeriodStats`, `get_session_detail(date: str) -> list[TimerSession]`, `refresh()` メソッドを含む（`src/services/dashboard_viewmodel.py`）
- [x] T014 [P] [US2] `SessionBarChart` ウィジェットを実装する：`QBarSeries` + `QBarSet` + `QBarCategoryAxis` を使用し、日別セッション数の棒グラフを描画する（`src/ui/charts/session_bar_chart.py`）
- [x] T015 [US2] `DashboardWindow` クラスを実装する（`QWidget` トップレベルウィンドウ）。当日統計（完了数・累計作業時間・短/長休憩回数）と `SessionBarChart` を配置する（`src/ui/dashboard_window.py`）
- [x] T016 [US2] `DashboardWindow` にモーダルレス表示ロジックを追加する。タイマーウィジェットの右クリックメニューに「統計を見る」を追加して `DashboardWindow.show()` を呼び出す（`src/ui/timer_widget.py`, `src/ui/dashboard_window.py`）
- [x] T017 [US2] `HistoryService.session_recorded` シグナル（または `TimerEngine.session_completed` シグナル経由）を `DashboardWindow.refresh_stats()` スロットに接続し、ダッシュボード表示中のリアルタイム更新を実現する（`src/ui/dashboard_window.py`）
- [x] T018 [US2] ダッシュボードで特定日付をクリックするとその日のセッション詳細一覧（開始/終了時刻・完了/中断状態）が表示されるビューを追加する（`src/ui/dashboard_window.py`）

**Checkpoint**: US2の独立テストを実行し全て通過すること。タイマーが動き続けながらダッシュボードが開けることを確認する

---

## Phase 5: User Story 3 - 週次・月次の集中傾向とストリーク (Priority: P2)

**Goal**: ダッシュボードの期間フィルターを切り替えると週次・月次データが表示され、ストリーク（連続達成日数）が強調表示される

**Independent Test**: 期間フィルターを「今週」に切り替えると7日分のグラフが表示され、「今月」で月次データが表示されること。ストリーク数が正確であることを確認する

### Implementation for User Story 3

- [x] T019 [US3] `DashboardViewModel.get_period_stats()` に `THIS_WEEK`（過去7日）と `THIS_MONTH`（今月）の集計ロジックを実装する（`src/services/dashboard_viewmodel.py`）
- [x] T020 [US3] `DashboardViewModel.get_streak()` にストリーク計算ロジックを実装する（当日から過去にさかのぼり連続達成日を数える）（`src/services/dashboard_viewmodel.py`）
- [x] T021 [US3] `DashboardWindow` に「今日 / 今週 / 今月」の期間フィルター切り替えUI（ボタングループまたはコンボボックス）を追加し、切り替え時に `SessionBarChart` とサマリー数値を更新する（`src/ui/dashboard_window.py`）
- [x] T022 [US3] `DashboardWindow` にストリーク日数と「最多セッション日」を強調表示するセクションを追加する（`src/ui/dashboard_window.py`）

**Checkpoint**: US3の独立テストを実行し全て通過すること

---

## Phase 6: User Story 4 - ウィジェット透明度カスタマイズ (Priority: P3)

**Goal**: 設定画面でウィジェットの透明度（20〜100%）を調整でき、ホバー時は自動的に100%不透明になり、設定が再起動後も保持される

**Independent Test**: 透明度を50%に設定して再起動し、ウィジェットが半透明で表示されること。ホバー時に100%不透明になることを確認する

### Implementation for User Story 4

- [x] T023 [P] [US4] `TimerWidget` に `setWindowOpacity()` 呼び出しを追加する：通常時は `settings.ui.window_opacity` の値を使用し、`enterEvent` 時は `1.0`、`leaveEvent` 時に元の値に戻す（`src/ui/timer_widget.py`）
- [x] T024 [P] [US4] `SettingsDialog`（または設定パネル）に透明度スライダー（20〜100%）を追加する。変更時に `SettingsService.save_settings()` を呼び出し、ウィジェットの透明度をリアルタイムで反映する（`src/ui/settings_dialog.py`）

**Checkpoint**: US4の独立テストを実行し全て通過すること

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 品質向上、テスト追加、エッジケース対応

- [x] T025 [P] `HistoryService` のユニットテストを実装する：`record_session()`, `load_daily()`, `get_streak()`, `cleanup()` の各メソッドをテストする（`tests/unit/test_history_service.py`）
- [x] T026 [P] `DashboardViewModel` のユニットテストを実装する：`get_today_stats()`, `get_period_stats(THIS_WEEK)`, `get_period_stats(THIS_MONTH)`, `get_streak()` をテストする（`tests/unit/test_dashboard_viewmodel.py`）
- [x] T027 統計フローの統合テストを実装する：セッション完了 → `HistoryService.record_session()` → `DashboardViewModel.refresh()` → 統計数値更新の一連の流れをテストする（`tests/integration/test_stats_flow.py`）
- [x] T028 [P] データが0件（初回起動直後）でダッシュボードを開いた場合の空状態表示（「まだデータがありません」）を実装する（`src/ui/dashboard_window.py`）
- [x] T029 [P] 高DPI対応（4K等）: `QApplication.setHighDpiScaleFactorRoundingPolicy()` を設定し、コンパクトウィジェットが4K環境でも正しく表示されることを確認する（`src/main.py`）
- [x] T030 `HistoryService.cleanup(keep_days=90)` をアプリ起動時に呼び出して90日超のデータを自動削除する（`src/main.py`）
- [x] T031 [P] `requirements.txt` を最終更新し、`quickstart.md` の手順通りに動作することを検証する

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし—すぐに開始可能
- **Foundational (Phase 2)**: Phase 1 完了後—全ユーザーストーリーをブロック
- **US1 (Phase 3)**: Phase 2 完了後
- **US2 (Phase 4)**: Phase 2 完了後（US1 と並行実装可能）
- **US3 (Phase 5)**: Phase 4 の DashboardViewModel が必要
- **US4 (Phase 6)**: Phase 3 の TimerWidget が必要
- **Polish (Phase 7)**: 全ストーリー完了後

### User Story Dependencies

- **US1 (P1)**: Phase 2 後に開始可能。他ストーリーに依存なし
- **US2 (P1)**: Phase 2 後に開始可能。US1 と並行実装可能
- **US3 (P2)**: US2 の DashboardWindow と DashboardViewModel が必要
- **US4 (P3)**: US1 の TimerWidget が必要

### Within Each User Story

- モデル/データクラス → サービス → UI の順で実装
- 各ストーリーの Checkpoint で独立テストを実行してから次へ進む

### Parallel Opportunities

- Phase 1: T002, T003 は並行実行可能
- Phase 2: T005 は T004 と並行実行可能
- Phase 4: T013（ViewModel）と T014（Chart ウィジェット）は並行実装可能
- Phase 7: T025, T026, T028, T029, T031 は並行実行可能

---

## Parallel Example: Phase 4 (US2)

```bash
# T013 と T014 は異なるファイルで依存関係なし—並行実装可能
Task T013: DashboardViewModel の実装 (src/services/dashboard_viewmodel.py)
Task T014: SessionBarChart の実装  (src/ui/charts/session_bar_chart.py)

# T013, T014 完了後に T015 を開始
Task T015: DashboardWindow の組み立て (src/ui/dashboard_window.py)
```

---

## Implementation Strategy

### MVP First（US1 + US2 のみ）

1. Phase 1: Setup 完了
2. Phase 2: Foundational 完了（CRITICAL）
3. Phase 3: US1（コンパクトウィジェット）完了 → 独立テスト
4. Phase 4: US2（統計ダッシュボード）完了 → 独立テスト
5. **STOP & VALIDATE**: アプリが動作する MVP として機能することを確認

### Incremental Delivery

1. Setup + Foundational → 基盤完成
2. US1 完了 → コンパクトウィジェット MVP
3. US2 完了 → 統計ダッシュボード追加（価値大）
4. US3 完了 → 週次・月次分析追加
5. US4 完了 → 透明度カスタマイズ追加（仕上げ）

---

## Notes

- [P] タスクは異なるファイルで依存なし—並行実行可能
- [Story] ラベルはタスクとユーザーストーリーのトレーサビリティを確保
- 各ストーリーの Checkpoint 後に git commit 推奨
- 004-desktop-pomodoro-timer の `TimerEngine` と `HistoryService` の既存コードを前提とする
- テストはスペックで明示的に要求されていないため任意（Polish フェーズに収録）
