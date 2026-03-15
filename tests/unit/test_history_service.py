"""Unit tests for HistoryService (T025)."""
from __future__ import annotations

import json
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from src.engine.session import DailyRecord, SessionStatus, SessionType, TimerSession
from src.services.history_service import HistoryService


def _make_session(
    date_str: str,
    stype: SessionType = SessionType.WORK,
    status: SessionStatus = SessionStatus.COMPLETED,
    duration_sec: int = 1500,
) -> TimerSession:
    s = TimerSession(
        type=stype,
        date=date_str,
        start_time=f"{date_str}T09:00:00",
        scheduled_duration_sec=duration_sec,
        session_index=1,
        cycle_number=1,
    )
    s.end_time = f"{date_str}T09:25:00"
    s.actual_duration_sec = duration_sec
    s.status = status
    return s


@pytest.fixture
def tmp_history(tmp_path):
    return HistoryService(history_dir=tmp_path)


class TestRecordSession:
    def test_creates_file(self, tmp_history, tmp_path):
        session = _make_session("2026-03-15")
        tmp_history.record_session(session)
        assert (tmp_path / "2026-03-15.json").exists()

    def test_increments_completed_count(self, tmp_history):
        session = _make_session("2026-03-15")
        tmp_history.record_session(session)
        record = tmp_history.load_daily("2026-03-15")
        assert record is not None
        assert record.work_sessions_completed == 1

    def test_interrupted_increments_interrupted(self, tmp_history):
        session = _make_session("2026-03-15", status=SessionStatus.INTERRUPTED)
        tmp_history.record_session(session)
        record = tmp_history.load_daily("2026-03-15")
        assert record.work_sessions_interrupted == 1
        assert record.work_sessions_completed == 0

    def test_accumulates_multiple_sessions(self, tmp_history):
        for _ in range(3):
            tmp_history.record_session(_make_session("2026-03-15"))
        record = tmp_history.load_daily("2026-03-15")
        assert record.work_sessions_completed == 3

    def test_emits_signal(self, tmp_history):
        received = []
        tmp_history.session_recorded.connect(lambda: received.append(True))
        tmp_history.record_session(_make_session("2026-03-15"))
        assert len(received) == 1


class TestLoadDaily:
    def test_returns_none_for_missing_date(self, tmp_history):
        assert tmp_history.load_daily("1999-01-01") is None

    def test_returns_record_for_existing(self, tmp_history):
        tmp_history.record_session(_make_session("2026-03-15"))
        record = tmp_history.load_daily("2026-03-15")
        assert isinstance(record, DailyRecord)
        assert record.date == "2026-03-15"


class TestGetStreak:
    def test_streak_zero_when_no_data(self, tmp_history):
        assert tmp_history.get_streak() == 0

    def test_streak_counts_consecutive_days(self, tmp_history):
        today = date.today()
        for i in range(3):
            d = (today - timedelta(days=i)).isoformat()
            tmp_history.record_session(_make_session(d))
        assert tmp_history.get_streak() == 3

    def test_streak_breaks_on_missing_day(self, tmp_history):
        today = date.today()
        tmp_history.record_session(_make_session(today.isoformat()))
        # Skip yesterday, add 2 days ago
        two_days_ago = (today - timedelta(days=2)).isoformat()
        tmp_history.record_session(_make_session(two_days_ago))
        assert tmp_history.get_streak() == 1


class TestCleanup:
    def test_deletes_old_files(self, tmp_history, tmp_path):
        old_date = (date.today() - timedelta(days=100)).isoformat()
        tmp_history.record_session(_make_session(old_date))
        assert (tmp_path / f"{old_date}.json").exists()
        deleted = tmp_history.cleanup(keep_days=90)
        assert deleted == 1
        assert not (tmp_path / f"{old_date}.json").exists()

    def test_keeps_recent_files(self, tmp_history, tmp_path):
        today = date.today().isoformat()
        tmp_history.record_session(_make_session(today))
        deleted = tmp_history.cleanup(keep_days=90)
        assert deleted == 0
        assert (tmp_path / f"{today}.json").exists()
