"""BGM service: loops background music per Pomodoro phase."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QUrl

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
    _MULTIMEDIA_AVAILABLE = True
except ImportError:
    _MULTIMEDIA_AVAILABLE = False

if TYPE_CHECKING:
    from src.engine.session import AppSettings

from src.engine.session import Phase

# QMediaPlayer.Infinite = -1 (loops forever)
_INFINITE = -1


class _Player:
    """Wrapper around QMediaPlayer + QAudioOutput for one BGM track."""

    def __init__(self, parent: QObject) -> None:
        if not _MULTIMEDIA_AVAILABLE:
            self._player = None
            self._audio = None
            return
        self._player = QMediaPlayer(parent)
        self._audio = QAudioOutput(parent)
        self._player.setAudioOutput(self._audio)
        self._player.setLoops(_INFINITE)

    def set_source(self, path: str, volume: float) -> None:
        if self._player is None:
            return
        self._audio.setVolume(max(0.0, min(1.0, volume)))
        if path and Path(path).exists():
            self._player.setSource(QUrl.fromLocalFile(path))
        else:
            self._player.setSource(QUrl())

    def play(self) -> None:
        if self._player is not None and self._player.source().isValid():
            self._player.play()

    def stop(self) -> None:
        if self._player is not None:
            self._player.stop()

    def set_volume(self, volume: float) -> None:
        if self._audio is not None:
            self._audio.setVolume(max(0.0, min(1.0, volume)))


class BgmService(QObject):
    """Plays looping BGM for work and break phases.

    Uses QMediaPlayer (supports WAV / MP3 / OGG / FLAC / AAC / M4A etc.)
    If QtMultimedia is unavailable, all operations are silently skipped.
    """

    def __init__(self, settings: "AppSettings", parent=None):
        super().__init__(parent)
        self._settings = settings
        self._work = _Player(self)
        self._break = _Player(self)
        self._load_sources()

    # ── Sources ───────────────────────────────────────────────────────

    def _load_sources(self) -> None:
        bgm = self._settings.bgm
        self._work.set_source(bgm.work_bgm_path, bgm.work_bgm_volume)
        self._break.set_source(bgm.break_bgm_path, bgm.break_bgm_volume)

    # ── Playback ──────────────────────────────────────────────────────

    def on_phase_changed(self, phase: Phase) -> None:
        """Start or stop BGM according to the new phase."""
        self.stop()
        if self._settings.behavior.is_muted:
            return
        bgm = self._settings.bgm
        if phase == Phase.WORKING:
            if bgm.work_bgm_enabled and bgm.work_bgm_path and Path(bgm.work_bgm_path).exists():
                self._work.play()
        elif phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            if bgm.break_bgm_enabled and bgm.break_bgm_path and Path(bgm.break_bgm_path).exists():
                self._break.play()
        # PAUSED / IDLE → already stopped above

    def stop(self) -> None:
        """Stop all BGM immediately."""
        self._work.stop()
        self._break.stop()

    def reload(self) -> None:
        """Reload sources and volumes after settings change."""
        self.stop()
        self._load_sources()
