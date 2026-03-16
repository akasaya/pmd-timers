# Implementation Plan: 音声ミュートトグル

**Branch**: `011-mute-toggle` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-mute-toggle/spec.md`

## Summary

`BehaviorSettings.is_muted` フラグを追加し、ウィジェットのボタン列（▶/⏸ と ⏭ の間）に🔊/🔇トグルボタンを配置する。`sound_service.play()` と `bgm_service.on_phase_changed()` でミュートフラグを参照し、ミュート中は音声を出力しない。設定は再起動後も保持される。

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: PyQt6 6.7+（既存 QToolButton を流用）
**Storage**: JSON設定ファイル（`behavior.is_muted` フィールド追加）
**Testing**: pytest
**Target Platform**: Windows/Linux デスクトップ
**Project Type**: Desktop app
**Performance Goals**: ボタンクリックからBGM停止まで即座（1秒以内）
**Constraints**: 新規ライブラリ不要。既存ボタン構造・サービスパターンを踏襲
**Scale/Scope**: 変更5ファイル、追加コード約30行

## Constitution Check

既存パターンとの整合性:
- [x] `BehaviorSettings` への追加は既存 `auto_start_next_session` と同一パターン
- [x] `sound_service.play()` の先頭ガード追加は既存 `sound_enabled` チェックと同一パターン
- [x] ウィジェットボタン追加は `_make_btn()` ファクトリを流用

## Project Structure

### Documentation (this feature)

```text
specs/011-mute-toggle/
├── plan.md
├── research.md
├── data-model.md
└── tasks.md
```

### Source Code

```text
src/
├── engine/
│   └── session.py              # BehaviorSettings.is_muted 追加
├── services/
│   ├── sound_service.py        # play() にミュートガード追加
│   └── bgm_service.py          # on_phase_changed() にミュートガード追加
├── ui/
│   └── timer_widget.py         # _mute_btn 追加、update_mute_state() 追加
└── main.py                     # on_mute ハンドラ実装
```

## 実装詳細

### 1. `session.py` — BehaviorSettings への追加

```python
@dataclass
class BehaviorSettings:
    auto_start_next_session: bool = False
    is_muted: bool = False
```

`to_dict()` と `from_dict()` に `"is_muted"` を追加（デフォルト `False`）。

### 2. `timer_widget.py` — ミュートボタン追加

`_build_ui()` 内:
```python
self._mute_btn = self._make_btn("🔊", self._on_mute_click)
btn_layout.addWidget(self._start_btn)
btn_layout.addWidget(self._pause_btn)
btn_layout.addWidget(self._mute_btn)   # pause と skip の間
btn_layout.addWidget(self._skip_btn)
```

初期状態の反映と新規メソッド:
```python
self.on_mute = lambda: None

def _on_mute_click(self) -> None:
    self.on_mute()

def update_mute_state(self, is_muted: bool) -> None:
    self._mute_btn.setText("🔇" if is_muted else "🔊")
```

`__init__` でミュート初期状態を反映:
```python
if self._settings.behavior.is_muted:
    self._mute_btn.setText("🔇")
```

### 3. `main.py` — on_mute ハンドラ

```python
def toggle_mute() -> None:
    settings.behavior.is_muted = not settings.behavior.is_muted
    if settings.behavior.is_muted:
        bgm_svc.stop()
    settings_svc.save(settings)
    widget.update_mute_state(settings.behavior.is_muted)

widget.on_mute = toggle_mute
```

### 4. `sound_service.py` — ミュートガード

```python
def play(self) -> None:
    if not self._settings.notifications.sound_enabled:
        return
    if self._settings.behavior.is_muted:   # 追加
        return
    ...
```

### 5. `bgm_service.py` — ミュートガード

```python
def on_phase_changed(self, phase: Phase) -> None:
    self.stop()
    if self._settings.behavior.is_muted:   # 追加
        return
    bgm = self._settings.bgm
    ...
```
