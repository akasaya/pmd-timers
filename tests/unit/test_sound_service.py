"""Unit tests for SoundService."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.engine.session import AppSettings


@pytest.fixture
def settings():
    return AppSettings()


@pytest.fixture
def settings_sound_off():
    s = AppSettings()
    s.notifications.sound_enabled = False
    return s


class TestSoundService:
    def test_play_skipped_when_sound_disabled(self, settings_sound_off):
        """play() does nothing when sound_enabled is False."""
        from src.services.sound_service import SoundService
        svc = SoundService(settings_sound_off)
        with patch.object(svc._effect, "play") as mock_play:
            svc.play()
            mock_play.assert_not_called()

    def test_play_called_when_sound_enabled(self, settings):
        """play() triggers QSoundEffect.play() when sound_enabled is True."""
        from src.services.sound_service import SoundService
        svc = SoundService(settings)
        with patch.object(svc._effect, "play") as mock_play:
            svc.play()
            mock_play.assert_called_once()

    def test_fallback_to_default_when_custom_path_empty(self, settings, tmp_path):
        """Empty custom_sound_path uses default bundled sound."""
        from src.services.sound_service import SoundService, _DEFAULT_SOUND
        settings.notifications.custom_sound_path = ""
        svc = SoundService(settings)
        assert svc._effect.source().toLocalFile() == str(_DEFAULT_SOUND)

    def test_fallback_to_default_when_custom_path_invalid(self, settings):
        """Non-existent custom_sound_path falls back to default."""
        from src.services.sound_service import SoundService, _DEFAULT_SOUND
        settings.notifications.custom_sound_path = "/nonexistent/sound.wav"
        svc = SoundService(settings)
        assert svc._effect.source().toLocalFile() == str(_DEFAULT_SOUND)

    def test_custom_path_used_when_valid(self, settings, tmp_path):
        """Valid custom_sound_path is used as source."""
        import wave, struct
        # Create minimal valid WAV
        wav_path = tmp_path / "test.wav"
        with wave.open(str(wav_path), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(struct.pack("<h", 0) * 100)

        from src.services.sound_service import SoundService
        settings.notifications.custom_sound_path = str(wav_path)
        svc = SoundService(settings)
        assert svc._effect.source().toLocalFile() == str(wav_path)

    def test_reload_reloads_source(self, settings):
        """reload() reinitializes sound source."""
        from src.services.sound_service import SoundService
        svc = SoundService(settings)
        with patch.object(svc, "_load_sound") as mock_load:
            svc.reload()
            mock_load.assert_called_once()
