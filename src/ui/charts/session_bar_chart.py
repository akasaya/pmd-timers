"""Bar chart widget for session statistics (T014)."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

try:
    from PyQt6.QtCharts import (
        QBarCategoryAxis,
        QBarSet,
        QBarSeries,
        QChart,
        QChartView,
        QValueAxis,
    )
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False

from PyQt6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from src.services.dashboard_viewmodel import DailyCount


class SessionBarChart(QWidget):
    """Bar chart showing daily session counts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._chart_view = None
        self._fallback_label = None

        if CHARTS_AVAILABLE:
            self._chart = QChart()
            self._chart.setTitle("セッション数")
            self._chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
            self._chart.legend().setVisible(False)
            self._chart_view = QChartView(self._chart)
            self._chart_view.setRenderHint(self._chart_view.renderHints())
            self._layout.addWidget(self._chart_view)
        else:
            self._text_chart_container = QWidget(self)
            self._text_chart_layout = QGridLayout(self._text_chart_container)
            self._text_chart_layout.setContentsMargins(4, 4, 4, 4)
            self._text_chart_layout.setSpacing(2)
            self._layout.addWidget(self._text_chart_container)
            # Initial empty state
            empty = QLabel("まだ記録がありません", self._text_chart_container)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: gray;")
            self._text_chart_layout.addWidget(empty, 0, 0, 1, 3)

    def update_data(self, daily_counts: "list[DailyCount]") -> None:
        if not CHARTS_AVAILABLE:
            self._build_text_chart(daily_counts)
            return
        if not daily_counts:
            return

        self._chart.removeAllSeries()
        for axis in self._chart.axes():
            self._chart.removeAxis(axis)

        bar_set = QBarSet("完了セッション数")
        bar_set.setColor(QColor("#4CAF50"))
        labels = []
        max_val = 0
        for dc in daily_counts:
            bar_set.append(dc.count)
            labels.append(dc.label)
            if dc.count > max_val:
                max_val = dc.count

        series = QBarSeries()
        series.append(bar_set)
        self._chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max(max_val + 1, 5))
        axis_y.setLabelFormat("%d")
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

    def _build_text_chart(self, daily_counts: "list[DailyCount]") -> None:
        """Text-based bar chart for environments without PyQt6-Qt6-Charts."""
        # Clear existing widgets
        while self._text_chart_layout.count():
            item = self._text_chart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not daily_counts or all(dc.count == 0 for dc in daily_counts):
            empty = QLabel("まだ記録がありません", self._text_chart_container)
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: gray;")
            self._text_chart_layout.addWidget(empty, 0, 0, 1, 3)
            return

        max_count = max(dc.count for dc in daily_counts) or 1
        bar_max = 12  # max bar width in characters

        for row, dc in enumerate(daily_counts):
            # Date label
            date_lbl = QLabel(dc.label, self._text_chart_container)
            date_lbl.setStyleSheet("font-size: 10px;")

            # Bar
            bar_len = int(dc.count / max_count * bar_max)
            bar_lbl = QLabel("█" * bar_len if bar_len > 0 else "▏", self._text_chart_container)
            bar_lbl.setStyleSheet("color: #4CAF50; font-size: 10px; letter-spacing: 0px;")

            # Count
            count_lbl = QLabel(str(dc.count), self._text_chart_container)
            count_lbl.setStyleSheet("font-size: 10px;")

            self._text_chart_layout.addWidget(date_lbl, row, 0)
            self._text_chart_layout.addWidget(bar_lbl, row, 1)
            self._text_chart_layout.addWidget(count_lbl, row, 2)
