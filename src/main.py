"""Application entry point."""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.engine.session import AppSettings, Phase
from src.engine.timer_engine import TimerEngine
from src.services.history_service import HistoryService
from src.services.notification_service import NotificationService
from src.services.settings_service import SettingsService
from src.services.bgm_service import BgmService
from src.services.sound_service import SoundService
from src.services.dashboard_viewmodel import DashboardViewModel
from src.ui.dashboard_window import DashboardWindow
from src.ui.settings_dialog import SettingsDialog
from src.ui.timer_widget import TimerWidget
from src.ui.tray_icon import TrayIcon


def main() -> None:
    # High DPI support (T029)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Services
    settings_svc = SettingsService()
    settings = settings_svc.load()
    history_svc = HistoryService()
    sound_svc = SoundService(settings)
    bgm_svc = BgmService(settings, app)
    notification_svc = NotificationService(sound_service=sound_svc)

    # Cleanup old history files (T030)
    history_svc.cleanup(keep_days=90)

    # Engine
    engine = TimerEngine(settings)

    # UI
    widget = TimerWidget(settings)
    widget._settings_service = settings_svc  # inject for position save
    tray = TrayIcon()
    tray.show()

    # Dashboard
    vm = DashboardViewModel(history_svc)
    dashboard: DashboardWindow | None = None

    def open_dashboard() -> None:
        nonlocal dashboard
        if dashboard is None or not dashboard.isVisible():
            dashboard = DashboardWindow(vm)
            # Connect real-time updates
            history_svc.session_recorded.connect(dashboard.refresh_stats)
            dashboard.show()
        else:
            dashboard.raise_()
            dashboard.activateWindow()

    def open_settings() -> None:
        dlg = SettingsDialog(settings, widget)
        if dlg.exec():
            new_settings = dlg.get_settings()
            settings_svc.save(new_settings)
            engine.update_settings(new_settings)
            widget.apply_settings(new_settings)
            sound_svc.reload()
            bgm_svc.reload()

    def toggle_mute() -> None:
        settings.behavior.is_muted = not settings.behavior.is_muted
        if settings.behavior.is_muted:
            bgm_svc.stop()
        settings_svc.save(settings)
        widget.update_mute_state(settings.behavior.is_muted)

    def quit_app() -> None:
        settings_svc.save(settings)
        app.quit()

    # Wire engine → widget
    engine.tick.connect(widget.update_time)
    engine.phase_changed.connect(
        lambda phase_val, idx: widget.update_phase(Phase(phase_val))
    )
    engine.phase_changed.connect(
        lambda phase_val, idx: tray.update_icon_for_phase(phase_val)
    )
    engine.phase_changed.connect(
        lambda phase_val, idx: bgm_svc.on_phase_changed(Phase(phase_val))
    )
    engine.daily_count_updated.connect(widget.update_daily_count)

    # Wire engine → history (T007)
    engine.session_completed.connect(history_svc.record_session)

    # Wire engine → notifications
    def _on_phase_changed(phase_val: str, idx: int) -> None:
        # Notification on session completion is handled in timer_engine advance
        pass

    # Wire widget callbacks
    widget.on_start = engine.start
    widget.on_pause = lambda: (engine.pause() if engine.phase != Phase.PAUSED else engine.resume())
    widget.on_reset = engine.reset
    widget.on_skip = engine.skip
    widget.on_mute = toggle_mute
    widget.on_open_settings = open_settings
    widget.on_open_dashboard = open_dashboard
    widget.on_quit = quit_app

    # Wire tray callbacks
    tray.set_callbacks(
        on_show=widget.show,
        on_dashboard=open_dashboard,
        on_settings=open_settings,
        on_quit=quit_app,
    )

    # Init display
    widget.update_time(settings.timers.work_duration_min * 60)
    widget.update_phase(Phase.IDLE)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
