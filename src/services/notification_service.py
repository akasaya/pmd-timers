"""Desktop notification service with plyer + QSystemTrayIcon fallback."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QSystemTrayIcon
    from src.services.sound_service import SoundService

from src.services.i18n_service import t

_PHASE_KEYS: dict[str, tuple[str, str]] = {
    "working_to_short_break": ("notification.work_done.title", "notification.work_done.msg_short"),
    "working_to_long_break": ("notification.long_milestone.title", "notification.work_done.msg_long"),
    "short_break_to_working": ("notification.break_done.title", "notification.break_done.msg"),
    "long_break_to_working": ("notification.long_break_done.title", "notification.long_break_done.msg"),
}


class NotificationService:
    def __init__(
        self,
        tray_icon: "QSystemTrayIcon | None" = None,
        sound_service: "SoundService | None" = None,
    ):
        self._tray = tray_icon
        self._sound = sound_service
        self._plyer_available = False
        try:
            import plyer  # noqa: F401
            self._plyer_available = True
        except ImportError:
            pass

    def notify_phase_change(self, from_phase: str, to_phase: str) -> None:
        key = f"{from_phase}_to_{to_phase}"
        title_key, msg_key = _PHASE_KEYS.get(
            key, ("notification.default.title", "notification.default.msg")
        )
        title, message = t(title_key), t(msg_key)
        if self._sound:
            self._sound.play()
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
