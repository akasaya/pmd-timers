"""設定画面を閉じたときに試聴が残らないことを検証する。"""

from unittest.mock import patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QWidget

from src.engine.session import AppSettings
from src.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("preview", ["_preview_work_bgm", "_preview_break_bgm"])
@pytest.mark.parametrize("exit_method", ["ok", "cancel", "close", "escape", "hide"])
def test_closing_settings_stops_preview(app, preview, exit_method):
    parent = QWidget()
    with (
        patch("src.ui.settings_dialog.BgmService") as bgm,
        patch("src.ui.settings_dialog.SoundService") as sound,
    ):
        sound.default_sound_path.return_value = "assets/sounds/notification.wav"
        dialog = SettingsDialog(AppSettings(), parent)
        dialog.show()
        app.processEvents()
        getattr(dialog, preview)()
        bgm.return_value.on_phase_changed.assert_called_once()
        bgm.return_value.stop.reset_mock()
        sound.return_value.stop.reset_mock()

        if exit_method == "ok":
            dialog._apply()
        elif exit_method == "cancel":
            dialog.reject()
        elif exit_method == "escape":
            QTest.keyClick(dialog, Qt.Key.Key_Escape)
        elif exit_method == "hide":
            dialog.hide()
        else:
            dialog.close()

        app.processEvents()
        assert not dialog.isVisible()
        # QDialog can remain owned by its parent after closing.
        bgm.return_value.stop.assert_called()
        sound.return_value.stop.assert_called()
        dialog.deleteLater()
    parent.close()


def test_switching_preview_stops_previous_audio(app):
    with (
        patch("src.ui.settings_dialog.BgmService") as bgm,
        patch("src.ui.settings_dialog.SoundService") as sound,
    ):
        sound.default_sound_path.return_value = "assets/sounds/notification.wav"
        dialog = SettingsDialog(AppSettings())
        dialog._preview_work_bgm()
        sound.return_value.stop.assert_called()
        bgm.return_value.stop.reset_mock()
        dialog._preview_sound()
        bgm.return_value.stop.assert_called()
        dialog.close()
