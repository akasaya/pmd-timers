"""Desktop notification service with plyer + QSystemTrayIcon fallback."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QSystemTrayIcon

_PHASE_MESSAGES = {
    "working_to_short_break": ("作業完了！", "5分間休憩しましょう 🎉"),
    "working_to_long_break": ("4セッション達成！", "15分間しっかり休憩を ✨"),
    "short_break_to_working": ("休憩終了", "次のセッションを始めましょう"),
    "long_break_to_working": ("長休憩終了", "リフレッシュできましたか？"),
}


class NotificationService:
    def __init__(self, tray_icon: "QSystemTrayIcon | None" = None):
        self._tray = tray_icon
        self._plyer_available = False
        try:
            import plyer  # noqa: F401
            self._plyer_available = True
        except ImportError:
            pass

    def notify_phase_change(self, from_phase: str, to_phase: str) -> None:
        key = f"{from_phase}_to_{to_phase}"
        title, message = _PHASE_MESSAGES.get(key, ("ポモドーロ", "フェーズが変わりました"))
        self._send(title, message)

    def _send(self, title: str, message: str) -> None:
        if self._plyer_available:
            try:
                import plyer
                plyer.notification.notify(
                    title=title,
                    message=message,
                    app_name="PomodoroTimer",
                    timeout=5,
                )
                return
            except Exception:
                pass
        if self._tray:
            from PyQt6.QtWidgets import QSystemTrayIcon
            self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 5000)
