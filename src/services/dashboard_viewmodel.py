"""Statistics aggregation view model (T013)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from src.services.history_service import HistoryService


class Period(Enum):
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"


@dataclass
class TodayStats:
    date: str
    completed_count: int = 0
    interrupted_count: int = 0
    total_work_time_str: str = "0分"
    short_breaks: int = 0
    long_breaks: int = 0
    current_streak_days: int = 0


@dataclass
class DailyCount:
    date: str
    label: str
    count: int


@dataclass
class PeriodStats:
    period: Period
    start_date: str
    end_date: str
    daily_counts: list[DailyCount] = field(default_factory=list)
    total_completed: int = 0
    total_work_sec: int = 0
    best_day_date: str | None = None
    best_day_count: int = 0


def _sec_to_str(sec: int) -> str:
    h = sec // 3600
    m = (sec % 3600) // 60
    if h > 0:
        return f"{h}時間{m}分"
    return f"{m}分"


class DashboardViewModel:
    def __init__(self, history_service: HistoryService):
        self._history = history_service
        self._cache: dict = {}

    def refresh(self) -> None:
        self._cache.clear()

    def get_today_stats(self) -> TodayStats:
        today = date.today().isoformat()
        record = self._history.load_daily(today)
        streak = self._history.get_streak()
        if record is None:
            return TodayStats(date=today, current_streak_days=streak)
        return TodayStats(
            date=today,
            completed_count=record.work_sessions_completed,
            interrupted_count=record.work_sessions_interrupted,
            total_work_time_str=_sec_to_str(record.total_work_sec),
            short_breaks=record.short_breaks_completed,
            long_breaks=record.long_breaks_completed,
            current_streak_days=streak,
        )

    def get_period_stats(self, period: Period) -> PeriodStats:
        today = date.today()
        if period == Period.TODAY:
            start_d = end_d = today
        elif period == Period.THIS_WEEK:
            start_d = today - timedelta(days=6)
            end_d = today
        else:  # THIS_MONTH
            start_d = today.replace(day=1)
            end_d = today

        start_str = start_d.isoformat()
        end_str = end_d.isoformat()
        records = self._history.load_period(start_str, end_str)

        record_map = {r.date: r for r in records}

        daily_counts: list[DailyCount] = []
        current = start_d
        while current <= end_d:
            d_str = current.isoformat()
            record = record_map.get(d_str)
            count = record.work_sessions_completed if record else 0
            label = f"{current.month}/{current.day}"
            daily_counts.append(DailyCount(date=d_str, label=label, count=count))
            current += timedelta(days=1)

        total_completed = sum(dc.count for dc in daily_counts)
        total_work_sec = sum(r.total_work_sec for r in records)

        best = max(daily_counts, key=lambda dc: dc.count, default=None)

        return PeriodStats(
            period=period,
            start_date=start_str,
            end_date=end_str,
            daily_counts=daily_counts,
            total_completed=total_completed,
            total_work_sec=total_work_sec,
            best_day_date=best.date if best and best.count > 0 else None,
            best_day_count=best.count if best else 0,
        )

    def get_session_detail(self, date_str: str):
        record = self._history.load_daily(date_str)
        if record is None:
            return []
        return record.sessions
