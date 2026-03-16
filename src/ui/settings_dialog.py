"""Settings dialog for timer and widget configuration (T024)."""
from __future__ import annotations

import wave
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
    QWidget,
)

from src.engine.session import AppSettings
from src.services.bgm_service import BgmService
from src.services.i18n_service import AUDIO_FILTER, t
from src.services.sound_service import SoundService

_MAX_SOUND_SEC = 5.0


def _wav_duration(path: str) -> float | None:
    """Return duration in seconds for a WAV file, or None on error."""
    try:
        with wave.open(path) as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        return None


def _ms_to_label(ms: int) -> str:
    return f"{ms / 1000:.1f}s"


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("settings.title"))
        self.setModal(True)
        self._settings = settings
        self._preview_svc = SoundService(settings, self)
        self._bgm_preview = BgmService(settings, self)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Timer group
        timer_group = QGroupBox(t("settings.group.timer"))
        timer_form = QFormLayout()

        self._work_spin = QSpinBox()
        self._work_spin.setRange(5, 90)
        self._work_spin.setSuffix(t("settings.suffix.minutes"))
        self._work_spin.setValue(self._settings.timers.work_duration_min)
        timer_form.addRow(t("settings.label.work_duration"), self._work_spin)

        self._short_spin = QSpinBox()
        self._short_spin.setRange(1, 30)
        self._short_spin.setSuffix(t("settings.suffix.minutes"))
        self._short_spin.setValue(self._settings.timers.short_break_min)
        timer_form.addRow(t("settings.label.short_break"), self._short_spin)

        self._long_spin = QSpinBox()
        self._long_spin.setRange(5, 60)
        self._long_spin.setSuffix(t("settings.suffix.minutes"))
        self._long_spin.setValue(self._settings.timers.long_break_min)
        timer_form.addRow(t("settings.label.long_break"), self._long_spin)

        self._sessions_spin = QSpinBox()
        self._sessions_spin.setRange(2, 10)
        self._sessions_spin.setValue(self._settings.timers.sessions_before_long_break)
        timer_form.addRow(t("settings.label.sessions_before_long"), self._sessions_spin)

        timer_group.setLayout(timer_form)
        layout.addWidget(timer_group)

        # UI group
        ui_group = QGroupBox(t("settings.group.widget"))
        ui_form = QFormLayout()

        self._opacity_label = QLabel(f"{int(self._settings.ui.window_opacity * 100)}%")
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(20, 100)
        self._opacity_slider.setValue(int(self._settings.ui.window_opacity * 100))
        self._opacity_slider.valueChanged.connect(
            lambda v: self._opacity_label.setText(f"{v}%")
        )
        ui_form.addRow(t("settings.label.opacity"), self._opacity_slider)
        ui_form.addRow("", self._opacity_label)
        opacity_hint = QLabel(t("settings.label.opacity_hint"))
        opacity_hint.setStyleSheet("color: gray; font-size: 10px;")
        ui_form.addRow("", opacity_hint)

        self._hover_check = QCheckBox(t("settings.checkbox.hover_buttons"))
        self._hover_check.setChecked(self._settings.ui.hover_reveal_buttons)
        ui_form.addRow(self._hover_check)

        self._ontop_check = QCheckBox(t("settings.checkbox.always_on_top"))
        self._ontop_check.setChecked(self._settings.ui.always_on_top)
        ui_form.addRow(self._ontop_check)

        self._notify_sound_check = QCheckBox(t("settings.checkbox.sound_enabled"))
        self._notify_sound_check.setChecked(self._settings.notifications.sound_enabled)
        ui_form.addRow(self._notify_sound_check)

        # Custom sound file row
        sound_row = QHBoxLayout()
        self._sound_name_label = QLabel(self._sound_display_name())
        self._sound_name_label.setStyleSheet("font-size: 10px; color: #555;")
        browse_btn = QPushButton(t("settings.button.browse"))
        browse_btn.setFixedWidth(50)
        browse_btn.clicked.connect(self._browse_sound)
        preview_btn = QPushButton("▶")
        preview_btn.setFixedWidth(30)
        preview_btn.clicked.connect(self._preview_sound)
        sound_row.addWidget(self._sound_name_label, 1)
        sound_row.addWidget(browse_btn)
        sound_row.addWidget(preview_btn)
        ui_form.addRow(t("settings.label.sound_file"), sound_row)

        self._sound_warn_label = QLabel(t("settings.label.sound_warn"))
        self._sound_warn_label.setStyleSheet("color: orange; font-size: 10px;")
        self._sound_warn_label.setVisible(self._is_sound_over_limit())
        ui_form.addRow("", self._sound_warn_label)

        # Start / end position sliders
        self._trim_widget = QWidget()
        trim_form = QFormLayout(self._trim_widget)
        trim_form.setContentsMargins(0, 0, 0, 0)

        dur_ms = self._current_sound_duration_ms()

        start_row = QHBoxLayout()
        self._start_slider = QSlider(Qt.Orientation.Horizontal)
        self._start_slider.setRange(0, dur_ms)
        self._start_slider.setSingleStep(100)
        self._start_slider.setPageStep(500)
        self._start_slider.setValue(self._settings.notifications.sound_start_ms)
        self._start_label = QLabel(_ms_to_label(self._settings.notifications.sound_start_ms))
        self._start_label.setFixedWidth(38)
        self._start_slider.valueChanged.connect(self._on_start_changed)
        start_row.addWidget(self._start_slider, 1)
        start_row.addWidget(self._start_label)
        trim_form.addRow(t("settings.label.sound_start"), start_row)

        end_row = QHBoxLayout()
        self._end_slider = QSlider(Qt.Orientation.Horizontal)
        self._end_slider.setRange(0, dur_ms)
        self._end_slider.setSingleStep(100)
        self._end_slider.setPageStep(500)
        end_val = self._settings.notifications.sound_end_ms or dur_ms
        self._end_slider.setValue(end_val)
        self._end_label = QLabel(_ms_to_label(end_val))
        self._end_label.setFixedWidth(38)
        self._end_slider.valueChanged.connect(self._on_end_changed)
        end_row.addWidget(self._end_slider, 1)
        end_row.addWidget(self._end_label)
        trim_form.addRow(t("settings.label.sound_end"), end_row)

        # Trim sliders only make sense for WAV files
        _init_path = self._settings.notifications.custom_sound_path
        self._trim_widget.setVisible(
            not _init_path or Path(_init_path).suffix.lower() == ".wav"
        )
        ui_form.addRow("", self._trim_widget)

        self._auto_start_check = QCheckBox(t("settings.checkbox.auto_start"))
        self._auto_start_check.setChecked(self._settings.behavior.auto_start_next_session)
        ui_form.addRow(self._auto_start_check)

        self._notify_desktop_check = QCheckBox(t("settings.checkbox.desktop_notify"))
        self._notify_desktop_check.setChecked(
            self._settings.notifications.desktop_notification_enabled
        )
        ui_form.addRow(self._notify_desktop_check)

        ui_group.setLayout(ui_form)
        layout.addWidget(ui_group)

        # BGM group
        bgm_group = QGroupBox(t("settings.group.bgm"))
        bgm_form = QFormLayout()

        # Work BGM
        work_row = QHBoxLayout()
        self._work_bgm_label = QLabel(self._bgm_display_name(self._settings.bgm.work_bgm_path))
        self._work_bgm_label.setStyleSheet("font-size: 10px; color: #555;")
        work_browse = QPushButton(t("settings.button.browse"))
        work_browse.setFixedWidth(50)
        work_browse.clicked.connect(self._browse_work_bgm)
        work_preview = QPushButton("▶")
        work_preview.setFixedWidth(30)
        work_preview.clicked.connect(self._preview_work_bgm)
        work_row.addWidget(self._work_bgm_label, 1)
        work_row.addWidget(work_browse)
        work_row.addWidget(work_preview)
        bgm_form.addRow(t("settings.label.work_bgm"), work_row)

        work_vol_row = QHBoxLayout()
        self._work_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._work_vol_slider.setRange(0, 100)
        self._work_vol_slider.setValue(int(self._settings.bgm.work_bgm_volume * 100))
        self._work_vol_label = QLabel(f"{int(self._settings.bgm.work_bgm_volume * 100)}%")
        self._work_vol_label.setFixedWidth(38)
        self._work_vol_slider.valueChanged.connect(
            lambda v: self._work_vol_label.setText(f"{v}%")
        )
        work_vol_row.addWidget(self._work_vol_slider, 1)
        work_vol_row.addWidget(self._work_vol_label)
        bgm_form.addRow(t("settings.label.volume"), work_vol_row)

        self._work_bgm_check = QCheckBox(t("settings.checkbox.work_bgm_enabled"))
        self._work_bgm_check.setChecked(self._settings.bgm.work_bgm_enabled)
        bgm_form.addRow(self._work_bgm_check)

        # Break BGM
        break_row = QHBoxLayout()
        self._break_bgm_label = QLabel(self._bgm_display_name(self._settings.bgm.break_bgm_path))
        self._break_bgm_label.setStyleSheet("font-size: 10px; color: #555;")
        break_browse = QPushButton(t("settings.button.browse"))
        break_browse.setFixedWidth(50)
        break_browse.clicked.connect(self._browse_break_bgm)
        break_preview = QPushButton("▶")
        break_preview.setFixedWidth(30)
        break_preview.clicked.connect(self._preview_break_bgm)
        break_row.addWidget(self._break_bgm_label, 1)
        break_row.addWidget(break_browse)
        break_row.addWidget(break_preview)
        bgm_form.addRow(t("settings.label.break_bgm"), break_row)

        break_vol_row = QHBoxLayout()
        self._break_vol_slider = QSlider(Qt.Orientation.Horizontal)
        self._break_vol_slider.setRange(0, 100)
        self._break_vol_slider.setValue(int(self._settings.bgm.break_bgm_volume * 100))
        self._break_vol_label = QLabel(f"{int(self._settings.bgm.break_bgm_volume * 100)}%")
        self._break_vol_label.setFixedWidth(38)
        self._break_vol_slider.valueChanged.connect(
            lambda v: self._break_vol_label.setText(f"{v}%")
        )
        break_vol_row.addWidget(self._break_vol_slider, 1)
        break_vol_row.addWidget(self._break_vol_label)
        bgm_form.addRow(t("settings.label.volume"), break_vol_row)

        self._break_bgm_check = QCheckBox(t("settings.checkbox.break_bgm_enabled"))
        self._break_bgm_check.setChecked(self._settings.bgm.break_bgm_enabled)
        bgm_form.addRow(self._break_bgm_check)

        bgm_group.setLayout(bgm_form)
        layout.addWidget(bgm_group)

        # General group (language selector)
        general_group = QGroupBox(t("settings.group.general"))
        general_form = QFormLayout()
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("日本語", "ja")
        self._lang_combo.addItem("English", "en")
        idx = self._lang_combo.findData(self._settings.general.language)
        self._lang_combo.setCurrentIndex(idx if idx >= 0 else 0)
        general_form.addRow(t("settings.label.language"), self._lang_combo)
        general_group.setLayout(general_form)
        layout.addWidget(general_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        reset_btn = QPushButton(t("settings.button.reset"))
        buttons.addButton(reset_btn, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        reset_btn.clicked.connect(self._reset)
        layout.addWidget(buttons)

    # ── Sound helpers ──────────────────────────────────────────────────

    def _current_sound_duration_ms(self) -> int:
        path = self._settings.notifications.custom_sound_path
        if not path or not Path(path).exists():
            path = SoundService.default_sound_path()
        dur = _wav_duration(path)
        return int((dur or 5.0) * 1000)

    def _sound_display_name(self) -> str:
        path = self._settings.notifications.custom_sound_path
        if path and Path(path).exists():
            return Path(path).name
        return t("settings.label.sound_default")

    def _is_sound_over_limit(self) -> bool:
        path = self._settings.notifications.custom_sound_path
        if not path or not Path(path).exists():
            return False
        dur = _wav_duration(path)
        return dur is not None and dur > _MAX_SOUND_SEC

    def _update_trim_sliders(self) -> None:
        """Refresh slider range after a sound file change."""
        dur_ms = self._current_sound_duration_ms()
        self._start_slider.setRange(0, dur_ms)
        self._end_slider.setRange(0, dur_ms)
        self._start_slider.setValue(0)
        self._end_slider.setValue(dur_ms)
        self._start_label.setText(_ms_to_label(0))
        self._end_label.setText(_ms_to_label(dur_ms))

    def _on_start_changed(self, value: int) -> None:
        self._start_label.setText(_ms_to_label(value))
        # Keep start < end
        if value >= self._end_slider.value():
            self._end_slider.setValue(min(value + 100, self._end_slider.maximum()))

    def _on_end_changed(self, value: int) -> None:
        self._end_label.setText(_ms_to_label(value))
        # Keep end > start
        if value <= self._start_slider.value():
            self._start_slider.setValue(max(value - 100, 0))

    def _browse_sound(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, t("settings.dialog.sound_title"), "", AUDIO_FILTER
        )
        if not path:
            return
        self._settings.notifications.custom_sound_path = path
        self._sound_name_label.setText(Path(path).name)
        is_wav = Path(path).suffix.lower() == ".wav"
        dur = _wav_duration(path) if is_wav else None
        over = dur is not None and dur > _MAX_SOUND_SEC
        self._sound_warn_label.setVisible(over)
        self._trim_widget.setVisible(is_wav)
        if is_wav:
            self._update_trim_sliders()

    def _preview_sound(self) -> None:
        # Temporarily reflect current UI state so preview respects it
        original_enabled = self._settings.notifications.sound_enabled
        original_start = self._settings.notifications.sound_start_ms
        original_end = self._settings.notifications.sound_end_ms
        self._settings.notifications.sound_enabled = self._notify_sound_check.isChecked()
        self._settings.notifications.sound_start_ms = self._start_slider.value()
        end_val = self._end_slider.value()
        dur_ms = self._current_sound_duration_ms()
        self._settings.notifications.sound_end_ms = 0 if end_val >= dur_ms else end_val
        self._preview_svc.reload()
        self._preview_svc.play()
        self._settings.notifications.sound_enabled = original_enabled
        self._settings.notifications.sound_start_ms = original_start
        self._settings.notifications.sound_end_ms = original_end

    # ── BGM helpers ───────────────────────────────────────────────────

    @staticmethod
    def _bgm_display_name(path: str) -> str:
        if path and Path(path).exists():
            return Path(path).name
        return t("settings.label.bgm_unset")

    def _browse_work_bgm(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, t("settings.dialog.work_bgm_title"), "", AUDIO_FILTER
        )
        if path:
            self._settings.bgm.work_bgm_path = path
            self._work_bgm_label.setText(Path(path).name)

    def _browse_break_bgm(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, t("settings.dialog.break_bgm_title"), "", AUDIO_FILTER
        )
        if path:
            self._settings.bgm.break_bgm_path = path
            self._break_bgm_label.setText(Path(path).name)

    def _preview_work_bgm(self) -> None:
        self._bgm_preview.stop()
        orig_path = self._settings.bgm.work_bgm_path
        orig_vol = self._settings.bgm.work_bgm_volume
        orig_enabled = self._settings.bgm.work_bgm_enabled
        self._settings.bgm.work_bgm_volume = self._work_vol_slider.value() / 100.0
        self._settings.bgm.work_bgm_enabled = True
        self._bgm_preview.reload()
        from src.engine.session import Phase
        self._bgm_preview.on_phase_changed(Phase.WORKING)
        self._settings.bgm.work_bgm_path = orig_path
        self._settings.bgm.work_bgm_volume = orig_vol
        self._settings.bgm.work_bgm_enabled = orig_enabled

    def _preview_break_bgm(self) -> None:
        self._bgm_preview.stop()
        orig_path = self._settings.bgm.break_bgm_path
        orig_vol = self._settings.bgm.break_bgm_volume
        orig_enabled = self._settings.bgm.break_bgm_enabled
        self._settings.bgm.break_bgm_volume = self._break_vol_slider.value() / 100.0
        self._settings.bgm.break_bgm_enabled = True
        self._bgm_preview.reload()
        from src.engine.session import Phase
        self._bgm_preview.on_phase_changed(Phase.SHORT_BREAK)
        self._settings.bgm.break_bgm_path = orig_path
        self._settings.bgm.break_bgm_volume = orig_vol
        self._settings.bgm.break_bgm_enabled = orig_enabled

    # ── Apply / Reset ─────────────────────────────────────────────────

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
        self._settings.notifications.sound_start_ms = self._start_slider.value()
        end_val = self._end_slider.value()
        dur_ms = self._current_sound_duration_ms()
        # Store 0 when end == file duration (means "end of file")
        self._settings.notifications.sound_end_ms = 0 if end_val >= dur_ms else end_val
        self._settings.behavior.auto_start_next_session = self._auto_start_check.isChecked()
        # BGM settings (paths already updated in _browse_* helpers)
        self._settings.bgm.work_bgm_enabled = self._work_bgm_check.isChecked()
        self._settings.bgm.work_bgm_volume = self._work_vol_slider.value() / 100.0
        self._settings.bgm.break_bgm_enabled = self._break_bgm_check.isChecked()
        self._settings.bgm.break_bgm_volume = self._break_vol_slider.value() / 100.0
        self._settings.general.language = self._lang_combo.currentData()
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
        self._sound_name_label.setText(t("settings.label.sound_default"))
        self._sound_warn_label.setVisible(False)
        self._update_trim_sliders()
        # Reset BGM
        self._settings.bgm.work_bgm_path = ""
        self._settings.bgm.break_bgm_path = ""
        self._work_bgm_label.setText(t("settings.label.bgm_unset"))
        self._break_bgm_label.setText(t("settings.label.bgm_unset"))
        self._work_bgm_check.setChecked(False)
        self._break_bgm_check.setChecked(False)
        self._work_vol_slider.setValue(50)
        self._break_vol_slider.setValue(50)
        self._bgm_preview.stop()
        self._auto_start_check.setChecked(defaults.behavior.auto_start_next_session)
        self._lang_combo.setCurrentIndex(self._lang_combo.findData("ja"))

    def get_settings(self) -> AppSettings:
        return self._settings
