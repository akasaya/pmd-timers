# Implementation Plan: フェーズ別BGM再生

**Branch**: `008-phase-bgm` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-phase-bgm/spec.md`

## Summary

作業フェーズと休憩フェーズでそれぞれ別のWAVファイルをループ再生するBGM機能を追加する。`QSoundEffect.setLoopCount(-1)` で無限ループ、`setVolume()` で音量制御。フェーズ遷移シグナルに `BgmService` を接続し、設定ダイアログにBGM設定UI（ファイル選択・音量スライダー・プレビュー）を追加する。

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: PyQt6 6.7+（QtMultimedia: QSoundEffect）
**Storage**: JSON設定ファイル（既存 AppSettings に BgmSettings を追加）
**Testing**: pytest
**Target Platform**: Windows（exe） / Linux / macOS
**Project Type**: デスクトップアプリ（PyQt6 ウィジェット）
**Performance Goals**: フェーズ切り替えから 500ms 以内に BGM 切り替え完了
**Constraints**: BGMファイル不存在時クラッシュなし、QtMultimedia 未インストール環境でも起動可能
**Scale/Scope**: シングルユーザー、WAVファイル最大数十MB想定

## Constitution Check

constitution.md はプレースホルダーのため、プロジェクト既存規約に従う:
- ✅ 既存 `SoundService` パターンに倣った設計
- ✅ QtMultimedia を try/except でオプション化（未インストール環境対応）
- ✅ 設定は `AppSettings.to_dict` / `from_dict` で永続化
- ✅ 単体テストを追加

## Project Structure

### Documentation (this feature)

```text
specs/008-phase-bgm/
├── plan.md         ✅
├── research.md     ✅
├── data-model.md   ✅
├── quickstart.md   ✅
└── tasks.md        # /speckit.tasks で生成
```

### Source Code

```text
src/
├── engine/
│   └── session.py          # BgmSettings dataclass 追加、AppSettings に bgm フィールド追加
├── services/
│   ├── bgm_service.py      # 新規: BGMループ再生サービス
│   └── sound_service.py    # 変更なし
└── ui/
    └── settings_dialog.py  # BGM設定グループ追加（ファイル選択・音量・プレビュー×2）
src/main.py                 # BgmService 初期化・phase_changed 接続

tests/unit/
└── test_bgm_service.py     # 新規ユニットテスト
```

## 設計詳細

### BgmService の実装方針

```
BgmService(QObject):
  _effect_work:  QSoundEffect  # 作業用（LoopCount=-1）
  _effect_break: QSoundEffect  # 休憩用（LoopCount=-1）

  on_phase_changed(phase: Phase):
    WORKING           → stop_all() → play_work()
    SHORT/LONG_BREAK  → stop_all() → play_break()
    PAUSED / IDLE     → stop_all()

  reload():
    stop_all()
    load sources from settings
    update volumes
```

### 音量

- `QSoundEffect.setVolume(float)` : 0.0〜1.0
- UI スライダー: 0〜100（整数）→ 内部で `/100.0` 変換
- 作業用・休憩用独立

### QtMultimedia 未インストール時

```python
try:
    from PyQt6.QtMultimedia import QSoundEffect
    _MULTIMEDIA_AVAILABLE = True
except ImportError:
    _MULTIMEDIA_AVAILABLE = False
```

`_MULTIMEDIA_AVAILABLE = False` の場合 BgmService は何もしない（ログも出さない）

### フェーズ連携（main.py）

```python
bgm_svc = BgmService(settings, app)
engine.phase_changed.connect(
    lambda phase_val, idx: bgm_svc.on_phase_changed(Phase(phase_val))
)
# 設定変更後
bgm_svc.reload()
```

### 設定ダイアログ UI レイアウト

```
[BGM設定]
  作業中BGM:  [ファイル名ラベル] [参照] [▶]
              音量: [=======|===] 50%
              [✓ 作業中BGMを有効にする]

  休憩中BGM:  [ファイル名ラベル] [参照] [▶]
              音量: [=======|===] 50%
              [✓ 休憩中BGMを有効にする]
```
