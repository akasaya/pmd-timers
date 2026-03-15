# Implementation Plan: デスクトップ常駐ポモドーロタイマー

**Branch**: `004-desktop-pomodoro-timer` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-desktop-pomodoro-timer/spec.md`

---

## Summary

デスクトップ上に常時最前面表示されるコンパクトなポモドーロタイマーアプリを Python + PyQt6 で実装する。フレームレスウィンドウで画面の任意の位置に配置でき、タイマーのセッション管理・通知・設定永続化を提供する。003-mascot-pomodoro との将来的な統合を見据えたモジュール構成とする。

---

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: PyQt6 6.7+, plyer 2.1+, PyInstaller 6.x（パッケージング用）
**Storage**: JSON ファイル（%APPDATA%\pmd-timers\）
**Testing**: pytest + pytest-qt
**Target Platform**: Windows 10/11（主要）、macOS/Linux（副次的対応）
**Project Type**: デスクトップアプリ（standalone GUI）
**Performance Goals**: 起動時間 5秒以内、タイマー誤差 1秒以内
**Constraints**: 常時最前面表示、オフライン動作必須、メモリ使用量 100MB 以下
**Scale/Scope**: シングルユーザー、ローカル動作のみ

---

## Constitution Check

*constitution.md はプロジェクト固有ルールが未設定のため、一般的な品質ゲートで評価する。*

| ゲート | 評価 | 備考 |
|--------|------|------|
| 実装詳細が spec に含まれていない | ✅ PASS | spec.md は技術スタック非言及 |
| テスト可能な要件 | ✅ PASS | 全 FR に受け入れシナリオあり |
| 単一責任の原則 | ✅ PASS | engine / services / ui に分離 |
| シンプルな設計 | ✅ PASS | 過剰なレイヤリングなし |

---

## Project Structure

### Documentation (this feature)

```text
specs/004-desktop-pomodoro-timer/
├── plan.md              # このファイル
├── research.md          # Phase 0 完了
├── data-model.md        # Phase 1 完了
├── quickstart.md        # Phase 1 完了
├── contracts/
│   └── ui-events.md     # Phase 1 完了
└── tasks.md             # Phase 2 (/speckit.tasks コマンドで生成)
```

### Source Code (repository root)

```text
src/
├── main.py                      # エントリーポイント（QApplication 初期化）
├── engine/
│   ├── __init__.py
│   ├── timer_engine.py          # タイマー状態機械・カウントダウンロジック
│   └── session.py               # TimerSession・PhaseEnum データクラス
├── services/
│   ├── __init__.py
│   ├── settings_service.py      # AppSettings 読み書き（JSON）
│   ├── history_service.py       # DailyRecord・セッション履歴管理
│   └── notification_service.py  # デスクトップ通知（plyer + QSystemTrayIcon）
└── ui/
    ├── __init__.py
    ├── timer_widget.py           # メインウィジェット（フレームレス・最前面）
    ├── settings_dialog.py        # 設定ダイアログ
    └── tray_icon.py              # システムトレイアイコンとコンテキストメニュー

tests/
├── unit/
│   ├── test_timer_engine.py     # 状態遷移・カウントダウンのユニットテスト
│   └── test_settings_service.py # 設定の読み書きバリデーション
└── integration/
    └── test_session_flow.py     # フルセッションフロー（IDLE→WORKING→SHORT_BREAK）

requirements.txt
```

**Structure Decision**: シングルプロジェクト構成（Option 1）。engine / services / ui の3層分離により、将来的に 003-mascot-pomodoro が `engine` と `services` を再利用できる。

---

## Design Decisions

### タイマー駆動方式

`QTimer` を 1秒間隔で使用。精度要件（±1秒以内）を満たすには十分。
高精度が必要な場合は `QElapsedTimer` でドリフト補正を行う。

### ウィンドウフラグの組み合わせ

```
Qt.WindowType.FramelessWindowHint       # タイトルバーなし
| Qt.WindowType.WindowStaysOnTopHint    # 常に最前面
| Qt.WindowType.Tool                    # タスクバーに表示しない
```

### ドラッグ移動の実装

`mousePressEvent` / `mouseMoveEvent` で差分座標を計算して `move()` を呼ぶ。
移動完了時（`mouseReleaseEvent`）に位置を `settings_service` で保存。

### スリープ検出（Windows）

PyQt6 の `nativeEvent` で `WM_POWERBROADCAST` を受信:
- `PBT_APMSUSPEND (0x0004)`: スリープ開始
- `PBT_APMRESUMEAUTOMATIC (0x0012)`: 復帰

### 設定保存フォーマット（settings.json の例）

```json
{
  "version": "1.0",
  "timers": {
    "work_duration_min": 25,
    "short_break_min": 5,
    "long_break_min": 15,
    "sessions_before_long_break": 4
  },
  "behavior": {
    "auto_start_next_session": false
  },
  "notifications": {
    "sound_enabled": true,
    "desktop_notification_enabled": true
  },
  "ui": {
    "always_on_top": true,
    "window_opacity": 0.95,
    "window_x": null,
    "window_y": null,
    "window_width": 200,
    "window_height": 120
  }
}
```

---

## Complexity Tracking

複雑性の違反なし。シンプルな3層構成で全要件を満たせる。

---

## Next Steps

`/speckit.tasks` を実行してタスクリストを生成する。
