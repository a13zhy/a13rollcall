# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 统计图表组件
使用QPainter绘制饼图、柱状图等可视化统计图表
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QPainterPath, QFontMetrics


class PieChartWidget(QWidget):
    """饼图组件"""

    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.data = []
        self.colors = [
            "#107c10",
            "#ca5010",
            "#c42b1c",
            "#0067c0",
            "#8764b8",
            "#999999",
        ]
        self.setMinimumHeight(280)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_data(self, data):
        """
        设置饼图数据
        data: [(label, value), ...]
        """
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if self.title:
            painter.setPen(QColor("#333333"))
            painter.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
            painter.drawText(0, 0, w, 30, Qt.AlignCenter, self.title)

        chart_size = int(min(w - 200, h - 50))
        chart_x = int((w - 200 - chart_size) / 2)
        chart_y = int(35 + (h - 50 - chart_size) / 2)

        total = sum(v for _, v in self.data) if self.data else 0

        if total == 0:
            painter.setPen(QColor("#999999"))
            painter.setFont(QFont("Microsoft YaHei", 11))
            painter.drawText(chart_x, chart_y, chart_size, chart_size, Qt.AlignCenter, "暂无数据")
        else:
            start_angle = 90 * 16
            for i, (label, value) in enumerate(self.data):
                if value <= 0:
                    continue
                span_angle = int(-(value / total) * 360 * 16)
                color = QColor(self.colors[i % len(self.colors)])

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawPie(QRectF(chart_x, chart_y, chart_size, chart_size), start_angle, span_angle)
                start_angle += span_angle

            center_x = chart_x + chart_size / 2
            center_y = chart_y + chart_size / 2
            inner_size = int(chart_size * 0.55)
            inner_x = int(center_x - inner_size / 2)
            inner_y = int(center_y - inner_size / 2)

            painter.setBrush(QBrush(QColor("white")))
            painter.drawEllipse(inner_x, inner_y, inner_size, inner_size)

            painter.setPen(QColor("#333333"))
            painter.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
            painter.drawText(inner_x, inner_y, inner_size, inner_size, Qt.AlignCenter, str(total))

        legend_x = chart_x + chart_size + 30
        legend_y = chart_y + 10
        for i, (label, value) in enumerate(self.data):
            color = QColor(self.colors[i % len(self.colors)])
            y = legend_y + i * 28

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(legend_x, y, 14, 14, 3, 3)

            painter.setPen(QColor("#333333"))
            painter.setFont(QFont("Microsoft YaHei", 10))
            percent = (value / total * 100) if total > 0 else 0
            text = f"{label}: {value} ({percent:.1f}%)"
            painter.drawText(legend_x + 22, y, 180, 14, Qt.AlignVCenter | Qt.AlignLeft, text)

        painter.end()


class BarChartWidget(QWidget):
    """柱状图组件"""

    def __init__(self, title="", parent=None, max_items=10):
        super().__init__(parent)
        self.title = title
        self.data = []
        self.max_items = max_items
        self.bar_color = "#0067c0"
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, data):
        """
        设置柱状图数据
        data: [(label, value), ...]
        """
        self.data = data[:self.max_items]
        self.update()

    def set_bar_color(self, color):
        self.bar_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        if self.title:
            painter.setPen(QColor("#333333"))
            painter.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
            painter.drawText(0, 0, w, 30, Qt.AlignCenter, self.title)

        chart_top = 45
        chart_bottom = h - 50
        chart_left = 50
        chart_right = w - 20
        chart_height = chart_bottom - chart_top
        chart_width = chart_right - chart_left

        max_value = max((v for _, v in self.data), default=1)
        if max_value <= 0:
            max_value = 1

        painter.setPen(QPen(QColor("#e0e0e0"), 1))
        for i in range(5):
            y = chart_top + chart_height * i / 4
            painter.drawLine(chart_left, int(y), chart_right, int(y))
            value = int(max_value * (4 - i) / 4)
            painter.setPen(QColor("#999999"))
            painter.setFont(QFont("Microsoft YaHei", 9))
            painter.drawText(5, int(y) - 8, 40, 16, Qt.AlignRight | Qt.AlignVCenter, str(value))
            painter.setPen(QPen(QColor("#e0e0e0"), 1))

        if not self.data:
            painter.setPen(QColor("#999999"))
            painter.setFont(QFont("Microsoft YaHei", 11))
            painter.drawText(chart_left, chart_top, chart_width, chart_height, Qt.AlignCenter, "暂无数据")
        else:
            bar_count = len(self.data)
            bar_gap = 10
            bar_width = max(20, (chart_width - bar_gap * (bar_count + 1)) // bar_count)

            for i, (label, value) in enumerate(self.data):
                x = chart_left + bar_gap + i * (bar_width + bar_gap)
                bar_height = int(chart_height * value / max_value)
                y = chart_bottom - bar_height

                gradient = QLinearGradient(x, y, x, chart_bottom)
                gradient.setColorAt(0, QColor(self.bar_color))
                gradient.setColorAt(1, QColor(self.bar_color).lighter(130))

                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_height), 4, 4)

                painter.setPen(QColor("#333333"))
                painter.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
                painter.drawText(int(x), int(y) - 20, int(bar_width), 16, Qt.AlignCenter, str(value))

                painter.setPen(QColor("#666666"))
                painter.setFont(QFont("Microsoft YaHei", 9))
                short_label = label if len(label) <= 6 else label[:5] + "..."
                painter.drawText(int(x) - 5, chart_bottom + 5, int(bar_width) + 10, 30, Qt.AlignHCenter | Qt.AlignTop, short_label)

        painter.setPen(QPen(QColor("#cccccc"), 1))
        painter.drawLine(chart_left, chart_bottom, chart_right, chart_bottom)

        painter.end()


class StatsChartCard(QFrame):
    """统计图表卡片"""

    def __init__(self, title="", chart_widget=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e5e5e5;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #0067c0;")
            layout.addWidget(title_label)

        if chart_widget:
            self.chart = chart_widget
            layout.addWidget(self.chart, 1)
        else:
            self.chart = None


def create_pie_chart(title=""):
    """创建饼图的便捷函数"""
    return PieChartWidget(title)


def create_bar_chart(title="", max_items=10):
    """创建柱状图的便捷函数"""
    return BarChartWidget(title, max_items=max_items)
