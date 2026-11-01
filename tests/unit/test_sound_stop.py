"""Notification cleanup for mute, preview close, and timeout."""

from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QApplication

from src.engine.session import AppSettings
from src.services.sound_service import SoundService


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def test_stop_cancels_timeout_and_all_backends(app, tmp_path):
    service = SoundService(AppSettings())
    temporary_audio = tmp_path / "trimmed.wav"
    temporary_audio.write_bytes(b"temporary audio")
    service._temp_wav = str(temporary_audio)
    service._timeout.start()
    assert service._timeout.isActive()
    windows_sound = SimpleNamespace(PlaySound=Mock(), SND_ASYNC=1)

    with (
        patch("sys.platform", "win32"),
        patch.dict("sys.modules", {"winsound": windows_sound}),
        patch.object(service._effect, "stop") as effect_stop,
        patch.object(service._media_player, "stop") as media_stop,
    ):
        service.stop()
        effect_stop.assert_called_once()
        media_stop.assert_called_once()
        windows_sound.PlaySound.assert_called_once_with(None, 1)

    assert not service._timeout.isActive()
    assert not temporary_audio.exists()
    assert service._temp_wav is None


def test_timeout_uses_same_stop_path(app):
    service = SoundService(AppSettings())
    with patch.object(service, "stop") as stop:
        service._timeout.timeout.emit()
        stop.assert_called_once()
