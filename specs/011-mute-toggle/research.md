# Research: 音声ミュートトグル

**Branch**: `011-mute-toggle`
**Date**: 2026-03-16

## コードベース調査結果

### 音声制御の現状

| サービス | ミュート関連の既存実装 |
|---|---|
| `sound_service.py:155` | `if not self._settings.notifications.sound_enabled: return` — 通知音の有効/無効チェックはここのみ |
| `bgm_service.py:87` | `if bgm.work_bgm_enabled and ...` — BGM再生条件チェック |
| `BehaviorSettings` | `is_muted` フラグなし（追加が必要） |

### ウィジェットボタン構造

`timer_widget.py:120-134`:
- `btn_layout`（QHBoxLayout）に `_start_btn` → `_pause_btn` → `_skip_btn` の順で追加
- `_start_btn` は IDLE/PAUSED 時のみ表示、`_pause_btn` は実行中のみ表示
- ミュートボタンは `_pause_btn` の後・`_skip_btn` の前に挿入する

---

## 実装アプローチ

### Decision: `BehaviorSettings.is_muted` フラグ + 各サービスの play/on_phase_changed で参照

**Rationale**:
- 既存の `sound_enabled` チェックパターン（`sound_service.py:155`）と同じ形で `is_muted` チェックを追加するだけ
- BGMは `on_phase_changed()` の先頭で `is_muted` をチェックし、True なら即 return
- ミュート有効化時はBGMを即時停止（`bgm_svc.stop()`）
- 解除時のBGMは自動再開しない（次フェーズ切り替えで自然に再生）

### ボタンアイコン

- ミュートOFF（通常）: `"🔊"`
- ミュートON: `"🔇"`

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `src/engine/session.py` | `BehaviorSettings.is_muted: bool = False` 追加、`to_dict`/`from_dict` 更新 |
| `src/ui/timer_widget.py` | `_mute_btn` 追加（pause と skip の間）、`on_mute` コールバック、`update_mute_state()` メソッド |
| `src/main.py` | `on_mute` ハンドラ実装（トグル → 保存 → サービス更新 → UI更新） |
| `src/services/sound_service.py` | `play()` に `if self._settings.behavior.is_muted: return` を追加 |
| `src/services/bgm_service.py` | `on_phase_changed()` に `if self._settings.behavior.is_muted: return` を追加 |
