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

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

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
            self._fallback_label = QLabel("グラフ表示には PyQt6-Qt6-Charts が必要です", self)
            self._fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout.addWidget(self._fallback_label)

    def update_data(self, daily_counts: "list[DailyCount]") -> None:
        if not CHARTS_AVAILABLE or not daily_counts:
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
