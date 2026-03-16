"""Sound service for notification audio playback with 5-second timeout."""
from __future__ import annotations

import os
import tempfile
import wave
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QTimer, QUrl

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer, QSoundEffect
    _MULTIMEDIA_AVAILABLE = True
except ImportError:
    _MULTIMEDIA_AVAILABLE = False

_WAV_SUFFIXES = {".wav"}
_AUDIO_SUFFIXES = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".opus"}


def _is_wav(path: str) -> bool:
    return Path(path).suffix.lower() in _WAV_SUFFIXES

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
        # QMediaPlayer for non-WAV formats (MP3, OGG, FLAC, AAC, ...)
        if _MULTIMEDIA_AVAILABLE:
            self._media_player = QMediaPlayer(self)
            self._media_audio = QAudioOutput(self)
            self._media_player.setAudioOutput(self._media_audio)
            self._media_audio.setVolume(1.0)
        else:
            self._media_player = None
            self._media_audio = None
        self._temp_wav: str | None = None  # temp file from last trim
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.setInterval(_MAX_DURATION_MS)
        self._timeout.timeout.connect(self._on_playback_finished)
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
        if self._media_player is not None:
            self._media_player.stop()
        import sys
        if sys.platform == "win32":
            try:
                import winsound
                winsound.PlaySound(None, winsound.SND_ASYNC)
            except Exception:
                pass

    def _on_playback_finished(self) -> None:
        """Called on timeout: stop sound and clean up any temp WAV file."""
        self._stop_sound()
        self._cleanup_temp()

    # ── Public API ────────────────────────────────────────────────────

    def play(self) -> None:
        if not self._settings.notifications.sound_enabled:
            return
        import sys
        path = self._raw_sound_path()
        duration_ms = self._clip_duration_ms()
        timeout = min(duration_ms, _MAX_DURATION_MS)
        self._timeout.setInterval(timeout)

        if not _is_wav(path):
            # Non-WAV: use QMediaPlayer (supports MP3/OGG/FLAC/AAC etc.)
            if self._media_player is not None:
                self._media_player.setSource(QUrl.fromLocalFile(path))
                self._media_player.play()
                self._timeout.start()
            return

        # WAV path: winsound on Windows, QSoundEffect elsewhere
        if sys.platform == "win32":
            self._play_winsound()
            self._timeout.start()
            return
        self._load_sound()
        if self._effect is not None:
            self._effect.play()
            self._timeout.start()
        else:
            self._play_fallback()
            self._timeout.start()

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
        self._stop_sound()
        self._timeout.stop()
        self._cleanup_temp()
        self._load_sound()

    def _on_playing_changed(self, playing: bool) -> None:
        if not playing:
            self._timeout.stop()
            self._cleanup_temp()
