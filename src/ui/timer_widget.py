"""Compact always-on-top timer widget with hover UI and drag support (T008-T012, T023)."""
from __future__ import annotations

from PyQt6.QtCore import (
    QPoint,
    QPropertyAnimation,
    Qt,
    QEasingCurve,
    QTimer,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.engine.session import AppSettings, Phase


_PHASE_LABELS = {
    Phase.IDLE: "待機中",
    Phase.WORKING: "作業中",
    Phase.SHORT_BREAK: "短休憩",
    Phase.LONG_BREAK: "長休憩",
    Phase.PAUSED: "一時停止",
}

_PHASE_COLORS = {
    Phase.WORKING: "#E53935",
    Phase.SHORT_BREAK: "#43A047",
    Phase.LONG_BREAK: "#1E88E5",
    Phase.IDLE: "#607D8B",
    Phase.PAUSED: "#FFA726",
}


class TimerWidget(QWidget):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._drag_start: QPoint | None = None
        self._current_phase = Phase.IDLE

        # Callbacks (set by main)
        self.on_start = lambda: None
        self.on_pause = lambda: None
        self.on_reset = lambda: None
        self.on_skip = lambda: None
        self.on_open_settings = lambda: None
        self.on_open_dashboard = lambda: None
        self.on_quit = lambda: None

        # Debounce timer for leaveEvent (prevents flicker when moving over child widgets)
        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(150)
        self._leave_timer.timeout.connect(self._on_leave_timeout)

        self._setup_window()
        self._build_ui()
        self._restore_position()
        self.setWindowOpacity(self._settings.ui.window_opacity)

    # ── Window setup ──────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(self._settings.ui.window_width, self._settings.ui.window_height)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Phase label
        self._phase_label = QLabel(_PHASE_LABELS[Phase.IDLE], self)
        self._phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_phase = QFont()
        font_phase.setPointSize(8)
        self._phase_label.setFont(font_phase)
        self._phase_label.setStyleSheet("color: #aaaaaa;")

        # Timer display
        self._time_label = QLabel("25:00", self)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_time = QFont()
        font_time.setPointSize(18)
        font_time.setBold(True)
        self._time_label.setFont(font_time)
        self._time_label.setStyleSheet("color: #ffffff;")

        # Session counter
        self._count_label = QLabel("今日: 0", self)
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_small = QFont()
        font_small.setPointSize(7)
        self._count_label.setFont(font_small)
        self._count_label.setStyleSheet("color: #888888;")

        layout.addWidget(self._phase_label)
        layout.addWidget(self._time_label)
        layout.addWidget(self._count_label)

        # Button container with opacity effect
        self._btn_container = QWidget(self)
        btn_layout = QHBoxLayout(self._btn_container)
        btn_layout.setContentsMargins(2, 0, 2, 0)
        btn_layout.setSpacing(4)

        self._start_btn = self._make_btn("▶", self._on_start_click)
        self._pause_btn = self._make_btn("⏸", self._on_pause_click)
        self._skip_btn = self._make_btn("⏭", self._on_skip_click)

        btn_layout.addWidget(self._start_btn)
        btn_layout.addWidget(self._pause_btn)
        btn_layout.addWidget(self._skip_btn)

        self._opacity_effect = QGraphicsOpacityEffect(self._btn_container)
        self._opacity_effect.setOpacity(0.0)
        self._btn_container.setGraphicsEffect(self._opacity_effect)
        self._btn_container.setVisible(False)

        layout.addWidget(self._btn_container)

        # Enable mouse tracking for entire widget
        self.setMouseTracking(True)

    def _make_btn(self, text: str, slot) -> QToolButton:
        btn = QToolButton(self)
        btn.setText(text)
        btn.setFixedSize(28, 22)
        btn.setStyleSheet(
            "QToolButton { background: rgba(255,255,255,40); border-radius:4px; color:white; }"
            "QToolButton:hover { background: rgba(255,255,255,80); }"
        )
        btn.clicked.connect(slot)
        return btn

    # ── Public update slots ───────────────────────────────────────────────

    def update_time(self, remaining_sec: int) -> None:
        m, s = divmod(remaining_sec, 60)
        self._time_label.setText(f"{m:02d}:{s:02d}")

    def update_phase(self, phase: Phase) -> None:
        self._current_phase = phase
        self._phase_label.setText(_PHASE_LABELS.get(phase, ""))
        color = _PHASE_COLORS.get(phase, "#ffffff")
        self._time_label.setStyleSheet(f"color: {color};")
        self._start_btn.setVisible(phase in (Phase.IDLE, Phase.PAUSED))
        self._pause_btn.setVisible(phase in (Phase.WORKING, Phase.SHORT_BREAK, Phase.LONG_BREAK))

    def update_daily_count(self, count: int) -> None:
        self._count_label.setText(f"今日: {count}")

    # ── Background rendering (T004) ──────────────────────────────────────

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(20, 20, 20, 180))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)

    # ── Hover UI (T008, T003) ─────────────────────────────────────────────

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._leave_timer.stop()
        if not self._settings.ui.hover_reveal_buttons:
            return
        self._btn_container.setVisible(True)
        anim_dur = self._settings.ui.animation_duration_ms
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(anim_dur)
        anim.setStartValue(self._opacity_effect.opacity())
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._fade_in_anim = anim  # keep reference
        # Also restore full opacity on hover (T023)
        self.setWindowOpacity(1.0)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        if not self._settings.ui.hover_reveal_buttons:
            return
        # Debounce: wait before fading out to avoid flicker on child widget boundaries
        self._leave_timer.start()

    def _on_leave_timeout(self) -> None:
        if self.underMouse():
            return  # mouse moved back inside — cancel fade out
        anim_dur = self._settings.ui.animation_duration_ms
        anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        anim.setDuration(anim_dur)
        anim.setStartValue(self._opacity_effect.opacity())
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.finished.connect(lambda: self._btn_container.setVisible(False))
        anim.start()
        self._fade_out_anim = anim  # keep reference
        # Restore configured opacity (T023)
        self.setWindowOpacity(self._settings.ui.window_opacity)

    # ── Drag move (T010) ──────────────────────────────────────────────────

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_start and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            clamped = self._clamp_to_screen(new_pos)
            self.move(clamped)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start:
            self._drag_start = None
            self._save_position()
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        menu.addAction("統計を見る", self.on_open_dashboard)
        menu.addAction("設定", self.on_open_settings)
        menu.addSeparator()
        menu.addAction("リセット", self.on_reset)
        menu.addSeparator()
        menu.addAction("終了", self.on_quit)
        menu.exec(event.globalPos())

    # ── Position persistence (T011) ──────────────────────────────────────

    def _restore_position(self) -> None:
        x = self._settings.ui.window_x
        y = self._settings.ui.window_y
        if x is None or y is None:
            screen = QApplication.primaryScreen()
            if screen:
                rect = screen.availableGeometry()
                x = rect.right() - self.width() - 16
                y = rect.top() + 16
        self.move(x, y)

    def _save_position(self) -> None:
        self._settings.ui.window_x = self.x()
        self._settings.ui.window_y = self.y()
        # Persist immediately (caller passes settings_service if needed)
        if hasattr(self, "_settings_service") and self._settings_service:
            self._settings_service.save(self._settings)

    def _clamp_to_screen(self, pos: QPoint) -> QPoint:
        screen = QApplication.primaryScreen()
        if screen is None:
            return pos
        rect = screen.availableGeometry()
        x = max(rect.left(), min(pos.x(), rect.right() - self.width()))
        y = max(rect.top(), min(pos.y(), rect.bottom() - self.height()))
        return QPoint(x, y)

    # ── Button callbacks ──────────────────────────────────────────────────

    def _on_start_click(self) -> None:
        if self._current_phase == Phase.PAUSED:
            self.on_pause()  # resume handled by engine
        else:
            self.on_start()

    def _on_pause_click(self) -> None:
        self.on_pause()

    def _on_skip_click(self) -> None:
        self.on_skip()

    # ── Settings ──────────────────────────────────────────────────────────

    def apply_settings(self, settings: AppSettings) -> None:
        self._settings = settings
        self.resize(settings.ui.window_width, settings.ui.window_height)
        self.setWindowOpacity(settings.ui.window_opacity)
        if settings.ui.always_on_top:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()
