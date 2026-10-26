"""Exercise the packaged UI without touching settings, history or notifications."""

from pathlib import Path

from PyQt6.QtCore import Qt

from src.engine.session import AppSettings, Phase
from src.engine.timer_engine import TimerEngine
from src.services.i18n_service import init
from src.services.sound_service import SoundService
from src.ui.timer_widget import TimerWidget


def run_smoke(app, destination: str) -> int:
    init("ja")
    settings = AppSettings()
    settings.ui.window_opacity = 1.0
    engine = TimerEngine(settings)
    sound = SoundService(settings)
    assert Path(sound.default_sound_path()).is_file()
    # Qt's playingChanged signal has no payload. Check the connected slot silently.
    sound._effect.playingChanged.emit()
    widget = TimerWidget(settings)
    widget.on_start = engine.start
    widget.on_pause = lambda: (
        engine.resume() if engine.phase == Phase.PAUSED else engine.pause()
    )
    widget.on_skip = engine.skip
    engine.tick.connect(widget.update_time)
    engine.phase_changed.connect(
        lambda phase, index: (
            widget.update_phase(Phase(phase)),
            widget.update_session_index(index),
        )
    )
    widget.show()
    app.processEvents()
    assert widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    widget._start_btn.click()
    assert engine.phase == Phase.WORKING
    engine._on_tick()
    assert widget._time_label.text() == "24:59"
    widget._pause_btn.click()
    assert engine.phase == Phase.PAUSED
    widget._start_btn.click()
    assert engine.phase == Phase.WORKING
    widget._skip_btn.click()
    assert engine.phase == Phase.SHORT_BREAK
    assert widget._time_label.text() == "05:00"
    engine.reset()
    widget._pin_btn.click()
    assert not widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    widget._pin_btn.click()
    assert widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    app.processEvents()
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    assert widget.grab().save(str(target))
    assert widget._btn_container.isVisible()
    for child in (widget._time_label, widget._btn_container, widget._phase_label):
        assert widget.rect().contains(child.geometry())
    widget.close()
    return 0
