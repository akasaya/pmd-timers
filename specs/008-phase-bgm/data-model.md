# Data Model: フェーズ別BGM再生

## エンティティ

### BgmSettings (新規 dataclass)

`src/engine/session.py` の `AppSettings` に追加。

| フィールド         | 型      | デフォルト | 説明                         |
|--------------------|---------|------------|------------------------------|
| work_bgm_path      | str     | ""         | 作業用BGMファイルパス（空=無効） |
| work_bgm_enabled   | bool    | False      | 作業用BGM 有効フラグ          |
| work_bgm_volume    | float   | 0.5        | 作業用BGM 音量（0.0〜1.0）    |
| break_bgm_path     | str     | ""         | 休憩用BGMファイルパス（空=無効） |
| break_bgm_enabled  | bool    | False      | 休憩用BGM 有効フラグ          |
| break_bgm_volume   | float   | 0.5        | 休憩用BGM 音量（0.0〜1.0）    |

**バリデーションルール**:
- volume は 0.0〜1.0 にクランプ
- path が空またはファイル不存在の場合は再生をスキップ（エラーにしない）

**シリアライズ** (`to_dict` / `from_dict`):
```json
"bgm": {
  "work_bgm_path": "",
  "work_bgm_enabled": false,
  "work_bgm_volume": 0.5,
  "break_bgm_path": "",
  "break_bgm_enabled": false,
  "break_bgm_volume": 0.5
}
```

---

### BgmService (新規クラス)

`src/services/bgm_service.py`

| メソッド/属性             | 説明                                          |
|---------------------------|-----------------------------------------------|
| `__init__(settings, parent)` | QSoundEffect 初期化、設定読み込み          |
| `on_phase_changed(phase)`    | フェーズに応じてBGM開始/停止              |
| `stop()`                     | 現在再生中のBGMを停止                     |
| `reload()`                   | 設定変更後に音源を再読み込み              |
| `_play(path, volume)`        | 指定パス・音量でループ再生開始            |
| `_effect_work`               | 作業用 QSoundEffect インスタンス          |
| `_effect_break`              | 休憩用 QSoundEffect インスタンス          |

**フェーズ → BGM マッピング**:

| Phase          | 動作                    |
|----------------|-------------------------|
| WORKING        | work BGM ループ開始     |
| SHORT_BREAK    | break BGM ループ開始    |
| LONG_BREAK     | break BGM ループ開始    |
| PAUSED         | 全BGM 停止              |
| IDLE           | 全BGM 停止              |

---

### AppSettings への統合

`src/engine/session.py` に `bgm: BgmSettings = field(default_factory=BgmSettings)` を追加。
