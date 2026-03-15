# Implementation Plan: 通知音改善とマルチモニター対応

**Branch**: `007-sound-multimonitor` | **Date**: 2026-03-16 | **Spec**: [spec.md](./spec.md)

## Summary

通知音が未実装だった問題を `PyQt6.QtMultimedia.QSoundEffect` + CC0フリー音声ファイルで解決し、カスタム音声設定UIを追加する。マルチモニター対応は `_clamp_to_screen` を `QApplication.screens()` 全スクリーン対応に変更するだけで実現できる。

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: PyQt6 6.7+（QtMultimediaを追加使用）、plyer 2.1+
**Storage**: JSON設定ファイルに `custom_sound_path` フィールド追加
**Testing**: pytest
**Target Platform**: Windows 10/11（主要）、macOS/Linux（動作確認）
**Project Type**: デスクトップアプリ（PyQt6 GUIウィジェット）
**Performance Goals**: 通知音はセッション終了から100ms以内に再生開始
**Constraints**: 追加ライブラリ不要（PyQt6に同梱のQtMultimediaを使用）
**Scale/Scope**: 新規ファイル1件 + 既存4ファイルの修正

## Constitution Check

プロジェクト固有のConstitutionは未定義。一般原則:
- 既存テストが全てパスすること
- 追加ライブラリを増やさない（PyQt6のQtMultimediaで完結）
- 既存設定ファイル（JSON）との後方互換性維持

## Project Structure

### Documentation (this feature)

```text
specs/007-sound-multimonitor/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code（変更・追加対象）

```text
assets/
└── sounds/
    └── notification.wav      # CC0音声（追加済み）

src/
├── engine/
│   └── session.py            # NotificationSettingsにcustom_sound_path追加
├── services/
│   ├── sound_service.py      # 新規: QSoundEffect管理・5秒タイムアウト
│   └── notification_service.py  # SoundServiceを呼び出すよう修正
└── ui/
    ├── settings_dialog.py    # 音声ファイル選択・プレビューUI追加
    └── timer_widget.py       # _clamp_to_screen をマルチモニター対応に

src/main.py                   # SoundServiceの初期化・接続

tests/unit/
└── test_sound_service.py     # SoundService単体テスト
```

## 修正方針詳細

### 通知音 (SoundService)

```python
# src/services/sound_service.py
class SoundService(QObject):
    MAX_DURATION_MS = 5000

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._effect = QSoundEffect(self)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(self.MAX_DURATION_MS)
        self._timer.timeout.connect(self._effect.stop)
        self._load_sound()

    def _load_sound(self):
        path = self._settings.notifications.custom_sound_path
        if path and Path(path).exists():
            url = QUrl.fromLocalFile(path)
        else:
            # デフォルト音声
            default = Path(__file__).parent.parent.parent / "assets/sounds/notification.wav"
            url = QUrl.fromLocalFile(str(default))
        self._effect.setSource(url)

    def play(self):
        if not self._settings.notifications.sound_enabled:
            return
        self._effect.play()
        self._timer.start()
```

### マルチモニター (_clamp_to_screen)

```python
def _clamp_to_screen(self, pos: QPoint) -> QPoint:
    from PyQt6.QtCore import QRect
    virtual_rect = QRect()
    for screen in QApplication.screens():
        virtual_rect = virtual_rect.united(screen.availableGeometry())
    x = max(virtual_rect.left(), min(pos.x(), virtual_rect.right() - self.width()))
    y = max(virtual_rect.top(), min(pos.y(), virtual_rect.bottom() - self.height()))
    return QPoint(x, y)
```

### 設定モデル (NotificationSettings)

```python
@dataclass
class NotificationSettings:
    sound_enabled: bool = True
    desktop_notification_enabled: bool = True
    custom_sound_path: str = ""   # 追加: 空文字でデフォルト音を使用
```

### 設定ダイアログ (音声選択UI)

- 「通知音ファイル」行を追加
- 「参照」ボタン → QFileDialog（*.wav フィルター）
- 「プレビュー」ボタン → SoundServiceを一時的に呼び出して再生
- ファイルが5秒超の場合は「⚠ 5秒でカットされます」ラベルを表示

## 後方互換性

- `custom_sound_path` がJSONに存在しない（旧設定ファイル）場合は空文字でデフォルト
- `_clamp_to_screen` の変更は単画面環境でも同一動作（`screens()` が1件の場合は従来と同じ）
