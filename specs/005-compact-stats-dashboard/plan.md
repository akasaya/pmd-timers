# Implementation Plan: コンパクトタイマーウィジェットと統計ダッシュボード

**Branch**: `005-compact-stats-dashboard` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-compact-stats-dashboard/spec.md`

---

## Summary

004-desktop-pomodoro-timer のタイマーウィジェットに対して、（1）ホバー時のみ操作ボタンを表示するコンパクトUI、（2）透明度調整、（3）統計ダッシュボード（当日/週次/月次の棒グラフ付き）を追加する。002-compact-window の主要要件もここで実装する。

---

## Technical Context

**Language/Version**: Python 3.12（004 と同一）
**Primary Dependencies**: PyQt6 6.7+, PyQt6-Qt6-Charts 6.7+, plyer 2.1+
**Storage**: JSON ファイル（%APPDATA%\pmd-timers\history\）
**Testing**: pytest + pytest-qt
**Target Platform**: Windows 10/11（主要）、macOS/Linux（副次的）
**Project Type**: デスクトップアプリ拡張（004 へのフィーチャー追加）
**Performance Goals**: ダッシュボード表示2秒以内、統計更新3秒以内
**Constraints**: グラフは最大90日分、オフライン動作必須
**Scale/Scope**: 004 の拡張。新規ファイル数: 約5〜7ファイル

---

## Constitution Check

*constitution.md はプロジェクト固有ルールが未設定のため一般品質ゲートで評価。*

| ゲート | 評価 | 備考 |
|--------|------|------|
| 004 のアーキテクチャと整合 | ✅ PASS | engine/services/ui の3層を継承・拡張 |
| テスト可能な要件 | ✅ PASS | 全 FR に受け入れシナリオあり |
| シンプルな設計 | ✅ PASS | SQLite 不使用、JSON ファイルで十分 |
| 過剰な抽象化なし | ✅ PASS | ViewModel は単純な集計関数 |

---

## Project Structure

### Documentation (this feature)

```text
specs/005-compact-stats-dashboard/
├── plan.md              # このファイル
├── research.md          # Phase 0 完了
├── data-model.md        # Phase 1 完了
├── quickstart.md        # Phase 1 完了
├── contracts/
│   └── ui-events.md     # Phase 1 完了
└── tasks.md             # Phase 2 (/speckit.tasks コマンドで生成)
```

### Source Code (004 からの差分)

```text
src/
├── services/
│   ├── history_service.py      # 既存（004）。record_session() を新規追加
│   └── dashboard_viewmodel.py  # ★ 新規：統計集計 (TodayStats, PeriodStats)
└── ui/
    ├── timer_widget.py          # ★ 更新：ホバーUI・透明度・ドラッグ改善
    ├── dashboard_window.py      # ★ 新規：統計ダッシュボード (QWidget)
    └── charts/
        ├── __init__.py
        └── session_bar_chart.py # ★ 新規：QtCharts を使った棒グラフ

tests/
├── unit/
│   ├── test_history_service.py      # ★ 新規
│   └── test_dashboard_viewmodel.py  # ★ 新規
└── integration/
    └── test_stats_flow.py           # ★ 新規（セッション記録→ダッシュボード表示）
```

---

## Design Decisions

### ホバーUI の実装

```python
class TimerWidget(QWidget):
    def enterEvent(self, event):
        self._fade_in_buttons()   # QPropertyAnimation で opacity 0→1（150ms）

    def leaveEvent(self, event):
        self._fade_out_buttons()  # QPropertyAnimation で opacity 1→0（150ms）
```

ボタン群は `QWidget` にまとめて `QGraphicsOpacityEffect` を適用することで、一括フェードを実現。

### 透明度の実装

```python
# 設定変更時
self.setWindowOpacity(settings.ui.window_opacity)

# ホバー時は強制 100% 不透明
def enterEvent(self, event):
    self.setWindowOpacity(1.0)

def leaveEvent(self, event):
    self.setWindowOpacity(self._settings.ui.window_opacity)
```

### ダッシュボードの棒グラフ

```python
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis

bar_set = QBarSet("完了セッション数")
bar_set.append([record.work_sessions_completed for record in daily_records])
series = QBarSeries()
series.append(bar_set)
chart = QChart()
chart.addSeries(series)
```

### 統計リアルタイム更新

- `TimerEngine.session_completed` シグナルを `HistoryService.record_session()` に接続
- `HistoryService.session_recorded` シグナルをダッシュボードの `refresh()` スロットに接続
- ダッシュボードが開いていない間はシグナルは無視される（Qt の自動切断なし; ダッシュボード側で接続/切断を管理）

### 設定の JSON スキーマ（005 追加分）

```json
{
  "ui": {
    "window_opacity": 0.95,
    "hover_reveal_buttons": true,
    "animation_duration_ms": 150,
    "window_x": null,
    "window_y": null,
    "window_width": 200,
    "window_height": 80
  }
}
```

---

## Complexity Tracking

複雑性の違反なし。004 のアーキテクチャを自然に拡張する構成。

---

## Next Steps

`/speckit.tasks` を実行してタスクリストを生成する。
