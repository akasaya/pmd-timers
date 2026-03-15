# Quickstart: コンパクトタイマーウィジェットと統計ダッシュボード

**Feature Branch**: `005-compact-stats-dashboard`
**Date**: 2026-03-15

> 004-desktop-pomodoro-timer の quickstart.md を前提とする。
> 本ドキュメントは 005 固有の追加セットアップと新機能の使い方のみ記載する。

---

## 追加依存ライブラリ

```bash
# PyQt6-Qt6-Charts の追加インストール
pip install PyQt6-Qt6-Charts
```

`requirements.txt` への追記:
```
PyQt6>=6.7.0
PyQt6-Qt6-Charts>=6.7.0
plyer>=2.1.0
```

---

## 新コンポーネントの起動確認

```bash
# ダッシュボードの単体動作確認
python src/ui/dashboard_window.py

# ウィジェットのホバーUI動作確認
python src/ui/timer_widget.py
```

---

## プロジェクト構造（004 からの差分）

```
src/
├── ...（004 の構造を継承）
├── services/
│   ├── history_service.py     # 既存（004で作成）
│   └── dashboard_viewmodel.py # ★ 新規：統計集計ロジック
└── ui/
    ├── timer_widget.py         # ★ 更新：ホバーUI・透明度を追加
    ├── dashboard_window.py     # ★ 新規：統計ダッシュボード画面
    └── charts/
        ├── __init__.py
        └── session_bar_chart.py # ★ 新規：日別棒グラフウィジェット

tests/
├── unit/
│   ├── test_history_service.py    # ★ 新規
│   └── test_dashboard_viewmodel.py # ★ 新規
└── integration/
    └── test_stats_flow.py          # ★ 新規
```

---

## 統計ダッシュボードの開き方

1. タイマーウィジェット上で **右クリック** → コンテキストメニューから「統計を見る」を選択
2. ショートカット: `Ctrl+D`（ウィジェットにフォーカスがある時）
3. システムトレイアイコンの右クリックメニューから「ダッシュボード」

---

## 履歴データの場所

| OS | パス |
|----|------|
| Windows | `%APPDATA%\pmd-timers\history\YYYY-MM-DD.json` |
| macOS | `~/Library/Application Support/pmd-timers/history/YYYY-MM-DD.json` |
| Linux | `~/.config/pmd-timers/history/YYYY-MM-DD.json` |

古いデータ（90日超）は起動時に自動削除されます。
