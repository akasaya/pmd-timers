# 🍅 pmd-timers

デスクトップに常時表示されるコンパクトなポモドーロタイマーアプリです。
作業の邪魔にならないミニウィジェットと、作業記録を振り返れる統計ダッシュボードを備えています。

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

---

## スクリーンショット

> *(準備中)*

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
| 左ドラッグ | ウィジェットを好きな場所に移動 |
| 右クリック | 統計ダッシュボード・設定・終了メニュー |
| `Ctrl+D` | ダッシュボードを開く |

### ポモドーロサイクル（デフォルト）

```
作業 25分 → 短休憩 5分  ×4回
                      ↓
                  長休憩 15分
```

---

## 設定

右クリックメニュー → **設定** から変更できます。

| 項目 | デフォルト | 範囲 |
|------|-----------|------|
| 作業時間 | 25分 | 5〜90分 |
| 短休憩 | 5分 | 1〜30分 |
| 長休憩 | 15分 | 5〜60分 |
| 長休憩までのセッション数 | 4回 | 2〜10回 |
| ウィジェット透明度 | 95% | 20〜100% |

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
| [001-pomodoro-desktop](specs/001-pomodoro-desktop/) | 基本ポモドーロタイマー |
| [002-compact-window](specs/002-compact-window/) | コンパクトウィンドウ |
| [003-mascot-pomodoro](specs/003-mascot-pomodoro/) | マスコットキャラクター応援タイマー |
| [004-desktop-pomodoro-timer](specs/004-desktop-pomodoro-timer/) | デスクトップ常駐タイマー（実装済み） |
| [005-compact-stats-dashboard](specs/005-compact-stats-dashboard/) | コンパクトウィジェット + 統計ダッシュボード（実装済み） |

---

## ライセンス

MIT
