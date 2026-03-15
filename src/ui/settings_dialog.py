"""Settings dialog for timer and widget configuration (T024)."""
from __future__ import annotations

import wave
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from src.engine.session import AppSettings

_MAX_SOUND_SEC = 5.0


def _wav_duration(path: str) -> float | None:
    """Return duration in seconds for a WAV file, or None on error."""
    try:
        with wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return None


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setModal(True)
        self._settings = settings
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Timer group
        timer_group = QGroupBox("タイマー設定")
        timer_form = QFormLayout()

        self._work_spin = QSpinBox()
        self._work_spin.setRange(5, 90)
        self._work_spin.setSuffix(" 分")
        self._work_spin.setValue(self._settings.timers.work_duration_min)
        timer_form.addRow("作業時間:", self._work_spin)

        self._short_spin = QSpinBox()
        self._short_spin.setRange(1, 30)
        self._short_spin.setSuffix(" 分")
        self._short_spin.setValue(self._settings.timers.short_break_min)
        timer_form.addRow("短休憩:", self._short_spin)

        self._long_spin = QSpinBox()
        self._long_spin.setRange(5, 60)
        self._long_spin.setSuffix(" 分")
        self._long_spin.setValue(self._settings.timers.long_break_min)
        timer_form.addRow("長休憩:", self._long_spin)

        self._sessions_spin = QSpinBox()
        self._sessions_spin.setRange(2, 10)
        self._sessions_spin.setValue(self._settings.timers.sessions_before_long_break)
        timer_form.addRow("長休憩までのセッション数:", self._sessions_spin)

        timer_group.setLayout(timer_form)
        layout.addWidget(timer_group)

        # UI group
        ui_group = QGroupBox("ウィジェット設定")
        ui_form = QFormLayout()

        self._opacity_label = QLabel(f"{int(self._settings.ui.window_opacity * 100)}%")
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(20, 100)
        self._opacity_slider.setValue(int(self._settings.ui.window_opacity * 100))
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        ui_form.addRow("不透明度（表示の濃さ）:", self._opacity_slider)
        ui_form.addRow("", self._opacity_label)
        opacity_hint = QLabel("100%=くっきり / 20%=うっすら")
        opacity_hint.setStyleSheet("color: gray; font-size: 10px;")
        ui_form.addRow("", opacity_hint)

        self._hover_check = QCheckBox("ホバー時のみ操作ボタンを表示")
        self._hover_check.setChecked(self._settings.ui.hover_reveal_buttons)
        ui_form.addRow(self._hover_check)

        self._ontop_check = QCheckBox("常に最前面に表示")
        self._ontop_check.setChecked(self._settings.ui.always_on_top)
        ui_form.addRow(self._ontop_check)

        self._notify_sound_check = QCheckBox("通知音を鳴らす")
        self._notify_sound_check.setChecked(self._settings.notifications.sound_enabled)
        ui_form.addRow(self._notify_sound_check)

        # Custom sound file
        sound_row = QHBoxLayout()
        self._sound_name_label = QLabel(self._sound_display_name())
        self._sound_name_label.setStyleSheet("font-size: 10px; color: #555;")
        browse_btn = QPushButton("参照")
        browse_btn.setFixedWidth(50)
        browse_btn.clicked.connect(self._browse_sound)
        preview_btn = QPushButton("▶")
        preview_btn.setFixedWidth(30)
        preview_btn.clicked.connect(self._preview_sound)
        sound_row.addWidget(self._sound_name_label, 1)
        sound_row.addWidget(browse_btn)
        sound_row.addWidget(preview_btn)
        ui_form.addRow("通知音ファイル:", sound_row)

        self._sound_warn_label = QLabel("⚠ 5秒でカットされます")
        self._sound_warn_label.setStyleSheet("color: orange; font-size: 10px;")
        self._sound_warn_label.setVisible(self._is_sound_over_limit())
        ui_form.addRow("", self._sound_warn_label)

        self._notify_desktop_check = QCheckBox("デスクトップ通知を表示")
        self._notify_desktop_check.setChecked(
            self._settings.notifications.desktop_notification_enabled
        )
        ui_form.addRow(self._notify_desktop_check)

        ui_group.setLayout(ui_form)
        layout.addWidget(ui_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        reset_btn = QPushButton("デフォルトに戻す")
        buttons.addButton(reset_btn, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        reset_btn.clicked.connect(self._reset)
        layout.addWidget(buttons)

    def _sound_display_name(self) -> str:
        path = self._settings.notifications.custom_sound_path
        if path and Path(path).exists():
            return Path(path).name
        return "デフォルト（notification.wav）"

    def _is_sound_over_limit(self) -> bool:
        path = self._settings.notifications.custom_sound_path
        if not path or not Path(path).exists():
            return False
        dur = _wav_duration(path)
        return dur is not None and dur > _MAX_SOUND_SEC

    def _browse_sound(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "通知音ファイルを選択", "", "WAV files (*.wav)"
        )
        if not path:
            return
        self._settings.notifications.custom_sound_path = path
        self._sound_name_label.setText(Path(path).name)
        dur = _wav_duration(path)
        over = dur is not None and dur > _MAX_SOUND_SEC
        self._sound_warn_label.setVisible(over)

    def _preview_sound(self) -> None:
        from src.services.sound_service import SoundService
        svc = SoundService(self._settings, self)
        svc.play()

    def _apply(self) -> None:
        self._settings.timers.work_duration_min = self._work_spin.value()
        self._settings.timers.short_break_min = self._short_spin.value()
        self._settings.timers.long_break_min = self._long_spin.value()
        self._settings.timers.sessions_before_long_break = self._sessions_spin.value()
        self._settings.ui.window_opacity = self._opacity_slider.value() / 100.0
        self._settings.ui.hover_reveal_buttons = self._hover_check.isChecked()
        self._settings.ui.always_on_top = self._ontop_check.isChecked()
        self._settings.notifications.sound_enabled = self._notify_sound_check.isChecked()
        self._settings.notifications.desktop_notification_enabled = (
            self._notify_desktop_check.isChecked()
        )
        # custom_sound_path already updated in _browse_sound
        self.accept()

    def _reset(self) -> None:
        defaults = AppSettings()
        self._work_spin.setValue(defaults.timers.work_duration_min)
        self._short_spin.setValue(defaults.timers.short_break_min)
        self._long_spin.setValue(defaults.timers.long_break_min)
        self._sessions_spin.setValue(defaults.timers.sessions_before_long_break)
        self._opacity_slider.setValue(int(defaults.ui.window_opacity * 100))
        self._hover_check.setChecked(defaults.ui.hover_reveal_buttons)
        self._ontop_check.setChecked(defaults.ui.always_on_top)
        self._notify_sound_check.setChecked(defaults.notifications.sound_enabled)
        self._notify_desktop_check.setChecked(defaults.notifications.desktop_notification_enabled)
        self._settings.notifications.custom_sound_path = ""
        self._sound_name_label.setText("デフォルト（notification.wav）")
        self._sound_warn_label.setVisible(False)

    def get_settings(self) -> AppSettings:
        return self._settings
