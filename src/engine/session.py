"""Data classes and enumerations for the Pomodoro timer application."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Phase(Enum):
    IDLE = "idle"
    WORKING = "working"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    PAUSED = "paused"


class SessionType(Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class SessionStatus(Enum):
    COMPLETED = "completed"
    INTERRUPTED = "interrupted"
    SKIPPED = "skipped"


@dataclass
class TimerSession:
    type: SessionType
    date: str  # ISO8601 date YYYY-MM-DD
    start_time: str  # ISO8601 datetime
    scheduled_duration_sec: int
    session_index: int
    cycle_number: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    end_time: Optional[str] = None
    actual_duration_sec: int = 0
    status: SessionStatus = SessionStatus.INTERRUPTED

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "scheduled_duration_sec": self.scheduled_duration_sec,
            "actual_duration_sec": self.actual_duration_sec,
            "status": self.status.value,
            "session_index": self.session_index,
            "cycle_number": self.cycle_number,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimerSession":
        return cls(
            id=data["id"],
            type=SessionType(data["type"]),
            date=data["date"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            scheduled_duration_sec=data["scheduled_duration_sec"],
            actual_duration_sec=data.get("actual_duration_sec", 0),
            status=SessionStatus(data.get("status", "interrupted")),
            session_index=data["session_index"],
            cycle_number=data["cycle_number"],
        )


@dataclass
class TimerState:
    phase: Phase = Phase.IDLE
    pre_pause_phase: Optional[Phase] = None
    remaining_sec: int = 0
    current_session_index: int = 1
    daily_completed_count: int = 0
    is_sleep_paused: bool = False
    sleep_start_time: Optional[datetime] = None


# ── Settings ──────────────────────────────────────────────────────────────────

@dataclass
class TimerSettings:
    work_duration_min: int = 25
    short_break_min: int = 5
    long_break_min: int = 15
    sessions_before_long_break: int = 4

    def validate(self) -> None:
        if not (5 <= self.work_duration_min <= 90):
            raise ValueError("work_duration_min must be 5–90")
        if not (1 <= self.short_break_min <= 30):
            raise ValueError("short_break_min must be 1–30")
        if not (5 <= self.long_break_min <= 60):
            raise ValueError("long_break_min must be 5–60")
        if not (2 <= self.sessions_before_long_break <= 10):
            raise ValueError("sessions_before_long_break must be 2–10")


@dataclass
class BehaviorSettings:
    auto_start_next_session: bool = False
    is_muted: bool = False


@dataclass
class NotificationSettings:
    sound_enabled: bool = True
    desktop_notification_enabled: bool = True
    custom_sound_path: str = ""  # empty = use default bundled sound
    sound_start_ms: int = 0   # playback start position (ms)
    sound_end_ms: int = 0     # playback end position (ms); 0 = end of file


@dataclass
class WidgetDisplaySettings:
    always_on_top: bool = True
    window_opacity: float = 0.95
    hover_reveal_buttons: bool = True
    animation_duration_ms: int = 150
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    window_width: int = 200
    window_height: int = 80

    def validate(self) -> None:
        if not (0.2 <= self.window_opacity <= 1.0):
            raise ValueError("window_opacity must be 0.2–1.0")
        if not (120 <= self.window_width <= 400):
            raise ValueError("window_width must be 120–400")
        if not (60 <= self.window_height <= 200):
            raise ValueError("window_height must be 60–200")


@dataclass
class GeneralSettings:
    language: str = "ja"


@dataclass
class BgmSettings:
    work_bgm_path: str = ""
    work_bgm_enabled: bool = False
    work_bgm_volume: float = 0.5
    break_bgm_path: str = ""
    break_bgm_enabled: bool = False
    break_bgm_volume: float = 0.5


@dataclass
class AppSettings:
    timers: TimerSettings = field(default_factory=TimerSettings)
    behavior: BehaviorSettings = field(default_factory=BehaviorSettings)
    notifications: NotificationSettings = field(default_factory=NotificationSettings)
    ui: WidgetDisplaySettings = field(default_factory=WidgetDisplaySettings)
    bgm: BgmSettings = field(default_factory=BgmSettings)
    general: GeneralSettings = field(default_factory=GeneralSettings)

    def to_dict(self) -> dict:
        return {
            "version": "1.0",
            "timers": {
                "work_duration_min": self.timers.work_duration_min,
                "short_break_min": self.timers.short_break_min,
                "long_break_min": self.timers.long_break_min,
                "sessions_before_long_break": self.timers.sessions_before_long_break,
            },
            "behavior": {
                "auto_start_next_session": self.behavior.auto_start_next_session,
                "is_muted": self.behavior.is_muted,
            },
            "notifications": {
                "sound_enabled": self.notifications.sound_enabled,
                "desktop_notification_enabled": self.notifications.desktop_notification_enabled,
                "custom_sound_path": self.notifications.custom_sound_path,
                "sound_start_ms": self.notifications.sound_start_ms,
                "sound_end_ms": self.notifications.sound_end_ms,
            },
            "bgm": {
                "work_bgm_path": self.bgm.work_bgm_path,
                "work_bgm_enabled": self.bgm.work_bgm_enabled,
                "work_bgm_volume": self.bgm.work_bgm_volume,
                "break_bgm_path": self.bgm.break_bgm_path,
                "break_bgm_enabled": self.bgm.break_bgm_enabled,
                "break_bgm_volume": self.bgm.break_bgm_volume,
            },
            "ui": {
                "always_on_top": self.ui.always_on_top,
                "window_opacity": self.ui.window_opacity,
                "hover_reveal_buttons": self.ui.hover_reveal_buttons,
                "animation_duration_ms": self.ui.animation_duration_ms,
                "window_x": self.ui.window_x,
                "window_y": self.ui.window_y,
                "window_width": self.ui.window_width,
                "window_height": self.ui.window_height,
            },
            "general": {
                "language": self.general.language,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        t = data.get("timers", {})
        b = data.get("behavior", {})
        n = data.get("notifications", {})
        u = data.get("ui", {})
        g = data.get("bgm", {})
        gen = data.get("general", {})
        return cls(
            timers=TimerSettings(
                work_duration_min=t.get("work_duration_min", 25),
                short_break_min=t.get("short_break_min", 5),
                long_break_min=t.get("long_break_min", 15),
                sessions_before_long_break=t.get("sessions_before_long_break", 4),
            ),
            behavior=BehaviorSettings(
                auto_start_next_session=b.get("auto_start_next_session", False),
                is_muted=b.get("is_muted", False),
            ),
            notifications=NotificationSettings(
                sound_enabled=n.get("sound_enabled", True),
                desktop_notification_enabled=n.get("desktop_notification_enabled", True),
                custom_sound_path=n.get("custom_sound_path", ""),
                sound_start_ms=n.get("sound_start_ms", 0),
                sound_end_ms=n.get("sound_end_ms", 0),
            ),
            ui=WidgetDisplaySettings(
                always_on_top=u.get("always_on_top", True),
                window_opacity=u.get("window_opacity", 0.95),
                hover_reveal_buttons=u.get("hover_reveal_buttons", True),
                animation_duration_ms=u.get("animation_duration_ms", 150),
                window_x=u.get("window_x"),
                window_y=u.get("window_y"),
                window_width=u.get("window_width", 200),
                window_height=u.get("window_height", 80),
            ),
            bgm=BgmSettings(
                work_bgm_path=g.get("work_bgm_path", ""),
                work_bgm_enabled=g.get("work_bgm_enabled", False),
                work_bgm_volume=g.get("work_bgm_volume", 0.5),
                break_bgm_path=g.get("break_bgm_path", ""),
                break_bgm_enabled=g.get("break_bgm_enabled", False),
                break_bgm_volume=g.get("break_bgm_volume", 0.5),
            ),
            general=GeneralSettings(
                language=gen.get("language", "ja"),
            ),
        )


# ── Daily Record ──────────────────────────────────────────────────────────────

@dataclass
class DailyRecord:
    date: str
    work_sessions_completed: int = 0
    work_sessions_interrupted: int = 0
    short_breaks_completed: int = 0
    long_breaks_completed: int = 0
    total_work_sec: int = 0
    total_break_sec: int = 0
    sessions: list = field(default_factory=list)  # list[TimerSession]

    def to_dict(self) -> dict:
        return {
            "date": self.date,
            "work_sessions_completed": self.work_sessions_completed,
            "work_sessions_interrupted": self.work_sessions_interrupted,
            "short_breaks_completed": self.short_breaks_completed,
            "long_breaks_completed": self.long_breaks_completed,
            "total_work_sec": self.total_work_sec,
            "total_break_sec": self.total_break_sec,
            "sessions": [s.to_dict() for s in self.sessions],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DailyRecord":
        record = cls(
            date=data["date"],
            work_sessions_completed=data.get("work_sessions_completed", 0),
            work_sessions_interrupted=data.get("work_sessions_interrupted", 0),
            short_breaks_completed=data.get("short_breaks_completed", 0),
            long_breaks_completed=data.get("long_breaks_completed", 0),
            total_work_sec=data.get("total_work_sec", 0),
            total_break_sec=data.get("total_break_sec", 0),
        )
        record.sessions = [TimerSession.from_dict(s) for s in data.get("sessions", [])]
        return record

    def add_session(self, session: TimerSession) -> None:
        self.sessions.append(session)
        if session.type == SessionType.WORK:
            if session.status == SessionStatus.COMPLETED:
                self.work_sessions_completed += 1
                self.total_work_sec += session.actual_duration_sec
            else:
                self.work_sessions_interrupted += 1
                self.total_work_sec += session.actual_duration_sec
        elif session.type == SessionType.SHORT_BREAK:
            if session.status == SessionStatus.COMPLETED:
                self.short_breaks_completed += 1
            self.total_break_sec += session.actual_duration_sec
        elif session.type == SessionType.LONG_BREAK:
            if session.status == SessionStatus.COMPLETED:
                self.long_breaks_completed += 1
            self.total_break_sec += session.actual_duration_sec
