"""A compact, draggable focus card for an always-visible desktop timer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, QRectF, Qt, QTimer
from PyQt6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPen,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.engine.session import AppSettings, Phase
from src.services.i18n_service import t

if TYPE_CHECKING:
    from src.services.settings_service import SettingsService

_PHASE_KEYS = {
    Phase.IDLE: "phase.idle",
    Phase.WORKING: "phase.working",
    Phase.SHORT_BREAK: "phase.short_break",
    Phase.LONG_BREAK: "phase.long_break",
    Phase.PAUSED: "phase.paused",
}
_PHASE_COLORS = {
    Phase.IDLE: "#86e1c3",
    Phase.WORKING: "#86e1c3",
    Phase.SHORT_BREAK: "#9bc9ff",
    Phase.LONG_BREAK: "#c5b3ff",
    Phase.PAUSED: "#f1c780",
}


class TimerWidget(QWidget):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._settings_service: SettingsService | None = None
        self._drag_start: QPoint | None = None
        self._current_phase = Phase.IDLE
        self._session_index = 1
        self._duration = settings.timers.work_duration_min * 60
        self._remaining = self._duration
        self._daily_count = 0
        for name in (
            "start",
            "pause",
            "reset",
            "skip",
            "mute",
            "open_settings",
            "open_dashboard",
            "quit",
        ):
            setattr(self, f"on_{name}", lambda: None)
        self._leave_timer = QTimer(self)
        self._leave_timer.setSingleShot(True)
        self._leave_timer.setInterval(150)
        self._leave_timer.timeout.connect(self._on_leave_timeout)
        self._setup_window()
        self._build_ui()
        self.apply_settings(settings)
        self._restore_position()
        self._shortcut = QShortcut(QKeySequence("Space"), self)
        self._shortcut.activated.connect(self._toggle_timer)

    def _setup_window(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        if self._settings.ui.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setWindowTitle("Focus · Pomodoro Timer")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(300, 248)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            QLabel { color: #edf3f8; background: transparent; }
            QToolButton { color: #a9b5c7; background: #242e3e; border: 1px solid #344055;
                          border-radius: 9px; padding: 4px; font-size: 12px; }
            QToolButton:hover { color: #ffffff; background: #344258; }
            QToolButton:pressed { background: #43526a; }
            QToolButton:checked { color: #86e1c3; background: #233d3c; border-color: #3d7164; }
            QToolButton:disabled { color: #5f6c80; background: #202938; }
            QToolButton:focus { border: 1px solid #86e1c3; }
            QToolTip { color: #edf3f8; background: #243044; border: 1px solid #46546a; }
            QMenu { color: #edf3f8; background: #1c2636; border: 1px solid #364459; padding: 6px; }
            QMenu::item { padding: 8px 20px; border-radius: 5px; }
            QMenu::item:selected { background: #344258; }
        """)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        header = QHBoxLayout()
        self._brand = QLabel("F O C U S", self)
        self._brand.setStyleSheet("color: #91a1b8; font-size: 11px; font-weight: 600;")
        header.addWidget(self._brand)
        header.addStretch()
        self._pin_btn = self._make_btn("", self._toggle_pin)
        self._pin_btn.setCheckable(True)
        self._pin_btn.setFixedSize(64, 28)
        self._menu_btn = self._make_btn("···", self._open_menu)
        self._menu_btn.setFixedSize(30, 28)
        header.addWidget(self._pin_btn)
        header.addWidget(self._menu_btn)
        layout.addLayout(header)

        self._time_label = QLabel(self)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 42)
        font.setWeight(QFont.Weight.DemiBold)
        self._time_label.setFont(font)
        self._time_label.setMinimumHeight(68)
        layout.addWidget(self._time_label)

        detail = QHBoxLayout()
        self._phase_label = QLabel(self)
        self._cycle_label = QLabel(self)
        self._cycle_label.setStyleSheet("color: #899ab1; font-size: 11px;")
        detail.addWidget(self._phase_label)
        detail.addStretch()
        detail.addWidget(self._cycle_label)
        layout.addLayout(detail)
        self._progress = QProgressBar(self)
        self._progress.setRange(0, 1000)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        layout.addWidget(self._progress)

        footer = QHBoxLayout()
        self._count_label = QLabel(self)
        self._count_label.setStyleSheet("color: #91a1b8; font-size: 11px;")
        self._hint = QLabel(self)
        self._hint.setStyleSheet("color: #72839b; font-size: 10px;")
        footer.addWidget(self._count_label)
        footer.addStretch()
        footer.addWidget(self._hint)
        layout.addLayout(footer)
        layout.addStretch()

        self._btn_container = QWidget(self)
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        policy.setRetainSizeWhenHidden(True)
        self._btn_container.setSizePolicy(policy)
        buttons = QHBoxLayout(self._btn_container)
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)
        self._start_btn = self._make_btn("", self._on_start_click)
        self._pause_btn = self._make_btn("", lambda: self.on_pause())
        for button in (self._start_btn, self._pause_btn):
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            button.setStyleSheet("""
                QToolButton { background: #86e1c3; color: #102b27; border: none;
                              font-weight: 600; border-radius: 9px; }
                QToolButton:hover { background: #a8eed7; }
                QToolButton:pressed { background: #66c7a9; }
                QToolButton:focus { border: 2px solid #edf3f8; }
            """)
            buttons.addWidget(button, 1)
        self._mute_btn = self._make_btn("", lambda: self.on_mute())
        self._skip_btn = self._make_btn("", lambda: self.on_skip())
        self._skip_btn.setFixedWidth(56)
        self._mute_btn.setFixedWidth(50)
        buttons.addWidget(self._mute_btn)
        buttons.addWidget(self._skip_btn)
        layout.addWidget(self._btn_container)

    def _make_btn(self, text: str, slot) -> QToolButton:
        button = QToolButton(self)
        button.setText(text)
        button.setFixedHeight(34)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(slot)
        return button

    def update_time(self, remaining_sec: int) -> None:
        self._remaining = max(0, remaining_sec)
        minutes, seconds = divmod(self._remaining, 60)
        self._time_label.setText(f"{minutes:02d}:{seconds:02d}")
        self._progress.setValue(
            round(1000 * max(0, min(1, 1 - self._remaining / max(1, self._duration))))
        )
        self.setWindowTitle(f"{minutes:02d}:{seconds:02d} · Focus")

    def update_phase(self, phase: Phase) -> None:
        previous = self._current_phase
        self._current_phase = phase
        if phase == Phase.IDLE or (phase != Phase.PAUSED and previous != Phase.PAUSED):
            timers = self._settings.timers
            self._duration = {
                Phase.SHORT_BREAK: timers.short_break_min * 60,
                Phase.LONG_BREAK: timers.long_break_min * 60,
            }.get(phase, timers.work_duration_min * 60)
        color = _PHASE_COLORS[phase]
        self._phase_label.setText("●  " + t(_PHASE_KEYS[phase]))
        self._phase_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._progress.setStyleSheet(
            "QProgressBar { background: #2d3849; border: none; border-radius: 2px; }"
            f"QProgressBar::chunk {{ background: {color}; border-radius: 2px; }}"
        )
        self._start_btn.setText(
            t("widget.resume") if phase == Phase.PAUSED else t("widget.start")
        )
        running = phase in (Phase.WORKING, Phase.SHORT_BREAK, Phase.LONG_BREAK)
        self._start_btn.setVisible(not running)
        self._pause_btn.setVisible(running)
        self._skip_btn.setEnabled(running)
        self.update_time(self._remaining)

    def update_session_index(self, index: int) -> None:
        self._session_index = index
        self._cycle_label.setText(
            f"{index:02d} / {self._settings.timers.sessions_before_long_break:02d}"
        )

    def update_daily_count(self, count: int) -> None:
        self._daily_count = count
        self._count_label.setText(t("widget.today_count", count=count))

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#202d3c"))
        gradient.setColorAt(1, QColor("#141c2a"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#39485c"), 1))
        painter.drawRoundedRect(
            QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 18, 18
        )

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._leave_timer.stop()
        self._btn_container.show()
        self.setWindowOpacity(1.0)

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._leave_timer.start()

    def _on_leave_timeout(self) -> None:
        if not self.underMouse():
            self._btn_container.setVisible(not self._settings.ui.hover_reveal_buttons)
            self.setWindowOpacity(self._settings.ui.window_opacity)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_start is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(
                self._clamp_to_screen(
                    event.globalPosition().toPoint() - self._drag_start
                )
            )
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_start is not None:
            self._drag_start = None
            self._save_position()
        super().mouseReleaseEvent(event)

    def _menu(self) -> QMenu:
        menu = QMenu(self)
        menu.addAction(t("widget.menu.stats"), self.on_open_dashboard)
        menu.addAction(t("widget.menu.settings"), self.on_open_settings)
        menu.addSeparator()
        menu.addAction(t("widget.menu.reset"), self.on_reset)
        menu.addSeparator()
        menu.addAction(t("widget.menu.quit"), self.on_quit)
        return menu

    def _open_menu(self) -> None:
        menu = self._menu()
        menu.exec(self._menu_btn.mapToGlobal(self._menu_btn.rect().bottomLeft()))
        menu.deleteLater()

    def contextMenuEvent(self, event) -> None:
        menu = self._menu()
        menu.exec(event.globalPos())
        menu.deleteLater()

    def _restore_position(self) -> None:
        x, y = self._settings.ui.window_x, self._settings.ui.window_y
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        if x is None or y is None:
            rect = screen.availableGeometry()
            pos = QPoint(rect.right() - self.width() - 24, rect.top() + 64)
        else:
            pos = QPoint(x, y)
        self.move(self._clamp_to_screen(pos))

    def _clamp_to_screen(self, pos: QPoint) -> QPoint:
        screens = QApplication.screens()
        if not screens:
            return pos
        screen = QApplication.screenAt(pos)
        if screen is None:
            screen = min(
                screens,
                key=lambda s: (s.availableGeometry().center() - pos).manhattanLength(),
            )
        rect = screen.availableGeometry()
        return QPoint(
            max(rect.left(), min(pos.x(), rect.right() + 1 - self.width())),
            max(rect.top(), min(pos.y(), rect.bottom() + 1 - self.height())),
        )

    def _save_position(self) -> None:
        self._settings.ui.window_x, self._settings.ui.window_y = self.x(), self.y()
        if self._settings_service:
            self._settings_service.save(self._settings)

    def _toggle_pin(self) -> None:
        self._settings.ui.always_on_top = self._pin_btn.isChecked()
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, self._settings.ui.always_on_top
        )
        self.show()
        self._save_position()

    def _toggle_timer(self) -> None:
        if self._current_phase in (Phase.IDLE, Phase.PAUSED):
            self._on_start_click()
        else:
            self.on_pause()

    def _on_start_click(self) -> None:
        if self._current_phase == Phase.PAUSED:
            self.on_pause()
        else:
            self.on_start()

    def update_mute_state(self, is_muted: bool) -> None:
        self._mute_btn.setText(t("widget.muted") if is_muted else t("widget.sound"))
        self._mute_btn.setToolTip(t("widget.mute_hint"))
        self._mute_btn.setAccessibleName(t("widget.mute_hint"))

    def apply_settings(self, settings: AppSettings) -> None:
        was_visible = self.isVisible()
        self._settings = settings
        self.resize(
            max(300, settings.ui.window_width), max(248, settings.ui.window_height)
        )
        self._pause_btn.setText(t("widget.pause"))
        self._skip_btn.setText(t("widget.skip"))
        self._pin_btn.setText(t("widget.pin"))
        self._pin_btn.setToolTip(t("settings.checkbox.always_on_top"))
        self._pin_btn.setChecked(settings.ui.always_on_top)
        self._menu_btn.setToolTip(t("widget.menu.settings"))
        self._menu_btn.setAccessibleName(t("widget.menu.settings"))
        self._hint.setText(t("widget.drag_hint"))
        self._btn_container.setVisible(
            not settings.ui.hover_reveal_buttons or self.underMouse()
        )
        self.setWindowOpacity(settings.ui.window_opacity)
        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, settings.ui.always_on_top
        )
        self.update_mute_state(settings.behavior.is_muted)
        self.update_phase(self._current_phase)
        self.update_session_index(self._session_index)
        self.update_daily_count(self._daily_count)
        if self._current_phase == Phase.IDLE:
            self.update_time(settings.timers.work_duration_min * 60)
        if was_visible:
            self.show()
