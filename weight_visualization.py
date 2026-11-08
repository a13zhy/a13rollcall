from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy, QPushButton, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QLinearGradient, QFontDatabase

import skin_engine as S


def _c(key, fallback):
    try:
        value = S.current()["c"].get(key)
        return value if value else fallback
    except Exception:
        return fallback


def _f(key, fallback):
    try:
        value = S.current()["f"].get(key)
        return value if value else fallback
    except Exception:
        return fallback


def _fam():
    family = _f("family", "")
    if family:
        return family
    return "Microsoft YaHei"


def _font(size, bold=False):
    f = QFont(_fam(), int(size))
    f.setBold(bool(bold))
    return f


def _color(hex_value, alpha=None):
    color = QColor(hex_value)
    if alpha is not None:
        color.setAlpha(int(alpha))
    return color


class WeightBarWidget(QWidget):

    def __init__(self, student_name="", weight=1.0, max_weight=10.0, parent=None):
        super().__init__(parent)
        self.student_name = student_name
        self.weight = weight
        self.max_weight = max_weight
        self.setMinimumHeight(34)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_weight(self, weight):
        self.weight = weight
        self.update()

    def set_student_name(self, name):
        self.student_name = name
        self.update()

    def refresh_skin(self):
        self.update()

    def _fill_colors(self, ratio):
        if ratio > 0.7:
            return _c("success", "#4ee1a0"), _c("success_h", "#5a8c3e")
        if ratio > 0.4:
            return _c("primary", "#0067c0"), _c("primary_h", "#0078d4")
        return _c("warning", "#ca5010"), _c("danger", "#ff6b6b")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = int(self.width())
        h = int(self.height())
        padding = 8
        base_size = int(_f("size", 13))

        name_width = int(min(110, w * 0.32))
        bar_x = int(padding + name_width + 8)
        bar_width = int(w - bar_x - padding - 52)
        bar_height = 16
        bar_y = int((h - bar_height) // 2)

        painter.setPen(_color(_c("text", "#1b1b1b")))
        painter.setFont(_font(max(9, base_size - 3), True))
        painter.drawText(padding, 0, name_width, h, Qt.AlignVCenter | Qt.AlignLeft, self.student_name)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(_color(_c("card3", "#f0f0f0"))))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 4, 4)

        if self.max_weight > 0:
            ratio = min(1.0, self.weight / self.max_weight)
            fill_width = max(4, int(bar_width * ratio))
            start_color, end_color = self._fill_colors(ratio)
            gradient = QLinearGradient(float(bar_x), 0.0, float(bar_x + fill_width), 0.0)
            gradient.setColorAt(0.0, _color(start_color))
            gradient.setColorAt(1.0, _color(end_color))
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(bar_x, bar_y, fill_width, bar_height, 4, 4)

        weight_text = "%.1f" % self.weight
        painter.setPen(_color(_c("text2", "#666666")))
        painter.setFont(_font(max(8, base_size - 5)))
        painter.drawText(int(w - 52), 0, 44, h, Qt.AlignVCenter | Qt.AlignRight, weight_text)

        painter.end()


class WeightVisualizationWidget(QWidget):

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

        self.title = QLabel("抽取权重分布")
        header.addWidget(self.title)

        header.addStretch()

        self.summary_label = QLabel("")
        header.addWidget(self.summary_label)

        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.bars_layout = QVBoxLayout(self.container)
        self.bars_layout.setContentsMargins(0, 0, 0, 0)
        self.bars_layout.setSpacing(2)
        self.bars_layout.addStretch()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)

        self._bar_widgets = {}
        self.refresh_skin()

    def refresh_skin(self):
        base_size = int(_f("size", 13))
        self.title.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; font-weight: 700; color: %s; background: transparent;"
            % (_fam(), max(10, base_size - 1), _c("primary", "#0067c0"))
        )
        self.summary_label.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; color: %s; background: transparent;"
            % (_fam(), max(8, base_size - 3), _c("text3", "#666666"))
        )
        for widget in self._bar_widgets.values():
            widget.refresh_skin()

    def update_weights(self, students, weights):
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
            empty_label.setStyleSheet(
                "font-family: \"%s\"; color: %s; font-size: %dpx; padding: 20px; background: transparent;"
                % (_fam(), _c("text3", "#999999"), max(9, int(_f("size", 13)) - 2))
            )
            self.bars_layout.addWidget(empty_label)
        else:
            sorted_students = sorted(students, key=lambda s: weights.get(s, 0), reverse=True)
            for student in sorted_students:
                weight = weights.get(student, 1.0)
                bar = WeightBarWidget(student, weight, self._max_weight)
                bar.setFixedHeight(36)
                self._bar_widgets[student] = bar
                self.bars_layout.addWidget(bar)

        self.bars_layout.addStretch()

        total_weight = sum(weights.values()) if weights else 0
        avg_weight = total_weight / len(students) if students else 0
        self.summary_label.setText("共%d人 | 总权重%.1f | 平均%.1f" % (len(students), total_weight, avg_weight))

    def highlight_student(self, student_name):
        for name, bar in self._bar_widgets.items():
            if name == student_name:
                bar.setStyleSheet("background: %s; border-radius: 5px;" % _c("sel", "#e5f1fb"))
            else:
                bar.setStyleSheet("")

    def clear_highlight(self):
        for bar in self._bar_widgets.values():
            bar.setStyleSheet("")


class WeightDistributionDialog(QDialog):

    def __init__(self, students=None, weights=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("抽取权重分布")
        self.setMinimumSize(520, 600)
        self.resize(560, 650)
        self.setObjectName("settingsroot")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        self.title = QLabel("抽取权重分布")
        layout.addWidget(self.title)

        self.desc = QLabel("动态权重模式下，未被抽取的学生权重会逐渐增加，被抽取的学生权重会降低，确保抽取公平性。")
        self.desc.setWordWrap(True)
        layout.addWidget(self.desc)

        self.visualization = WeightVisualizationWidget()
        layout.addWidget(self.visualization, 1)

        if students and weights:
            self.visualization.update_weights(students, weights)

        self.refresh_skin()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("primary")
        close_btn.setFixedHeight(38)
        close_btn.setMinimumWidth(96)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def refresh_skin(self):
        base_size = int(_f("size", 13))
        self.title.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; font-weight: 800; color: %s; background: transparent;"
            % (_fam(), max(14, int(_f("h1", 21)) + 2), _c("primary", "#0067c0"))
        )
        self.desc.setStyleSheet(
            "font-family: \"%s\"; font-size: %dpx; color: %s; background: transparent;"
            % (_fam(), max(9, base_size - 2), _c("text3", "#666666"))
        )
        self.setStyleSheet("QDialog { background: %s; }" % _c("bg", "#f3f6fb"))
        self.visualization.refresh_skin()


def create_weight_visualization(parent=None):
    return WeightVisualizationWidget(parent)
