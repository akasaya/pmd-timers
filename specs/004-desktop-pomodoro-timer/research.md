# Research: デスクトップ常駐ポモドーロタイマー

**Feature Branch**: `004-desktop-pomodoro-timer`
**Date**: 2026-03-15
**Phase**: Phase 0 - Research

---

## 1. 技術スタック選定

### 決定: Python + PyQt6

**根拠:**
- プロジェクト全体が Python ベース（`pr-agent/` ディレクトリ参照）で、言語の一貫性を保てる
- 003-mascot-pomodoro のようなアニメーション付きマスコット機能も PyQt6 のアニメーションフレームワークで対応可能
- Windows 10以降での always-on-top は `Qt.WindowType.WindowStaysOnTopHint` で信頼性高く実装できる
- デスクトップ通知は `win10toast` または `plyer` ライブラリで Windows toast 通知に対応
- PyInstaller による単一 `.exe` 配布が可能
- 開発速度が最も速く、ソロ開発者に適している

**比較検討:**

| 観点 | Python/PyQt6 | Tauri (Rust+Web) | Electron (JS) | C# WPF |
|------|-------------|-----------------|---------------|--------|
| 常時最前面の信頼性 | ⚠️ 概ね動作（OS依存の例外あり） | ✅ ネイティブ | ✅ ネイティブ | ✅ 完全 |
| デスクトップ通知 | ⚠️ plyer経由 | ✅ ネイティブ toast | ✅ ネイティブ | ✅ toast API |
| バンドルサイズ | ~80MB | ~60MB | ~150MB | ~30MB |
| プロジェクト言語統一 | ✅ Python統一 | ❌ Rust+JS | ❌ JS | ❌ C# |
| 開発速度 | ✅ 最速 | 中程度 | 中程度 | 中程度 |
| マスコット機能(003)との共存 | ✅ 共通コード | ❌ 別実装 | ❌ 別実装 | ❌ 別実装 |

**却下した代替案:**
- **Tauri**: Rust 学習コストが高く、Python プロジェクトとの親和性がない
- **Electron**: バンドルサイズが大きく、Python プロジェクトとの統一性がない
- **C# WPF**: 優れた Windows ネイティブ性能だが、プロジェクト言語が分断される

---

## 2. Always-On-Top の実装方針

### 決定: `Qt.WindowType.WindowStaysOnTopHint` + フレームレスウィンドウ

**根拠:**
- `setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)` の組み合わせで Windows 上の最前面表示が最も安定する
- `Qt.WindowType.Tool` フラグを加えることでタスクバーに表示せずシステムトレイのみに残せる
- フレームレスにすることでコンパクトなウィジェット外観を実現（002-compact-window の要件と一致）

**既知の制限事項:**
- Windows 11 の「常に最前面」設定を持つシステムウィンドウ（タスクバー等）には隠れることがある
- 全画面ゲームアプリの上には表示できない（OS の仕様）

---

## 3. タイマー状態機械

### 決定: 6状態モデル

```
IDLE → WORKING → SHORT_BREAK → WORKING → ... → LONG_BREAK → IDLE
          ↓           ↓              ↓                ↓
        PAUSED      PAUSED         PAUSED           PAUSED
```

**状態定義:**

| 状態 | 説明 | 有効な遷移先 |
|------|------|------------|
| IDLE | 待機中。タイマーは初期値を表示 | WORKING |
| WORKING | 作業セッション実行中 | PAUSED, SHORT_BREAK, LONG_BREAK, IDLE |
| SHORT_BREAK | 短休憩実行中 | PAUSED, WORKING, IDLE |
| LONG_BREAK | 長休憩実行中 | PAUSED, WORKING, IDLE |
| PAUSED | 一時停止中。前の状態を記憶 | 前の状態, IDLE |

---

## 4. スリープ/復帰ハンドリング

### 決定: スリープ検出 + スマート一時停止

**実装方針:**
- Windows の電源管理イベント（`WM_POWERBROADCAST`）を PyQt6 の `nativeEvent` で受信
- スリープ発生時: 現在のセッション状態を保存し、タイマーを強制一時停止
- 復帰時の判断:
  - スリープ時間 < 2分: そのまま再開
  - 2〜30分: ユーザーに「再開 / リセット」の選択ダイアログを表示
  - 30分超: セッションを中断済みとしてマークし IDLE に戻る

---

## 5. ウィンドウ位置とサイズの永続化

### 決定: JSON ファイルによるローカル保存

**保存先**: `%APPDATA%\pmd-timers\settings.json`（Windows）/ `~/.config/pmd-timers/settings.json`（その他）

**保存タイミング:**
- ウィンドウ移動完了時（`mousePressEvent` / `mouseReleaseEvent`）
- 設定変更時
- アプリ終了時（`closeEvent`）

---

## 6. デスクトップ通知

### 決定: `plyer` ライブラリ（クロスプラットフォーム）

**根拠:**
- `plyer.notification` が Windows toast 通知、macOS 通知センター、Linux デスクトップ通知を統一的に扱える
- フォールバックとして PyQt6 の `QSystemTrayIcon.showMessage()` を使用

---

## 7. 設定のデフォルト値

研究結果に基づく推奨デフォルト値:

| 設定項目 | デフォルト値 | 範囲 |
|---------|------------|------|
| 作業時間 | 25分 | 5〜90分 |
| 短休憩時間 | 5分 | 1〜30分 |
| 長休憩時間 | 15分 | 5〜60分 |
| 長休憩までのセッション数 | 4 | 2〜10 |
| 次のセッション自動開始 | オフ | - |
| 通知音 | オン | - |
| デスクトップ通知 | オン | - |
| 常に最前面 | オン | - |
| ウィンドウ透明度 | 95% | 50〜100% |

---

## 解決済みの不明点

| 項目 | 決定内容 |
|------|---------|
| 技術スタック | Python 3.12 + PyQt6 |
| パッケージング | PyInstaller（単一 .exe） |
| 通知方式 | plyer + QSystemTrayIcon フォールバック |
| 設定保存 | JSON ファイル（%APPDATA%） |
| スリープ処理 | スマート一時停止（時間に応じて分岐） |
| ウィンドウ位置 | 起動時デフォルト: 右上隅 16px オフセット |
