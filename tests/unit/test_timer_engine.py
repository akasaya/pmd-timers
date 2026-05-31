"""Unit tests for TimerEngine phase-completion notifications."""
from __future__ import annotations

import pytest

from src.engine.session import AppSettings
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


def test_short_break_completion_emits_short_break_to_working_when_no_auto_start(settings):
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
