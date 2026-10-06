# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 现代化错误提示对话框
美观的错误展示窗口，支持错误详情查看、复制、报告等功能
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QSizePolicy, QApplication, QWidget
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen, QIcon, QPixmap


class ErrorIconWidget(QWidget):
    """错误图标组件"""

    def __init__(self, error_type="error", parent=None):
        super().__init__(parent)
        self.error_type = error_type
        self.setFixedSize(64, 64)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        colors = {
            "error": ("#c42b1c", "#e81123"),
            "warning": ("#ca5010", "#ff8c00"),
            "info": ("#0067c0", "#0078d4"),
            "success": ("#107c10", "#0e6c0e")
        }
        color1, color2 = colors.get(self.error_type, colors["error"])

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(color1)))
        painter.drawEllipse(4, 4, 56, 56)

        painter.setBrush(QBrush(QColor(color2)))
        painter.drawEllipse(8, 8, 48, 48)

        painter.setPen(QPen(QColor("white"), 4, Qt.SolidLine, Qt.RoundCap))
        if self.error_type == "error":
            painter.drawLine(22, 22, 42, 42)
            painter.drawLine(42, 22, 22, 42)
        elif self.error_type == "warning":
            painter.drawLine(32, 18, 32, 36)
            painter.drawEllipse(30, 40, 4, 4)
        elif self.error_type == "info":
            painter.drawLine(32, 18, 32, 22)
            painter.drawEllipse(30, 14, 4, 4)
            painter.drawLine(32, 28, 32, 44)
        elif self.error_type == "success":
            painter.drawLine(20, 32, 28, 40)
            painter.drawLine(28, 40, 44, 24)

        painter.end()


class ModernErrorDialog(QDialog):
    """
    现代化错误提示对话框
    美观的错误展示，支持详情查看、复制、报告
    """

    def __init__(self, title="发生错误", message="", details="",
                 error_type="error", parent=None):
        super().__init__(parent)
        self.title_text = title
        self.message_text = message
        self.details_text = details
        self.error_type = error_type
        self._show_details = False
        self._setup_ui()
        self._setup_animation()

    def _setup_ui(self):
        self.setWindowTitle(self.title_text)
        self.setMinimumWidth(480)
        self.setMaximumWidth(600)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        main_container = QFrame()
        main_container.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)

        shadow_layout = QVBoxLayout(self)
        shadow_layout.setContentsMargins(12, 12, 12, 12)
        shadow_layout.addWidget(main_container)

        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        header = QHBoxLayout()
        header.setSpacing(16)

        self.icon_widget = ErrorIconWidget(self.error_type)
        header.addWidget(self.icon_widget)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(self.title_text)
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 800;
            color: #1a1a1a;
        """)
        text_layout.addWidget(title_label)

        if self.message_text:
            message_label = QLabel(self.message_text)
            message_label.setStyleSheet("""
                font-size: 13px;
                color: #666666;
            """)
            message_label.setWordWrap(True)
            text_layout.addWidget(message_label)

        header.addLayout(text_layout, 1)
        layout.addLayout(header)

        self.details_container = QFrame()
        self.details_container.setStyleSheet("""
            QFrame {
                background: #f8f8f8;
                border-radius: 8px;
                border: 1px solid #e8e8e8;
            }
        """)
        details_layout = QVBoxLayout(self.details_container)
        details_layout.setContentsMargins(12, 12, 12, 12)
        details_layout.setSpacing(8)

        details_header = QHBoxLayout()
        details_title = QLabel("错误详情")
        details_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #333;")
        details_header.addWidget(details_title)
        details_header.addStretch()
        details_layout.addLayout(details_header)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        self.details_text.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 8px;
                font-family: Consolas, monospace;
                font-size: 11px;
                color: #333;
            }
        """)
        self.details_text.setPlainText(self.details_text or "暂无详细信息")
        details_layout.addWidget(self.details_text)

        self.details_container.setVisible(False)
        layout.addWidget(self.details_container)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        if self.details_text:
            self.toggle_btn = QPushButton("显示详情")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #0067c0;
                    border: 1px solid #0067c0;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #e5f1fb;
                }
            """)
            self.toggle_btn.setCursor(Qt.PointingHandCursor)
            self.toggle_btn.clicked.connect(self._toggle_details)
            btn_layout.addWidget(self.toggle_btn)

            copy_btn = QPushButton("复制错误")
            copy_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #666;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: #f5f5f5;
                }
            """)
            copy_btn.setCursor(Qt.PointingHandCursor)
            copy_btn.clicked.connect(self._copy_error)
            btn_layout.addWidget(copy_btn)

        btn_layout.addStretch()

        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #0067c0;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 700;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #106ebe;
            }
            QPushButton:pressed {
                background: #005a9e;
            }
        """)
        ok_btn.setCursor(Qt.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        btn_layout.addWidget(ok_btn)

        layout.addLayout(btn_layout)

    def _setup_animation(self):
        self._opacity = 0.0
        self.setWindowOpacity(0.0)
        self._fade_timer = QTimer(self)
        self._fade_timer.timeout.connect(self._fade_in_step)
        self._fade_timer.start(16)

    def _fade_in_step(self):
        self._opacity += 0.08
        if self._opacity >= 1.0:
            self._opacity = 1.0
            self._fade_timer.stop()
        self.setWindowOpacity(self._opacity)

    def _toggle_details(self):
        self._show_details = not self._show_details
        self.details_container.setVisible(self._show_details)
        self.toggle_btn.setText("隐藏详情" if self._show_details else "显示详情")
        if self._show_details:
            self.setMinimumHeight(400)
        else:
            self.setMinimumHeight(0)
            self.adjustSize()

    def _copy_error(self):
        try:
            clipboard = QApplication.clipboard()
            error_info = f"错误标题: {self.title_text}\n错误信息: {self.message_text}\n\n错误详情:\n{self.details_text}"
            clipboard.setText(error_info)
            self._show_toast("错误信息已复制到剪贴板")
        except Exception as e:
            print(f"复制失败: {e}")

    def _show_toast(self, message):
        try:
            toast = QLabel(message, self)
            toast.setStyleSheet("""
                background: #333;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 12px;
            """)
            toast.adjustSize()
            x = (self.width() - toast.width()) // 2
            y = self.height() - 60
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(1500, toast.close)
        except Exception:
            pass


def show_error_dialog(title="发生错误", message="", details="",
                      error_type="error", parent=None):
    """显示现代化错误对话框的便捷函数"""
    dialog = ModernErrorDialog(title, message, details, error_type, parent)
    return dialog.exec_()


def show_exception_dialog(exception: Exception, title="程序异常", parent=None):
    """显示异常对话框的便捷函数"""
    import traceback
    details = traceback.format_exc()
    message = str(exception)
    return show_error_dialog(title, message, details, "error", parent)
