"""Application entry point."""

from __future__ import annotations

import sys
from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.engine.session import Phase
from src.engine.timer_engine import TimerEngine
from src.services.bgm_service import BgmService
from src.services.dashboard_viewmodel import DashboardViewModel
from src.services.history_service import HistoryService
from src.services.i18n_service import init as init_i18n
from src.services.notification_service import NotificationService
from src.services.settings_service import SettingsService
from src.services.sound_service import SoundService
from src.ui.dashboard_window import DashboardWindow
from src.ui.settings_dialog import SettingsDialog
from src.ui.timer_widget import TimerWidget
from src.ui.tray_icon import TrayIcon, _make_icon


def main() -> None:
    # High DPI support (T029)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Focus Pomodoro")
    app.setWindowIcon(_make_icon())
    from src.ui.appearance import apply_appearance

    apply_appearance(app)
    if "--smoke-test" in sys.argv:
        from src.ui.smoke import run_smoke

        sys.exit(run_smoke(app, sys.argv[sys.argv.index("--smoke-test") + 1]))
    app.setQuitOnLastWindowClosed(False)

    # Services
    settings_svc = SettingsService()
    settings = settings_svc.load()
    init_i18n(settings.general.language)
    history_svc = HistoryService()
    sound_svc = SoundService(settings)
    bgm_svc = BgmService(settings, app)
    notification_svc = NotificationService(settings=settings, sound_service=sound_svc)

    # Engine
    engine = TimerEngine(settings)

    # UI
    widget = TimerWidget(settings)
    widget._settings_service = settings_svc  # inject for position save
    tray = TrayIcon()
    tray.show()
    notification_svc._tray = tray

    # Dashboard
    vm = DashboardViewModel(history_svc)
    dashboard: DashboardWindow | None = None

    def open_dashboard() -> None:
        nonlocal dashboard
        if dashboard is None or not dashboard.isVisible():
            dashboard = DashboardWindow(vm)
            history_svc.session_recorded.connect(dashboard.refresh_stats)
            dashboard.show()
        else:
            dashboard.raise_()
            dashboard.activateWindow()

    def open_settings() -> None:
        from copy import deepcopy

        dlg = SettingsDialog(deepcopy(settings), widget)
        if dlg.exec():
            new_settings = dlg.get_settings()
            # Services keep a reference to this shared settings object.
            settings.__dict__.update(new_settings.__dict__)
            new_settings = settings
            settings_svc.save(new_settings)
            engine.update_settings(new_settings)
            init_i18n(new_settings.general.language)
            widget.apply_settings(new_settings)
            widget.update_phase(engine.phase)
            refresh_today()
            sound_svc.reload()
            bgm_svc.reload()
            bgm_svc.on_phase_changed(engine.phase)
            widget.show()

    def toggle_mute() -> None:
        settings.behavior.is_muted = not settings.behavior.is_muted
        settings_svc.save(settings)
        widget.update_mute_state(settings.behavior.is_muted)
        if settings.behavior.is_muted:
            bgm_svc.stop()
        else:
            bgm_svc.on_phase_changed(engine.phase)

    def quit_app() -> None:
        bgm_svc.stop()
        settings_svc.save(settings)
        app.quit()

    # Reflect phase changes in the widget, tray icon and BGM (every transition,
    # including pause/resume/reset).
    def _on_phase_changed(phase_val: str, _idx: int) -> None:
        new_phase = Phase(phase_val)
        widget.update_phase(new_phase)
        widget.update_session_index(_idx)
        tray.update_icon_for_phase(phase_val)
        bgm_svc.on_phase_changed(new_phase)

    # Notification + sound fire only when a timer naturally expires (not on
    # manual skip/pause/reset), driven by the engine's phase_completed signal.
    def _on_phase_completed(from_phase: str, to_phase: str) -> None:
        notification_svc.notify_phase_change(from_phase, to_phase)

    # Wire engine signals
    engine.tick.connect(widget.update_time)
    engine.phase_changed.connect(_on_phase_changed)
    engine.phase_completed.connect(_on_phase_completed)
    engine.session_completed.connect(history_svc.record_session)

    def refresh_today() -> None:
        record = history_svc.load_daily(date.today().isoformat())
        widget.update_daily_count(record.work_sessions_completed if record else 0)

    history_svc.session_recorded.connect(refresh_today)
    from PyQt6.QtCore import QTimer

    day_timer = QTimer(app)
    day_timer.setInterval(30_000)
    day_timer.timeout.connect(refresh_today)
    day_timer.start()

    # Wire widget callbacks
    widget.on_start = engine.start
    widget.on_pause = lambda: (
        engine.pause() if engine.phase != Phase.PAUSED else engine.resume()
    )
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
    refresh_today()
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
