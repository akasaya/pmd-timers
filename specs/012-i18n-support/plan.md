# Implementation Plan: UIの多言語対応（i18n）

**Branch**: `012-i18n-support` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-i18n-support/spec.md`

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
**Performance Goals**: N/A（起動時に一度辞書をロードするだけ）
**Constraints**: 言語変更は再起動後反映。外部ツール・依存ライブラリの追加なし
**Scale/Scope**: 翻訳文字列約81件、変更ファイル11件

## Constitution Check

Constitution は未設定のため、既存コードパターンとの整合性のみ確認:
- [x] 外部依存ライブラリを追加しない（標準 Python モジュールのみ）
- [x] 設定スキーマの変更は既存の `to_dict()` / `from_dict()` パターンに従う
- [x] 新規サービスは既存サービスと同じ構造（`src/services/`）

## Project Structure

### Documentation (this feature)

```text
specs/012-i18n-support/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
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

tests/
└── unit/
    └── test_i18n_service.py     # 新規: i18n_service ユニットテスト
```
