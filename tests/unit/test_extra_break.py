"""Extra work earns break time once per interval, without extra alerts."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QScrollArea

from src.engine.session import AppSettings, Phase
from src.engine.timer_engine import TimerEngine
from src.services.i18n_service import init
from src.services.settings_service import SettingsService
from src.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


def advance(engine, seconds):
    engine._qt_timer.stop()
    for _ in range(seconds):
        engine._on_tick()


def begin_extension(settings, index=1):
    engine = TimerEngine(settings)
    engine.start()
    engine.state.current_session_index = index
    engine.state.remaining_sec = 1
    advance(engine, 1)
    engine.toggle_extra_work()
    engine._qt_timer.stop()
    return engine


@pytest.mark.parametrize("seconds,bonus", [(299, 0), (300, 60), (301, 60), (600, 120)])
@pytest.mark.parametrize(
    "index,base,phase", [(1, 300, Phase.SHORT_BREAK), (4, 900, Phase.LONG_BREAK)]
)
def test_threshold_boundaries(app, seconds, bonus, index, base, phase):
    engine = begin_extension(AppSettings(), index)
    alerts, sessions = [], []
    engine.phase_completed.connect(lambda *args: alerts.append(args))
    engine.session_completed.connect(sessions.append)
    advance(engine, seconds)
    assert alerts == []
    engine.toggle_extra_work()
    assert engine.phase == phase
    assert engine.remaining_sec == base + bonus
    assert engine.scheduled_duration_sec == base + bonus
    assert sessions[0].actual_duration_sec == seconds
    assert sessions[0].is_extension
    assert engine.state.daily_completed_count == 1
    advance(engine, base + bonus)
    assert len(alerts) == 1
    assert sessions[-1].scheduled_duration_sec == base + bonus
    assert sessions[-1].actual_duration_sec == base + bonus
    engine.reset()


def test_repeated_extensions_pause_and_skip(app):
    engine = begin_extension(AppSettings())
    advance(engine, 180)
    engine.pause()
    advance(engine, 300)
    engine.toggle_extra_work()
    assert engine.remaining_sec == 300
    advance(engine, 60)  # Break time does not count as extra work.
    engine.toggle_extra_work()
    advance(engine, 120)
    engine.skip()
    assert engine.remaining_sec == 360
    engine.toggle_extra_work()
    advance(engine, 1)
    engine.toggle_extra_work()
    assert engine.remaining_sec == 360  # No duplicate bonus on reopening.
    engine.toggle_extra_work()
    advance(engine, 299)
    engine.toggle_extra_work()
    assert engine.remaining_sec == 420
    engine.skip()
    engine.start()
    engine.state.remaining_sec = 1
    advance(engine, 1)
    engine.toggle_extra_work()
    advance(engine, 299)
    engine.toggle_extra_work()
    assert engine.remaining_sec == 300  # A new break starts a new total.
    engine.reset()


def test_disabled_and_custom_rule_is_frozen_until_next_break(app):
    settings = AppSettings()
    settings.timers.extra_break_enabled = False
    engine = begin_extension(settings)
    changed = deepcopy(settings)
    changed.timers.extra_break_enabled = True
    changed.timers.extra_work_threshold_min = 2
    changed.timers.extra_break_increment_min = 3
    engine.update_settings(changed)
    advance(engine, 600)
    engine.toggle_extra_work()
    assert engine.remaining_sec == 300
    engine.reset()
    engine.start()
    engine.state.remaining_sec = 1
    advance(engine, 1)
    engine.toggle_extra_work()
    advance(engine, 240)
    engine.toggle_extra_work()
    assert engine.remaining_sec == 660
    engine.reset()


def test_old_settings_and_round_trip(tmp_path):
    service = SettingsService(tmp_path)
    old = AppSettings.from_dict({"timers": {"short_break_min": 7}})
    assert old.timers.short_break_min == 7
    assert old.timers.extra_break_enabled
    assert old.timers.extra_work_threshold_min == 5
    assert old.timers.extra_break_increment_min == 1
    old.timers.extra_break_enabled = False
    old.timers.extra_work_threshold_min = 12
    old.timers.extra_break_increment_min = 4
    service.save(old)
    assert service.load().timers == old.timers


@pytest.mark.parametrize(
    "field,value",
    [
        ("extra_work_threshold_min", 0),
        ("extra_work_threshold_min", 91),
        ("extra_break_increment_min", 0),
        ("extra_break_increment_min", 31),
    ],
)
def test_invalid_extra_break_settings(field, value):
    settings = AppSettings()
    setattr(settings.timers, field, value)
    with pytest.raises(ValueError):
        settings.timers.validate()


@pytest.mark.parametrize("language", ["ja", "en"])
def test_settings_controls_apply_reset_and_fit(app, language):
    init(language)
    with (
        patch("src.ui.settings_dialog.SoundService") as sound,
        patch("src.ui.settings_dialog.BgmService"),
    ):
        sound.default_sound_path.return_value = "assets/sounds/notification.wav"
        original = AppSettings()
        dialog = SettingsDialog(deepcopy(original))
        dialog.show()
        app.processEvents()
        dialog._extra_threshold_spin.setValue(10)
        dialog._extra_increment_spin.setValue(5)
        dialog._extra_break_check.setChecked(False)
        assert not dialog._extra_threshold_spin.isEnabled()
        assert original.timers.extra_work_threshold_min == 5
        scroll = dialog.findChild(QScrollArea)
        assert scroll.verticalScrollBar().maximum() > 0
        buttons = dialog.findChild(QDialogButtonBox)
        assert dialog.rect().contains(buttons.geometry())
        assert dialog.height() <= dialog.screen().availableGeometry().height()
        dialog._apply()
        assert not dialog.get_settings().timers.extra_break_enabled
        assert dialog.get_settings().timers.extra_work_threshold_min == 10
        assert dialog.get_settings().timers.extra_break_increment_min == 5
        dialog._reset()
        dialog._apply()
        assert dialog.get_settings().timers == AppSettings().timers
        dialog.deleteLater()
    init("ja")
