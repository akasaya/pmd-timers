# Implementation Plan: UIバグ修正 - 透明度・ホバー・文字視認性・Windows統計

**Branch**: `006-fix-ui-bugs` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)

## Summary

4つのUIバグを修正する。(1) 透明度ラベルが「不透明度」の意味で使われているため表示を修正、(2) ホバーボタンのガタつきをデバウンスタイマーで解消、(3) フレームレス透明ウィンドウでの文字視認性を背景パネルで改善、(4) WindowsでPyQt6-Qt6-Chartsが使えない環境でのダッシュボード代替表示を強化する。

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: PyQt6 6.7+, plyer 2.1+
**Storage**: N/A（このフィーチャーではデータ変更なし）
**Testing**: pytest
**Target Platform**: Windows 10/11（主要）、macOS/Linux（動作確認）
**Project Type**: デスクトップアプリ（PyQt6 GUIウィジェット）
**Performance Goals**: ホバーアニメーション 150ms以内にレスポンス
**Constraints**: 既存設定ファイル（window_opacity の値）との後方互換性維持
**Scale/Scope**: 4ファイルの修正のみ

## Constitution Check

プロジェクト固有の Constitution は未定義。一般原則として:
- 既存テストが全てパスすること
- 最小限の変更（オーバーエンジニアリングしない）
- 既存の設定ファイル形式を破壊しない

## Project Structure

### Documentation (this feature)

```text
specs/006-fix-ui-bugs/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Root cause analysis
├── quickstart.md        # Manual test scenarios
├── contracts/           # UI behavior contracts
└── tasks.md             # Phase 2 output
```

### Source Code (変更対象ファイル)

```text
src/
└── ui/
    ├── timer_widget.py          # バグ2（ホバー）+ バグ3（文字視認性）
    ├── settings_dialog.py       # バグ1（透明度ラベル）
    └── charts/
        └── session_bar_chart.py # バグ4（Windowsフォールバック）

tests/
└── unit/
    └── test_timer_widget.py     # ホバー修正の単体テスト（新規）
```

## 修正方針詳細

### バグ1: 透明度ラベル修正（settings_dialog.py）

```
変更前: ラベル「透明度」スライダー範囲 20-100
変更後: ラベル「不透明度（表示の濃さ）」説明「100%=くっきり / 20%=うっすら」
```

値の計算ロジックは変更不要（`slider_value / 100.0` → `setWindowOpacity()`は正しい）。

### バグ2: ホバーデバウンス（timer_widget.py）

```python
# leaveEvent でいきなりフェードアウトせず、150ms後にunderMouse()確認
def leaveEvent(self, event):
    self._leave_timer.start(150)  # QTimer シングルショット

def _on_leave_timeout(self):
    if not self.underMouse():
        # 実際に出たのでフェードアウト実行
        self._start_fade_out()
```

### バグ3: 文字視認性（timer_widget.py）

ウィジェット背景に半透明パネルを適用:
```css
QWidget#container { background: rgba(20, 20, 20, 180); border-radius: 8px; }
```
フェーズラベルと数字の色は白系を維持（暗い背景の上なので見やすくなる）。

### バグ4: Windowsグラフ代替（session_bar_chart.py）

```python
# CHARTS_AVAILABLE=False 時、テキスト形式で日別データを表示
# 例:
# 月 ████ 4
# 火 ██   2
# 水 ███  3
```
QLabel を複数使ったシンプルな棒グラフ表示、または`QGridLayout`で日付・バー・数値を並べる。

## 後方互換性

- `window_opacity` の値は 0.2-1.0 の範囲で変更なし（設定ファイルは互換）
- ラベル変更はUIのみ、保存データに影響なし
- ホバーの挙動変更は既存設定 `hover_reveal_buttons`/`animation_duration_ms` を引き続き尊重
