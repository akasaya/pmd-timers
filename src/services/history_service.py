"""Session history persistence service (T006)."""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from src.engine.session import DailyRecord, TimerSession


def _get_history_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    history_dir = base / "pmd-timers" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


class HistoryService(QObject):
    session_recorded = pyqtSignal()

    def __init__(self, history_dir: Path | None = None, parent=None):
        super().__init__(parent)
        self._dir = history_dir or _get_history_dir()

    def record_session(self, session: TimerSession) -> None:
        record = self.load_daily(session.date) or DailyRecord(date=session.date)
        record.add_session(session)
        self._save_daily(record)
        self.session_recorded.emit()

    def load_daily(self, date_str: str) -> DailyRecord | None:
        path = self._dir / f"{date_str}.json"
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return DailyRecord.from_dict(data)
        except Exception:
            return None

    def load_period(self, start: str, end: str) -> list[DailyRecord]:
        records = []
        start_d = date.fromisoformat(start)
        end_d = date.fromisoformat(end)
        current = start_d
        while current <= end_d:
            record = self.load_daily(current.isoformat())
            if record:
                records.append(record)
            current += timedelta(days=1)
        return records

    def get_streak(self) -> int:
        streak = 0
        today = date.today()
        for i in range(90):
            d = today - timedelta(days=i)
            record = self.load_daily(d.isoformat())
            if not record or record.work_sessions_completed == 0:
                break
            streak += 1
        return streak

    def cleanup(self, keep_days: int = 90) -> int:
        cutoff = date.today() - timedelta(days=keep_days)
        deleted = 0
        for path in self._dir.glob("*.json"):
            try:
                file_date = date.fromisoformat(path.stem)
                if file_date < cutoff:
                    path.unlink()
                    deleted += 1
            except ValueError:
                pass
        return deleted

    def _save_daily(self, record: DailyRecord) -> None:
        path = self._dir / f"{record.date}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)
