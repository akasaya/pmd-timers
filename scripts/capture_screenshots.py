"""WindowsでREADME用の実UIを撮影する。ユーザーの設定・履歴は読み書きしない。"""

import argparse
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.engine.session import AppSettings, Phase
from src.engine.timer_engine import TimerEngine
from src.services.i18n_service import init
from src.ui.appearance import apply_appearance
from src.ui.timer_widget import TimerWidget


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("docs"))
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("WindowsのPythonで実行してください。")

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication([])
    apply_appearance(app)
    init("ja")
    settings = AppSettings()
    settings.ui.window_opacity = 1.0
    engine = TimerEngine(settings)
    widget = TimerWidget(settings)
    widget.on_start = engine.start
    widget.on_extra_work = engine.toggle_extra_work
    engine.tick.connect(widget.update_time)
    engine.phase_changed.connect(
        lambda phase, index: (
            widget.update_phase(Phase(phase)),
            widget.update_session_index(index),
        )
    )
    engine.daily_count_updated.connect(widget.update_daily_count)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(name: str, expected_time: str) -> None:
        engine._qt_timer.stop()
        app.processEvents()
        assert widget._time_label.text() == expected_time
        for child in (widget._time_label, widget._btn_container, widget._phase_label):
            assert widget.rect().contains(child.geometry())
        if widget._extra_work_btn.isVisible():
            assert widget.rect().contains(widget._extra_work_btn.geometry())
            assert (
                widget._extra_work_btn.width()
                >= widget._extra_work_btn.sizeHint().width()
            )
        target = args.output_dir / name
        assert widget.grab().save(str(target)), target
        print(f"Saved {target.name}: {expected_time}")

    try:
        widget.show()
        app.processEvents()
        widget._start_btn.click()
        engine._qt_timer.stop()
        # 撮影用に時間だけを進める。保存・通知・音声サービスには接続しない。
        for _ in range(300):
            engine._on_tick()
        capture("focus-windows-preview.png", "20:00")

        for _ in range(engine.remaining_sec):
            engine._on_tick()
        assert engine.phase == Phase.SHORT_BREAK
        assert widget._extra_work_btn.text() == "作業を続ける"
        capture("focus-windows-break.png", "05:00")

        widget._extra_work_btn.click()
        engine._qt_timer.stop()
        for _ in range(125):
            engine._on_tick()
        assert engine.phase == Phase.EXTRA_WORK
        assert widget._extra_work_btn.text() == "休憩に入る"
        capture("focus-windows-extra-work.png", "+02:05")

        widget._extra_work_btn.click()
        assert engine.phase == Phase.SHORT_BREAK
        assert engine.remaining_sec == settings.timers.short_break_min * 60
        assert engine.state.daily_completed_count == 1
    finally:
        engine._qt_timer.stop()
        widget.close()


if __name__ == "__main__":
    main()
