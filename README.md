# 🍅 pmd-timers

[日本語](#-pmd-timers) | [English](#-pmd-timers-english)

> ⚠️ **このアプリは生成AI（Claude）との協働で開発されています。**
> コード・仕様書・ドキュメントの大部分はAIが生成したものです。動作確認はしていますが、利用は自己責任でお願いします。

---

デスクトップに常時表示されるコンパクトなポモドーロタイマーアプリです。
作業の邪魔にならないミニウィジェットと、作業記録を振り返れる統計ダッシュボードを備えています。

---

## とりあえず使いたい人へ（Windowsのみ）

**Pythonの知識は不要です。** [Releases](https://github.com/akasaya/pmd-timers/releases) から `PomodoroTimer.exe` をダウンロードしてダブルクリックするだけで起動します。

初回起動時にWindowsのセキュリティ警告が出る場合は「詳細情報」→「実行」を選んでください。
設定や作業記録は `%APPDATA%\pmd-timers\` に自動保存されます。

---

## 特徴

- **常時最前面表示** — 他のアプリを操作中もタイマーが常に見える
- **コンパクトデザイン** — 画面の5%以下に収まる小さなウィジェット
- **ホバーUI** — マウスを乗せたときだけ操作ボタンが現れる
- **自由に移動** — ドラッグで好きな位置に配置、再起動後も記憶
- **統計ダッシュボード** — 今日・今週・今月の作業記録をグラフで確認
- **透明度調整** — 作業中は半透明にして邪魔を最小化
- **デスクトップ通知** — セッション終了時に通知とサウンドでお知らせ
- **ポモドーロサイクル管理** — 4セッション後に長休憩を自動提案
- **カスタム通知音** — WAV/MP3/OGG/FLACなど主要フォーマット対応、再生区間もトリムできる
- **フェーズ別BGM** — 作業中と休憩中で別々の音楽を流せる（ループ再生・音量個別調整）
- **休憩後の自動スタート** — 休憩が終わったら次の作業タイマーを自動で開始するオプション
- **ミュートトグル** — 🔊/🔇ボタンで通知音・BGMをワンタッチでまとめてミュート、状態は再起動後も保持
- **多言語対応（日本語 / English）** — 設定画面で言語を切り替え可能、再起動後に反映

---

## 注目ポイント

- ウィジェットはホバー時のみボタンを表示。普段は時間と状態だけが見える
- 休憩後の自動スタートをオンにするとサイクルが手動操作なしで回り続ける
- 作業中と休憩中でBGMを個別に設定できる
- 🔊/🔇ボタンで通知音・BGMをワンタッチでまとめてミュート・アンミュートできる
- 設定で言語を日本語・英語から選べる（再起動後に反映）
- 統計ダッシュボードで日・週・月の作業セッション数と累計時間を確認できる

---

## スクリーンショット

![作業中のタイマーウィジェット](ss.png)

*右上に小さく表示されるウィジェット。作業中は赤いタイマー、休憩中は緑のタイマーで一目で状態がわかります。*

---

## インストール

### 動作環境

- Windows 10 / 11（主要対象）
- macOS / Linux（動作確認済み）
- Python 3.12+

### セットアップ

```bash
git clone https://github.com/akasaya/pmd-timers.git
cd pmd-timers

# 仮想環境（推奨）
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux

# 依存ライブラリ
pip install -r requirements.txt

# 起動
python src/main.py
```

---

## exe ビルド（Windows）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "PomodoroTimer" src/main.py
# dist/PomodoroTimer.exe が生成されます
```

---

## 使い方

| 操作 | 内容 |
|------|------|
| ウィジェット上にホバー | 操作ボタン（開始/停止/スキップ）が表示される |
| 画面を左ドラッグ | ウィジェットを好きな場所に移動 |
| 画面を右クリック | 統計ダッシュボード・設定・終了メニュー |

### ポモドーロサイクル（デフォルト）

```
作業 25分 → 短休憩 5分  ×4回
                      ↓
                  長休憩 15分
```

---

## 設定

右クリックメニュー → **設定** から変更できます。

| 項目 | デフォルト | 範囲・備考 |
|------|-----------|-----------|
| 作業時間 | 25分 | 5〜90分 |
| 短休憩 | 5分 | 1〜30分 |
| 長休憩 | 15分 | 5〜60分 |
| 長休憩までのセッション数 | 4回 | 2〜10回 |
| ウィジェット透明度 | 95% | 20〜100% |
| 休憩後の自動スタート | オフ | オンで休憩終了後に作業タイマーを自動開始 |
| 通知音 | デフォルト音 | WAV/MP3/OGG/FLAC など対応、再生区間トリム可 |
| 作業中BGM / 休憩中BGM | 無効 | ファイル指定・音量個別調整・ループ再生 |
| ミュート | オフ | 🔊/🔇ボタンで通知音・BGMをまとめて即時ミュート、状態を永続保存 |
| 言語 | 日本語 | 日本語 / English、再起動後に反映 |

設定・作業記録の保存場所:

| OS | パス |
|----|------|
| Windows | `%APPDATA%\pmd-timers\` |
| macOS | `~/Library/Application Support/pmd-timers/` |
| Linux | `~/.config/pmd-timers/` |

---

## 開発

```bash
# テスト実行
python -m pytest tests/ -v

# ディレクトリ構成
src/
├── engine/          # タイマーエンジン・データクラス
├── services/        # 設定・履歴・通知・統計集計
└── ui/
    ├── charts/      # 統計グラフ (QtCharts)
    ├── timer_widget.py      # メインウィジェット
    ├── dashboard_window.py  # 統計ダッシュボード
    └── settings_dialog.py   # 設定ダイアログ
```

---

## 仕様・設計ドキュメント

`specs/` 以下に各フィーチャーの仕様書・設計ドキュメントが格納されています。

| フィーチャー | 概要 |
|------------|------|
| [004-desktop-pomodoro-timer](specs/004-desktop-pomodoro-timer/) | デスクトップ常駐タイマー |
| [005-compact-stats-dashboard](specs/005-compact-stats-dashboard/) | コンパクトウィジェット + 統計ダッシュボード |
| [006-fix-ui-bugs](specs/006-fix-ui-bugs/) | UIバグ修正 |
| [007-sound-multimonitor](specs/007-sound-multimonitor/) | カスタム通知音・マルチモニター対応 |
| [008-phase-bgm](specs/008-phase-bgm/) | フェーズ別BGM再生 |
| [009-auto-resume-work](specs/009-auto-resume-work/) | 休憩後の作業タイマー自動スタート |
| [010-i18n-support](specs/010-i18n-support/) | UI多言語対応（仕様・設計フェーズ） |
| [011-mute-toggle](specs/011-mute-toggle/) | 通知音・BGMのワンタッチミュートトグル |
| [012-i18n-support](specs/012-i18n-support/) | UI多言語対応 実装（日本語 / English） |

---

---

# 🍅 pmd-timers (English)

> ⚠️ **This app is developed in collaboration with AI (Claude).**
> Most of the code, specs, and documentation are AI-generated. It has been tested, but use at your own risk.

---

A compact always-on-top Pomodoro timer that stays visible on your desktop.
Includes a mini widget that stays out of your way, plus a statistics dashboard to review your work history.

---

## Quick Start (Windows only)

**No Python knowledge needed.** Download `PomodoroTimer.exe` from [Releases](https://github.com/akasaya/pmd-timers/releases) and double-click to launch.

If Windows shows a security warning on first launch, click "More info" → "Run anyway".
Settings and work history are saved automatically to `%APPDATA%\pmd-timers\`.

---

## Features

- **Always on top** — Timer stays visible while you work in other apps
- **Compact design** — Tiny widget that takes less than 5% of your screen
- **Hover UI** — Buttons appear only when you hover over the widget
- **Draggable** — Place it anywhere; position is remembered after restart
- **Stats dashboard** — View work records by day, week, or month
- **Adjustable opacity** — Go semi-transparent to minimize distraction
- **Desktop notifications** — Sound and notification when a session ends
- **Pomodoro cycle** — Long break suggested automatically after 4 sessions
- **Custom notification sound** — WAV/MP3/OGG/FLAC and more, with trim support
- **Phase BGM** — Play different music during work and break phases
- **Auto-start after break** — Automatically start the next work session when a break ends
- **Mute toggle** — 🔊/🔇 button to instantly mute all sounds; state persists across restarts
- **Multi-language (Japanese / English)** — Switch language in Settings; takes effect after restart

---

## Highlights

- Widget shows buttons only on hover — just the time and phase otherwise
- Enable auto-start and the Pomodoro cycle runs without any manual input
- Work BGM and break BGM are configured independently
- One-tap 🔊/🔇 mute covers both notification sounds and BGM
- Switch language between Japanese and English in Settings (restart to apply)
- Dashboard shows completed sessions and total work time by day/week/month

---

## Screenshot

![Timer widget during work session](ss.png)

*Small widget in the top-right corner. Red timer = working, green timer = on break.*

---

## Installation

### Requirements

- Windows 10 / 11 (primary target)
- macOS / Linux (confirmed working)
- Python 3.12+

### Setup

```bash
git clone https://github.com/akasaya/pmd-timers.git
cd pmd-timers

# Virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

---

## Build exe (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "PomodoroTimer" src/main.py
# Generates dist/PomodoroTimer.exe
```

---

## Usage

| Action | Result |
|--------|--------|
| Hover over widget | Shows control buttons (start / pause / skip) |
| Left-drag | Move widget anywhere on screen |
| Right-click | Open stats dashboard, settings, or quit |

### Default Pomodoro cycle

```
Work 25min → Short break 5min  × 4
                               ↓
                          Long break 15min
```

---

## Settings

Right-click → **Settings** to configure.

| Setting | Default | Notes |
|---------|---------|-------|
| Work duration | 25 min | 5–90 min |
| Short break | 5 min | 1–30 min |
| Long break | 15 min | 5–60 min |
| Sessions before long break | 4 | 2–10 |
| Widget opacity | 95% | 20–100% |
| Auto-start after break | Off | Starts next work session automatically |
| Notification sound | Default | WAV/MP3/OGG/FLAC, with trim support |
| Work BGM / Break BGM | Disabled | File picker, per-phase volume control |
| Mute | Off | 🔊/🔇 instantly mutes all sounds; state saved |
| Language | Japanese | Japanese / English; restart to apply |

Data storage locations:

| OS | Path |
|----|------|
| Windows | `%APPDATA%\pmd-timers\` |
| macOS | `~/Library/Application Support/pmd-timers/` |
| Linux | `~/.config/pmd-timers/` |

---

## Development

```bash
# Run tests
python -m pytest tests/ -v

# Directory structure
src/
├── engine/          # Timer engine & data classes
├── services/        # Settings, history, notifications, stats
└── ui/
    ├── charts/      # Stats charts (QtCharts)
    ├── timer_widget.py      # Main widget
    ├── dashboard_window.py  # Statistics dashboard
    └── settings_dialog.py   # Settings dialog
```

---
