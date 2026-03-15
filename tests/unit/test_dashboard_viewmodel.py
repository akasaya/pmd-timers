"""Unit tests for DashboardViewModel (T026)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from src.engine.session import SessionStatus, SessionType, TimerSession
from src.services.dashboard_viewmodel import DashboardViewModel, Period
from src.services.history_service import HistoryService


def _make_session(date_str: str, duration_sec: int = 1500) -> TimerSession:
    s = TimerSession(
        type=SessionType.WORK,
        date=date_str,
        start_time=f"{date_str}T09:00:00",
        scheduled_duration_sec=duration_sec,
        session_index=1,
        cycle_number=1,
    )
    s.end_time = f"{date_str}T09:25:00"
    s.actual_duration_sec = duration_sec
    s.status = SessionStatus.COMPLETED
    return s


@pytest.fixture
def svc(tmp_path):
    return HistoryService(history_dir=tmp_path)


@pytest.fixture
def vm(svc):
    return DashboardViewModel(svc)


class TestGetTodayStats:
    def test_empty_when_no_data(self, vm):
        stats = vm.get_today_stats()
        assert stats.completed_count == 0
        assert stats.interrupted_count == 0

    def test_reflects_recorded_sessions(self, svc, vm):
        today = date.today().isoformat()
        svc.record_session(_make_session(today))
        svc.record_session(_make_session(today))
        vm.refresh()
        stats = vm.get_today_stats()
        assert stats.completed_count == 2

    def test_work_time_str_format(self, svc, vm):
        today = date.today().isoformat()
        svc.record_session(_make_session(today, duration_sec=1500))  # 25分
        vm.refresh()
        stats = vm.get_today_stats()
        assert "25分" in stats.total_work_time_str


class TestGetPeriodStats:
    def test_today_has_one_entry(self, vm):
        stats = vm.get_period_stats(Period.TODAY)
        assert len(stats.daily_counts) == 1

    def test_this_week_has_seven_entries(self, vm):
        stats = vm.get_period_stats(Period.THIS_WEEK)
        assert len(stats.daily_counts) == 7

    def test_this_month_covers_month(self, vm):
        stats = vm.get_period_stats(Period.THIS_MONTH)
        today = date.today()
        expected_days = today.day  # days from start of month to today
        assert len(stats.daily_counts) == expected_days

    def test_total_completed_sums_correctly(self, svc, vm):
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        svc.record_session(_make_session(today))
        svc.record_session(_make_session(today))
        svc.record_session(_make_session(yesterday))
        vm.refresh()
        stats = vm.get_period_stats(Period.THIS_WEEK)
        assert stats.total_completed == 3

    def test_best_day_identified(self, svc, vm):
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        svc.record_session(_make_session(today))
        for _ in range(3):
            svc.record_session(_make_session(yesterday))
        vm.refresh()
        stats = vm.get_period_stats(Period.THIS_WEEK)
        assert stats.best_day_date == yesterday
        assert stats.best_day_count == 3

    def test_best_day_none_when_no_data(self, vm):
        stats = vm.get_period_stats(Period.THIS_WEEK)
        assert stats.best_day_date is None


class TestGetStreak:
    def test_streak_zero_initially(self, vm):
        stats = vm.get_today_stats()
        assert stats.current_streak_days == 0

    def test_streak_increments_with_daily_sessions(self, svc, vm):
        today = date.today()
        for i in range(3):
            d = (today - timedelta(days=i)).isoformat()
            svc.record_session(_make_session(d))
        vm.refresh()
        stats = vm.get_today_stats()
        assert stats.current_streak_days == 3
