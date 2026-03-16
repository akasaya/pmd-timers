# Tasks: UIの多言語対応（i18n）

**Input**: Design documents from `/specs/012-i18n-support/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: `i18n_service` のユニットテストのみ Foundational フェーズに含める。

**Organization**: Foundational で翻訳基盤を構築し、US1（英語切り替え）で全UIを対応、US2（日本語に戻す）は US1 完成時点で自動的に動作するため確認のみ。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 並列実行可能（異なるファイル、依存なし）
- **[Story]**: 対応するユーザーストーリー（US1, US2）
- ファイルパスを含める

---

## Phase 1: Setup（新規ファイル骨格）

**Purpose**: 新規ファイル・ディレクトリの骨格を作る

- [x] T001 `src/locale/` ディレクトリを作成し `src/locale/__init__.py`（空ファイル）を追加する
- [x] T002 `src/services/i18n_service.py` を新規作成する — `init(language: str)` と `t(key: str, **kwargs) -> str` と `AUDIO_FILTER` 定数を実装する（辞書未ロード時はキーをそのまま返す）
- [x] T003 [P] `src/locale/ja.py` を新規作成する — data-model.md の日本語翻訳辞書（約70キー）を `STRINGS: dict[str, str]` として実装する
- [x] T004 [P] `src/locale/en.py` を新規作成する — data-model.md の英語翻訳辞書（約70キー）を `STRINGS: dict[str, str]` として実装する

**Checkpoint**: `from src.services.i18n_service import init, t` が import でき、`init("en")` + `t("phase.working")` が `"Working"` を返す

---

## Phase 2: Foundational（設定スキーマ + 起動配線）

**Purpose**: 全UIコンポーネントが依存する設定データとサービス初期化を整備する

**⚠️ CRITICAL**: このフェーズが完了するまで UI の変更を開始しない

- [x] T005 `src/engine/session.py` に `GeneralSettings` データクラスを追加する（`language: str = "ja"`）し、`AppSettings` に `general: GeneralSettings = field(default_factory=GeneralSettings)` フィールドを追加する
- [x] T006 `src/engine/session.py` の `AppSettings.to_dict()` に `"general": {"language": self.general.language}` を追加する
- [x] T007 `src/engine/session.py` の `AppSettings.from_dict()` で `general` キーを読み込み `GeneralSettings(language=g.get("language", "ja"))` を生成する
- [x] T008 `src/main.py` の起動処理（`settings = settings_svc.load()` の直後）に `from src.services.i18n_service import init as init_i18n` と `init_i18n(settings.general.language)` を追加する
- [x] T009 [P] `tests/unit/test_i18n_service.py` を新規作成する — `init("ja")` / `init("en")` 後の `t()` 動作、動的フォーマット（`t("widget.today_count", count=5)`）、未知キーのフォールバックをテストする

**Checkpoint**: `pytest tests/unit/test_i18n_service.py -v` がパスし、アプリ起動して設定ファイルに `general.language` が保存されることを確認

---

## Phase 3: User Story 1 — 英語UIに切り替えて使う (Priority: P1) 🎯 MVP

**Goal**: 設定ダイアログで English に切り替えて再起動すると全UIが英語表示になる

**Independent Test**: `general.language` を `"en"` に設定して起動し、ウィジェット・設定ダイアログ・トレイメニュー・ダッシュボード・デスクトップ通知がすべて英語で表示される

### Implementation for User Story 1

- [x] T010[P] [US1] `src/ui/timer_widget.py` の全ハードコード文字列を `t()` に置き換える — `_PHASE_LABELS` 辞書の値を `t("phase.idle")` 等に変更、`contextMenuEvent` のメニュー項目を `t("widget.menu.*")` に変更、`update_daily_count` の `f"今日: {count}"` を `t("widget.today_count", count=count)` に変更（`from src.services.i18n_service import t` をインポート）
- [x] T011 [P] [US1] `src/ui/tray_icon.py` の全ハードコード文字列を `t()` に置き換える — `_setup_menu` 内の `"ウィジェットを表示"` → `t("tray.show_widget")` 等、4件すべてを対応するキーに変換する（`from src.services.i18n_service import t` をインポート）
- [x] T012 [P] [US1] `src/services/notification_service.py` の `_PHASE_MESSAGES` 辞書を削除し、`notify_phase_change` 内で `t("notification.work_done.title")` 等を直接参照するよう変更する（`from src.services.i18n_service import t` をインポート）
- [x] T013 [US1] `src/ui/settings_dialog.py` に言語セレクタを追加する — BGMグループの後に `QGroupBox(t("settings.group.general"))` を追加し `QComboBox`（`"日本語"/"ja"`、`"English"/"en"`）を配置、現在の `self._settings.general.language` 値で初期選択する（`QComboBox` を import に追加）
- [x] T014 [US1] `src/ui/settings_dialog.py` の `_apply()` に `self._settings.general.language = self._lang_combo.currentData()` を追加する
- [x] T015 [US1] `src/ui/settings_dialog.py` の `_reset()` に `self._lang_combo.setCurrentIndex(self._lang_combo.findData("ja"))` を追加する
- [x] T016 [US1] `src/ui/settings_dialog.py` の全ハードコード文字列（グループタイトル・フォームラベル・チェックボックス・ボタン・ファイルダイアログタイトル）を `t()` に置き換える — `setWindowTitle(t("settings.title"))`、`QSpinBox.setSuffix(t("settings.suffix.minutes"))` 等、全30件を変換する（`from src.services.i18n_service import t, AUDIO_FILTER` をインポート）
- [x] T017 [US1] `src/ui/dashboard_window.py` の全ハードコード文字列を `t()` に置き換える — ウィンドウタイトル・期間ボタン・統計カードタイトル・動的フォーマット文字列（`t("dashboard.chart.best", date=d, count=c, total=tot)`）・セッション詳細のセッションタイプ文字列を含む全18件を変換する（`from src.services.i18n_service import t` をインポート）

**Checkpoint**: `general.language = "en"` で起動してすべての画面が英語表示になる

---

## Phase 4: User Story 2 — 日本語に戻す (Priority: P2)

**Goal**: 英語表示から日本語に戻せることを確認する

**Independent Test**: English 表示の状態から設定で「日本語」を選択 → 再起動 → 全UIが日本語に戻る

### Implementation for User Story 2

- [x] T018 [US2] US1 完了後、`general.language = "ja"` で起動して全UIが日本語で表示されることを確認する（コード変更なし — US1 の実装が正しければ自動的に動作する）
- [x] T019 [US2] エッジケース確認: 設定ファイルを削除（または `general` キーを手動削除）して起動したとき `"ja"` にフォールバックすることを確認する

**Checkpoint**: 日本語 ⇆ 英語の双方向切り替えが動作する

---

## Phase 5: Polish & 動作確認

**Purpose**: コード品質・手動スモークテスト

- [x] T020 [P] `python -m py_compile src/services/i18n_service.py src/locale/ja.py src/locale/en.py src/engine/session.py src/main.py src/ui/timer_widget.py src/ui/tray_icon.py src/ui/settings_dialog.py src/ui/dashboard_window.py src/services/notification_service.py` で構文エラーがないことを確認する
- [x] T021 [P] `pytest tests/unit/test_i18n_service.py -v` を実行してテストがパスすることを確認する
- [x] T022 手動スモークテスト（日本語）: アプリ起動 → 全UI日本語 → 設定に「一般設定」グループと言語セレクタが表示される → OK
- [x] T023 手動スモークテスト（English）: 言語を English に変更して保存 → 再起動 → ウィジェット・設定ダイアログ・トレイ・ダッシュボードが英語 → 通知も英語で発火する
- [x] T024 手動スモークテスト（戻す）: 日本語に戻して再起動 → 全UI日本語に戻る

---

## Dependencies & Execution Order

### フェーズ依存関係

- **Phase 1（Setup）**: 依存なし — 即開始可能
- **Phase 2（Foundational）**: Phase 1 完了後 — **すべての US をブロック**
- **Phase 3（US1）**: Phase 2 完了後 — T010〜T012 は並列実行可、T013〜T017 は順次
- **Phase 4（US2）**: Phase 3 完了後 — 確認のみ
- **Phase 5（Polish）**: Phase 3・4 完了後

### 並列実行の機会

| グループ | 並列実行可能タスク |
|---|---|
| Phase 1 | T003, T004（別ファイル） |
| Phase 2 | T005〜T008 は順次、T009 は並列可 |
| Phase 3 | T010, T011, T012 は別ファイルのため並列可 |
| Phase 5 | T020, T021 は並列可 |

### 同一ファイルの競合に注意

- `settings_dialog.py`: T013→T014→T015→T016 は順次（同一ファイル）
- `session.py`: T005→T006→T007 は順次

---

## Parallel Example: User Story 1

```bash
# Phase 3 の並列実行可能グループ:
Task T010: src/ui/timer_widget.py の文字列置換
Task T011: src/ui/tray_icon.py の文字列置換
Task T012: src/services/notification_service.py の文字列置換
# ↑ 3タスクは同時実行可

# その後 settings_dialog.py と dashboard_window.py を順次:
T013 → T014 → T015 → T016 (settings_dialog.py — 同一ファイル)
T017 (dashboard_window.py — 独立)
```

---

## Implementation Strategy

### MVP First（US1 の英語切り替えのみ）

1. Phase 1: locale ファイルと i18n_service を作成
2. Phase 2: GeneralSettings + main.py 配線 + ユニットテスト
3. Phase 3: 全UIを `t()` に置換 + 言語セレクタ
4. **STOP and VALIDATE**: English で起動して全画面確認
5. Phase 4・5: 日本語への戻り確認 + クリーンアップ

### 実装量の見積もり

| 変更種別 | ファイル数 | 主な作業 |
|---|---|---|
| 新規作成 | 4 | `i18n_service.py`, `locale/__init__.py`, `ja.py`, `en.py` |
| 設定スキーマ変更 | 1 | `session.py`（+10行程度） |
| 起動配線 | 1 | `main.py`（+2行） |
| UI文字列置換 | 5 | 各UIファイル（1ファイルあたり10〜30行の変更） |

---

## Notes

- `t()` のインポートは各UIファイルの先頭に `from src.services.i18n_service import t` を追加
- `AUDIO_FILTER` は `settings_dialog.py` の3箇所すべてで `i18n_service.AUDIO_FILTER` に統一
- 言語変更の「再起動が必要」をユーザーに伝えるUIメッセージは今回のスコープ外
- `settings.suffix.minutes` は `" 分"` / `" min"` — QSpinBox の `setSuffix()` に使用
