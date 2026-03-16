# Data Model: UIの多言語対応（i18n）

**Branch**: `010-i18n-support`
**Date**: 2026-03-16

## 新規エンティティ

### GeneralSettings (`src/engine/session.py` に追加)

| フィールド | 型 | デフォルト | 説明 |
|---|---|---|---|
| `language` | `str` | `"ja"` | 選択言語コード。`"ja"` または `"en"` |

`AppSettings` に `general: GeneralSettings` フィールドとして追加。
`to_dict()` → `"general": {"language": "ja"}` / `from_dict()` で読み込み。

---

## 新規ファイル

### `src/locale/ja.py` — 日本語翻訳辞書

```python
STRINGS: dict[str, str] = {
    # フェーズ名
    "phase.idle": "待機中",
    "phase.working": "作業中",
    "phase.short_break": "短休憩",
    "phase.long_break": "長休憩",
    "phase.paused": "一時停止",
    # ウィジェット
    "widget.today_count": "今日: {count}",
    "widget.menu.stats": "統計を見る",
    "widget.menu.settings": "設定",
    "widget.menu.reset": "リセット",
    "widget.menu.quit": "終了",
    # 設定ダイアログ
    "settings.title": "設定",
    "settings.group.timer": "タイマー設定",
    "settings.group.widget": "ウィジェット設定",
    "settings.group.bgm": "BGM設定",
    "settings.group.general": "一般設定",
    "settings.label.work_duration": "作業時間:",
    "settings.label.short_break": "短休憩:",
    "settings.label.long_break": "長休憩:",
    "settings.label.sessions_before_long": "長休憩までのセッション数:",
    "settings.label.opacity": "不透明度（表示の濃さ）:",
    "settings.label.opacity_hint": "100%=くっきり / 20%=うっすら",
    "settings.label.sound_file": "通知音ファイル:",
    "settings.label.sound_warn": "⚠ 5秒でカットされます",
    "settings.label.sound_start": "開始位置:",
    "settings.label.sound_end": "終了位置:",
    "settings.label.sound_default": "デフォルト（notification.wav）",
    "settings.label.work_bgm": "作業中BGM:",
    "settings.label.break_bgm": "休憩中BGM:",
    "settings.label.volume": "音量:",
    "settings.label.bgm_unset": "未設定",
    "settings.label.language": "言語:",
    "settings.checkbox.hover_buttons": "ホバー時のみ操作ボタンを表示",
    "settings.checkbox.always_on_top": "常に最前面に表示",
    "settings.checkbox.sound_enabled": "通知音を鳴らす",
    "settings.checkbox.desktop_notify": "デスクトップ通知を表示",
    "settings.checkbox.auto_start": "休憩終了後に次の作業を自動スタート",
    "settings.checkbox.work_bgm_enabled": "作業中BGMを有効にする",
    "settings.checkbox.break_bgm_enabled": "休憩中BGMを有効にする",
    "settings.button.browse": "参照",
    "settings.button.reset": "デフォルトに戻す",
    "settings.dialog.sound_title": "通知音ファイルを選択",
    "settings.dialog.work_bgm_title": "作業中BGMファイルを選択",
    "settings.dialog.break_bgm_title": "休憩中BGMファイルを選択",
    # audio_filter は翻訳不要 → i18n_service.AUDIO_FILTER 定数として管理（下記参照）
    "settings.suffix.minutes": " 分",
    # トレイ
    "tray.show_widget": "ウィジェットを表示",
    "tray.dashboard": "ダッシュボード",
    "tray.settings": "設定",
    "tray.quit": "終了",
    # ダッシュボード
    "dashboard.title": "統計ダッシュボード",
    "dashboard.period.label": "期間:",
    "dashboard.period.today": "今日",
    "dashboard.period.week": "今週",
    "dashboard.period.month": "今月",
    "dashboard.stat.completed": "完了セッション",
    "dashboard.stat.work_time": "作業時間",
    "dashboard.stat.breaks": "休憩回数",
    "dashboard.stat.streak": "連続達成日数",
    "dashboard.stat.streak_unit": "{count}日",
    "dashboard.chart.title": "セッション推移",
    "dashboard.chart.best": "最多: {date} ({count}セッション)  |  期間合計: {total}セッション",
    "dashboard.no_data": "まだデータがありません",
    "dashboard.detail.title": "セッション詳細",
    "dashboard.detail.no_records": "セッション記録なし",
    "dashboard.session.work": "作業",
    "dashboard.session.short_break": "短休憩",
    "dashboard.session.long_break": "長休憩",
    "dashboard.today.title": "本日の記録",
    # 通知
    "notification.work_done.title": "作業完了！",
    "notification.work_done.msg_short": "5分間休憩しましょう 🎉",
    "notification.work_done.msg_long": "15分間しっかり休憩を ✨",
    "notification.long_milestone.title": "4セッション達成！",
    "notification.break_done.title": "休憩終了",
    "notification.break_done.msg": "次のセッションを始めましょう",
    "notification.long_break_done.title": "長休憩終了",
    "notification.long_break_done.msg": "リフレッシュできましたか？",
    "notification.default.title": "ポモドーロ",
    "notification.default.msg": "フェーズが変わりました",
}
```

### `src/locale/en.py` — 英語翻訳辞書（同じキー、英語値）

```python
STRINGS: dict[str, str] = {
    "phase.idle": "Idle",
    "phase.working": "Working",
    "phase.short_break": "Short Break",
    "phase.long_break": "Long Break",
    "phase.paused": "Paused",
    "widget.today_count": "Today: {count}",
    "widget.menu.stats": "Statistics",
    "widget.menu.settings": "Settings",
    "widget.menu.reset": "Reset",
    "widget.menu.quit": "Quit",
    "settings.title": "Settings",
    "settings.group.timer": "Timer",
    "settings.group.widget": "Widget",
    "settings.group.bgm": "Background Music",
    "settings.group.general": "General",
    "settings.label.work_duration": "Work Duration:",
    "settings.label.short_break": "Short Break:",
    "settings.label.long_break": "Long Break:",
    "settings.label.sessions_before_long": "Sessions Before Long Break:",
    "settings.label.opacity": "Opacity:",
    "settings.label.opacity_hint": "100%=opaque / 20%=transparent",
    "settings.label.sound_file": "Notification Sound:",
    "settings.label.sound_warn": "⚠ Trimmed to 5 seconds",
    "settings.label.sound_start": "Start:",
    "settings.label.sound_end": "End:",
    "settings.label.sound_default": "Default (notification.wav)",
    "settings.label.work_bgm": "Work BGM:",
    "settings.label.break_bgm": "Break BGM:",
    "settings.label.volume": "Volume:",
    "settings.label.bgm_unset": "Not set",
    "settings.label.language": "Language:",
    "settings.checkbox.hover_buttons": "Show buttons on hover only",
    "settings.checkbox.always_on_top": "Always on top",
    "settings.checkbox.sound_enabled": "Enable notification sound",
    "settings.checkbox.desktop_notify": "Show desktop notification",
    "settings.checkbox.auto_start": "Auto-start work after break",
    "settings.checkbox.work_bgm_enabled": "Enable work BGM",
    "settings.checkbox.break_bgm_enabled": "Enable break BGM",
    "settings.button.browse": "Browse",
    "settings.button.reset": "Reset to Defaults",
    "settings.dialog.sound_title": "Select Notification Sound",
    "settings.dialog.work_bgm_title": "Select Work BGM",
    "settings.dialog.break_bgm_title": "Select Break BGM",
    # audio_filter は翻訳不要 → i18n_service.AUDIO_FILTER 定数として管理（下記参照）
    "settings.suffix.minutes": " min",
    "tray.show_widget": "Show Widget",
    "tray.dashboard": "Dashboard",
    "tray.settings": "Settings",
    "tray.quit": "Quit",
    "dashboard.title": "Statistics",
    "dashboard.period.label": "Period:",
    "dashboard.period.today": "Today",
    "dashboard.period.week": "This Week",
    "dashboard.period.month": "This Month",
    "dashboard.stat.completed": "Completed",
    "dashboard.stat.work_time": "Work Time",
    "dashboard.stat.breaks": "Breaks",
    "dashboard.stat.streak": "Streak",
    "dashboard.stat.streak_unit": "{count}d",
    "dashboard.chart.title": "Session Trend",
    "dashboard.chart.best": "Best: {date} ({count} sessions)  |  Total: {total} sessions",
    "dashboard.no_data": "No data yet",
    "dashboard.detail.title": "Session Details",
    "dashboard.detail.no_records": "No sessions recorded",
    "dashboard.session.work": "Work",
    "dashboard.session.short_break": "Short Break",
    "dashboard.session.long_break": "Long Break",
    "dashboard.today.title": "Today",
    "notification.work_done.title": "Session Complete!",
    "notification.work_done.msg_short": "Take a 5-minute break 🎉",
    "notification.work_done.msg_long": "Time for a 15-minute break ✨",
    "notification.long_milestone.title": "4 Sessions Done!",
    "notification.break_done.title": "Break Over",
    "notification.break_done.msg": "Ready to start the next session?",
    "notification.long_break_done.title": "Long Break Over",
    "notification.long_break_done.msg": "Feeling refreshed?",
    "notification.default.title": "Pomodoro",
    "notification.default.msg": "Phase changed",
}
```
