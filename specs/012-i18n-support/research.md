# Research: UIの多言語対応（i18n）

**Branch**: `012-i18n-support`
**Date**: 2026-03-16

## 翻訳アプローチの選定

### Decision: Pythonモジュール形式の辞書ベース翻訳

**Rationale**:
- Qt標準の `.ts`/`.qm` 方式は `pylupdate6`・`lrelease` 等の外部ツールが必要で環境依存が高い
- `gettext` は `.po`/`.mo` ファイルのコンパイル手順が必要
- アプリ規模（81文字列）に対して最もシンプルな選択肢は Python dict
- 言語ファイルを `src/locale/ja.py`・`src/locale/en.py` として管理し、キー文字列で参照する

**Alternatives considered**:
- `Qt Linguist (.ts/.qm)`: 本格的だが外部ツール依存、小規模アプリには過剰
- `gettext`: 標準的だが .po ファイルのコンパイルが必要
- `fluent-python`: Mozilla Fluent 形式、構文学習コストあり

---

## 翻訳対象文字列の全量

コードベース調査により、翻訳が必要なユーザー向けUI文字列を確認:

| ファイル | 文字列数 |
|---|---|
| timer_widget.py | 10 |
| settings_dialog.py | 30 |
| tray_icon.py | 4 |
| dashboard_window.py | 18 |
| notification_service.py | 8 |
| **合計** | **約70** |

---

## i18n サービス設計

### Decision: モジュールレベルシングルトン

```python
# src/services/i18n_service.py
_strings: dict[str, str] = {}

AUDIO_FILTER = "Audio files (*.wav *.mp3 *.ogg *.flac *.aac *.m4a *.opus);;All files (*)"

def init(language: str) -> None:
    global _strings
    if language == "en":
        from src.locale.en import STRINGS
    else:
        from src.locale.ja import STRINGS
    _strings = STRINGS

def t(key: str, **kwargs) -> str:
    s = _strings.get(key, key)
    if not kwargs:
        return s
    try:
        return s.format(**kwargs)
    except KeyError:
        return s
```

**Rationale**: モジュールレベルで `_strings` を保持するシングルトンパターン。
全UIファイルから `from src.services.i18n_service import t` でインポートするだけで使える。

---

## 設定スキーマへの変更

`AppSettings` に `GeneralSettings` を追加:

```python
@dataclass
class GeneralSettings:
    language: str = "ja"  # "ja" | "en"
```

`to_dict()` / `from_dict()` を更新して `general.language` を永続化。

---

## 翻訳キー命名規則

カテゴリプレフィックスで管理:

```
phase.idle / phase.working / phase.short_break / phase.long_break / phase.paused
widget.today_count / widget.menu.stats / widget.menu.settings / widget.menu.reset / widget.menu.quit
settings.title / settings.group.* / settings.label.* / settings.checkbox.* / settings.button.*
tray.show_widget / tray.dashboard / tray.settings / tray.quit
dashboard.title / dashboard.period.* / dashboard.stat.* / dashboard.chart.* / dashboard.session.*
notification.*
```

動的文字列（`今日: {count}`）は `t("widget.today_count", count=n)` のキーワード引数形式。

---

## 注意点

- `AUDIO_FILTER`（ファイル選択ダイアログのフィルター文字列）は翻訳不要のため定数として `i18n_service` に一元管理
- 言語変更は再起動後に反映（UIの即時 rebuild は対象外）
- 設定ダイアログの言語セレクタはネイティブ表記（`日本語`・`English`）
- `settings.suffix.minutes` は `" 分"` / `" min"` — QSpinBox の `setSuffix()` に使用
