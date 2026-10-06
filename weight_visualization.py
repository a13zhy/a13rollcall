# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 抽取权重可视化组件
动态显示每个学生的当前抽取权重，支持条形图和列表两种模式
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QPushButton, QButtonGroup, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient


class WeightBarWidget(QWidget):
    """单个学生的权重条形图"""

    def __init__(self, student_name="", weight=1.0, max_weight=10.0, parent=None):
        super().__init__(parent)
        self.student_name = student_name
        self.weight = weight
        self.max_weight = max_weight
        self.setMinimumHeight(32)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_weight(self, weight):
        self.weight = weight
        self.update()

    def set_student_name(self, name):
        self.student_name = name
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        padding = 8

        name_width = int(min(100, w * 0.3))
        bar_x = int(padding + name_width + 8)
        bar_width = int(w - bar_x - padding - 50)
        bar_height = 16
        bar_y = int((h - bar_height) // 2)

        painter.setPen(QColor("#333333"))
        painter.setFont(QFont("Microsoft YaHei", 9))
        painter.drawText(padding, 0, name_width, h, Qt.AlignVCenter | Qt.AlignLeft, self.student_name)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor("#f0f0f0")))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 4, 4)

        if self.max_weight > 0:
            ratio = min(1.0, self.weight / self.max_weight)
            fill_width = max(4, int(bar_width * ratio))

            gradient = QLinearGradient(bar_x, 0, bar_x + fill_width, 0)
            if ratio > 0.7:
                gradient.setColorAt(0, QColor("#107c10"))
                gradient.setColorAt(1, QColor("#0e6c0e"))
            elif ratio > 0.4:
                gradient.setColorAt(0, QColor("#0067c0"))
                gradient.setColorAt(1, QColor("#005a9e"))
            else:
                gradient.setColorAt(0, QColor("#ca5010"))
                gradient.setColorAt(1, QColor("#b04810"))

            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(bar_x, bar_y, fill_width, bar_height, 4, 4)

        weight_text = f"{self.weight:.1f}"
        painter.setPen(QColor("#666666"))
        painter.setFont(QFont("Microsoft YaHei", 8))
        painter.drawText(int(w - 50), 0, 42, h, Qt.AlignVCenter | Qt.AlignRight, weight_text)

        painter.end()


class WeightVisualizationWidget(QWidget):
    """
    抽取权重可视化组件
    显示所有学生的当前权重，支持动态更新
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._students = []
        self._weights = {}
        self._max_weight = 10.0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("抽取权重分布")
        title.setStyleSheet("font-size: 12px; font-weight: 700; color: #0067c0;")
        header.addWidget(title)

        header.addStretch()

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-size: 10px; color: #666666;")
        header.addWidget(self.summary_label)

        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.container = QWidget()
        self.bars_layout = QVBoxLayout(self.container)
        self.bars_layout.setContentsMargins(0, 0, 0, 0)
        self.bars_layout.setSpacing(2)
        self.bars_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        self._bar_widgets = {}

    def update_weights(self, students, weights):
        """
        更新权重显示
        students: 学生列表
        weights: {student_name: weight} 字典
        """
        self._students = students
        self._weights = weights

        if weights:
            self._max_weight = max(weights.values()) if weights else 10.0
            if self._max_weight <= 0:
                self._max_weight = 1.0

        for i in reversed(range(self.bars_layout.count())):
            item = self.bars_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        self._bar_widgets = {}

        if not students:
            empty_label = QLabel("暂无学生数据")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #999999; font-size: 11px; padding: 20px;")
            self.bars_layout.addWidget(empty_label)
        else:
            sorted_students = sorted(students, key=lambda s: weights.get(s, 0), reverse=True)
            for student in sorted_students:
                weight = weights.get(student, 1.0)
                bar = WeightBarWidget(student, weight, self._max_weight)
                self._bar_widgets[student] = bar
                self.bars_layout.addWidget(bar)

        self.bars_layout.addStretch()

        total_weight = sum(weights.values()) if weights else 0
        avg_weight = total_weight / len(students) if students else 0
        self.summary_label.setText(f"共{len(students)}人 | 总权重{total_weight:.1f} | 平均{avg_weight:.1f}")

    def highlight_student(self, student_name):
        """高亮显示某个学生"""
        for name, bar in self._bar_widgets.items():
            if name == student_name:
                bar.setStyleSheet("background: #e5f1fb; border-radius: 4px;")
            else:
                bar.setStyleSheet("")

    def clear_highlight(self):
        """清除所有高亮"""
        for bar in self._bar_widgets.values():
            bar.setStyleSheet("")


class WeightDistributionDialog(QDialog):
    """
    权重分布查看对话框
    全屏显示所有学生的权重分布
    """

    def __init__(self, students=None, weights=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("抽取权重分布")
        self.setMinimumSize(500, 600)
        self.resize(550, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("📊 抽取权重分布")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0067c0;")
        layout.addWidget(title)

        desc = QLabel("动态权重模式下，未被抽取的学生权重会逐渐增加，被抽取的学生权重会降低，确保抽取公平性。")
        desc.setStyleSheet("font-size: 11px; color: #666666;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.visualization = WeightVisualizationWidget()
        layout.addWidget(self.visualization, 1)

        if students and weights:
            self.visualization.update_weights(students, weights)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primary")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


def create_weight_visualization(parent=None):
    """创建权重可视化组件的工厂函数"""
    return WeightVisualizationWidget(parent)
