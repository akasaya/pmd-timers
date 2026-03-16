"""Statistics dashboard window (T015-T018, T021-T022, T028)."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.services.dashboard_viewmodel import DashboardViewModel, Period
from src.services.i18n_service import t
from src.ui.charts.session_bar_chart import SessionBarChart


class _StatCard(QFrame):
    def __init__(self, title: str, value: str = "–", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        self._title = QLabel(title, self)
        self._title.setStyleSheet("color: #888; font-size: 11px;")
        self._value = QLabel(value, self)
        self._value.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(self._title)
        layout.addWidget(self._value)

    def set_value(self, value: str) -> None:
        self._value.setText(value)


class DashboardWindow(QWidget):
    def __init__(self, viewmodel: DashboardViewModel, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("dashboard.title"))
        self.resize(600, 500)
        self._vm = viewmodel
        self._current_period = Period.TODAY
        self._build_ui()
        self.refresh_stats()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Period filter buttons
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(t("dashboard.period.label")))
        self._period_group = QButtonGroup(self)
        for label, period in [
            (t("dashboard.period.today"), Period.TODAY),
            (t("dashboard.period.week"), Period.THIS_WEEK),
            (t("dashboard.period.month"), Period.THIS_MONTH),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedWidth(70)
            if period == Period.TODAY:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, p=period: self._on_period_changed(p))
            self._period_group.addButton(btn)
            filter_layout.addWidget(btn)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Today's stats cards
        today_group = QGroupBox(t("dashboard.today.title"))
        cards_layout = QGridLayout()
        self._card_completed = _StatCard(t("dashboard.stat.completed"))
        self._card_work_time = _StatCard(t("dashboard.stat.work_time"))
        self._card_breaks = _StatCard(t("dashboard.stat.breaks"))
        self._card_streak = _StatCard(t("dashboard.stat.streak"))
        cards_layout.addWidget(self._card_completed, 0, 0)
        cards_layout.addWidget(self._card_work_time, 0, 1)
        cards_layout.addWidget(self._card_breaks, 0, 2)
        cards_layout.addWidget(self._card_streak, 0, 3)
        today_group.setLayout(cards_layout)
        main_layout.addWidget(today_group)

        # Bar chart
        chart_group = QGroupBox(t("dashboard.chart.title"))
        chart_layout = QVBoxLayout()
        self._chart = SessionBarChart()
        self._chart.setMinimumHeight(180)
        chart_layout.addWidget(self._chart)
        chart_group.setLayout(chart_layout)
        main_layout.addWidget(chart_group)

        # Best day / streak info
        self._best_label = QLabel("", self)
        self._best_label.setStyleSheet("color: #888; font-size: 11px;")
        main_layout.addWidget(self._best_label)

        # Session detail list (shown when period == TODAY)
        detail_group = QGroupBox(t("dashboard.detail.title"))
        detail_layout = QVBoxLayout()
        self._detail_list = QListWidget()
        self._detail_list.setMaximumHeight(150)
        detail_layout.addWidget(self._detail_list)
        detail_group.setLayout(detail_layout)
        main_layout.addWidget(detail_group)
        self._detail_group = detail_group

        main_layout.addStretch()

    def _on_period_changed(self, period: Period) -> None:
        self._current_period = period
        self.refresh_stats()

    def refresh_stats(self) -> None:
        self._vm.refresh()
        today_stats = self._vm.get_today_stats()
        period_stats = self._vm.get_period_stats(self._current_period)

        # Update cards
        breaks_total = today_stats.short_breaks + today_stats.long_breaks
        self._card_completed.set_value(str(today_stats.completed_count))
        self._card_work_time.set_value(today_stats.total_work_time_str)
        self._card_breaks.set_value(str(breaks_total))
        self._card_streak.set_value(t("dashboard.stat.streak_unit", count=today_stats.current_streak_days))

        # Update chart
        if period_stats.daily_counts:
            self._chart.update_data(period_stats.daily_counts)

        # Best day info
        if period_stats.best_day_date:
            self._best_label.setText(
                t("dashboard.chart.best",
                  date=period_stats.best_day_date,
                  count=period_stats.best_day_count,
                  total=period_stats.total_completed)
            )
        else:
            self._best_label.setText(t("dashboard.no_data"))

        # Session detail (today only)
        self._detail_group.setVisible(self._current_period == Period.TODAY)
        if self._current_period == Period.TODAY:
            self._detail_list.clear()
            from src.engine.session import SessionStatus, SessionType
            sessions = self._vm.get_session_detail(today_stats.date)
            if not sessions:
                self._detail_list.addItem(t("dashboard.detail.no_records"))
            for s in sessions:
                if s.type == SessionType.WORK:
                    stype = t("dashboard.session.work")
                elif s.type == SessionType.SHORT_BREAK:
                    stype = t("dashboard.session.short_break")
                else:
                    stype = t("dashboard.session.long_break")
                status = "✓" if s.status == SessionStatus.COMPLETED else "✗"
                start = s.start_time[11:16] if s.start_time else "–"
                end = s.end_time[11:16] if s.end_time else "–"
                self._detail_list.addItem(f"{status} {stype}  {start}〜{end}")
