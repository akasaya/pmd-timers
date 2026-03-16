# Quickstart: UIの多言語対応（i18n）

**Branch**: `012-i18n-support`

## 実装ガイド

### 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `src/locale/__init__.py` | 新規（空） |
| `src/locale/ja.py` | 新規: 日本語翻訳辞書 |
| `src/locale/en.py` | 新規: 英語翻訳辞書 |
| `src/services/i18n_service.py` | 新規: `init()` + `t()` + `AUDIO_FILTER` |
| `src/engine/session.py` | `GeneralSettings` 追加・`AppSettings` 更新 |
| `src/main.py` | `init_i18n(settings.general.language)` を起動時に追加 |
| `src/ui/timer_widget.py` | 全ハードコード文字列を `t()` で置換 |
| `src/ui/tray_icon.py` | 全ハードコード文字列を `t()` で置換 |
| `src/ui/settings_dialog.py` | 言語セレクタ追加 + 全文字列を `t()` で置換 |
| `src/ui/dashboard_window.py` | 全ハードコード文字列を `t()` で置換 |
| `src/services/notification_service.py` | `_PHASE_MESSAGES` を `t()` で置換 |

### 実装順序（依存関係）

1. **locale ファイル** (`ja.py`, `en.py`, `__init__.py`) — 依存なし
2. **i18n_service.py** — locale ファイルに依存
3. **session.py** — 独立して変更可能
4. **main.py** — session.py + i18n_service.py に依存
5. **UIファイル群** — i18n_service.py に依存（並列変更可）

### i18n_service の使い方

```python
# 起動時（main.py）
from src.services.i18n_service import init as init_i18n
init_i18n(settings.general.language)

# 各UIファイル
from src.services.i18n_service import t

# 静的文字列
label = t("phase.working")  # → "作業中" or "Working"

# 動的文字列
text = t("widget.today_count", count=5)  # → "今日: 5" or "Today: 5"

# スピンボックスのサフィックス
spin.setSuffix(t("settings.suffix.minutes"))  # → " 分" or " min"
```

### 設定ダイアログへの言語セレクタ追加

BGMグループの後に「一般設定」グループとして追加:

```python
from PyQt6.QtWidgets import QComboBox

general_group = QGroupBox(t("settings.group.general"))
general_form = QFormLayout()
self._lang_combo = QComboBox()
self._lang_combo.addItem("日本語", "ja")
self._lang_combo.addItem("English", "en")
idx = self._lang_combo.findData(self._settings.general.language)
self._lang_combo.setCurrentIndex(idx if idx >= 0 else 0)
general_form.addRow(t("settings.label.language"), self._lang_combo)
general_group.setLayout(general_form)
layout.addWidget(general_group)  # BGMグループの後に追加
```

`_apply()` に追加:
```python
self._settings.general.language = self._lang_combo.currentData()
```

`_reset()` に追加:
```python
self._lang_combo.setCurrentIndex(self._lang_combo.findData("ja"))
```

## テスト確認手順

1. `pytest tests/unit/test_i18n_service.py -v` でユニットテストがパス
2. 日本語起動: 全UI日本語、設定に言語セレクタ表示
3. English に変更 → 再起動 → 全UI英語
4. 日本語に戻す → 再起動 → 全UI日本語
