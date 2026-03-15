"""Integration test: session completion → history → dashboard update (T027)."""
from __future__ import annotations

from datetime import date

import pytest

from src.engine.session import SessionStatus, SessionType, TimerSession
from src.services.dashboard_viewmodel import DashboardViewModel, Period
from src.services.history_service import HistoryService


def _completed_work_session(date_str: str) -> TimerSession:
    s = TimerSession(
        type=SessionType.WORK,
        date=date_str,
        start_time=f"{date_str}T09:00:00",
        scheduled_duration_sec=1500,
        session_index=1,
        cycle_number=1,
    )
    s.end_time = f"{date_str}T09:25:00"
    s.actual_duration_sec = 1500
    s.status = SessionStatus.COMPLETED
    return s


@pytest.fixture
def history_svc(tmp_path):
    return HistoryService(history_dir=tmp_path)


@pytest.fixture
def viewmodel(history_svc):
    return DashboardViewModel(history_svc)


class TestSessionToStats:
    def test_completed_session_appears_in_today_stats(self, history_svc, viewmodel):
        today = date.today().isoformat()
        history_svc.record_session(_completed_work_session(today))
        viewmodel.refresh()
        stats = viewmodel.get_today_stats()
        assert stats.completed_count == 1

    def test_multiple_sessions_accumulate(self, history_svc, viewmodel):
        today = date.today().isoformat()
        for _ in range(4):
            history_svc.record_session(_completed_work_session(today))
        viewmodel.refresh()
        stats = viewmodel.get_today_stats()
        assert stats.completed_count == 4

    def test_period_stats_reflect_history(self, history_svc, viewmodel):
        today = date.today().isoformat()
        history_svc.record_session(_completed_work_session(today))
        viewmodel.refresh()
        period_stats = viewmodel.get_period_stats(Period.TODAY)
        assert period_stats.total_completed == 1
        assert period_stats.daily_counts[0].count == 1

    def test_session_detail_accessible(self, history_svc, viewmodel):
        today = date.today().isoformat()
        s = _completed_work_session(today)
        history_svc.record_session(s)
        sessions = viewmodel.get_session_detail(today)
        assert len(sessions) == 1
        assert sessions[0].id == s.id

    def test_signal_emitted_on_record(self, history_svc):
        received = []
        history_svc.session_recorded.connect(lambda: received.append(True))
        today = date.today().isoformat()
        history_svc.record_session(_completed_work_session(today))
        assert len(received) == 1

    def test_viewmodel_refresh_clears_stale_cache(self, history_svc, viewmodel):
        today = date.today().isoformat()
        # First read: empty
        stats_before = viewmodel.get_today_stats()
        assert stats_before.completed_count == 0
        # Record, then refresh
        history_svc.record_session(_completed_work_session(today))
        viewmodel.refresh()
        stats_after = viewmodel.get_today_stats()
        assert stats_after.completed_count == 1
