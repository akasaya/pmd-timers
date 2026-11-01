"""Unit tests for TimerEngine phase-completion notifications."""

from __future__ import annotations

import pytest

from src.engine.session import (
    AppSettings,
    DailyRecord,
    Phase,
    SessionStatus,
    TimerSession,
)
from src.engine.timer_engine import TimerEngine


@pytest.fixture
def settings():
    return AppSettings()


def _completions(engine: TimerEngine) -> list[tuple[str, str]]:
    """Collect phase_completed (from, to) emissions."""
    received: list[tuple[str, str]] = []
    engine.phase_completed.connect(lambda f, t: received.append((f, t)))
    return received


def test_work_completion_emits_working_to_short_break(settings):
    engine = TimerEngine(settings)
    received = _completions(engine)
    engine.start()  # WORKING, session_index = 1
    engine._on_phase_complete()  # natural timer expiry
    assert received == [("working", "short_break")]


def test_work_completion_emits_working_to_long_break_on_last_session(settings):
    settings.timers.sessions_before_long_break = 2
    engine = TimerEngine(settings)
    received = _completions(engine)
    engine.start()
    engine._state.current_session_index = 2  # final work session before long break
    engine._on_phase_complete()
    assert received == [("working", "long_break")]


def test_short_break_completion_emits_short_break_to_working_when_no_auto_start(
    settings,
):
    settings.behavior.auto_start_next_session = False
    engine = TimerEngine(settings)
    received = _completions(engine)
    engine.start()
    engine._on_phase_complete()  # WORKING -> SHORT_BREAK
    received.clear()
    engine._on_phase_complete()  # SHORT_BREAK -> (IDLE) but notifies "to working"
    assert received == [("short_break", "working")]


def test_skip_does_not_emit_phase_completed(settings):
    engine = TimerEngine(settings)
    received = _completions(engine)
    engine.start()
    engine.skip()  # manual skip — no completion sound
    assert received == []


@pytest.mark.parametrize(
    "index, break_phase, duration",
    [
        (1, Phase.SHORT_BREAK, 300),
        (4, Phase.LONG_BREAK, 900),
    ],
)
@pytest.mark.parametrize("auto_start", [False, True])
def test_extra_work_returns_to_full_original_break(
    settings, index, break_phase, duration, auto_start
):
    settings.behavior.auto_start_next_session = auto_start
    engine = TimerEngine(settings)
    sessions = []
    engine.session_completed.connect(sessions.append)
    notifications = _completions(engine)
    engine.start()
    engine.state.current_session_index = index
    engine.state.remaining_sec = 1
    engine._on_tick()
    assert engine.phase == break_phase
    engine._on_tick()  # The user notices the button after the break starts.
    engine.toggle_extra_work()
    assert engine.phase == Phase.EXTRA_WORK
    for _ in range(65):
        engine._on_tick()
    assert engine.state.extra_work_sec == 65
    engine.pause()
    engine._on_tick()
    assert engine.state.extra_work_sec == 65
    engine.resume()
    engine._on_tick()
    # Editing preferences must not replace the originally scheduled break.
    settings.timers.short_break_min = 10
    settings.timers.long_break_min = 30
    engine.toggle_extra_work()
    assert engine.phase == break_phase
    assert engine.remaining_sec == duration
    assert engine.state.current_session_index == index
    assert engine.state.daily_completed_count == 1
    assert len(notifications) == 1
    extension = sessions[-1]
    assert extension.is_extension
    assert extension.actual_duration_sec == 66
    assert extension.status == SessionStatus.COMPLETED
    record = DailyRecord(date=extension.date)
    for session in sessions:
        record.add_session(TimerSession.from_dict(session.to_dict()))
    assert record.work_sessions_completed == 1
    assert record.work_sessions_interrupted == 0
    assert record.total_work_sec == 67
    assert record.total_break_sec == 1
    engine.state.remaining_sec = 1
    engine._on_tick()
    assert engine.phase == (Phase.WORKING if auto_start else Phase.IDLE)
    assert engine.state.current_session_index == (1 if index == 4 else 2)
    engine.reset()


def test_extra_work_reset_and_repeated_extensions(settings):
    engine = TimerEngine(settings)
    sessions = []
    engine.session_completed.connect(sessions.append)
    engine.start()
    engine._on_phase_complete()
    for _ in range(2):
        engine.toggle_extra_work()
        engine._on_tick()
        engine.skip()  # "Next" during extra work starts the planned break.
        assert engine.phase == Phase.SHORT_BREAK
        assert engine.remaining_sec == 300
    engine.pause()
    engine.toggle_extra_work()  # Also available on a paused break.
    assert engine.phase == Phase.EXTRA_WORK
    engine._on_tick()
    engine.pause()
    engine.toggle_extra_work()  # Finish without resuming first.
    assert engine.phase == Phase.SHORT_BREAK
    engine.toggle_extra_work()
    engine._on_tick()
    engine.reset()
    assert engine.phase == Phase.IDLE
    assert sessions[-1].is_extension
    assert sessions[-1].status == SessionStatus.INTERRUPTED
    assert sessions[-1].actual_duration_sec == 1
    engine.toggle_extra_work()
    assert engine.phase == Phase.IDLE
    engine.start()
    engine.toggle_extra_work()
    assert engine.phase == Phase.WORKING
    engine.reset()


def test_old_work_history_defaults_to_regular_session(settings):
    engine = TimerEngine(settings)
    sessions = []
    engine.session_completed.connect(sessions.append)
    engine.start()
    engine._on_phase_complete()
    old_data = sessions[0].to_dict()
    del old_data["is_extension"]
    assert not TimerSession.from_dict(old_data).is_extension
    engine.reset()
