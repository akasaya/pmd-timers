"""Regression coverage for the persistent desktop controls and progress display."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.engine.session import AppSettings, Phase
from src.services.i18n_service import init
from src.ui.smoke import run_smoke
from src.ui.timer_widget import TimerWidget


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def widget(app):
    init("ja")
    window = TimerWidget(AppSettings())
    window.show()
    app.processEvents()
    yield window
    window.close()


def test_full_control_flow(app, tmp_path):
    assert run_smoke(app, str(tmp_path / "preview.png")) == 0


def test_controls_remain_available_without_hover(widget, app):
    widget._on_leave_timeout()
    assert widget._btn_container.isVisible()
    settings = AppSettings()
    settings.ui.hover_reveal_buttons = True
    widget.apply_settings(settings)
    widget._on_leave_timeout()
    assert not widget._btn_container.isVisible()
    settings.ui.hover_reveal_buttons = False
    widget.apply_settings(settings)
    assert widget._btn_container.isVisible()


def test_pin_preference_survives_settings_and_restart(widget):
    settings = AppSettings()
    settings.ui.always_on_top = False
    widget.apply_settings(settings)
    assert widget.isVisible()
    assert not widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    reopened = TimerWidget(settings)
    assert not reopened.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    reopened.close()


def test_paused_break_progress_and_reset(widget):
    widget.update_phase(Phase.SHORT_BREAK)
    widget.update_time(150)
    assert widget._progress.value() == 500
    widget.update_phase(Phase.PAUSED)
    widget.update_phase(Phase.SHORT_BREAK)
    assert widget._progress.value() == 500
    widget.update_phase(Phase.PAUSED)
    widget.update_phase(Phase.IDLE)
    widget.update_time(1500)
    assert widget._progress.value() == 0


def test_old_small_window_fits_controls(widget, app):
    settings = AppSettings()
    settings.ui.window_width = 200
    settings.ui.window_height = 80
    widget.apply_settings(settings)
    app.processEvents()
    assert widget.width() >= 300
    assert widget.height() >= 248
    assert widget.rect().contains(widget._btn_container.geometry())
