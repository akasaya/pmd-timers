"""System tray icon and context menu."""
from __future__ import annotations

from PyQt6.QtGui import QColor, QIcon, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


def _make_icon(color: str = "#E53935") -> QIcon:
    px = QPixmap(16, 16)
    px.fill(QColor(color))
    return QIcon(px)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(_make_icon(), parent)
        self.setToolTip("PomodoroTimer")
        self._setup_menu()

    def _setup_menu(self) -> None:
        menu = QMenu()
        self._show_action = menu.addAction("ウィジェットを表示")
        menu.addSeparator()
        self._dashboard_action = menu.addAction("ダッシュボード")
        self._settings_action = menu.addAction("設定")
        menu.addSeparator()
        self._quit_action = menu.addAction("終了")
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
            "working": "#E53935",
            "short_break": "#43A047",
            "long_break": "#1E88E5",
            "paused": "#FFA726",
            "idle": "#607D8B",
        }
        color = colors.get(phase_value, "#607D8B")
        self.setIcon(_make_icon(color))
