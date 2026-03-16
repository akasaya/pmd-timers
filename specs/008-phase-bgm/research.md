# Research: フェーズ別BGM再生

## 1. WAVループ再生（PyQt6 / Windows）

### Decision: QSoundEffect.setLoopCount(-1) をプライマリとし、Windows exe では --collect-all PyQt6 でプラグインをバンドル

**Rationale**:
- `QSoundEffect` は `setLoopCount(QSoundEffect.Infinite)` / `-1` で無限ループをネイティブサポート
- `setVolume(0.0〜1.0)` で音量制御も可能
- 通知音で QSoundEffect が Windows exe でクラッシュした原因は `windowsmediafoundation` バックエンドプラグイン未同梱。`--collect-all PyQt6` を PyInstaller コマンドに追加することで解決できる

**Alternatives considered**:
- `winsound.PlaySound(SND_LOOP | SND_ASYNC)`: ループ可能だが音量制御不可。BGM では音量が重要なため不採用
- `subprocess` + `ffplay`/`vlc`: 外部ツール依存で配布困難
- `pygame.mixer`: 追加依存。QSoundEffect で足りるため不採用
- 振幅スケール済み temp WAV 作成: 複雑かつパフォーマンス懸念

**Fallback** (QtMultimedia インポート失敗時):
- BGM を無音でスキップ（クラッシュしない）
- 通知音と同じ import guard パターン

---

## 2. 音量制御

### Decision: QSoundEffect.setVolume(float) を使用。0.0〜1.0 の内部値で管理し、UI は 0〜100% スライダーで表示

**Rationale**:
- `QSoundEffect.setVolume()` は Qt6 でサポート済み
- winsound には音量 API がないが、BGM は QSoundEffect 専用とするため問題なし
- 作業用・休憩用で独立した音量値（デフォルト 50%）

---

## 3. フェーズ連携パターン

### Decision: engine.phase_changed シグナルに BgmService.on_phase_changed() を接続

**Rationale**:
- `engine.phase_changed` は全フェーズ遷移（WORKING / SHORT_BREAK / LONG_BREAK / PAUSED / IDLE など）で発火する
- PAUSED フェーズの検出も同シグナルで可能（Phase.PAUSED）
- 既存の `notification_service` と同じ接続パターンで一貫性を保てる

**Phase → BGM マッピング**:
- `Phase.WORKING` → work_bgm 再生
- `Phase.SHORT_BREAK` / `Phase.LONG_BREAK` → break_bgm 再生
- `Phase.PAUSED` / `Phase.IDLE` → BGM 停止

---

## 4. 設定データ構造

### Decision: AppSettings に BgmSettings dataclass を追加（work / break 分離）

**Rationale**:
- 既存 `NotificationSettings` と対称なフラット設計
- `to_dict` / `from_dict` による JSON 永続化（既存パターンと統一）

**フィールド**:
```
BgmSettings:
  work_bgm_path:    str   = ""     # 空=無効
  work_bgm_enabled: bool  = False
  work_bgm_volume:  float = 0.5    # 0.0〜1.0
  break_bgm_path:   str   = ""
  break_bgm_enabled: bool = False
  break_bgm_volume:  float = 0.5
```

---

## 5. PyInstaller バンドル対応

### Decision: --collect-all PyQt6 を追加

```powershell
pyinstaller --onefile --windowed --name "PomodoroTimer" `
  --add-data "assets/sounds/notification.wav;assets/sounds" `
  --collect-all PyQt6 `
  src/main.py
```

**注意**: `--collect-all PyQt6` はバイナリサイズが増加する（推定 +50〜100MB）。許容範囲内。
