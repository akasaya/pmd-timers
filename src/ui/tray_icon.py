"""System tray icon and context menu."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from src.services.i18n_service import t


def _make_icon(color: str = "#86e1c3") -> QIcon:
    px = QPixmap(64, 64)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#1b2534"))
    painter.drawRoundedRect(0, 0, 64, 64, 15, 15)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(
        QPen(QColor(color), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
    )
    painter.drawEllipse(13, 15, 38, 38)
    painter.drawLine(27, 7, 37, 7)
    painter.drawLine(32, 24, 32, 35)
    painter.drawLine(32, 35, 41, 40)
    painter.end()
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(_make_icon(), parent)
        self.setToolTip("Focus Pomodoro")
        self._setup_menu()

    def _setup_menu(self) -> None:
        menu = QMenu()
        self._show_action = menu.addAction(t("tray.show_widget"))
        menu.addSeparator()
        self._dashboard_action = menu.addAction(t("tray.dashboard"))
        self._settings_action = menu.addAction(t("tray.settings"))
        menu.addSeparator()
        self._quit_action = menu.addAction(t("tray.quit"))
        self.setContextMenu(menu)

    def set_callbacks(
        self,
        on_show,
        on_dashboard,
        on_settings,
        on_quit,
    ) -> None:
        self._show_action.triggered.connect(on_show)
        self._dashboard_action.triggered.connect(on_dashboard)
        self._settings_action.triggered.connect(on_settings)
        self._quit_action.triggered.connect(on_quit)

    def update_icon_for_phase(self, phase_value: str) -> None:
        colors = {
            "working": "#86e1c3",
            "short_break": "#9bc9ff",
            "long_break": "#c5b3ff",
            "paused": "#f1c780",
            "idle": "#86e1c3",
        }
        color = colors.get(phase_value, "#607D8B")
        self.setIcon(_make_icon(color))
