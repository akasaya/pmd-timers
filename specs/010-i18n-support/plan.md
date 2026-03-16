# Implementation Plan: UIの多言語対応（i18n）

**Branch**: `010-i18n-support` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-i18n-support/spec.md`

## Summary

設定ダイアログに言語選択（日本語・English）を追加し、Pythonモジュール形式の辞書ベース翻訳システムを実装する。
起動時に `i18n_service.init(language)` を呼び出し、全UIコンポーネントがモジュールレベルの `t(key)` 関数経由で文字列を取得する。言語変更は再起動後に反映される。

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: PyQt6 6.7+（QComboBox追加）
**Storage**: JSON設定ファイル（`general.language` フィールド追加）
**Testing**: pytest
**Target Platform**: Windows/Linux デスクトップ
**Project Type**: Desktop app
**Performance Goals**: N/A
**Constraints**: 言語変更は再起動後反映。外部ツール・依存ライブラリの追加なし
**Scale/Scope**: 翻訳文字列約81件、変更ファイル11件

## Constitution Check

Constitution未設定のため、既存コードパターンとの整合性のみ確認:
- [x] 外部依存ライブラリを追加しない（標準Pythonモジュールのみ）
- [x] 設定スキーマの変更は既存の `to_dict()` / `from_dict()` パターンに従う
- [x] 新規サービスは既存サービスと同じ構造（`src/services/`）

## Project Structure

### Documentation (this feature)

```text
specs/010-i18n-support/
├── plan.md
├── research.md
├── data-model.md
└── tasks.md
```

### Source Code

```text
src/
├── locale/
│   ├── __init__.py        # 新規
│   ├── ja.py              # 新規: 日本語翻訳辞書
│   └── en.py              # 新規: 英語翻訳辞書
├── services/
│   └── i18n_service.py    # 新規: 翻訳サービス
├── engine/
│   └── session.py         # 変更: GeneralSettings追加、AppSettings更新
├── main.py                # 変更: i18n_service.init() を起動時に呼ぶ
└── ui/
    ├── settings_dialog.py  # 変更: 言語セレクタ追加 + 全文字列をt()で参照
    ├── timer_widget.py     # 変更: 全文字列をt()で参照
    ├── tray_icon.py        # 変更: 全文字列をt()で参照
    └── dashboard_window.py # 変更: 全文字列をt()で参照

src/services/
    └── notification_service.py  # 変更: 全文字列をt()で参照
```

## i18n サービス設計

```python
# src/services/i18n_service.py
_strings: dict[str, str] = {}

def init(language: str) -> None:
    global _strings
    if language == "en":
        from src.locale.en import STRINGS
    else:
        from src.locale.ja import STRINGS
    _strings = STRINGS

def t(key: str, **kwargs) -> str:
    s = _strings.get(key, key)
    return s.format(**kwargs) if kwargs else s
```

## 設定スキーマ変更

`src/engine/session.py` に追加:
```python
@dataclass
class GeneralSettings:
    language: str = "ja"
```

`AppSettings.to_dict()` に追加:
```python
"general": {"language": self.general.language}
```

`AppSettings.from_dict()` に追加:
```python
g = data.get("general", {})
general=GeneralSettings(language=g.get("language", "ja"))
```

## 設定ダイアログへの言語セレクタ追加

「ウィジェット設定」グループの先頭（作業中BGMグループの後）に「一般設定」グループとして追加:

```python
general_group = QGroupBox(t("settings.group.general"))
general_form = QFormLayout()
self._lang_combo = QComboBox()
self._lang_combo.addItem("日本語", "ja")
self._lang_combo.addItem("English", "en")
current_lang = self._settings.general.language
idx = self._lang_combo.findData(current_lang)
self._lang_combo.setCurrentIndex(idx)
general_form.addRow(t("settings.label.language"), self._lang_combo)
```

`_apply()` に追加:
```python
self._settings.general.language = self._lang_combo.currentData()
```

`_reset()` に追加:
```python
self._lang_combo.setCurrentIndex(self._lang_combo.findData("ja"))
```

## Testing Strategy

- `t()` 関数のユニットテスト: 既知のキーで正しい文字列を返す、未知のキーはキー名自体を返す
- 動的フォーマット: `t("widget.today_count", count=5)` → `"Today: 5"`（English）
- `GeneralSettings` の永続化: `to_dict()` / `from_dict()` のラウンドトリップ
