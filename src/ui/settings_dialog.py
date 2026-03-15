"""Settings dialog for timer and widget configuration (T024)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from src.engine.session import AppSettings


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

    def get_settings(self) -> AppSettings:
        return self._settings
