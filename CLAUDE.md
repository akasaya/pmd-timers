# pmd-timers Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-15

## Active Technologies
- Python 3.12（004 と同一） + PyQt6 6.7+, PyQt6-Qt6-Charts 6.7+, plyer 2.1+ (005-compact-stats-dashboard)
- JSON ファイル（%APPDATA%\pmd-timers\history\） (005-compact-stats-dashboard)
- N/A（このフィーチャーではデータ変更なし） (006-fix-ui-bugs)
- Python 3.12 + PyQt6 6.7+（QtMultimediaを追加使用）、plyer 2.1+ (007-sound-multimonitor)
- JSON設定ファイルに `custom_sound_path` フィールド追加 (007-sound-multimonitor)
- Python 3.12 + PyQt6 6.7+（QtMultimedia: QSoundEffect） (008-phase-bgm)
- JSON設定ファイル（既存 AppSettings に BgmSettings を追加） (008-phase-bgm)
- Python 3.12 + PyQt6 6.7+（QCheckBox, QFormLayout） (009-auto-resume-work)
- JSON設定ファイル（既存スキーマ変更なし） (009-auto-resume-work)
- Python 3.12 + PyQt6 6.7+（QComboBox追加） (010-i18n-support)
- JSON設定ファイル（`general.language` フィールド追加） (010-i18n-support)
- Python 3.12 + PyQt6 6.7+（既存 QToolButton を流用） (011-mute-toggle)
- JSON設定ファイル（`behavior.is_muted` フィールド追加） (011-mute-toggle)

- Python 3.12 + PyQt6 6.7+, plyer 2.1+, PyInstaller 6.x（パッケージング用） (004-desktop-pomodoro-timer)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 011-mute-toggle: Added Python 3.12 + PyQt6 6.7+（既存 QToolButton を流用）
- 010-i18n-support: Added Python 3.12 + PyQt6 6.7+（QComboBox追加）
- 009-auto-resume-work: Added Python 3.12 + PyQt6 6.7+（QCheckBox, QFormLayout）


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
