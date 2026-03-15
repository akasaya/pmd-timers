"""Sound service for notification audio playback with 5-second timeout."""
from __future__ import annotations

import os
import tempfile
import wave
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


def _trim_wav(src: str, start_ms: int, end_ms: int) -> str | None:
    """Write a trimmed portion of a WAV file to a temp file.

    Returns the temp file path, or None on any error.
    end_ms == 0 means end of file.
    """
    try:
        with wave.open(src, "rb") as r:
            rate = r.getframerate()
            ch = r.getnchannels()
            sw = r.getsampwidth()
            total = r.getnframes()
            s_frame = min(int(start_ms / 1000 * rate), total)
            e_frame = min(int(end_ms / 1000 * rate), total) if end_ms > 0 else total
            if e_frame <= s_frame:
                return None
            r.setpos(s_frame)
            data = r.readframes(e_frame - s_frame)
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with wave.open(path, "wb") as w:
            w.setnchannels(ch)
            w.setsampwidth(sw)
            w.setframerate(rate)
            w.writeframes(data)
        return path
    except Exception:
        return None


class SoundService(QObject):
    """Plays notification sounds with automatic 5-second cutoff."""

    def __init__(self, settings: "AppSettings", parent=None):
        super().__init__(parent)
        self._settings = settings
        self._effect = QSoundEffect(self) if _MULTIMEDIA_AVAILABLE else None
        self._temp_wav: str | None = None  # temp file from last trim
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(_MAX_DURATION_MS)
        self._timeout.timeout.connect(self._stop_sound)
        if self._effect is not None:
            self._effect.playingChanged.connect(self._on_playing_changed)
            self._load_sound()

    # ── Internal helpers ───────────────────────────────────────────────

    def _raw_sound_path(self) -> str:
        """Return the configured (or default) WAV path without trimming."""
        path = self._settings.notifications.custom_sound_path
        if path and Path(path).exists():
            return path
        return str(_get_base_dir() / "assets" / "sounds" / "notification.wav")

    def _resolved_play_path(self) -> str:
        """Return path to play: trimmed temp file if start/end are set, else raw."""
        raw = self._raw_sound_path()
        start = self._settings.notifications.sound_start_ms
        end = self._settings.notifications.sound_end_ms
        if start == 0 and end == 0:
            return raw
        trimmed = _trim_wav(raw, start, end)
        if trimmed:
            self._cleanup_temp()
            self._temp_wav = trimmed
            return trimmed
        return raw

    def _cleanup_temp(self) -> None:
        if self._temp_wav and Path(self._temp_wav).exists():
            try:
                os.unlink(self._temp_wav)
            except Exception:
                pass
            self._temp_wav = None

    def _load_sound(self) -> None:
        """Set QSoundEffect source (non-Windows path only)."""
        if self._effect is None:
            return
        path = self._resolved_play_path()
        self._effect.setSource(QUrl.fromLocalFile(path))

    def _stop_sound(self) -> None:
        """Stop playback regardless of backend."""
        if self._effect is not None:
            self._effect.stop()
        import sys
        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_ASYNC)
            except Exception:
                pass

    # ── Public API ────────────────────────────────────────────────────

    def play(self) -> None:
        if not self._settings.notifications.sound_enabled:
            return
        import sys
        # On Windows prefer winsound — QSoundEffect requires multimedia
        # backend plugins not reliably bundled by PyInstaller.
        if sys.platform == "win32":
            self._play_winsound()
            duration_ms = self._clip_duration_ms()
            self._timeout.setInterval(min(duration_ms, _MAX_DURATION_MS))
            self._timeout.start()
            return
        # Non-Windows: reload source (handles start/end trim) then play
        self._load_sound()
        if self._effect is not None:
            duration_ms = self._clip_duration_ms()
            self._timeout.setInterval(min(duration_ms, _MAX_DURATION_MS))
            self._effect.play()
            self._timeout.start()
        else:
            self._play_fallback()

    def _clip_duration_ms(self) -> int:
        """Return playback clip length in ms (capped at _MAX_DURATION_MS)."""
        start = self._settings.notifications.sound_start_ms
        end = self._settings.notifications.sound_end_ms
        if end > 0 and end > start:
            return end - start
        # Try to get full file duration
        try:
            path = self._raw_sound_path()
            with wave.open(path, "rb") as w:
                duration_ms = int(w.getnframes() / w.getframerate() * 1000)
            return max(duration_ms - start, 100)
        except Exception:
            return _MAX_DURATION_MS

    def _play_winsound(self) -> None:
        sound_path = self._resolved_play_path()
        try:
            import winsound
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception:
            pass

    def _play_fallback(self) -> None:
        """Fallback sound using subprocess (macOS/Linux)."""
        import sys
        sound_path = self._resolved_play_path()
        try:
            if sys.platform == "darwin":
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
            self._cleanup_temp()
