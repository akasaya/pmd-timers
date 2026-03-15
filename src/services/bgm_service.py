"""BGM service: loops background music per Pomodoro phase."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QUrl

try:
    from PyQt6.QtMultimedia import QSoundEffect
    _MULTIMEDIA_AVAILABLE = True
except ImportError:
    _MULTIMEDIA_AVAILABLE = False

if TYPE_CHECKING:
    from src.engine.session import AppSettings

from src.engine.session import Phase


class BgmService(QObject):
    """Plays looping BGM for work and break phases.

    Uses QSoundEffect with infinite loop count and per-phase volume.
    If QtMultimedia is unavailable, all operations are silently skipped.
    """

    def __init__(self, settings: "AppSettings", parent=None):
        super().__init__(parent)
        self._settings = settings
        if _MULTIMEDIA_AVAILABLE:
            self._effect_work = QSoundEffect(self)
            self._effect_work.setLoopCount(-2)  # QSoundEffect::Infinite = -2
            self._effect_break = QSoundEffect(self)
            self._effect_break.setLoopCount(-2)  # QSoundEffect::Infinite = -2
            self._load_sources()
        else:
            self._effect_work = None
            self._effect_break = None

    # ── Sources ───────────────────────────────────────────────────────

    def _load_sources(self) -> None:
        if not _MULTIMEDIA_AVAILABLE:
            return
        bgm = self._settings.bgm
        self._set_source(self._effect_work, bgm.work_bgm_path, bgm.work_bgm_volume)
        self._set_source(self._effect_break, bgm.break_bgm_path, bgm.break_bgm_volume)

    @staticmethod
    def _set_source(effect: "QSoundEffect", path: str, volume: float) -> None:
        if effect is None:
            return
        effect.setVolume(max(0.0, min(1.0, volume)))
        if path and Path(path).exists():
            effect.setSource(QUrl.fromLocalFile(path))
        else:
            effect.setSource(QUrl())  # clear source — nothing to play

    # ── Playback ──────────────────────────────────────────────────────

    def on_phase_changed(self, phase: Phase) -> None:
        """Start or stop BGM according to the new phase."""
        self.stop()
        bgm = self._settings.bgm
        if phase == Phase.WORKING:
            if bgm.work_bgm_enabled and bgm.work_bgm_path and Path(bgm.work_bgm_path).exists():
                self._play(self._effect_work)
        elif phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            if bgm.break_bgm_enabled and bgm.break_bgm_path and Path(bgm.break_bgm_path).exists():
                self._play(self._effect_break)
        # PAUSED / IDLE → already stopped above

    @staticmethod
    def _play(effect) -> None:
        if effect is not None and effect.source().isValid():
            effect.play()

    def stop(self) -> None:
        """Stop all BGM immediately."""
        if self._effect_work is not None:
            self._effect_work.stop()
        if self._effect_break is not None:
            self._effect_break.stop()

    def reload(self) -> None:
        """Reload sources and volumes after settings change."""
        self.stop()
        self._load_sources()
