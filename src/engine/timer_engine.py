"""Pomodoro timer state machine with Qt signals."""
from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from src.engine.session import (
    AppSettings,
    Phase,
    SessionStatus,
    SessionType,
    TimerSession,
    TimerState,
)


class TimerEngine(QObject):
    # Signals
    tick = pyqtSignal(int)                  # remaining_sec
    phase_changed = pyqtSignal(str, int)    # phase.value, session_index
    session_completed = pyqtSignal(object)  # TimerSession
    daily_count_updated = pyqtSignal(int)   # completed_count

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._state = TimerState()
        self._current_session: TimerSession | None = None
        self._cycle_number = 1

        self._qt_timer = QTimer(self)
        self._qt_timer.setInterval(1000)
        self._qt_timer.timeout.connect(self._on_tick)

    # ── Public API ─────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._state.phase == Phase.IDLE:
            self._begin_work_session()
        elif self._state.phase == Phase.PAUSED:
            self.resume()

    def pause(self) -> None:
        if self._state.phase not in (Phase.WORKING, Phase.SHORT_BREAK, Phase.LONG_BREAK):
            return
        self._state.pre_pause_phase = self._state.phase
        self._state.phase = Phase.PAUSED
        self._qt_timer.stop()
        self.phase_changed.emit(Phase.PAUSED.value, self._state.current_session_index)

    def resume(self) -> None:
        if self._state.phase != Phase.PAUSED or self._state.pre_pause_phase is None:
            return
        self._state.phase = self._state.pre_pause_phase
        self._state.pre_pause_phase = None
        self._qt_timer.start()
        self.phase_changed.emit(self._state.phase.value, self._state.current_session_index)

    def reset(self) -> None:
        self._qt_timer.stop()
        if self._current_session:
            self._finalize_session(SessionStatus.INTERRUPTED)
        self._state = TimerState()
        self._current_session = None
        self.phase_changed.emit(Phase.IDLE.value, 1)
        self.tick.emit(self._settings.timers.work_duration_min * 60)

    def skip(self) -> None:
        if self._state.phase in (Phase.WORKING, Phase.SHORT_BREAK, Phase.LONG_BREAK):
            self._qt_timer.stop()
            if self._current_session:
                self._finalize_session(SessionStatus.SKIPPED)
            self._advance_phase()

    def update_settings(self, settings: AppSettings) -> None:
        self._settings = settings

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def remaining_sec(self) -> int:
        return self._state.remaining_sec

    @property
    def phase(self) -> Phase:
        return self._state.phase

    # ── Internal ──────────────────────────────────────────────────────────

    def _on_tick(self) -> None:
        if self._state.remaining_sec > 0:
            self._state.remaining_sec -= 1
            if self._current_session:
                self._current_session.actual_duration_sec += 1
            self.tick.emit(self._state.remaining_sec)
        if self._state.remaining_sec == 0:
            self._qt_timer.stop()
            self._on_phase_complete()

    def _on_phase_complete(self) -> None:
        if self._current_session:
            self._finalize_session(SessionStatus.COMPLETED)
        self._advance_phase()

    def _advance_phase(self) -> None:
        s = self._settings.timers
        if self._state.phase == Phase.WORKING:
            self._state.daily_completed_count += 1
            self.daily_count_updated.emit(self._state.daily_completed_count)
            if self._state.current_session_index >= s.sessions_before_long_break:
                self._begin_long_break()
            else:
                self._begin_short_break()
        elif self._state.phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            if self._state.phase == Phase.LONG_BREAK:
                self._state.current_session_index = 1
                self._cycle_number += 1
            else:
                self._state.current_session_index += 1
            if self._settings.behavior.auto_start_next_session:
                self._begin_work_session()
            else:
                self._state.phase = Phase.IDLE
                self._state.remaining_sec = s.work_duration_min * 60
                self.phase_changed.emit(Phase.IDLE.value, self._state.current_session_index)
                self.tick.emit(self._state.remaining_sec)

    def _begin_work_session(self) -> None:
        sec = self._settings.timers.work_duration_min * 60
        self._state.phase = Phase.WORKING
        self._state.remaining_sec = sec
        self._current_session = self._new_session(SessionType.WORK, sec)
        self._qt_timer.start()
        self.phase_changed.emit(Phase.WORKING.value, self._state.current_session_index)
        self.tick.emit(sec)

    def _begin_short_break(self) -> None:
        sec = self._settings.timers.short_break_min * 60
        self._state.phase = Phase.SHORT_BREAK
        self._state.remaining_sec = sec
        self._current_session = self._new_session(SessionType.SHORT_BREAK, sec)
        self._qt_timer.start()
        self.phase_changed.emit(Phase.SHORT_BREAK.value, self._state.current_session_index)
        self.tick.emit(sec)

    def _begin_long_break(self) -> None:
        sec = self._settings.timers.long_break_min * 60
        self._state.phase = Phase.LONG_BREAK
        self._state.remaining_sec = sec
        self._current_session = self._new_session(SessionType.LONG_BREAK, sec)
        self._qt_timer.start()
        self.phase_changed.emit(Phase.LONG_BREAK.value, self._state.current_session_index)
        self.tick.emit(sec)

    def _new_session(self, stype: SessionType, duration_sec: int) -> TimerSession:
        now = datetime.now()
        return TimerSession(
            type=stype,
            date=now.strftime("%Y-%m-%d"),
            start_time=now.isoformat(),
            scheduled_duration_sec=duration_sec,
            session_index=self._state.current_session_index,
            cycle_number=self._cycle_number,
        )

    def _finalize_session(self, status: SessionStatus) -> None:
        if self._current_session is None:
            return
        self._current_session.end_time = datetime.now().isoformat()
        self._current_session.status = status
        session = self._current_session
        self._current_session = None
        self.session_completed.emit(session)
