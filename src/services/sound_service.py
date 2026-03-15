"""Sound service for notification audio playback with 5-second timeout."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QTimer, QUrl

try:
    from PyQt6.QtMultimedia import QSoundEffect
    _MULTIMEDIA_AVAILABLE = True
except ImportError:
    _MULTIMEDIA_AVAILABLE = False

if TYPE_CHECKING:
    from src.engine.session import AppSettings

def _get_base_dir() -> Path:
    """Return base directory, supporting both source and PyInstaller bundles."""
    import sys
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent.parent.parent


_DEFAULT_SOUND = _get_base_dir() / "assets" / "sounds" / "notification.wav"
_MAX_DURATION_MS = 5000


class SoundService(QObject):
    """Plays notification sounds with automatic 5-second cutoff."""

    def __init__(self, settings: "AppSettings", parent=None):
        super().__init__(parent)
        self._settings = settings
        self._effect = QSoundEffect(self) if _MULTIMEDIA_AVAILABLE else None
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(_MAX_DURATION_MS)
        if self._effect is not None:
            self._timeout.timeout.connect(self._effect.stop)
            self._effect.playingChanged.connect(self._on_playing_changed)
            self._load_sound()

    def _load_sound(self) -> None:
        if self._effect is None:
            return
        path = self._settings.notifications.custom_sound_path
        if path and Path(path).exists():
            source = QUrl.fromLocalFile(path)
        else:
            default = _get_base_dir() / "assets" / "sounds" / "notification.wav"
            source = QUrl.fromLocalFile(str(default))
        self._effect.setSource(source)

    def play(self) -> None:
        if not self._settings.notifications.sound_enabled:
            return
        import sys
        # On Windows prefer winsound (stdlib) — QSoundEffect requires
        # multimedia backend plugins that are not reliably bundled by PyInstaller.
        if sys.platform == "win32":
            self._play_fallback()
            return
        if self._effect is not None:
            self._effect.play()
            self._timeout.start()
        else:
            self._play_fallback()

    def _play_fallback(self) -> None:
        """Fallback sound using winsound (Windows) or subprocess (macOS/Linux)."""
        import sys
        sound_path = self._settings.notifications.custom_sound_path
        if not sound_path or not Path(sound_path).exists():
            sound_path = str(_DEFAULT_SOUND)
        try:
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["afplay", sound_path])
            else:
                import subprocess
                subprocess.Popen(["aplay", "-q", sound_path])
        except Exception:
            pass  # Sound is non-critical; never crash

    @staticmethod
    def default_sound_path() -> str:
        return str(_get_base_dir() / "assets" / "sounds" / "notification.wav")

    def reload(self) -> None:
        """Reload sound file after settings change."""
        if self._effect is not None:
            self._effect.stop()
        self._timeout.stop()
        self._load_sound()

    def _on_playing_changed(self, playing: bool) -> None:
        if not playing:
            self._timeout.stop()
