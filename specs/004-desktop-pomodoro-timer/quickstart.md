# Quickstart: デスクトップ常駐ポモドーロタイマー

**Feature Branch**: `004-desktop-pomodoro-timer`
**Date**: 2026-03-15

---

## 前提条件

- Python 3.12+
- pip

---

## セットアップ

```bash
# リポジトリクローン後
cd pmd-timers

# 仮想環境の作成
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# 依存ライブラリのインストール
pip install PyQt6 plyer

# アプリ起動
python src/main.py
```

---

## 開発用コマンド

```bash
# テスト実行
python -m pytest tests/

# 型チェック
python -m mypy src/

# exe 生成（配布用）
pip install pyinstaller
pyinstaller --onefile --windowed --name "PomodoroTimer" src/main.py
# dist/PomodoroTimer.exe が生成される
```

---

## プロジェクト構造

```
pmd-timers/
├── src/
│   ├── main.py              # エントリーポイント
│   ├── engine/
│   │   ├── timer_engine.py  # タイマーロジック・状態機械
│   │   └── session.py       # TimerSession データクラス
│   ├── services/
│   │   ├── settings_service.py    # 設定の読み書き
│   │   ├── history_service.py     # セッション履歴の管理
│   │   └── notification_service.py # デスクトップ通知
│   └── ui/
│       ├── timer_widget.py   # メインタイマーウィジェット（常駐）
│       ├── settings_dialog.py # 設定ダイアログ
│       └── tray_icon.py      # システムトレイアイコン
├── tests/
│   ├── unit/
│   │   ├── test_timer_engine.py
│   │   └── test_settings_service.py
│   └── integration/
│       └── test_session_flow.py
├── specs/
│   └── 004-desktop-pomodoro-timer/  # この仕様書群
├── requirements.txt
└── README.md
```

---

## 基本的な使い方

1. アプリを起動すると、画面右上にコンパクトなタイマーウィジェットが表示されます
2. **左クリック** でタイマー開始 / 一時停止
3. **右クリック** でコンテキストメニュー（リセット・設定・終了）
4. ウィジェットを **ドラッグ** して好きな位置に移動できます
5. タイマー終了時にデスクトップ通知と通知音でお知らせします

---

## 設定ファイルの場所

| OS | パス |
|----|------|
| Windows | `%APPDATA%\pmd-timers\settings.json` |
| macOS | `~/Library/Application Support/pmd-timers/settings.json` |
| Linux | `~/.config/pmd-timers/settings.json` |
