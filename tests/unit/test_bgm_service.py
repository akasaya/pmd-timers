"""Unit tests for BgmService."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.engine.session import AppSettings, Phase


@pytest.fixture
def settings():
    return AppSettings()


@pytest.fixture
def settings_with_work_bgm(tmp_path):
    import wave, struct
    wav = tmp_path / "work.wav"
    with wave.open(str(wav), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(struct.pack("<h", 0) * 100)
    s = AppSettings()
    s.bgm.work_bgm_path = str(wav)
    s.bgm.work_bgm_enabled = True
    s.bgm.work_bgm_volume = 0.8
    return s


@pytest.fixture
def settings_with_break_bgm(tmp_path):
    import wave, struct
    wav = tmp_path / "break.wav"
    with wave.open(str(wav), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(struct.pack("<h", 0) * 100)
    s = AppSettings()
    s.bgm.break_bgm_path = str(wav)
    s.bgm.break_bgm_enabled = True
    return s


class TestBgmService:
    def test_work_bgm_disabled_does_not_play(self, settings):
        """on_phase_changed(WORKING) does nothing when work_bgm_enabled is False."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings)
        with patch.object(svc._effect_work, "play") as mock_play:
            svc.on_phase_changed(Phase.WORKING)
            mock_play.assert_not_called()

    def test_work_bgm_plays_on_working_phase(self, settings_with_work_bgm):
        """on_phase_changed(WORKING) calls play() on work effect when enabled."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings_with_work_bgm)
        with patch.object(svc._effect_work, "play") as mock_play:
            svc.on_phase_changed(Phase.WORKING)
            mock_play.assert_called_once()

    def test_break_bgm_plays_on_short_break(self, settings_with_break_bgm):
        """on_phase_changed(SHORT_BREAK) plays break BGM."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings_with_break_bgm)
        with patch.object(svc._effect_break, "play") as mock_play:
            svc.on_phase_changed(Phase.SHORT_BREAK)
            mock_play.assert_called_once()

    def test_break_bgm_plays_on_long_break(self, settings_with_break_bgm):
        """on_phase_changed(LONG_BREAK) plays break BGM."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings_with_break_bgm)
        with patch.object(svc._effect_break, "play") as mock_play:
            svc.on_phase_changed(Phase.LONG_BREAK)
            mock_play.assert_called_once()

    def test_stop_on_paused_phase(self, settings_with_work_bgm):
        """on_phase_changed(PAUSED) stops all BGM."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings_with_work_bgm)
        with patch.object(svc, "stop") as mock_stop:
            svc.on_phase_changed(Phase.PAUSED)
            mock_stop.assert_called()

    def test_stop_on_idle_phase(self, settings):
        """on_phase_changed(IDLE) stops all BGM."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings)
        with patch.object(svc, "stop") as mock_stop:
            svc.on_phase_changed(Phase.IDLE)
            mock_stop.assert_called()

    def test_reload_calls_load_sources(self, settings):
        """reload() reinitializes sound sources."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings)
        with patch.object(svc, "_load_sources") as mock_load:
            svc.reload()
            mock_load.assert_called_once()

    def test_work_bgm_volume_applied(self, settings_with_work_bgm):
        """Work BGM volume from settings is applied to the effect."""
        from src.services.bgm_service import BgmService
        svc = BgmService(settings_with_work_bgm)
        assert abs(svc._effect_work.volume() - 0.8) < 0.01
