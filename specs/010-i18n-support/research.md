# Research: UIの多言語対応（i18n）

**Branch**: `010-i18n-support`
**Date**: 2026-03-16

## 翻訳対象文字列の全量

コードベース調査により、翻訳が必要なユーザー向けUI文字列を81件確認。

| ファイル | 文字列数 |
|---|---|
| timer_widget.py | 15 |
| settings_dialog.py | 36 |
| tray_icon.py | 5 |
| dashboard_window.py | 20 |
| notification_service.py | 10 |
| **合計** | **86（重複含む）** |

---

## 実装アプローチの選定

### Decision: Pythonモジュール形式の辞書ベース翻訳

**Rationale**:
- Qt標準の `.ts`/`.qm` 方式は `pylupdate6`・`lrelease` などの外部ツールが必要で環境依存が高い
- `gettext` は `.po`/.`mo` ファイルのコンパイル手順が必要
- アプリ規模（81文字列）に対して最もシンプルな選択肢は Python dict
- 言語ファイルを `src/locale/ja.py`・`src/locale/en.py` として管理し、キー文字列で参照する

**Alternatives considered**:
- `Qt Linguist (.ts/.qm)`: 本格的だが外部ツール依存、小規模アプリには過剰
- `gettext`: 標準的だが .po ファイルのコンパイルが必要
- `fluent-python`: Mozilla Fluent 形式、構文学習コストあり

---

## 翻訳キー設計

カテゴリプレフィックスで管理:

```
phase.idle / phase.working / phase.short_break / phase.long_break / phase.paused
widget.today_count / widget.start / widget.pause / widget.skip
widget.menu.stats / widget.menu.settings / widget.menu.reset / widget.menu.quit
settings.title / settings.group.timer / settings.group.widget / settings.group.bgm
settings.label.* / settings.checkbox.* / settings.button.*
tray.show / tray.dashboard / tray.settings / tray.quit
dashboard.title / dashboard.period.* / dashboard.stat.* / dashboard.label.*
notification.work_done.title / notification.work_done.msg / ...
```

---

## i18n サービス設計

`src/services/i18n_service.py` にモジュールレベルのシングルトン:

```python
_strings: dict[str, str] = {}

def init(language: str) -> None:
    """アプリ起動時に一度だけ呼ぶ"""
    ...

def t(key: str, **kwargs) -> str:
    """翻訳文字列を返す。未定義キーはキー文字列自体を返す"""
    s = _strings.get(key, key)
    return s.format(**kwargs) if kwargs else s
```

`**kwargs` で動的フォーマット（`t("dashboard.best_day", date=d, count=n)`）に対応。

---

## 設定スキーマへの追加

`AppSettings` に `GeneralSettings` を追加:

```python
@dataclass
class GeneralSettings:
    language: str = "ja"  # "ja" | "en"

class AppSettings:
    general: GeneralSettings = field(default_factory=GeneralSettings)
    ...
```

`to_dict()` / `from_dict()` を更新し `general.language` を永続化。

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `src/engine/session.py` | `GeneralSettings` 追加、`AppSettings` 更新 |
| `src/services/i18n_service.py` | 新規: 翻訳サービス |
| `src/locale/__init__.py` | 新規 |
| `src/locale/ja.py` | 新規: 日本語翻訳辞書 |
| `src/locale/en.py` | 新規: 英語翻訳辞書 |
| `src/main.py` | 起動時に `i18n_service.init(language)` を呼ぶ |
| `src/ui/settings_dialog.py` | 言語選択UI追加 + 全文字列を `t()` で参照 |
| `src/ui/timer_widget.py` | 全文字列を `t()` で参照 |
| `src/ui/tray_icon.py` | 全文字列を `t()` で参照 |
| `src/ui/dashboard_window.py` | 全文字列を `t()` で参照 |
| `src/services/notification_service.py` | 全文字列を `t()` で参照 |

---

## 注意点

- 動的文字列（`今日: {count}`・`{count}日`・`最多: {date}...`）は `t(key, count=n)` 形式で対応
- 言語変更は再起動後に反映（UIの `rebuild` は対象外）
- 設定ダイアログの言語セレクタは言語名をネイティブ表記で表示（`日本語`・`English`）
