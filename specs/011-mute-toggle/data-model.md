# Data Model: 音声ミュートトグル

**Branch**: `011-mute-toggle`
**Date**: 2026-03-16

## 既存エンティティの変更

### BehaviorSettings (`src/engine/session.py:106`)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `auto_start_next_session` | `bool` | `False` | 既存 |
| `is_muted` | `bool` | `False` | **追加** — 全音声ミュートのオン/オフ |

**永続化** (`to_dict`):
```python
"behavior": {
    "auto_start_next_session": ...,
    "is_muted": self.behavior.is_muted,   # 追加
}
```

**読み込み** (`from_dict`):
```python
BehaviorSettings(
    auto_start_next_session=b.get("auto_start_next_session", False),
    is_muted=b.get("is_muted", False),    # 追加
)
```

## UIバインディング（新規追加）

| UIウィジェット | 説明 |
|---|---|
| `_mute_btn: QToolButton` | `_pause_btn` と `_skip_btn` の間に配置。ミュートOFF: `"🔊"`、ミュートON: `"🔇"` |

## 処理フロー

```
ミュートON:
  settings.behavior.is_muted = True
  bgm_svc.stop()          # BGMを即時停止
  settings_svc.save()     # 永続化
  widget.update_mute_state(True)  # ボタンを 🔇 に変更

ミュートOFF:
  settings.behavior.is_muted = False
  settings_svc.save()     # 永続化
  widget.update_mute_state(False) # ボタンを 🔊 に変更
  # BGMは次のフェーズ切り替えで自然に再生される

通知音再生時（sound_service.play()）:
  if self._settings.behavior.is_muted: return  # ミュート中は再生しない

BGM再生時（bgm_service.on_phase_changed()）:
  if self._settings.behavior.is_muted: return  # ミュート中は再生しない
```
