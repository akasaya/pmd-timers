# Research: 通知音改善とマルチモニター対応

## 通知音: 現状の問題

### 根本原因

`NotificationService._send()` はデスクトップ通知（plyer / QSystemTrayIcon）のみを実装しており、**音声再生のコードが存在しない**。`AppSettings.notifications.sound_enabled = True` がデフォルトだが、音を再生する処理が未実装。

### 決定: PyQt6.QtMultimedia の QSoundEffect を使用

- **採用**: `PyQt6.QtMultimedia.QSoundEffect`
- **理由**:
  - 既存依存 `PyQt6` に含まれており追加ライブラリ不要
  - WAVファイルの低レイテンシ再生に最適化
  - `setLoopCount(1)` で単発再生、`stop()` で即時停止 → 5秒タイムアウト実装が容易
  - Windows/macOS/Linuxでクロスプラットフォーム動作
- **代替案**: `pygame.mixer` — 追加依存が必要、PyInstaller時に複雑化するため却下
- **代替案**: `winsound` — Windows専用のため却下
- **代替案**: `playsound` — 追加依存が必要、スレッドブロッキング問題があるため却下

### デフォルト音声ファイル

- **採用**: `assets/sounds/notification.wav`
  - ソース: OpenGameArt.org (https://opengameart.org/content/alertnotification-sound)
  - ライセンス: **CC0 (Public Domain)** — 帰属表示不要、商用利用可
  - 仕様: 1.03秒、48kHz、ステレオ、WAV PCM
  - 既にダウンロード済み: `assets/sounds/notification.wav`

### 5秒タイムアウト実装

```python
# QTimer で5秒後に stop() を呼ぶ
self._sound_timer = QTimer(self)
self._sound_timer.setSingleShot(True)
self._sound_timer.setInterval(5000)
self._sound_timer.timeout.connect(self._sound_effect.stop)
self._sound_effect.playingChanged.connect(self._on_playing_changed)

def play(self):
    self._sound_effect.play()
    self._sound_timer.start()

def _on_playing_changed(self, playing):
    if not playing:
        self._sound_timer.stop()  # 自然終了時はタイマーをキャンセル
```

### カスタム音声: 対応フォーマット

QSoundEffect は WAV のみ対応。カスタム音声も WAV に限定するか、QMediaPlayer（MP3/OGG対応）にフォールバックするか。

- **採用**: ファイル選択フィルターを `*.wav` のみにし、WAVを要件とする
- **理由**: QSoundEffect の方が低レイテンシで通知音に適している。フォーマット変換は実装コスト過大
- **代替案**: QMediaPlayer で全フォーマット対応 — 再生開始遅延が大きくなる可能性あり

---

## マルチモニター: 現状の問題

### 根本原因

`_clamp_to_screen()` が `QApplication.primaryScreen()` のみを参照しているため、プライマリディスプレイの範囲内にしかドラッグできない。

```python
# 現在のコード（問題箇所）
def _clamp_to_screen(self, pos: QPoint) -> QPoint:
    screen = QApplication.primaryScreen()  # ← プライマリのみ
    rect = screen.availableGeometry()
    ...
```

### 決定: QApplication.screens() で全ディスプレイの仮想矩形を算出

```python
def _clamp_to_screen(self, pos: QPoint) -> QPoint:
    # 全ディスプレイを包含する仮想矩形を計算
    virtual_rect = QRect()
    for screen in QApplication.screens():
        virtual_rect = virtual_rect.united(screen.availableGeometry())

    x = max(virtual_rect.left(), min(pos.x(), virtual_rect.right() - self.width()))
    y = max(virtual_rect.top(), min(pos.y(), virtual_rect.bottom() - self.height()))
    return QPoint(x, y)
```

- **採用**: 全スクリーンのunited矩形でクランプ
- **理由**: `QApplication.screens()` はPyQt6標準APIで追加依存なし。全ディスプレイを包含する矩形で自由にドラッグできる
- **代替案**: `QDesktopWidget` — PyQt6では非推奨のため却下
- **注意**: マルチモニター配置が非矩形（L字型等）の場合、ウィジェットが仮想矩形内の「隙間」に入る可能性があるが、一般的な使用ケースでは問題にならない

### 位置復元

`AppSettings.ui.window_x / window_y` に保存 → 復元時に全ディスプレイの仮想矩形内にあるか確認し、範囲外ならメインディスプレイにリセットする。

---

## まとめ: 修正対象ファイル・新規ファイル

| 項目 | ファイル | 変更内容 |
|------|---------|---------|
| デフォルト音声 | `assets/sounds/notification.wav` | 新規追加済み（CC0） |
| 音声再生サービス | `src/services/sound_service.py` | 新規作成 |
| 通知サービス連携 | `src/services/notification_service.py` | SoundServiceを呼び出す |
| 設定モデル | `src/engine/session.py` | `custom_sound_path` フィールド追加 |
| 設定ダイアログ | `src/ui/settings_dialog.py` | 音声ファイル選択・プレビューUI追加 |
| マルチモニター | `src/ui/timer_widget.py` | `_clamp_to_screen` を全スクリーン対応に |
| メイン | `src/main.py` | SoundServiceの初期化・接続 |
