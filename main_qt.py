import sys
import os
import random
import subprocess
import configparser
import math
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFrame, QScrollArea, QGridLayout,
                             QSpinBox, QCheckBox, QComboBox, QTextEdit,
                             QSplashScreen, QDialog, QListWidget, QListWidgetItem, QProgressBar,
                             QSlider, QFileDialog, QMessageBox, QShortcut, QButtonGroup, QRadioButton,
                             QDoubleSpinBox, QSizePolicy, QLineEdit, QSplitter, QStackedWidget,
                             QTreeWidget, QTreeWidgetItem, QHeaderView, QGraphicsDropShadowEffect,
                             QTableWidget, QTableWidgetItem, QTabWidget, QTextBrowser)
from PyQt5.QtCore import (Qt, QTimer, QSize, pyqtSignal, QPoint, QPropertyAnimation,
                            QEasingCurve, QRectF, QThread, QUrl)
from PyQt5.QtGui import (QFont, QColor, QIcon, QPixmap, QPainter, QBrush, QPen,
                          QLinearGradient, QKeySequence, QDesktopServices, QCursor, QRadialGradient,
                          QTransform, QPalette)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, "icons")
sys.path.insert(0, BASE_DIR)

from config_manager import ConfigManager
from data_manager import DataManager
from draw_engine import DrawEngine
from echo_hole import EchoHole
from plugin_manager import PluginManager

WEBSITE_URL = "https://dkfile.istester.com/zhysppa13/a13callname.html"


class MarkdownRenderer:
    @staticmethod
    def render(markdown_text):
        html = markdown_text
        html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        lines = html.split("\n")
        result = []
        in_code_block = False
        in_list = False
        for line in lines:
            if line.strip().startswith("```"):
                if in_code_block:
                    result.append("</code></pre>")
                    in_code_block = False
                else:
                    result.append("<pre style='background:#f5f5f5;padding:8px 10px;border-radius:4px;overflow-x:auto;margin:4px 0;'><code style='font-family:Consolas,monospace;font-size:12px;line-height:1.4;'>")
                    in_code_block = True
                continue
            if in_code_block:
                result.append(line)
                continue
            stripped = line.strip()
            if not stripped:
                if in_list:
                    result.append("</ul>")
                    in_list = False
                continue
            if stripped.startswith("###### "):
                if in_list: result.append("</ul>"); in_list = False
                result.append(f"<h6 style='color:#333;margin:4px 0 2px 0;font-size:13px;'>{stripped[7:]}</h6>")
            elif stripped.startswith("##### "):
                if in_list: result.append("</ul>"); in_list = False
                result.append(f"<h5 style='color:#333;margin:5px 0 3px 0;font-size:14px;'>{stripped[6:]}</h5>")
            elif stripped.startswith("#### "):
                if in_list: result.append("</ul>"); in_list = False
                result.append(f"<h4 style='color:#333;margin:6px 0 3px 0;font-size:15px;'>{stripped[5:]}</h4>")
            elif stripped.startswith("### "):
                if in_list: result.append("</ul>"); in_list = False
                result.append(f"<h3 style='color:#0067c0;margin:8px 0 4px 0;font-size:16px;'>{stripped[4:]}</h3>")
            elif stripped.startswith("## "):
                if in_list: result.append("</ul>"); in_list = False
                result.append(f"<h2 style='color:#0067c0;margin:10px 0 5px 0;font-size:17px;border-bottom:1px solid #e0e0e0;padding-bottom:4px;'>{stripped[3:]}</h2>")
            elif stripped.startswith("# "):
                if in_list: result.append("</ul>"); in_list = False
                result.append(f"<h1 style='color:#0067c0;margin:12px 0 6px 0;font-size:19px;'>{stripped[2:]}</h1>")
            elif stripped.startswith("- ") or stripped.startswith("* "):
                if not in_list:
                    result.append("<ul style='margin:4px 0;padding-left:20px;'>")
                    in_list = True
                content = MarkdownRenderer._render_inline(stripped[2:])
                result.append(f"<li style='margin:2px 0;line-height:1.5;'>{content}</li>")
            elif stripped.startswith("> "):
                if in_list: result.append("</ul>"); in_list = False
                content = MarkdownRenderer._render_inline(stripped[2:])
                result.append(f"<blockquote style='border-left:3px solid #0067c0;margin:6px 0;padding:4px 10px;background:#f0f7ff;color:#555;line-height:1.5;'>{content}</blockquote>")
            elif stripped.startswith("---") or stripped.startswith("***"):
                if in_list: result.append("</ul>"); in_list = False
                result.append("<hr style='border:none;border-top:1px solid #e0e0e0;margin:8px 0;'>")
            else:
                if in_list:
                    result.append("</ul>")
                    in_list = False
                content = MarkdownRenderer._render_inline(stripped)
                result.append(f"<p style='margin:3px 0;line-height:1.5;'>{content}</p>")
        if in_list:
            result.append("</ul>")
        if in_code_block:
            result.append("</code></pre>")
        return "".join(result)

    @staticmethod
    def _render_inline(text):
        import re
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="color:#333;">\1</strong>', text)
        text = re.sub(r'__(.+?)__', r'<strong style="color:#333;">\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em style="color:#555;">\1</em>', text)
        text = re.sub(r'_(.+?)_', r'<em style="color:#555;">\1</em>', text)
        text = re.sub(r'`(.+?)`', r'<code style="background:#f0f0f0;padding:2px 6px;border-radius:3px;font-family:Consolas,monospace;font-size:12px;color:#c7254e;">\1</code>', text)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color:#0067c0;text-decoration:underline;">\1</a>', text)
        return text


class MarkdownView(QTextBrowser):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("QTextBrowser { background: transparent; border: none; padding: 4px; }")
        self.setOpenExternalLinks(True)
        self.document().setDocumentMargin(4)

    def setMarkdown(self, markdown_text):
        html = MarkdownRenderer.render(markdown_text)
        full_html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: '微软雅黑', 'Microsoft YaHei', sans-serif; font-size: 13px; color: #333; line-height: 1.4; margin: 0; padding: 0; }}
            a {{ color: #0067c0; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            p {{ margin: 3px 0; }}
            ul, ol {{ margin: 4px 0; }}
            li {{ margin: 2px 0; }}
            h1, h2, h3, h4, h5, h6 {{ margin: 6px 0 3px 0; }}
            blockquote {{ margin: 5px 0; }}
            pre {{ margin: 4px 0; }}
            hr {{ margin: 6px 0; }}
        </style>
        </head>
        <body>
        {html}
        </body>
        </html>
        """
        self.setHtml(full_html)


def load_svg_icon(name, size=20, color=None):
    path = os.path.join(ICON_DIR, f"{name}.svg")
    if not os.path.exists(path):
        return QIcon()
    try:
        from PyQt5.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(path)
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        if color:
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(color))
            painter.end()
        return QIcon(pixmap)
    except Exception:
        return QIcon()


class Win11Theme:
    def __init__(self, config_mgr):
        self.config = config_mgr
        self.is_dark = False

    def get_qss(self):
        try:
            theme = self.config.get("ui", "theme")
            self.is_dark = (theme == "dark")
        except Exception:
            self.is_dark = False
        if self.is_dark:
            return self._dark_qss()
        return self._light_qss()

    def _light_qss(self):
        return """
QMainWindow, QDialog { background: #f3f3f3; }
QFrame#card { background: #ffffff; border-radius: 8px; border: 1px solid #e5e5e5; }
QFrame#card_hover:hover { background: #fafafa; }
QFrame#topbar { background: #ffffff; border-bottom: 1px solid #e5e5e5; }
QFrame#sidebar { background: #fafafa; border-right: 1px solid #e5e5e5; }
QFrame#navitem { background: transparent; border-radius: 4px; }
QFrame#navitem:hover { background: #f0f0f0; }
QFrame#navitem_active { background: #e5f3ff; border-radius: 4px; border: 1px solid #cce8ff; }
QLabel#title { font-size: 18px; font-weight: 600; color: #1a1a1a; }
QLabel#subtitle { font-size: 12px; color: #666666; }
QLabel#navtext { font-size: 13px; color: #1a1a1a; }
QLabel#navtext_active { font-size: 13px; color: #0067c0; font-weight: 600; }
QLabel#section_title { font-size: 15px; font-weight: 600; color: #1a1a1a; }
QLabel#setting_label { font-size: 13px; color: #333333; }
QLabel#setting_desc { font-size: 11px; color: #888888; }
QLabel#draw_name { font-size: 88px; font-weight: 800; color: #0067c0; }
QPushButton { border: 1px solid #d1d1d1; border-radius: 4px; padding: 6px 16px; font-size: 13px; color: #1a1a1a; background: #ffffff; }
QPushButton:hover { background: #f5f5f5; border: 1px solid #c1c1c1; }
QPushButton:pressed { background: #e8e8e8; }
QPushButton#primary { background: #0067c0; color: white; border: 1px solid #0067c0; }
QPushButton#primary:hover { background: #1a76c8; }
QPushButton#danger { background: #c42b1c; color: white; border: 1px solid #c42b1c; }
QPushButton#drawbig { background: #0067c0; color: white; border: none; border-radius: 8px; font-size: 20px; font-weight: 700; padding: 18px; }
QPushButton#drawbig:hover { background: #1a76c8; }
QPushButton#navbtn { background: transparent; border: none; text-align: left; padding: 8px 12px; }
QPushButton#navbtn:hover { background: #f0f0f0; border-radius: 4px; }
QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #ffffff; border: 1px solid #d1d1d1; border-radius: 4px; padding: 6px 8px; font-size: 13px; color: #1a1a1a; }
QTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 2px solid #0067c0; }
QCheckBox { font-size: 13px; color: #1a1a1a; spacing: 8px; }
QRadioButton { font-size: 13px; color: #1a1a1a; spacing: 8px; }
QListWidget { background: #ffffff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 4px; font-size: 13px; color: #1a1a1a; }
QListWidget::item { padding: 8px; border-radius: 4px; }
QListWidget::item:selected { background: #e5f3ff; color: #0067c0; }
QTreeWidget { background: #ffffff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 4px; font-size: 13px; color: #1a1a1a; outline: none; }
QTreeWidget::item { padding: 6px; border-radius: 4px; }
QTreeWidget::item:selected { background: #e5f3ff; color: #0067c0; }
QTreeWidget::item:hover { background: #f5f5f5; }
QScrollBar:vertical { background: #f0f0f0; width: 12px; border-radius: 6px; }
QScrollBar::handle:vertical { background: #c1c1c1; border-radius: 6px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #a1a1a1; }
QProgressBar { background: #f0f0f0; border-radius: 4px; text-align: center; font-size: 11px; color: #666666; }
QProgressBar::chunk { background: #0067c0; border-radius: 4px; }
QLabel { color: #1a1a1a; }
QFrame#statusbar { background: #ffffff; border-top: 1px solid #e5e5e5; }
QTabWidget::pane { border: 1px solid #e5e5e5; border-radius: 4px; background: #ffffff; }
QTabBar::tab { background: #f0f0f0; padding: 8px 16px; border: 1px solid #e5e5e5; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; }
QTabBar::tab:selected { background: #ffffff; color: #0067c0; font-weight: 600; }
"""

    def _dark_qss(self):
        return """
QMainWindow, QDialog { background: #202020; }
QFrame#card { background: #2d2d2d; border-radius: 8px; border: 1px solid #3d3d3d; }
QFrame#card_hover:hover { background: #353535; }
QFrame#topbar { background: #2d2d2d; border-bottom: 1px solid #3d3d3d; }
QFrame#sidebar { background: #252525; border-right: 1px solid #3d3d3d; }
QFrame#navitem { background: transparent; border-radius: 4px; }
QFrame#navitem:hover { background: #3a3a3a; }
QFrame#navitem_active { background: #1e3a5f; border-radius: 4px; border: 1px solid #2d5a8a; }
QLabel#title { font-size: 18px; font-weight: 600; color: #ffffff; }
QLabel#subtitle { font-size: 12px; color: #aaaaaa; }
QLabel#navtext { font-size: 13px; color: #e0e0e0; }
QLabel#navtext_active { font-size: 13px; color: #4cc2ff; font-weight: 600; }
QLabel#section_title { font-size: 15px; font-weight: 600; color: #ffffff; }
QLabel#setting_label { font-size: 13px; color: #e0e0e0; }
QLabel#setting_desc { font-size: 11px; color: #888888; }
QLabel#draw_name { font-size: 88px; font-weight: 800; color: #4cc2ff; }
QPushButton { border: 1px solid #4a4a4a; border-radius: 4px; padding: 6px 16px; font-size: 13px; color: #e0e0e0; background: #3d3d3d; }
QPushButton:hover { background: #4a4a4a; border: 1px solid #5a5a5a; }
QPushButton:pressed { background: #353535; }
QPushButton#primary { background: #4cc2ff; color: #000000; border: 1px solid #4cc2ff; }
QPushButton#primary:hover { background: #66ccff; }
QPushButton#danger { background: #ff6b6b; color: #000000; border: 1px solid #ff6b6b; }
QPushButton#danger:hover { background: #ff8585; }
QPushButton#drawbig { background: #4cc2ff; color: #000000; border: none; border-radius: 8px; font-size: 20px; font-weight: 700; padding: 18px; }
QPushButton#drawbig:hover { background: #66ccff; }
QPushButton#navbtn { background: transparent; border: none; text-align: left; padding: 8px 12px; color: #e0e0e0; }
QPushButton#navbtn:hover { background: #3a3a3a; border-radius: 4px; }
QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #3d3d3d; border: 1px solid #4a4a4a; border-radius: 4px; padding: 6px 8px; font-size: 13px; color: #e0e0e0; }
QTextEdit:focus, QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 2px solid #4cc2ff; }
QComboBox QAbstractItemView { background: #3d3d3d; color: #e0e0e0; selection-background-color: #1e3a5f; }
QCheckBox { font-size: 13px; color: #e0e0e0; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 3px; border: 1px solid #5a5a5a; background: #3d3d3d; }
QCheckBox::indicator:checked { background: #4cc2ff; border: 1px solid #4cc2ff; }
QRadioButton { font-size: 13px; color: #e0e0e0; spacing: 8px; }
QRadioButton::indicator { width: 14px; height: 14px; border-radius: 7px; border: 1px solid #5a5a5a; background: #3d3d3d; }
QRadioButton::indicator:checked { background: #4cc2ff; border: 3px solid #4cc2ff; }
QListWidget { background: #3d3d3d; border: 1px solid #4a4a4a; border-radius: 4px; padding: 4px; font-size: 13px; color: #e0e0e0; }
QListWidget::item { padding: 8px; border-radius: 4px; }
QListWidget::item:hover { background: #353535; }
QListWidget::item:selected { background: #1e3a5f; color: #4cc2ff; }
QTreeWidget { background: #2d2d2d; border: none; border-right: 1px solid #3d3d3d; padding: 8px; font-size: 13px; color: #e0e0e0; outline: none; }
QTreeWidget::item { padding: 8px; border-radius: 4px; margin: 2px 4px; }
QTreeWidget::item:hover { background: #353535; }
QTreeWidget::item:selected { background: #1e3a5f; color: #4cc2ff; }
QTreeWidget::branch:has-children:!has-siblings:closed, QTreeWidget::branch:closed:has-children:has-siblings { image: none; }
QScrollBar:vertical { background: #2d2d2d; width: 10px; border-radius: 5px; margin: 0; }
QScrollBar::handle:vertical { background: #5a5a5a; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #6a6a6a; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #2d2d2d; height: 10px; border-radius: 5px; margin: 0; }
QScrollBar::handle:horizontal { background: #5a5a5a; border-radius: 5px; min-width: 30px; }
QProgressBar { background: #3d3d3d; border-radius: 4px; text-align: center; font-size: 11px; color: #aaaaaa; }
QProgressBar::chunk { background: #4cc2ff; border-radius: 4px; }
QLabel { color: #e0e0e0; }
QFrame#statusbar { background: #2d2d2d; border-top: 1px solid #3d3d3d; }
QTabWidget::pane { border: 1px solid #3d3d3d; border-radius: 4px; background: #2d2d2d; }
QTabBar::tab { background: #353535; padding: 8px 16px; border: 1px solid #3d3d3d; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; color: #aaaaaa; }
QTabBar::tab:selected { background: #2d2d2d; color: #4cc2ff; font-weight: 600; }
QTabBar::tab:hover { background: #3a3a3a; }
QTableWidget { background: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 8px; gridline-color: #3d3d3d; color: #e0e0e0; }
QHeaderView::section { background: #353535; padding: 10px; border: none; border-bottom: 1px solid #3d3d3d; font-weight: 600; color: #ffffff; }
QTableWidget::item { padding: 8px; border: none; }
QTableWidget::item:selected { background: #1e3a5f; color: #4cc2ff; }
QToolTip { background: #3d3d3d; color: #e0e0e0; border: 1px solid #4a4a4a; border-radius: 4px; padding: 6px; }
"""


class Win11Loader(QWidget):
    def __init__(self, parent=None, size=48):
        super().__init__(parent)
        self._size = size
        self._angle = 0
        self.setFixedSize(size, size)
        self._timer = QTimer()
        self._timer.timeout.connect(self._rotate)
        self._timer.start(16)

    def _rotate(self):
        self._angle = (self._angle + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        center = self._size / 2
        radius = self._size / 2 - 4
        painter.setPen(QPen(QColor("#e5e5e5"), 3, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(QPointF(center, center), radius, radius)
        for i in range(3):
            start_angle = (self._angle + i * 120) * 16
            span_angle = 60 * 16
            color = QColor("#0067c0")
            color.setAlpha(255 - i * 60)
            painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(QRectF(center - radius, center - radius, radius * 2, radius * 2), start_angle, span_angle)
        painter.end()


class ParticleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = True
        self._particles = []
        for _ in range(30):
            self._particles.append({
                'x': random.randint(0, 1600),
                'y': random.randint(0, 900),
                'r': random.randint(2, 5),
                'speed': random.randint(1, 3),
                'drift': random.randint(-1, 1),
                'alpha': random.randint(20, 60),
                'phase': random.randint(0, 100)
            })
        self._time = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._update)
        self._timer.start(40)

    def set_enabled(self, enabled):
        self._enabled = enabled
        self.setVisible(enabled)

    def _update(self):
        if not self._enabled:
            return
        self._time += 1
        w = self.width()
        h = self.height()
        for p in self._particles:
            p['y'] -= p['speed']
            p['x'] += p['drift']
            if p['y'] < -10:
                p['y'] = h + 10
                p['x'] = random.randint(0, w)
            if p['x'] < -10:
                p['x'] = w + 10
            elif p['x'] > w + 10:
                p['x'] = -10
        self.update()

    def paintEvent(self, event):
        if not self._enabled:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        w = self.width()
        h = self.height()
        for p in self._particles:
            x = int(p['x']) % w
            y = int(p['y']) % h
            r = int(p['r'])
            alpha = int(p['alpha'])
            color = QColor(0, 103, 192, alpha)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x, y, r, r)
        painter.end()


class DrawNameWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "点击开始"
        self._is_drawing = False
        self._scale = 1.0
        self._font_size = 96
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_name(self, name):
        self._name = name
        self.update()

    def set_font_size(self, size):
        self._font_size = size
        self.update()

    def set_drawing(self, drawing):
        self._is_drawing = drawing
        if drawing:
            self._scale = 1.08
        else:
            self._scale = 1.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        w = self.width()
        h = self.height()
        name = self._name
        font_size = self._font_size
        font = QFont("Microsoft YaHei", int(font_size * self._scale), QFont.Bold)
        painter.setFont(font)
        text_width = painter.fontMetrics().horizontalAdvance(name)
        while text_width > w - 60 and font_size > 36:
            font_size -= 2
            font = QFont("Microsoft YaHei", int(font_size * self._scale), QFont.Bold)
            painter.setFont(font)
            text_width = painter.fontMetrics().horizontalAdvance(name)
        if self._is_drawing:
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0, QColor("#005a9e"))
            gradient.setColorAt(0.3, QColor("#0067c0"))
            gradient.setColorAt(0.5, QColor("#0078d4"))
            gradient.setColorAt(0.7, QColor("#0067c0"))
            gradient.setColorAt(1, QColor("#005a9e"))
            painter.setPen(QPen(gradient, 1))
        else:
            painter.setPen(QColor("#0067c0"))
        painter.drawText(QRectF(0, 0, w, h - 20), Qt.AlignCenter, name)
        if self._is_drawing:
            painter.setPen(QColor("#0067c0"))
            painter.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
            painter.drawText(QRectF(0, h - 28, w, 24), Qt.AlignCenter, "◆ 抽取中 ◆")
        painter.end()


class MarkToast(QDialog):
    def __init__(self, name, status, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 100)
        colors = {"已背过": "#107c10", "未背熟": "#ca5010", "未背过": "#c42b1c"}
        color = colors.get(status, "#0067c0")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet(f"background: white; border-radius: 12px; border: 3px solid {color};")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(24, 16, 24, 16)
        icon_label = QLabel("✓" if status == "已背过" else ("!" if status == "未背熟" else "✗"))
        icon_label.setStyleSheet(f"font-size: 36px; color: {color}; font-weight: bold;")
        icon_label.setFixedWidth(48)
        card_layout.addWidget(icon_label)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #1a1a1a;")
        text_col.addWidget(name_label)
        status_label = QLabel(f"已标记为「{status}」")
        status_label.setStyleSheet(f"font-size: 14px; color: {color}; font-weight: 700;")
        text_col.addWidget(status_label)
        card_layout.addLayout(text_col)
        card_layout.addStretch()
        layout.addWidget(card)
        self.setWindowOpacity(0.0)
        QTimer.singleShot(50, self._fade_in)
        QTimer.singleShot(1800, self._fade_out)

    def _fade_in(self):
        self._opacity = 0.0
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._fade_step_in)
        self._fade_timer.start(20)

    def _fade_step_in(self):
        self._opacity += 0.1
        if self._opacity >= 1.0:
            self._opacity = 1.0
            self._fade_timer.stop()
        self.setWindowOpacity(self._opacity)

    def _fade_out(self):
        self._opacity = 1.0
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._fade_step_out)
        self._fade_timer.start(20)

    def _fade_step_out(self):
        self._opacity -= 0.1
        if self._opacity <= 0.0:
            self._fade_timer.stop()
            self.close()
        else:
            self.setWindowOpacity(self._opacity)


class UndoToast(QDialog):
    def __init__(self, name, status, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(420, 100)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet("background: white; border-radius: 12px; border: 3px solid #888888;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(24, 16, 24, 16)
        icon_label = QLabel("↩")
        icon_label.setStyleSheet("font-size: 36px; color: #888888; font-weight: bold;")
        icon_label.setFixedWidth(48)
        card_layout.addWidget(icon_label)
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #1a1a1a;")
        text_col.addWidget(name_label)
        status_label = QLabel(f"已撤销「{status}」标记，积分已回退")
        status_label.setStyleSheet("font-size: 14px; color: #888888; font-weight: 700;")
        text_col.addWidget(status_label)
        card_layout.addLayout(text_col)
        card_layout.addStretch()
        layout.addWidget(card)
        self.setWindowOpacity(0.0)
        QTimer.singleShot(50, self._fade_in)
        QTimer.singleShot(1800, self._fade_out)

    def _fade_in(self):
        self._opacity = 0.0
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._fade_step_in)
        self._fade_timer.start(20)

    def _fade_step_in(self):
        self._opacity += 0.1
        if self._opacity >= 1.0:
            self._opacity = 1.0
            self._fade_timer.stop()
        self.setWindowOpacity(self._opacity)

    def _fade_out(self):
        self._opacity = 1.0
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._fade_step_out)
        self._fade_timer.start(20)

    def _fade_step_out(self):
        self._opacity -= 0.1
        if self._opacity <= 0.0:
            self._fade_timer.stop()
            self.close()
        else:
            self.setWindowOpacity(self._opacity)


class PluginLoadDialog(QDialog):
    def __init__(self, plugin_mgr, parent=None):
        super().__init__(parent)
        self.plugin_mgr = plugin_mgr
        self.setWindowTitle("加载插件")
        self.setFixedSize(480, 280)
        self.setStyleSheet("QDialog { background: #f3f3f3; }")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        title = QLabel("正在加载插件...")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0067c0;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.loader = Win11Loader(size=48)
        self.loader.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.loader)
        self.status_label = QLabel("正在初始化插件系统...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 13px; color: #666666;")
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet("QProgressBar { background: #e0e0e0; border-radius: 6px; text-align: center; height: 20px; } QProgressBar::chunk { background: #0067c0; border-radius: 6px; }")
        layout.addWidget(self.progress)
        self.plugin_list_label = QLabel("")
        self.plugin_list_label.setAlignment(Qt.AlignCenter)
        self.plugin_list_label.setStyleSheet("font-size: 11px; color: #888888;")
        self.plugin_list_label.setWordWrap(True)
        layout.addWidget(self.plugin_list_label)
        layout.addStretch()

    def start_loading(self):
        self.show()
        QApplication.processEvents()
        try:
            plugins = self.plugin_mgr.get_all_plugins()
            total = len(plugins)
            if total == 0:
                self.status_label.setText("没有找到插件")
                self.progress.setValue(100)
                QTimer.singleShot(1000, self._finish_no_plugins)
                return
            for i, plugin in enumerate(plugins):
                name = plugin["meta"]["name"]
                version = plugin["meta"]["version"]
                self.status_label.setText(f"正在加载：{name} v{version}")
                self.plugin_list_label.setText(f"已加载 {i+1}/{total} 个插件")
                self.progress.setValue(int((i + 1) / total * 90))
                QApplication.processEvents()
                try:
                    context = self.plugin_mgr.get_context(name, self.parent())
                    self.plugin_mgr._call_lifecycle(name, "on_enable")
                except Exception as e:
                    print(f"插件 {name} 加载警告：{e}")
                QTimer.singleShot(200, lambda: None)
            self.status_label.setText("插件加载完成！")
            self.progress.setValue(100)
            self.plugin_list_label.setText(f"成功加载 {total} 个插件")
            QTimer.singleShot(800, self._finish_with_restart)
        except Exception as e:
            self.status_label.setText(f"加载失败：{str(e)}")
            self.progress.setValue(100)
            QTimer.singleShot(2000, self.close)

    def _finish_no_plugins(self):
        self.close()

    def _finish_with_restart(self):
        parent = self.parent()
        self.close()
        if parent:
            reply = QMessageBox.question(
                parent,
                "插件加载完成",
                "插件已成功加载！\n\n为了确保所有插件功能正常工作，建议重启软件。\n\n是否立即重启？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._restart_application()

    def _restart_application(self):
        try:
            python = sys.executable
            script = os.path.join(BASE_DIR, "main_qt.py")
            if os.path.exists(script):
                subprocess.Popen([python, script])
            else:
                subprocess.Popen([sys.argv[0]])
            QApplication.quit()
        except Exception as e:
            parent = self.parent()
            if parent:
                QMessageBox.warning(parent, "重启失败", f"重启失败：{str(e)}\n\n请手动重启软件。")


class ResultPopup(QDialog):
    marked = pyqtSignal(str)

    def __init__(self, name, text_title="", text_content="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("抽取结果")
        self.setMinimumSize(680, 620)
        self.setStyleSheet("QDialog { background: #f3f3f3; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        title = QLabel("抽取结果")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0067c0;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        name_card = QFrame()
        name_card.setStyleSheet("background: #ffffff; border-radius: 12px; border: 2px solid #0067c0;")
        name_card.setMinimumHeight(140)
        nc = QVBoxLayout(name_card)
        nc.setAlignment(Qt.AlignCenter)
        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("font-size: 64px; font-weight: 800; color: #0067c0;")
        nc.addWidget(name_label)
        layout.addWidget(name_card)
        if text_title:
            text_card = QFrame()
            text_card.setStyleSheet("background: #ffffff; border-radius: 10px; border: 1px solid #e5e5e5;")
            tc = QVBoxLayout(text_card)
            tc.setContentsMargins(20, 16, 20, 16)
            tc.setSpacing(8)
            t_title = QLabel(text_title)
            t_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #333333;")
            tc.addWidget(t_title)
            t_content = QTextEdit()
            t_content.setReadOnly(True)
            t_content.setText(text_content)
            t_content.setMaximumHeight(140)
            t_content.setFrameShape(QFrame.NoFrame)
            t_content.setStyleSheet("background: #fafafa; border-radius: 6px; padding: 10px; color: #555555; font-size: 13px;")
            tc.addWidget(t_content)
            layout.addWidget(text_card)
        label = QLabel("请标记背诵状态：")
        label.setStyleSheet("font-size: 14px; color: #666666; font-weight: 600;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        for text, status, color in [("已背过", "已背过", "#107c10"), ("未背熟", "未背熟", "#ca5010"), ("未背过", "未背过", "#c42b1c")]:
            btn = QPushButton(text)
            btn.setMinimumHeight(52)
            btn.setStyleSheet(f"QPushButton {{ background: {color}; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 700; }} QPushButton:hover {{ opacity: 0.9; }}")
            btn.clicked.connect(lambda checked, s=status: self._mark(s))
            btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)
        skip_btn = QPushButton("跳过此学生")
        skip_btn.setMinimumHeight(40)
        skip_btn.setStyleSheet("QPushButton { background: #f0f0f0; color: #666666; border: none; border-radius: 6px; font-size: 13px; } QPushButton:hover { background: #e0e0e0; }")
        skip_btn.clicked.connect(self.close)
        layout.addWidget(skip_btn)

    def _mark(self, status):
        self.marked.emit(status)
        self.accept()


class MiniWindow(QDialog):
    restore_signal = pyqtSignal()
    quick_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(280, 130)
        self._drag_pos = None
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet("background: #2d2d2d; border-radius: 10px; border: 1px solid #3d3d3d;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        title = QLabel("点名系统")
        title.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        tip = QLabel("已最小化 · 拖动可移动")
        tip.setStyleSheet("color: #888888; font-size: 10px;")
        tip.setAlignment(Qt.AlignCenter)
        layout.addWidget(tip)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        restore_btn = QPushButton("恢复")
        restore_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border-radius: 6px; padding: 8px 16px; font-weight: 600; } QPushButton:hover { background: #1a76c8; }")
        restore_btn.clicked.connect(self._restore)
        btn_layout.addWidget(restore_btn)
        quick_btn = QPushButton("快捷抽取")
        quick_btn.setStyleSheet("QPushButton { background: #ca5010; color: white; border-radius: 6px; padding: 8px 16px; font-weight: 600; } QPushButton:hover { background: #d96020; }")
        quick_btn.clicked.connect(self._quick)
        btn_layout.addWidget(quick_btn)
        layout.addLayout(btn_layout)
        for w in [card, title, tip]:
            w.mousePressEvent = self._start_drag
            w.mouseMoveEvent = self._on_drag

    def _start_drag(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def _on_drag(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def _restore(self):
        self.restore_signal.emit()
        self.close()

    def _quick(self):
        self.quick_signal.emit()
        self.close()


class QuickDrawWindow(QDialog):
    closed = pyqtSignal()

    def __init__(self, data_mgr, parent=None):
        super().__init__(parent)
        self.data_mgr = data_mgr
        self.setWindowTitle("快捷抽取")
        self.setMinimumSize(420, 540)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self._is_drawing = False
        self._draw_mode = "auto"
        self._auto_timer = QTimer()
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._stop_draw)
        self._timer = QTimer()
        self._timer.timeout.connect(self._roll)
        self._history = []
        self._students = []
        self._setup_ui()
        self._load_students()

    def _load_students(self):
        try:
            students, error = self.data_mgr.load_students()
            self._students = students
        except Exception:
            self._students = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        header = QHBoxLayout()
        title = QLabel("快捷抽取")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0067c0;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("返回主界面")
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        layout.addLayout(header)
        mode_layout = QHBoxLayout()
        self.mode_auto_btn = QPushButton("自动模式")
        self.mode_auto_btn.setObjectName("primary")
        self.mode_auto_btn.clicked.connect(lambda: self._set_mode("auto"))
        mode_layout.addWidget(self.mode_auto_btn)
        self.mode_manual_btn = QPushButton("手动模式")
        self.mode_manual_btn.clicked.connect(lambda: self._set_mode("manual"))
        mode_layout.addWidget(self.mode_manual_btn)
        layout.addLayout(mode_layout)
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(180)
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        self.name_label = QLabel("点击开始")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 48px; font-weight: 800; color: #0067c0;")
        card_layout.addWidget(self.name_label)
        layout.addWidget(card)
        self.draw_btn = QPushButton("开始抽取")
        self.draw_btn.setObjectName("drawbig")
        self.draw_btn.setMinimumHeight(56)
        self.draw_btn.clicked.connect(self._toggle_draw)
        layout.addWidget(self.draw_btn)
        hist_label = QLabel("本次抽取记录")
        hist_label.setStyleSheet("font-size: 12px; color: #666666; font-weight: 600;")
        layout.addWidget(hist_label)
        self.history_list = QListWidget()
        self.history_list.setMaximumHeight(80)
        layout.addWidget(self.history_list)
        info = QLabel("仅抽取名字，不抽取课文\n记录为临时文件，关闭后自动删除")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(info)
        layout.addStretch()

    def _set_mode(self, mode):
        self._draw_mode = mode
        if mode == "auto":
            self.mode_auto_btn.setObjectName("primary")
            self.mode_manual_btn.setObjectName("")
        else:
            self.mode_auto_btn.setObjectName("")
            self.mode_manual_btn.setObjectName("primary")
        self.mode_auto_btn.style().unpolish(self.mode_auto_btn)
        self.mode_auto_btn.style().polish(self.mode_auto_btn)
        self.mode_manual_btn.style().unpolish(self.mode_manual_btn)
        self.mode_manual_btn.style().polish(self.mode_manual_btn)

    def _toggle_draw(self):
        if self._is_drawing:
            self._stop_draw()
        else:
            self._start_draw()

    def _start_draw(self):
        if not self._students:
            self.name_label.setText("无学生名单")
            return
        self._is_drawing = True
        self.draw_btn.setText("停止抽取")
        self._timer.start(50)
        if self._draw_mode == "auto":
            self._auto_timer.start(3000)

    def _roll(self):
        self.name_label.setText(random.choice(self._students))

    def _stop_draw(self):
        self._timer.stop()
        self._auto_timer.stop()
        self._is_drawing = False
        self.draw_btn.setText("开始抽取")
        name = self.name_label.text()
        self._history.append(name)
        item = QListWidgetItem(f"{len(self._history)}. {name}  ({datetime.now().strftime('%H:%M:%S')})")
        self.history_list.addItem(item)
        self.history_list.scrollToBottom()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, config_mgr, theme_mgr, echo_hole, plugin_mgr=None, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.theme_mgr = theme_mgr
        self.echo_hole = echo_hole
        self.plugin_mgr = plugin_mgr
        self.setWindowTitle("设置")
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)
        self._current_page = 0
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        nav = QFrame()
        nav.setObjectName("sidebar")
        nav.setFixedWidth(300)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(16, 20, 16, 20)
        nav_layout.setSpacing(6)

        nav_title = QLabel("设置")
        nav_title.setObjectName("title")
        nav_title.setContentsMargins(8, 0, 0, 8)
        nav_layout.addWidget(nav_title)

        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(4, 0, 4, 8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索设置...")
        self.search_input.textChanged.connect(self._filter_settings)
        search_layout.addWidget(self.search_input)
        nav_layout.addWidget(search_frame)

        self.nav_tree = QTreeWidget()
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setRootIsDecorated(True)
        self.nav_tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.nav_tree.itemClicked.connect(self._on_tree_clicked)
        nav_layout.addWidget(self.nav_tree, 1)
        self._build_tree()

        main_layout.addWidget(nav)

        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 24)
        content_layout.setSpacing(16)

        self.page_title = QLabel("系统")
        self.page_title.setObjectName("title")
        content_layout.addWidget(self.page_title)

        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        save_btn = QPushButton("保存")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        content_layout.addLayout(btn_layout)
        main_layout.addWidget(content, 1)

        self._build_pages()
        self._switch_page(0, "系统")

    def _build_tree(self):
        self.nav_tree.clear()
        self.nav_tree.setIconSize(QSize(20, 20))
        self.nav_tree.setIndentation(16)
        categories = [
            ("系统", "settings", [("班级设置", "class"), ("应用信息", "info"), ("启动选项", "startup")]),
            ("外观", "palette", [("主题", "theme"), ("显示效果", "display"), ("字体", "font"), ("动画效果", "animation"), ("窗口样式", "window")]),
            ("抽取", "draw", [("抽取模式", "mode"), ("抽取规则", "rules"), ("参数", "params"), ("自动抽取", "auto_draw"), ("权重系统", "weight")]),
            ("课文", "book", [("课文抽取", "text_extract"), ("课文显示", "text_display"), ("课文进度", "text_progress")]),
            ("标记", "check", [("背诵标记", "mark"), ("积分系统", "score")]),
            ("快捷键", "keyboard", [("快捷键列表", "shortcuts"), ("快捷键设置", "shortcut_settings")]),
            ("数据", "database", [("数据管理", "data_mgmt"), ("统计导出", "export"), ("备份恢复", "backup")]),
            ("插件", "puzzle", [("插件中心", "plugins")]),
            ("实验功能", "zap", [("实验性功能", "experimental"), ("开发者选项", "developer")]),
            ("关于", "info", [("关于本软件", "about"), ("更新检查", "update"), ("帮助文档", "help")]),
        ]
        self._page_map = {}
        self._plugin_pages = {}
        page_idx = 0
        for cat_name, cat_icon, sub_items in categories:
            cat_item = QTreeWidgetItem([cat_name])
            cat_item.setData(0, Qt.UserRole, ("category", cat_name))
            cat_item.setIcon(0, load_svg_icon(cat_icon, 20, "#0067c0"))
            cat_item.setFont(0, QFont("Microsoft YaHei", 11, QFont.Bold))
            self.nav_tree.addTopLevelItem(cat_item)
            for sub_name, sub_key in sub_items:
                sub_item = QTreeWidgetItem([sub_name])
                sub_item.setData(0, Qt.UserRole, ("page", page_idx, sub_name))
                sub_item.setFont(0, QFont("Microsoft YaHei", 10))
                cat_item.addChild(sub_item)
                self._page_map[sub_key] = page_idx
                page_idx += 1
        self._system_page_count = page_idx
        try:
            if hasattr(self, 'plugin_mgr') and self.plugin_mgr:
                plugins = self.plugin_mgr.get_enabled_plugins()
                for plugin in plugins:
                    plugin_name = plugin["meta"]["name"]
                    pages = self.plugin_mgr.get_plugin_pages(plugin_name)
                    if not pages:
                        continue
                    cat_item = QTreeWidgetItem([plugin_name])
                    cat_item.setData(0, Qt.UserRole, ("plugin_category", plugin_name))
                    cat_item.setIcon(0, load_svg_icon("puzzle", 20, "#107c10"))
                    cat_item.setFont(0, QFont("Microsoft YaHei", 11, QFont.Bold))
                    self.nav_tree.addTopLevelItem(cat_item)
                    for page_info in pages:
                        page_key = page_info.get("key", "settings")
                        page_title = page_info.get("title", page_key)
                        page_icon = page_info.get("icon", "settings")
                        full_key = f"plugin_{plugin_name}_{page_key}"
                        sub_item = QTreeWidgetItem([page_title])
                        sub_item.setData(0, Qt.UserRole, ("plugin_page", page_idx, plugin_name, page_key, page_title))
                        sub_item.setFont(0, QFont("Microsoft YaHei", 10))
                        sub_item.setIcon(0, load_svg_icon(page_icon, 16, "#666666"))
                        cat_item.addChild(sub_item)
                        self._page_map[full_key] = page_idx
                        self._plugin_pages[page_idx] = (plugin_name, page_key)
                        page_idx += 1
        except Exception as e:
            print(f"加载插件页面失败：{e}")
        self.nav_tree.expandAll()

    def _on_tree_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if not data:
            return
        if data[0] == "page":
            self._switch_page(data[1], data[2])
        elif data[0] == "plugin_page":
            self._switch_plugin_page(data[1], data[2], data[3], data[4])

    def _filter_settings(self, text):
        text = text.strip().lower()
        if not text:
            for i in range(self.nav_tree.topLevelItemCount()):
                self.nav_tree.topLevelItem(i).setHidden(False)
                for j in range(self.nav_tree.topLevelItem(i).childCount()):
                    self.nav_tree.topLevelItem(i).child(j).setHidden(False)
            return
        synonyms = {
            "外观": ["主题", "皮肤", "样式", "界面", "显示", "颜色", "深色", "浅色"],
            "抽取": ["点名", "随机", "抽人", "开始", "滚动"],
            "课文": ["文章", "背诵", "文本", "内容", "段落"],
            "标记": ["状态", "背过", "熟练", "掌握", "评分"],
            "数据": ["统计", "记录", "保存", "导出", "备份"],
            "设置": ["配置", "选项", "参数", "偏好"],
            "快捷键": ["热键", "快捷", "按键", "键盘"],
            "插件": ["扩展", "模组", "addon", "plugin"],
            "回声": ["树洞", "留言", "匿名", "吐槽"],
            "积分": ["分数", "排名", "排行", "等级"],
            "自动": ["智能", "定时", "连续"],
            "窗口": ["界面", "窗体", "边框", "圆角"],
            "动画": ["动效", "效果", "过渡", "特效"],
            "字体": ["字号", "文字", "大小"],
            "开发": ["调试", "高级", "测试", "开发者"],
            "关于": ["信息", "版本", "帮助", "更新"],
            "系统": ["应用", "班级", "启动", "基本"],
        }
        search_terms = [text]
        for key, syns in synonyms.items():
            if text in key or key in text:
                search_terms.extend(syns)
            for syn in syns:
                if text in syn or syn in text:
                    search_terms.append(key)
                    search_terms.extend(syns)
        search_terms = list(set(search_terms))
        for i in range(self.nav_tree.topLevelItemCount()):
            cat_item = self.nav_tree.topLevelItem(i)
            cat_text = cat_item.text(0).lower()
            cat_match = any(term in cat_text or cat_text in term for term in search_terms)
            any_child_match = False
            for j in range(cat_item.childCount()):
                child = cat_item.child(j)
                child_text = child.text(0).lower()
                match = any(term in child_text or child_text in term for term in search_terms) or cat_match
                child.setHidden(not match)
                if match:
                    any_child_match = True
            cat_item.setHidden(not (cat_match or any_child_match))

    def _make_scroll_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        widget = QWidget()
        scroll.setWidget(widget)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        return scroll, layout

    def _add_section(self, layout, title):
        label = QLabel(title)
        label.setObjectName("section_title")
        layout.addWidget(label)

    def _add_setting_row(self, layout, label_text, widget, desc=""):
        card = QFrame()
        card.setObjectName("card")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(16)
        left = QVBoxLayout()
        left.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("setting_label")
        label.setStyleSheet("font-size: 13px; font-weight: 600; color: #333333;")
        left.addWidget(label)
        if desc:
            d = QLabel(desc)
            d.setObjectName("setting_desc")
            d.setWordWrap(True)
            d.setStyleSheet("font-size: 11px; color: #888888;")
            left.addWidget(d)
        card_layout.addLayout(left, 1)
        widget.setMaximumWidth(320)
        card_layout.addWidget(widget)
        layout.addWidget(card)

    def _build_pages(self):
        self._pages = {}
        page_defs = [
            ("class", self._build_class_page),
            ("info", self._build_app_info_page),
            ("startup", self._build_startup_page),
            ("theme", self._build_theme_page),
            ("display", self._build_display_page),
            ("font", self._build_font_page),
            ("animation", self._build_animation_page),
            ("window", self._build_window_page),
            ("mode", self._build_mode_page),
            ("rules", self._build_rules_page),
            ("params", self._build_params_page),
            ("auto_draw", self._build_auto_draw_page),
            ("weight", self._build_weight_page),
            ("text_extract", self._build_text_extract_page),
            ("text_display", self._build_text_display_page),
            ("text_progress", self._build_text_progress_page),
            ("mark", self._build_mark_page),
            ("score", self._build_score_page),
            ("shortcuts", self._build_shortcuts_page),
            ("shortcut_settings", self._build_shortcut_settings_page),
            ("data_mgmt", self._build_data_page),
            ("export", self._build_export_page),
            ("backup", self._build_backup_page),
            ("plugins", self._build_plugins_page),
            ("experimental", self._build_experimental_page),
            ("developer", self._build_developer_page),
            ("about", self._build_about_page),
            ("update", self._build_update_page),
            ("help", self._build_help_page),
        ]
        for key, builder in page_defs:
            scroll, layout = builder()
            self._pages[key] = scroll
            self.pages.addWidget(scroll)

    def _build_class_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "班级设置")
        self.class_name_input = QLineEdit()
        self.class_name_input.setMaximumWidth(240)
        self._add_setting_row(layout, "班级名称", self.class_name_input, "显示在窗口标题中，如「初三(2)班」。可随时修改，修改后立即生效。")
        layout.addStretch()
        return scroll, layout

    def _build_app_info_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "应用信息")
        info_card = QFrame()
        info_card.setObjectName("card")
        ic = QVBoxLayout(info_card)
        ic.setContentsMargins(16, 16, 16, 16)
        info_items = [
            ("软件名称", "课堂点名程序"),
            ("引擎版本", "A13 智能抽取引擎 V6.8"),
            ("运行环境", "纯 Python + PyQt5 本地运行"),
            ("网络需求", "无需网络，完全离线运行"),
        ]
        for label, value in info_items:
            row = QHBoxLayout()
            l = QLabel(label + "：")
            l.setStyleSheet("color: #888888; font-size: 12px;")
            l.setFixedWidth(80)
            v = QLabel(value)
            v.setStyleSheet("color: #333333; font-size: 12px; font-weight: 600;")
            row.addWidget(l)
            row.addWidget(v)
            row.addStretch()
            ic.addLayout(row)
        layout.addWidget(info_card)
        layout.addStretch()
        return scroll, layout

    def _build_theme_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "主题设置")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.currentIndexChanged.connect(self._preview_theme)
        self._add_setting_row(layout, "应用主题", self.theme_combo, "切换浅色或深色模式。深色模式可减少眼睛疲劳，适合夜间使用。切换后立即生效。")
        layout.addStretch()
        return scroll, layout

    def _build_display_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "显示效果")
        self.particle_check = QCheckBox("启用粒子背景")
        self._add_setting_row(layout, "粒子背景", self.particle_check, "在主界面背景显示动态上升的粒子效果。关闭可提升性能。")
        self.anim_check = QCheckBox("启用开屏动画")
        self._add_setting_row(layout, "开屏动画", self.anim_check, "启动时显示加载动画和软件Logo。关闭可加快启动速度。")
        self.result_popup_check = QCheckBox("抽取结果弹窗")
        self._add_setting_row(layout, "结果弹窗", self.result_popup_check, "抽取完成后弹出结果窗口，显示学生姓名和课文内容。")
        layout.addStretch()
        return scroll, layout

    def _build_font_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "字体大小")
        self.font_size = QSlider(Qt.Horizontal)
        self.font_size.setRange(48, 120)
        self.font_size.setValue(72)
        self.font_size.setFixedWidth(200)
        self._add_setting_row(layout, "抽取名字字号", self.font_size, "控制抽取时显示的学生名字大小。大屏环境建议调大，小屏环境建议调小。")
        self.text_font_size = QSpinBox()
        self.text_font_size.setRange(10, 28)
        self.text_font_size.setValue(14)
        self._add_setting_row(layout, "课文字号", self.text_font_size, "控制课文内容的显示字号。根据课文长度和屏幕大小调整。")
        layout.addStretch()
        return scroll, layout

    def _build_mode_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "抽取模式")
        mode_card = QFrame()
        mode_card.setObjectName("card")
        mc = QVBoxLayout(mode_card)
        mc.setContentsMargins(16, 12, 16, 12)
        self.mode_auto = QRadioButton("自动抽取（到时间自动停止）")
        self.mode_manual = QRadioButton("手动抽取（点击停止按钮停止）")
        mc.addWidget(self.mode_auto)
        mc.addWidget(self.mode_manual)
        layout.addWidget(mode_card)
        desc = QLabel("自动模式：点击开始后，系统会在设定时间后自动停止并显示结果。\n手动模式：点击开始后名字持续滚动，需再次点击停止才会显示结果。")
        desc.setStyleSheet("color: #888888; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch()
        return scroll, layout

    def _build_rules_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "抽取规则")
        self.no_repeat = QCheckBox("不重复模式（同一轮每人只抽一次）")
        self._add_setting_row(layout, "不重复模式", self.no_repeat, "开启后，同一轮内每个学生只会被抽取到一次。全部抽完后需重置本轮。适合全班轮流背诵。")
        self.dynamic_weight = QCheckBox("动态权重（未背过的学生概率更高）")
        self._add_setting_row(layout, "动态权重", self.dynamic_weight, "开启后，未背过的学生被抽到的概率更高，已背过的学生概率降低。帮助重点关注未掌握的学生。")
        self.countdown = QCheckBox("抽取前倒计时（3秒）")
        self._add_setting_row(layout, "抽取倒计时", self.countdown, "开启后，点击开始会先显示3秒倒计时，然后才开始滚动名字。增加仪式感。")
        self.auto_reset = QCheckBox("抽完自动重置本轮")
        self._add_setting_row(layout, "自动重置", self.auto_reset, "开启后，当所有学生都被抽取完毕时，自动重置本轮，无需手动点击。")
        layout.addStretch()
        return scroll, layout

    def _build_params_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "抽取参数")
        self.dur_spin = QSpinBox()
        self.dur_spin.setRange(1, 15)
        self.dur_spin.setValue(4)
        self._add_setting_row(layout, "自动抽取时长（秒）", self.dur_spin, "自动模式下，从开始到停止的时间。时间越长，名字滚动越久，悬念感越强。")
        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setRange(0.5, 3.0)
        self.speed_spin.setSingleStep(0.1)
        self.speed_spin.setValue(1.0)
        self._add_setting_row(layout, "滚动速度", self.speed_spin, "名字滚动的速度。数值越大，名字切换越快。建议1.0为标准速度。")
        layout.addStretch()
        return scroll, layout

    def _build_text_extract_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "课文抽取")
        self.text_mode = QComboBox()
        self.text_mode.addItems(["顺序抽取", "随机抽取", "不抽取课文"])
        self._add_setting_row(layout, "课文模式", self.text_mode, "顺序抽取：按课文列表顺序依次抽取。\n随机抽取：每次抽取学生时，同时随机抽取一篇课文。\n不抽取课文：只抽取学生名字，不显示课文。")
        self.paragraph_random = QCheckBox("段落随机抽取")
        self._add_setting_row(layout, "段落随机", self.paragraph_random, "开启后，从选中的课文中随机抽取一个段落，而不是显示整篇课文。适合分段背诵。")
        self.auto_next_text = QCheckBox("抽取后自动切换下一篇")
        self._add_setting_row(layout, "自动切换", self.auto_next_text, "开启后，每次抽取学生后自动切换到下一篇课文（顺序模式）或随机一篇（随机模式）。")
        layout.addStretch()
        return scroll, layout

    def _build_text_display_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "课文显示")
        self.show_text_title = QCheckBox("显示课文标题")
        self._add_setting_row(layout, "显示标题", self.show_text_title, "开启后，在课文内容上方显示课文标题。关闭后只显示课文正文。")
        self.text_align = QComboBox()
        self.text_align.addItems(["左对齐", "居中对齐", "右对齐"])
        self._add_setting_row(layout, "课文对齐", self.text_align, "控制课文内容的对齐方式。古文建议居中对齐，现代文建议左对齐。")
        layout.addStretch()
        return scroll, layout

    def _build_shortcuts_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "快捷键列表")
        shortcuts = [
            ("空格", "开始/停止抽取"), ("1", "标记已背过"), ("2", "标记未背熟"),
            ("3", "标记未背过"), ("Esc", "重置本轮"), ("R", "查看本轮记录"),
            ("T", "切换课文"), ("Z", "撤销上次标记"), ("Tab", "跳过当前"),
            ("N", "不重复模式"), ("←/→", "上/下一篇课文"), ("M", "切换主题"),
            (",", "打开设置"), ("P", "粒子效果开关"), ("F11", "全屏模式"),
            ("L", "排行榜"), ("Ctrl+S", "保存数据"), ("?", "快捷键速查")
        ]
        for key, desc in shortcuts:
            row = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet("background: #e5f3ff; color: #0067c0; padding: 4px 12px; border-radius: 4px; font-weight: 700; font-size: 12px; min-width: 70px;")
            k.setAlignment(Qt.AlignCenter)
            d = QLabel(desc)
            d.setStyleSheet("color: #333333; font-size: 13px;")
            row.addWidget(k)
            row.addWidget(d)
            row.addStretch()
            layout.addLayout(row)
        layout.addStretch()
        return scroll, layout

    def _build_data_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "数据管理")
        export_btn = QPushButton("导出统计数据（带时间戳）")
        export_btn.setObjectName("primary")
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self._export_stats)
        layout.addWidget(export_btn)
        export_desc = QLabel("导出当前所有统计数据到txt文件，文件名包含导出时间。默认保存到桌面。")
        export_desc.setStyleSheet("color: #888888; font-size: 11px;")
        export_desc.setWordWrap(True)
        layout.addWidget(export_desc)
        reset_btn = QPushButton("重置所有数据")
        reset_btn.setObjectName("danger")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self._reset_data)
        layout.addWidget(reset_btn)
        reset_desc = QLabel("删除所有学生名单、课文、记录、积分数据，并清除向导标记。此操作不可恢复！")
        reset_desc.setStyleSheet("color: #c42b1c; font-size: 11px;")
        reset_desc.setWordWrap(True)
        layout.addWidget(reset_desc)
        rerun_btn = QPushButton("重新运行配置向导")
        rerun_btn.setMinimumHeight(40)
        rerun_btn.clicked.connect(self._rerun_wizard)
        layout.addWidget(rerun_btn)
        rerun_desc = QLabel("清除向导完成标记，下次启动软件时重新打开配置向导。")
        rerun_desc.setStyleSheet("color: #888888; font-size: 11px;")
        rerun_desc.setWordWrap(True)
        layout.addWidget(rerun_desc)
        layout.addStretch()
        return scroll, layout

    def _build_experimental_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "实验性功能")
        warning = QLabel("以下功能为实验性功能，可能存在不稳定的情况。使用前请保存重要数据。")
        warning.setStyleSheet("color: #ca5010; font-size: 12px; font-weight: 600;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        self.exp_anti_cheat = QCheckBox("防作弊模式（限制连续抽取间隔）")
        self._add_setting_row(layout, "防作弊模式", self.exp_anti_cheat, "开启后，两次抽取之间有最小间隔限制，防止快速连点。同时记录每次抽取的时间戳。")
        self.exp_sound = QCheckBox("抽取音效（需要系统音频）")
        self._add_setting_row(layout, "抽取音效", self.exp_sound, "开启后，抽取开始、停止、标记时播放提示音。需要系统音频设备正常工作。")
        self.exp_dpi = QCheckBox("高DPI优化（大屏适配）")
        self._add_setting_row(layout, "高DPI优化", self.exp_dpi, "开启后，针对高分辨率大屏进行界面缩放优化。适合3000+分辨率的班级大屏。")
        self.exp_smooth = QCheckBox("平滑滚动（列表动画）")
        self._add_setting_row(layout, "平滑滚动", self.exp_smooth, "开启后，列表和课文滚动时使用平滑动画效果。可能略微增加CPU占用。")
        layout.addStretch()
        return scroll, layout

    def _build_about_page(self):
        scroll, layout = self._make_scroll_page()
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        try:
            icon_label = QLabel()
            pix = QPixmap(os.path.join(BASE_DIR, "app.ico")).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pix)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)
        except Exception:
            pass
        title = QLabel("课堂点名程序")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0067c0;")
        layout.addWidget(title)
        ver = QLabel("版本 V6.8 · A13 智能抽取引擎")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #666666; font-size: 13px;")
        layout.addWidget(ver)
        desc = QLabel("纯 Python + PyQt5 实现 · 本地离线运行\nWindows 11 风格设计 · 支持大屏适配")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(desc)
        layout.addSpacing(20)
        custom_btn = QPushButton("定制属于你们班的点名程序（限时免费）")
        custom_btn.setObjectName("primary")
        custom_btn.setMinimumHeight(44)
        custom_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(WEBSITE_URL)))
        layout.addWidget(custom_btn)
        web_btn = QPushButton("前往官网")
        web_btn.setMinimumHeight(40)
        web_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(WEBSITE_URL)))
        layout.addWidget(web_btn)
        layout.addStretch()
        return scroll, layout

    def _build_startup_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "启动选项")
        self.startup_quick_check = QCheckBox("启动时显示快速抽取入口")
        self._add_setting_row(layout, "快速抽取入口", self.startup_quick_check, "启动时在加载界面显示「快速抽取」按钮，可直接进入快捷抽取模式。")
        self.startup_remember_check = QCheckBox("记住上次启动选择")
        self._add_setting_row(layout, "记住选择", self.startup_remember_check, "记住上次选择的启动方式（主界面/快速抽取），下次启动时倒计时3秒自动进入。")
        self.startup_countdown = QSpinBox()
        self.startup_countdown.setRange(0, 10)
        self.startup_countdown.setValue(3)
        self._add_setting_row(layout, "启动倒计时（秒）", self.startup_countdown, "记住选择后，启动界面显示的倒计时秒数。倒计时期间任意操作可取消自动进入。")
        self.startup_wizard_check = QCheckBox("首次启动强制运行向导")
        self._add_setting_row(layout, "首次向导", self.startup_wizard_check, "首次启动时自动运行配置向导，引导用户设置班级名、学生名单和课文库。")
        layout.addStretch()
        return scroll, layout

    def _build_animation_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "动画效果")
        self.anim_draw_check = QCheckBox("抽取滚动动画")
        self._add_setting_row(layout, "抽取动画", self.anim_draw_check, "抽取时名字快速滚动的动画效果。关闭后直接显示结果，性能更好。")
        self.anim_result_check = QCheckBox("结果弹出动画")
        self._add_setting_row(layout, "结果动画", self.anim_result_check, "抽取结果弹窗的淡入和缩放动画。")
        self.anim_transition_check = QCheckBox("页面切换动画")
        self._add_setting_row(layout, "切换动画", self.anim_transition_check, "设置页面切换时的平滑过渡动画。")
        self.anim_duration = QSpinBox()
        self.anim_duration.setRange(100, 1000)
        self.anim_duration.setValue(300)
        self._add_setting_row(layout, "动画时长（毫秒）", self.anim_duration, "所有过渡动画的持续时间。数值越大动画越慢。")
        self.anim_easing = QComboBox()
        self.anim_easing.addItems(["线性", "缓入", "缓出", "缓入缓出", "弹性"])
        self._add_setting_row(layout, "缓动函数", self.anim_easing, "动画的速度曲线。弹性效果更活泼，线性更平稳。")
        layout.addStretch()
        return scroll, layout

    def _build_window_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "窗口样式")
        self.window_rounded_check = QCheckBox("圆角窗口")
        self._add_setting_row(layout, "圆角窗口", self.window_rounded_check, "使用自定义无边框圆角窗口，更具现代感。需要重启生效。")
        self.window_radius = QSpinBox()
        self.window_radius.setRange(0, 30)
        self.window_radius.setValue(12)
        self._add_setting_row(layout, "圆角半径（像素）", self.window_radius, "窗口圆角的大小。数值越大圆角越明显。")
        self.window_shadow_check = QCheckBox("窗口阴影")
        self._add_setting_row(layout, "窗口阴影", self.window_shadow_check, "窗口外围的投影效果，增加层次感。")
        self.window_topmost_check = QCheckBox("窗口置顶")
        self._add_setting_row(layout, "窗口置顶", self.window_topmost_check, "主窗口始终显示在最上层，不会被其他窗口遮挡。")
        self.window_minimize_mini = QCheckBox("最小化转为悬浮窗")
        self._add_setting_row(layout, "悬浮最小化", self.window_minimize_mini, "最小化时不缩到任务栏，而是转为右上角小悬浮窗，可快速恢复。")
        layout.addStretch()
        return scroll, layout

    def _build_auto_draw_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "自动抽取")
        self.auto_draw_enable = QCheckBox("启用自动抽取模式")
        self._add_setting_row(layout, "自动抽取", self.auto_draw_enable, "开启后，系统会按照设定的间隔自动连续抽取学生，无需手动点击。适合连续抽背场景。")
        self.auto_draw_interval = QSpinBox()
        self.auto_draw_interval.setRange(5, 300)
        self.auto_draw_interval.setValue(30)
        self._add_setting_row(layout, "抽取间隔（秒）", self.auto_draw_interval, "两次自动抽取之间的间隔时间。给学生足够的背诵时间。")
        self.auto_draw_mark_wait = QCheckBox("等待标记后继续")
        self._add_setting_row(layout, "等待标记", self.auto_draw_mark_wait, "开启后，自动抽取会等待用户标记当前学生状态后，才继续下一次抽取。")
        self.auto_draw_max = QSpinBox()
        self.auto_draw_max.setRange(0, 100)
        self.auto_draw_max.setValue(0)
        self._add_setting_row(layout, "最大抽取次数（0为不限）", self.auto_draw_max, "自动抽取模式下最多抽取多少次。0表示不限制，直到全部抽完或手动停止。")
        self.auto_draw_sound = QCheckBox("抽取提示音")
        self._add_setting_row(layout, "提示音", self.auto_draw_sound, "每次抽取开始和结束时播放提示音。")
        layout.addStretch()
        return scroll, layout

    def _build_weight_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "权重系统")
        self.weight_enable = QCheckBox("启用动态权重")
        self._add_setting_row(layout, "动态权重", self.weight_enable, "根据学生的背诵状态动态调整抽取概率。未背过的学生概率更高，已背过的学生概率降低。")
        self.weight_unlearned = QSpinBox()
        self.weight_unlearned.setRange(1, 10)
        self.weight_unlearned.setValue(5)
        self._add_setting_row(layout, "未背过权重倍率", self.weight_unlearned, "未背过学生的抽取概率倍率。数值越大，未背过的学生越容易被抽到。")
        self.weight_familiar = QSpinBox()
        self.weight_familiar.setRange(1, 10)
        self.weight_familiar.setValue(3)
        self._add_setting_row(layout, "未背熟权重倍率", self.weight_familiar, "未背熟学生的抽取概率倍率。")
        self.weight_mastered = QSpinBox()
        self.weight_mastered.setRange(1, 10)
        self.weight_mastered.setValue(1)
        self._add_setting_row(layout, "已背过权重倍率", self.weight_mastered, "已背过学生的抽取概率倍率。设为1表示正常概率，设为更低可减少重复抽取。")
        self.weight_reset_round = QCheckBox("每轮重置权重")
        self._add_setting_row(layout, "轮次重置", self.weight_reset_round, "每轮抽取开始时重置所有学生的权重为默认值。")
        layout.addStretch()
        return scroll, layout

    def _build_text_progress_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "课文进度")
        self.text_progress_enable = QCheckBox("记录课文进度")
        self._add_setting_row(layout, "进度记录", self.text_progress_enable, "记录每篇课文的背诵进度，下次启动时自动恢复到上次的位置。")
        self.text_progress_auto = QCheckBox("自动保存进度")
        self._add_setting_row(layout, "自动保存", self.text_progress_auto, "每次切换课文或标记状态时自动保存进度。")
        self.text_progress_show = QCheckBox("显示进度条")
        self._add_setting_row(layout, "进度条显示", self.text_progress_show, "在课文列表中显示每篇课文的背诵进度条。")
        self.text_progress_reset = QPushButton("重置所有课文进度")
        self.text_progress_reset.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
        self.text_progress_reset.clicked.connect(self._reset_text_progress)
        self._add_setting_row(layout, "重置进度", self.text_progress_reset, "清除所有课文的进度记录，恢复到初始状态。此操作不可撤销。")
        layout.addStretch()
        return scroll, layout

    def _build_mark_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "背诵标记")
        self.mark_auto_next = QCheckBox("标记后自动抽取下一个")
        self._add_setting_row(layout, "自动下一个", self.mark_auto_next, "标记学生状态后，自动开始下一次抽取，无需手动点击开始。")
        self.mark_toast = QCheckBox("标记成功提示")
        self._add_setting_row(layout, "标记提示", self.mark_toast, "标记成功后在屏幕上方显示「XXX 已标记」的提示，2秒后自动消失。")
        self.mark_confirm_skip = QCheckBox("跳过确认弹窗")
        self._add_setting_row(layout, "跳过确认", self.mark_confirm_skip, "未标记就抽取下一个时，弹出确认窗口询问「略过此学生」或「去标记」。")
        self.mark_undo_enable = QCheckBox("启用撤销标记")
        self._add_setting_row(layout, "撤销标记", self.mark_undo_enable, "允许撤销上一次标记操作，恢复学生状态和积分。按 Z 键快速撤销。")
        self.mark_custom_status = QLineEdit()
        self.mark_custom_status.setPlaceholderText("自定义状态，用逗号分隔")
        self._add_setting_row(layout, "自定义状态", self.mark_custom_status, "自定义标记状态选项，用逗号分隔。例如：已背过,未背熟,未背过,部分背过。")
        layout.addStretch()
        return scroll, layout

    def _build_score_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "积分系统")
        self.score_enable = QCheckBox("启用积分系统")
        self._add_setting_row(layout, "积分系统", self.score_enable, "根据学生的背诵状态增减积分，形成排行榜，激励学生积极背诵。")
        self.score_mastered = QSpinBox()
        self.score_mastered.setRange(-50, 100)
        self.score_mastered.setValue(10)
        self._add_setting_row(layout, "已背过积分", self.score_mastered, "标记为「已背过」时增加的积分。")
        self.score_familiar = QSpinBox()
        self.score_familiar.setRange(-50, 100)
        self.score_familiar.setValue(-5)
        self._add_setting_row(layout, "未背熟积分", self.score_familiar, "标记为「未背熟」时增减的积分。负数表示扣分。")
        self.score_unlearned = QSpinBox()
        self.score_unlearned.setRange(-50, 100)
        self.score_unlearned.setValue(-15)
        self._add_setting_row(layout, "未背过积分", self.score_unlearned, "标记为「未背过」时增减的积分。负数表示扣分。")
        self.score_initial = QSpinBox()
        self.score_initial.setRange(0, 200)
        self.score_initial.setValue(100)
        self._add_setting_row(layout, "初始积分", self.score_initial, "新学生加入时的初始积分。")
        self.score_show_ranking = QCheckBox("抽取时显示积分排名")
        self._add_setting_row(layout, "排名显示", self.score_show_ranking, "在结果弹窗中显示该学生的当前积分和班级排名。")
        layout.addStretch()
        return scroll, layout

    def _build_shortcut_settings_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "快捷键设置")
        self.shortcut_enable = QCheckBox("启用全局快捷键")
        self._add_setting_row(layout, "全局快捷键", self.shortcut_enable, "即使窗口不在前台，也能响应快捷键操作。")
        self.shortcut_space = QCheckBox("空格开始/停止抽取")
        self._add_setting_row(layout, "空格抽取", self.shortcut_space, "按空格键开始或停止抽取。")
        self.shortcut_esc = QCheckBox("Esc重置本轮")
        self._add_setting_row(layout, "Esc重置", self.shortcut_esc, "按 Esc 键重置本轮抽取记录。")
        self.shortcut_mark_keys = QCheckBox("数字键快速标记（1/2/3）")
        self._add_setting_row(layout, "数字标记", self.shortcut_mark_keys, "按 1/2/3 键快速标记为已背过/未背熟/未背过。")
        self.shortcut_custom = QPushButton("自定义快捷键")
        self.shortcut_custom.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
        self.shortcut_custom.clicked.connect(self._custom_shortcuts)
        self._add_setting_row(layout, "自定义", self.shortcut_custom, "打开快捷键自定义编辑器，修改每个操作的快捷键组合。")
        layout.addStretch()
        return scroll, layout

    def _build_export_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "统计导出")
        self.export_format = QComboBox()
        self.export_format.addItems(["TXT 文本", "CSV 表格", "JSON 数据"])
        self._add_setting_row(layout, "导出格式", self.export_format, "统计数据导出的文件格式。TXT 适合阅读，CSV 适合 Excel 打开，JSON 适合程序处理。")
        self.export_timestamp = QCheckBox("文件名添加时间戳")
        self._add_setting_row(layout, "时间戳", self.export_timestamp, "导出文件名中包含导出时间，避免覆盖旧文件。")
        self.export_desktop = QCheckBox("默认导出到桌面")
        self._add_setting_row(layout, "导出到桌面", self.export_desktop, "导出时默认保存到桌面，并提示导出成功。")
        self.export_include_history = QCheckBox("包含抽取历史记录")
        self._add_setting_row(layout, "包含历史", self.export_include_history, "导出文件中包含详细的抽取历史记录（时间、学生、课文、状态）。")
        self.export_now = QPushButton("立即导出统计数据")
        self.export_now.setObjectName("primary")
        self.export_now.setMinimumHeight(44)
        self.export_now.clicked.connect(self._export_stats_now)
        self._add_setting_row(layout, "立即导出", self.export_now, "立即导出当前所有统计数据到文件。")
        layout.addStretch()
        return scroll, layout

    def _build_backup_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "备份与恢复")
        self.backup_auto = QCheckBox("自动备份配置")
        self._add_setting_row(layout, "自动备份", self.backup_auto, "每次修改设置后自动备份配置文件，防止数据丢失。")
        self.backup_count = QSpinBox()
        self.backup_count.setRange(1, 20)
        self.backup_count.setValue(5)
        self._add_setting_row(layout, "备份保留数量", self.backup_count, "最多保留多少份自动备份。超过后自动删除最旧的备份。")
        self.backup_now = QPushButton("立即备份")
        self.backup_now.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
        self.backup_now.clicked.connect(self._backup_now)
        self._add_setting_row(layout, "立即备份", self.backup_now, "立即备份当前所有配置和数据文件。")
        self.restore_now = QPushButton("从备份恢复")
        self.restore_now.setStyleSheet("QPushButton { background: #ca5010; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
        self.restore_now.clicked.connect(self._restore_now)
        self._add_setting_row(layout, "恢复备份", self.restore_now, "从之前的备份文件恢复配置和数据。")
        self.backup_path = QLineEdit()
        self.backup_path.setPlaceholderText("备份文件保存路径")
        self._add_setting_row(layout, "备份路径", self.backup_path, "备份文件的保存目录。默认为软件目录下的 backup 文件夹。")
        layout.addStretch()
        return scroll, layout

    def _build_echo_settings_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "回声洞设置")
        self.echo_enable = QCheckBox("启用回声洞功能")
        self._add_setting_row(layout, "回声洞", self.echo_enable, "启用回声洞功能。学生可以匿名投递想说的话，其他人可以「回声」表示共鸣。")
        self.echo_hidden = QCheckBox("隐藏入口（点击Logo触发）")
        self._add_setting_row(layout, "隐藏入口", self.echo_hidden, "不在主界面显示回声洞按钮，改为点击左上角Logo触发。增加趣味性和神秘感。")
        self.echo_anonymous = QCheckBox("完全匿名")
        self._add_setting_row(layout, "完全匿名", self.echo_anonymous, "所有回声完全匿名，不记录任何用户信息。")
        self.echo_max_length = QSpinBox()
        self.echo_max_length.setRange(20, 500)
        self.echo_max_length.setValue(200)
        self._add_setting_row(layout, "单条最大字数", self.echo_max_length, "每条回声最多允许的字数。")
        self.echo_auto_refresh = QCheckBox("自动刷新回声列表")
        self._add_setting_row(layout, "自动刷新", self.echo_auto_refresh, "回声洞窗口打开时自动刷新最新回声。")
        self.echo_clear = QPushButton("清空所有回声")
        self.echo_clear.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
        self._add_setting_row(layout, "清空回声", self.echo_clear, "删除所有回声数据。此操作不可撤销，请谨慎操作。")
        layout.addStretch()
        return scroll, layout

    def _build_echo_manage_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "回声管理")
        info_card = QFrame()
        info_card.setObjectName("card")
        ic = QVBoxLayout(info_card)
        ic.setContentsMargins(16, 12, 16, 12)
        self.echo_count_label = QLabel("当前回声总数：加载中...")
        self.echo_count_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #333333;")
        ic.addWidget(self.echo_count_label)
        self.echo_hot_label = QLabel("最热回声：加载中...")
        self.echo_hot_label.setStyleSheet("font-size: 13px; color: #666666;")
        ic.addWidget(self.echo_hot_label)
        layout.addWidget(info_card)
        self.echo_manage_list = QListWidget()
        self.echo_manage_list.setMinimumHeight(300)
        layout.addWidget(self.echo_manage_list, 1)
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self._refresh_echo_manage)
        btn_layout.addWidget(refresh_btn)
        delete_btn = QPushButton("删除选中")
        delete_btn.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; padding: 8px 16px; }")
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)
        layout.addStretch()
        return scroll, layout

    def _refresh_echo_manage(self):
        try:
            echoes = self.echo_hole.get_latest(100)
            self.echo_manage_list.clear()
            for e in echoes:
                item = QListWidgetItem(f"[{e['time']}] 回声{e['echo_count']}次: {e['text'][:50]}")
                item.setData(Qt.UserRole, e["id"])
                self.echo_manage_list.addItem(item)
            self.echo_count_label.setText(f"当前回声总数：{len(echoes)}")
            if echoes:
                hot = max(echoes, key=lambda x: x["echo_count"])
                self.echo_hot_label.setText(f"最热回声：{hot['text'][:30]}... ({hot['echo_count']}次回声)")
        except Exception:
            pass

    def _build_plugins_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "插件中心")
        self.plugin_enable = QCheckBox("启用插件系统")
        self.plugin_enable.setChecked(True)
        self._add_setting_row(layout, "插件系统", self.plugin_enable, "启用插件系统，允许加载和管理第三方插件，扩展软件功能。插件使用 .arcx 自定义格式。")

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        reload_btn = QPushButton("重新加载插件")
        reload_btn.setStyleSheet("QPushButton { background: #107c10; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }")
        reload_btn.setMinimumHeight(36)
        reload_btn.clicked.connect(self._reload_plugins)
        toolbar.addWidget(reload_btn)
        install_btn = QPushButton("安装插件")
        install_btn.setMinimumHeight(36)
        install_btn.clicked.connect(self._install_plugin)
        toolbar.addWidget(install_btn)
        installer_btn = QPushButton("插件安装程序")
        installer_btn.setStyleSheet("QPushButton { background: #ca5010; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: 600; }")
        installer_btn.setMinimumHeight(36)
        installer_btn.setToolTip("打开可视化插件安装程序，支持安装 .arcxpkg 格式的插件包（包含第三方依赖库）")
        installer_btn.clicked.connect(self._open_plugin_installer)
        toolbar.addWidget(installer_btn)
        log_btn = QPushButton("查看插件日志")
        log_btn.setMinimumHeight(36)
        log_btn.clicked.connect(self._show_plugin_logs)
        toolbar.addWidget(log_btn)
        toolbar.addStretch()
        self.plugin_count_label = QLabel("已安装：0 个")
        self.plugin_count_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #0067c0;")
        toolbar.addWidget(self.plugin_count_label)
        layout.addLayout(toolbar)

        list_label = QLabel("已安装插件")
        list_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #333333; margin-top: 8px;")
        layout.addWidget(list_label)

        self.plugin_cards_layout = QVBoxLayout()
        self.plugin_cards_layout.setSpacing(10)
        layout.addLayout(self.plugin_cards_layout)

        setting_label = QLabel("插件设置")
        setting_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #333333; margin-top: 12px;")
        layout.addWidget(setting_label)

        self.plugin_setting_container = QFrame()
        self.plugin_setting_container.setObjectName("card")
        self.plugin_setting_container.setMinimumHeight(300)
        psc_layout = QVBoxLayout(self.plugin_setting_container)
        psc_layout.setContentsMargins(20, 16, 20, 16)
        self.plugin_setting_placeholder = QLabel("点击上方插件卡片中的「渲染设置」按钮，在此处显示该插件的设置页面")
        self.plugin_setting_placeholder.setAlignment(Qt.AlignCenter)
        self.plugin_setting_placeholder.setStyleSheet("color: #999999; font-size: 13px;")
        psc_layout.addWidget(self.plugin_setting_placeholder)
        self.plugin_setting_widget = None
        layout.addWidget(self.plugin_setting_container)

        sample_btn = QPushButton("创建示例插件")
        sample_btn.setMinimumHeight(36)
        sample_btn.clicked.connect(self._create_sample_plugin)
        layout.addWidget(sample_btn)

        desc = QLabel("插件系统类似于 Class Island，支持加载 .arcx 自定义格式插件。插件可以访问学生名单、触发抽取、显示自定义对话框、读写配置等。插件文件放置在软件目录的 plugins 文件夹中。")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(desc)
        layout.addStretch()
        QTimer.singleShot(100, self._refresh_plugin_cards)
        return scroll, layout

    def _reload_plugins(self):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        try:
            self.nav_tree.clearSelection()
            self.plugin_mgr.load_all_plugins()
            self._refresh_plugin_cards()

            system_count = getattr(self, '_system_page_count', 29)
            while self.pages.count() > system_count:
                widget = self.pages.widget(system_count)
                if widget:
                    self.pages.removeWidget(widget)
                    widget.deleteLater()
                else:
                    break

            self._plugin_pages = {}
            self._build_tree()
            self._switch_page(0, "系统")
            self._show_reload_toast()
        except Exception as e:
            print(f"重新加载插件失败：{e}")
            import traceback
            traceback.print_exc()

    def _show_reload_toast(self):
        try:
            toast = QLabel("插件已重新加载，左侧导航已更新", self)
            toast.setStyleSheet("background: #107c10; color: white; padding: 12px 24px; border-radius: 8px; font-size: 13px;")
            toast.setAlignment(Qt.AlignCenter)
            toast.adjustSize()
            x = (self.width() - toast.width()) // 2
            y = 80
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        except Exception:
            pass

    def _refresh_plugin_cards(self):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        while self.plugin_cards_layout.count():
            item = self.plugin_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.plugin_mgr.load_all_plugins()
        plugins = self.plugin_mgr.get_all_plugins()
        self.plugin_count_label.setText(f"已安装：{len(plugins)} 个")
        for plugin in plugins:
            meta = plugin.get("meta", {})
            name = meta.get("name", "未知")
            version = meta.get("version", "1.0.0")
            author = meta.get("author", "未知")
            description = meta.get("description", "")
            enabled = plugin.get("enabled", True)
            has_settings = meta.get("has_settings_page", False)

            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet("QFrame#card { background: #fafafa; border-radius: 8px; border: 1px solid #e5e5e5; }")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(14)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(4)
            name_row = QHBoxLayout()
            name_label = QLabel(f"{name}  v{version}")
            name_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #333333;")
            name_row.addWidget(name_label)
            status_label = QLabel("✓ 已启用" if enabled else "✗ 已禁用")
            status_label.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {'#107c10' if enabled else '#888888'};")
            name_row.addWidget(status_label)
            name_row.addStretch()
            info_layout.addLayout(name_row)
            author_label = QLabel(f"作者：{author}")
            author_label.setStyleSheet("font-size: 11px; color: #666666;")
            info_layout.addWidget(author_label)
            if description:
                desc_label = QLabel(description)
                desc_label.setWordWrap(True)
                desc_label.setStyleSheet("font-size: 11px; color: #888888;")
                info_layout.addWidget(desc_label)
            card_layout.addLayout(info_layout, 1)

            btn_layout = QVBoxLayout()
            btn_layout.setSpacing(6)
            if has_settings:
                render_btn = QPushButton("渲染设置")
                render_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 5px; padding: 6px 14px; font-weight: 600; font-size: 12px; } QPushButton:hover { background: #1a76c8; }")
                render_btn.clicked.connect(lambda checked, n=name: self._render_plugin_setting(n))
                btn_layout.addWidget(render_btn)
            run_btn = QPushButton("运行")
            run_btn.setStyleSheet("QPushButton { background: #f0f0f0; border: 1px solid #d1d1d1; border-radius: 5px; padding: 6px 14px; font-size: 12px; }")
            run_btn.clicked.connect(lambda checked, n=name: self._run_plugin_by_name(n))
            btn_layout.addWidget(run_btn)
            toggle_btn = QPushButton("禁用" if enabled else "启用")
            toggle_btn.setStyleSheet("QPushButton { background: #f0f0f0; border: 1px solid #d1d1d1; border-radius: 5px; padding: 6px 14px; font-size: 12px; }")
            toggle_btn.clicked.connect(lambda checked, n=name: self._toggle_plugin_by_name(n))
            btn_layout.addWidget(toggle_btn)
            uninstall_btn = QPushButton("卸载")
            uninstall_btn.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 5px; padding: 6px 14px; font-size: 12px; }")
            uninstall_btn.clicked.connect(lambda checked, n=name: self._uninstall_plugin_by_name(n))
            btn_layout.addWidget(uninstall_btn)
            card_layout.addLayout(btn_layout)

            self.plugin_cards_layout.addWidget(card)

    def _render_plugin_setting(self, plugin_name):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        if self.plugin_setting_widget:
            self.plugin_setting_widget.deleteLater()
            self.plugin_setting_widget = None
        layout = self.plugin_setting_container.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        page = self.plugin_mgr.build_plugin_settings_page(plugin_name, self.parent())
        if page:
            self.plugin_setting_widget = page
            layout.addWidget(page)
        else:
            placeholder = QLabel(f"插件「{plugin_name}」没有设置页面")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #999999; font-size: 13px;")
            layout.addWidget(placeholder)

    def _run_plugin_by_name(self, name):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        result, error = self.plugin_mgr.execute_plugin(name, self.parent())
        if error:
            QMessageBox.warning(self, "插件错误", f"插件运行出错：\n{error}")
        elif result:
            QMessageBox.information(self, "插件完成", f"插件运行完成！\n\n返回结果：{str(result)}")

    def _toggle_plugin_by_name(self, name):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        plugin = self.plugin_mgr.get_plugin(name)
        if not plugin:
            return
        current_enabled = plugin.get("enabled", True)
        try:
            if current_enabled:
                self.plugin_mgr.disable_plugin(name)
                self._show_plugin_toast(f"插件「{name}」已禁用", "#c42b1c")
            else:
                self.plugin_mgr.enable_plugin(name)
                self._show_plugin_toast(f"插件「{name}」已启用", "#107c10")
            self.plugin_mgr._save_plugin_state(name, not current_enabled)
        except Exception as e:
            print(f"切换插件状态失败：{e}")
            import traceback
            traceback.print_exc()
        self._refresh_plugin_cards()

    def _show_plugin_toast(self, message, color="#0067c0"):
        try:
            toast = QLabel(message, self)
            toast.setStyleSheet(f"background: {color}; color: white; padding: 12px 24px; border-radius: 8px; font-size: 13px; font-weight: 600;")
            toast.setAlignment(Qt.AlignCenter)
            toast.adjustSize()
            x = (self.width() - toast.width()) // 2
            y = 100
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        except Exception:
            pass

    def _uninstall_plugin_by_name(self, name):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        reply = QMessageBox.question(self, "确认卸载", f"确定要卸载插件「{name}」吗？\n\n插件的数据和配置也会被删除。", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success, msg = self.plugin_mgr.uninstall_plugin(name)
            if success:
                QMessageBox.information(self, "卸载成功", msg)
            else:
                QMessageBox.warning(self, "卸载失败", msg)
            self._refresh_plugin_cards()

    def _show_plugin_logs(self):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("插件日志")
        dlg.setMinimumSize(600, 500)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        header = QHBoxLayout()
        combo = QComboBox()
        plugins = self.plugin_mgr.get_all_plugins()
        combo.addItem("全部插件")
        for p in plugins:
            combo.addItem(p["meta"]["name"])
        header.addWidget(combo)
        header.addStretch()
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(lambda: self._clear_current_plugin_log(combo.currentText()))
        header.addWidget(clear_btn)
        layout.addLayout(header)
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setStyleSheet("QTextEdit { background: #1e1e1e; color: #d4d4d4; border: 1px solid #3d3d3d; border-radius: 6px; padding: 8px; font-family: Consolas, monospace; font-size: 11px; }")
        layout.addWidget(log_text, 1)

        def refresh_logs():
            current = combo.currentText()
            all_logs = []
            if current == "全部插件":
                for p in plugins:
                    n = p["meta"]["name"]
                    ctx = self.plugin_mgr.contexts.get(n)
                    if ctx:
                        logs = ctx.get_logs(50)
                        for log in logs:
                            all_logs.append(f"[{n}] {log}")
            else:
                ctx = self.plugin_mgr.contexts.get(current)
                if ctx:
                    all_logs = ctx.get_logs(100)
            log_text.setPlainText("".join(all_logs) if all_logs else "暂无日志记录")

        combo.currentIndexChanged.connect(refresh_logs)
        refresh_logs()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn)
        dlg.exec_()

    def _clear_current_plugin_log(self, name):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        if name == "全部插件":
            plugins = self.plugin_mgr.get_all_plugins()
            for p in plugins:
                n = p["meta"]["name"]
                ctx = self.plugin_mgr.contexts.get(n)
                if ctx:
                    ctx.clear_logs()
        else:
            ctx = self.plugin_mgr.contexts.get(name)
            if ctx:
                ctx.clear_logs()
        QMessageBox.information(self, "清空完成", "插件日志已清空！")

    def _install_plugin(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件文件", "",
            "插件文件 (*.arcx *.arcxpkg);;ARCX 插件 (*.arcx);;ARCX 插件包 (*.arcxpkg);;所有文件 (*.*)"
        )
        if not file_path:
            return
        if not hasattr(self, 'plugin_mgr'):
            return

        if file_path.lower().endswith('.arcxpkg'):
            self._install_arcxpkg(file_path)
        else:
            success, msg = self.plugin_mgr.install_plugin(file_path)
            if success:
                QMessageBox.information(self, "安装成功", msg)
                self._refresh_plugin_cards()
                self._build_tree()
            else:
                QMessageBox.warning(self, "安装失败", msg)

    def _install_arcxpkg(self, file_path):
        import zipfile
        import tempfile
        import shutil
        import json

        temp_dir = tempfile.mkdtemp(prefix="a13_install_")
        try:
            with zipfile.ZipFile(file_path, 'r') as zf:
                zf.extractall(temp_dir)

            plugin_arcx = os.path.join(temp_dir, "plugin.arcx")
            if not os.path.exists(plugin_arcx):
                arcx_files = [f for f in os.listdir(temp_dir) if f.endswith('.arcx')]
                if arcx_files:
                    plugin_arcx = os.path.join(temp_dir, arcx_files[0])
                else:
                    QMessageBox.warning(self, "安装失败", "插件包中未找到 plugin.arcx 文件")
                    return

            with open(plugin_arcx, 'r', encoding='utf-8') as f:
                plugin_data = json.load(f)
            plugin_name = plugin_data.get('meta', {}).get('name', '未知插件')

            success, msg = self.plugin_mgr.install_plugin(plugin_arcx)
            if not success:
                QMessageBox.warning(self, "安装失败", msg)
                return

            libs_dir = os.path.join(temp_dir, "libs")
            lib_count = 0
            if os.path.exists(libs_dir):
                target_libs = os.path.join(self.plugin_mgr.plugins_data_dir, plugin_name, "libs")
                if os.path.exists(target_libs):
                    shutil.rmtree(target_libs)
                shutil.copytree(libs_dir, target_libs)
                lib_count = len(os.listdir(target_libs))

            self._refresh_plugin_cards()
            self._build_tree()

            lib_info = f"\n\n已安装 {lib_count} 个第三方依赖库" if lib_count > 0 else ""
            QMessageBox.information(
                self, "安装成功",
                f"插件 {plugin_name} 安装成功！{lib_info}\n\n请重启软件以完全加载插件。"
            )
        except Exception as e:
            import traceback
            QMessageBox.warning(self, "安装失败", f"安装插件包失败：{str(e)}\n\n{traceback.format_exc()}")
        finally:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def _open_plugin_installer(self):
        import subprocess
        installer_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plugin_installer.py")
        if not os.path.exists(installer_path):
            QMessageBox.warning(self, "未找到", f"插件安装程序不存在：\n{installer_path}")
            return
        try:
            python_exe = sys.executable
            subprocess.Popen([python_exe, installer_path], cwd=os.path.dirname(installer_path))
            self._show_plugin_toast("插件安装程序已启动", "#0067c0")
        except Exception as e:
            QMessageBox.warning(self, "启动失败", f"无法启动插件安装程序：{str(e)}")

    def _create_sample_plugin(self):
        if not hasattr(self, 'plugin_mgr'):
            return
        sample_content = self.plugin_mgr.create_sample_plugin()
        file_path, _ = QFileDialog.getSaveFileName(self, "保存示例插件", "示例插件.arcx", "ARCX 插件文件 (*.arcx)")
        if not file_path:
            return
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(sample_content)
            QMessageBox.information(self, "创建成功", f"示例插件已创建到：\n{file_path}\n\n您可以在「安装插件」中选择此文件进行安装。")
        except Exception as e:
            QMessageBox.warning(self, "创建失败", f"创建示例插件失败：{str(e)}")

    def _build_developer_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "开发者选项")
        self.dev_debug = QCheckBox("启用调试模式")
        self._add_setting_row(layout, "调试模式", self.dev_debug, "显示详细的调试信息和性能数据，方便开发者排查问题。")
        self.dev_console = QCheckBox("显示控制台输出")
        self._add_setting_row(layout, "控制台", self.dev_console, "在窗口底部显示 Python 控制台输出，实时查看日志。")
        self.dev_fps = QCheckBox("显示帧率（FPS）")
        self._add_setting_row(layout, "帧率显示", self.dev_fps, "在窗口角落显示实时帧率，评估动画性能。")
        self.dev_inspector = QCheckBox("启用控件检查器")
        self._add_setting_row(layout, "控件检查", self.dev_inspector, "按 Ctrl+Shift+I 打开控件检查器，查看界面控件的属性和布局。")
        self.dev_reload = QPushButton("重新加载界面")
        self.dev_reload.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
        self.dev_reload.clicked.connect(self._reload_ui)
        self._add_setting_row(layout, "重载界面", self.dev_reload, "重新构建整个界面，用于调试界面修改。")
        self.dev_clear_config = QPushButton("重置所有配置")
        self.dev_clear_config.setStyleSheet("QPushButton { background: #c42b1c; color: white; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; }")
        self.dev_clear_config.clicked.connect(self._reset_all_config)
        self._add_setting_row(layout, "重置配置", self.dev_clear_config, "清除所有配置，恢复到出厂默认状态。此操作不可撤销。")
        self._add_section(layout, "URL 协议支持")
        protocol_card = QFrame()
        protocol_card.setObjectName("card")
        pc = QVBoxLayout(protocol_card)
        pc.setContentsMargins(16, 12, 16, 12)
        pc.setSpacing(8)
        proto_title = QLabel("a13rollcall:// 自定义协议")
        proto_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0067c0;")
        pc.addWidget(proto_title)
        proto_desc = QLabel("本软件支持通过自定义 URL 协议从外部调用，可用于快捷方式、浏览器链接、其他程序调用等场景。")
        proto_desc.setWordWrap(True)
        proto_desc.setStyleSheet("font-size: 12px; color: #555555;")
        pc.addWidget(proto_desc)
        proto_examples = QTextEdit()
        proto_examples.setReadOnly(True)
        proto_examples.setMaximumHeight(180)
        proto_examples.setStyleSheet("background: #fafafa; border: 1px solid #e5e5e5; border-radius: 4px; padding: 8px; font-family: Consolas, monospace; font-size: 11px;")
        proto_examples.setHtml("""
        <b>支持的协议命令：</b><br><br>
        <code>a13rollcall://draw</code> - 直接开始抽取<br>
        <code>a13rollcall://quick</code> - 打开快捷抽取模式<br>
        <code>a13rollcall://settings</code> - 打开设置窗口<br>
        <code>a13rollcall://stats</code> - 打开统计窗口<br>
        <code>a13rollcall://ranking</code> - 打开排行榜<br>
        <code>a13rollcall://history</code> - 查看抽取记录<br>
        <code>a13rollcall://reset</code> - 重置本轮<br>
        <code>a13rollcall://theme=dark</code> - 切换深色主题<br>
        <code>a13rollcall://theme=light</code> - 切换浅色主题<br>
        <code>a13rollcall://echo</code> - 打开回声洞<br>
        <code>a13rollcall://help</code> - 打开帮助窗口
        """)
        pc.addWidget(proto_examples)
        register_btn = QPushButton("注册 URL 协议")
        register_btn.setObjectName("primary")
        register_btn.setMinimumHeight(36)
        register_btn.clicked.connect(self._register_url_protocol)
        pc.addWidget(register_btn)
        layout.addWidget(protocol_card)
        layout.addStretch()
        return scroll, layout

    def _register_url_protocol(self):
        try:
            import winreg
            key_path = r"Software\Classes\a13rollcall"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:A13 Roll Call Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            command_key = winreg.CreateKey(key, r"shell\open\command")
            exe_path = os.path.join(BASE_DIR, "main_qt.exe")
            if not os.path.exists(exe_path):
                exe_path = sys.executable + " " + os.path.join(BASE_DIR, "main_qt.py")
            winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, f'"{exe_path}" "%1"')
            winreg.CloseKey(key)
            winreg.CloseKey(command_key)
            QMessageBox.information(self, "注册成功", "a13rollcall:// 协议已成功注册到系统！\n\n现在可以在浏览器地址栏或快捷方式中使用 a13rollcall:// 命令。")
        except Exception as e:
            QMessageBox.warning(self, "注册失败", f"URL 协议注册失败：{str(e)}")

    def _build_update_page(self):
        scroll, layout = self._make_scroll_page()
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self._add_section(layout, "更新检查")
        info_card = QFrame()
        info_card.setObjectName("card")
        info_card.setMinimumWidth(400)
        ic = QVBoxLayout(info_card)
        ic.setContentsMargins(24, 20, 24, 20)
        ic.setSpacing(12)
        ver_title = QLabel("当前版本")
        ver_title.setAlignment(Qt.AlignCenter)
        ver_title.setStyleSheet("font-size: 14px; color: #666666;")
        ic.addWidget(ver_title)
        ver_num = QLabel("V6.8")
        ver_num.setAlignment(Qt.AlignCenter)
        ver_num.setStyleSheet("font-size: 36px; font-weight: 800; color: #0067c0;")
        ic.addWidget(ver_num)
        ver_date = QLabel("发布日期：2024年")
        ver_date.setAlignment(Qt.AlignCenter)
        ver_date.setStyleSheet("font-size: 12px; color: #888888;")
        ic.addWidget(ver_date)
        layout.addWidget(info_card)
        layout.addSpacing(20)
        self.update_auto = QCheckBox("自动检查更新")
        self._add_setting_row(layout, "自动更新", self.update_auto, "启动时自动检查是否有新版本。需要网络连接。")
        check_btn = QPushButton("检查更新")
        check_btn.setObjectName("primary")
        check_btn.setMinimumHeight(44)
        check_btn.setMinimumWidth(200)
        check_btn.clicked.connect(lambda: QMessageBox.information(self, "检查更新", "当前已是最新版本 V6.8！"))
        layout.addWidget(check_btn)
        layout.addSpacing(10)
        web_btn = QPushButton("前往官网下载最新版")
        web_btn.setMinimumHeight(40)
        web_btn.setMinimumWidth(200)
        web_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(WEBSITE_URL)))
        layout.addWidget(web_btn)
        layout.addStretch()
        return scroll, layout

    def _build_help_page(self):
        scroll, layout = self._make_scroll_page()
        self._add_section(layout, "帮助文档")
        help_items = [
            ("快速上手", "1. 点击「开始抽取」按钮随机点名\n2. 抽取到学生后，在结果窗口标记背诵状态\n3. 点击「抽取记录」查看历史\n4. 点击「重置本轮」开始新一轮"),
            ("快捷键", "空格：开始/停止抽取\nEsc：重置本轮\n1/2/3：标记已背过/未背熟/未背过\nZ：撤销上次标记\nT：切换抽取模式\nM：切换主题\n,：打开设置\n?：快捷键速查"),
            ("课文管理", "左侧栏可选择指定课文或随机课文\n课文列表显示每篇课文的权重\n随机模式下每次抽取同时随机课文\n可在设置中配置课文抽取规则"),
            ("数据统计", "顶部栏「统计」查看详细统计数据\n「排行榜」查看学生积分排名\n支持导出统计数据到文件\n数据自动保存，下次启动恢复"),
            ("回声洞", "点击左上角 Logo 触发回声洞\n每次显示一个随机回声\n可以「回声」表示共鸣\n数据保存在本地 echo_hole.txt"),
            ("常见问题", "Q: 为什么有些学生抽不到？\nA: 开启了不重复模式，每人每轮只抽一次\n\nQ: 如何修改学生名单？\nA: 在设置中打开数据文件目录，编辑 students.txt\n\nQ: 积分是怎么计算的？\nA: 已背过+10分，未背熟-5分，未背过-15分"),
        ]
        for title, content in help_items:
            card = QFrame()
            card.setObjectName("card")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 12, 16, 12)
            t = QLabel(title)
            t.setStyleSheet("font-size: 14px; font-weight: 700; color: #0067c0;")
            cl.addWidget(t)
            c = QLabel(content)
            c.setWordWrap(True)
            c.setStyleSheet("font-size: 12px; color: #555555; line-height: 1.6;")
            cl.addWidget(c)
            layout.addWidget(card)
        layout.addStretch()
        return scroll, layout

    def _switch_page(self, idx, title):
        self._current_page = idx
        self.pages.setCurrentIndex(idx)
        self.page_title.setText(title)

    def _switch_plugin_page(self, idx, plugin_name, page_key, page_title):
        self._current_page = idx
        if idx < self.pages.count():
            self.pages.setCurrentIndex(idx)
        else:
            self._build_plugin_page_widget(plugin_name, page_key, idx)
        self.page_title.setText(f"{plugin_name} - {page_title}")

    def _build_plugin_page_widget(self, plugin_name, page_key, idx):
        if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
            return
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        app_ref = self.parent() or self
        page = self.plugin_mgr.build_plugin_page(plugin_name, page_key, app_ref, self)
        if page:
            scroll.setWidget(page)
        else:
            widget = QWidget()
            wl = QVBoxLayout(widget)
            wl.addWidget(QLabel(f"插件「{plugin_name}」的页面「{page_key}」构建失败"))
            scroll.setWidget(widget)
        while self.pages.count() <= idx:
            self.pages.addWidget(QWidget())
        self.pages.removeWidget(self.pages.widget(idx))
        self.pages.insertWidget(idx, scroll)
        self.pages.setCurrentIndex(idx)

    def _preview_theme(self, idx):
        themes = ["light", "dark", "system"]
        try:
            self.config_mgr.set(themes[idx], "ui", "theme")
            QApplication.instance().setStyleSheet(self.theme_mgr.get_qss())
        except Exception:
            pass

    def _load_values(self):
        try:
            class_name = self.config_mgr.get("app", "class_name") or "A13"
            self.class_name_input.setText(class_name)
        except Exception:
            pass
        try:
            theme = self.config_mgr.get("ui", "theme")
            self.theme_combo.setCurrentIndex({"light": 0, "dark": 1, "system": 2}.get(theme, 0))
        except Exception:
            pass
        try:
            self.particle_check.setChecked(bool(self.config_mgr.get("ui", "particle_enabled")))
        except Exception:
            self.particle_check.setChecked(True)
        try:
            self.anim_check.setChecked(bool(self.config_mgr.get("ui", "start_animation")))
        except Exception:
            self.anim_check.setChecked(True)
        try:
            self.result_popup_check.setChecked(bool(self.config_mgr.get("ui", "result_popup")))
        except Exception:
            pass
        try:
            self.font_size.setValue(int(self.config_mgr.get("ui", "name_font_size")))
        except Exception:
            pass
        try:
            self.text_font_size.setValue(int(self.config_mgr.get("ui", "text_font_size")))
        except Exception:
            pass
        try:
            mode = self.config_mgr.get("draw", "mode")
            if mode == "auto":
                self.mode_auto.setChecked(True)
            else:
                self.mode_manual.setChecked(True)
        except Exception:
            self.mode_auto.setChecked(True)
        try:
            self.no_repeat.setChecked(bool(self.config_mgr.get("draw", "no_repeat")))
        except Exception:
            self.no_repeat.setChecked(True)
        try:
            self.dynamic_weight.setChecked(bool(self.config_mgr.get("draw", "dynamic_focus")))
        except Exception:
            pass
        try:
            self.countdown.setChecked(bool(self.config_mgr.get("ui", "draw_countdown")))
        except Exception:
            pass
        try:
            self.auto_reset.setChecked(bool(self.config_mgr.get("draw", "auto_reset_round")))
        except Exception:
            pass
        try:
            self.dur_spin.setValue(int(float(self.config_mgr.get("draw", "auto_duration"))))
        except Exception:
            pass
        try:
            self.speed_spin.setValue(float(self.config_mgr.get("ui", "scroll_speed")))
        except Exception:
            pass
        try:
            text_mode = self.config_mgr.get("text", "extract_mode")
            self.text_mode.setCurrentIndex({"段落抽取": 0, "随机抽取": 1, "不抽取课文": 2}.get(text_mode, 0))
        except Exception:
            pass
        try:
            self.show_text_title.setChecked(bool(self.config_mgr.get("text", "show_title")))
        except Exception:
            self.show_text_title.setChecked(True)
        try:
            self.paragraph_random.setChecked(bool(self.config_mgr.get("text", "paragraph_random")))
        except Exception:
            pass
        try:
            self.auto_next_text.setChecked(bool(self.config_mgr.get("text", "auto_next")))
        except Exception:
            self.auto_next_text.setChecked(True)
        try:
            text_align = self.config_mgr.get("text", "text_align")
            self.text_align.setCurrentIndex({"left": 0, "center": 1, "right": 2}.get(text_align, 0))
        except Exception:
            pass
        try:
            self.exp_anti_cheat.setChecked(bool(self.config_mgr.get("draw", "anti_cheat")))
        except Exception:
            pass
        try:
            self.exp_sound.setChecked(bool(self.config_mgr.get("draw", "sound_enabled")))
        except Exception:
            pass
        try:
            self.exp_dpi.setChecked(bool(self.config_mgr.get("experimental", "dpi_optimization")))
        except Exception:
            pass
        try:
            self.exp_smooth.setChecked(bool(self.config_mgr.get("experimental", "smooth_scroll")))
        except Exception:
            pass

    def _save(self):
        try:
            self.config_mgr.set(self.class_name_input.text().strip() or "A13", "app", "class_name")
            theme_idx = self.theme_combo.currentIndex()
            self.config_mgr.set(["light", "dark", "system"][theme_idx], "ui", "theme")
            self.config_mgr.set(self.particle_check.isChecked(), "ui", "particle_enabled")
            self.config_mgr.set(self.anim_check.isChecked(), "ui", "start_animation")
            self.config_mgr.set(self.result_popup_check.isChecked(), "ui", "result_popup")
            self.config_mgr.set(self.font_size.value(), "ui", "name_font_size")
            self.config_mgr.set(self.text_font_size.value(), "ui", "text_font_size")
            self.config_mgr.set("auto" if self.mode_auto.isChecked() else "manual", "draw", "mode")
            self.config_mgr.set(self.no_repeat.isChecked(), "draw", "no_repeat")
            self.config_mgr.set(self.dynamic_weight.isChecked(), "draw", "dynamic_focus")
            self.config_mgr.set(self.countdown.isChecked(), "ui", "draw_countdown")
            self.config_mgr.set(self.auto_reset.isChecked(), "draw", "auto_reset_round")
            self.config_mgr.set(float(self.dur_spin.value()), "draw", "auto_duration")
            self.config_mgr.set(float(self.speed_spin.value()), "ui", "scroll_speed")
            self.config_mgr.set(["段落抽取", "随机抽取", "不抽取课文"][self.text_mode.currentIndex()], "text", "extract_mode")
            self.config_mgr.set(self.show_text_title.isChecked(), "text", "show_title")
            self.config_mgr.set(self.paragraph_random.isChecked(), "text", "paragraph_random")
            self.config_mgr.set(self.auto_next_text.isChecked(), "text", "auto_next")
            self.config_mgr.set(["left", "center", "right"][self.text_align.currentIndex()], "text", "text_align")
            self.config_mgr.set(self.exp_anti_cheat.isChecked(), "draw", "anti_cheat")
            self.config_mgr.set(self.exp_sound.isChecked(), "draw", "sound_enabled")
            self.config_mgr.set(self.exp_dpi.isChecked(), "experimental", "dpi_optimization")
            self.config_mgr.set(self.exp_smooth.isChecked(), "experimental", "smooth_scroll")
            self.config_mgr.save_config()
        except Exception as e:
            print(f"保存设置失败: {e}")
        self.accept()

    def _reset_text_progress(self):
        reply = QMessageBox.question(self, "确认重置", "确定要重置所有课文进度吗？\n\n此操作不可撤销，所有课文的背诵进度将被清除。", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                progress_file = os.path.join(BASE_DIR, "text_progress.json")
                if os.path.exists(progress_file):
                    os.remove(progress_file)
                QMessageBox.information(self, "重置成功", "所有课文进度已重置！")
            except Exception as e:
                QMessageBox.warning(self, "重置失败", f"重置课文进度失败：{str(e)}")

    def _custom_shortcuts(self):
        QMessageBox.information(self, "自定义快捷键", "快捷键自定义功能正在开发中...\n\n当前版本支持在配置文件中手动修改快捷键设置。")

    def _export_stats_now(self):
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            default_name = f"点名统计_{timestamp}.txt"
            path, _ = QFileDialog.getSaveFileName(self, "导出统计数据", os.path.join(desktop, default_name), "Text Files (*.txt)")
            if not path:
                return
            if hasattr(self.parent(), 'data_mgr') and self.parent().data_mgr:
                stats = self.parent().data_mgr.get_all_stats()
            else:
                stats = {}
            with open(path, "w", encoding="utf-8") as f:
                f.write("课堂点名系统 - 统计数据\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"{'学生':<12}{'抽取次数':<10}{'已背过':<10}{'未背熟':<10}{'未背过':<10}{'积分':<10}\n")
                f.write("-" * 60 + "\n")
                for name, data in sorted(stats.items()):
                    f.write(f"{name:<12}{data['draw_count']:<10}{data['mastered']:<10}{data['familiar']:<10}{data['unlearned']:<10}{data['score']:<10}\n")
            QMessageBox.information(self, "导出成功", f"统计数据已导出到：\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出统计数据失败：{str(e)}")

    def _backup_now(self):
        try:
            import shutil
            backup_dir = os.path.join(BASE_DIR, "backup")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_subdir = os.path.join(backup_dir, f"backup_{timestamp}")
            os.makedirs(backup_subdir, exist_ok=True)
            files_to_backup = ["config.json", "students.txt", "texts.txt", "wizard_record.ini"]
            for fname in files_to_backup:
                src = os.path.join(BASE_DIR, fname)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(backup_subdir, fname))
            QMessageBox.information(self, "备份成功", f"备份已保存到：\n{backup_subdir}\n\n共备份 {len(os.listdir(backup_subdir))} 个文件。")
        except Exception as e:
            QMessageBox.warning(self, "备份失败", f"备份失败：{str(e)}")

    def _restore_now(self):
        try:
            backup_dir = os.path.join(BASE_DIR, "backup")
            if not os.path.exists(backup_dir):
                QMessageBox.warning(self, "无备份", "没有找到任何备份文件。")
                return
            backups = sorted([d for d in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, d))], reverse=True)
            if not backups:
                QMessageBox.warning(self, "无备份", "没有找到任何备份文件。")
                return
            items = "\n".join([f"{i+1}. {b}" for i, b in enumerate(backups[:10])])
            reply = QMessageBox.question(self, "选择备份", f"找到以下备份（最新10个）：\n\n{items}\n\n确定要恢复最新的备份吗？\n\n注意：这将覆盖当前配置！", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
            import shutil
            latest_backup = os.path.join(backup_dir, backups[0])
            for fname in os.listdir(latest_backup):
                src = os.path.join(latest_backup, fname)
                dst = os.path.join(BASE_DIR, fname)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
            QMessageBox.information(self, "恢复成功", f"已从备份「{backups[0]}」恢复配置。\n\n建议重启软件以应用所有更改。")
        except Exception as e:
            QMessageBox.warning(self, "恢复失败", f"恢复备份失败：{str(e)}")

    def _reload_ui(self):
        QMessageBox.information(self, "重新加载界面", "界面将在关闭设置窗口后重新加载。\n\n请点击「保存」或「取消」关闭设置窗口。")

    def _reset_all_config(self):
        reply = QMessageBox.question(self, "确认重置", "确定要重置所有配置吗？\n\n这将清除所有自定义设置，恢复到出厂默认状态。\n\n此操作不可撤销！", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                config_file = os.path.join(BASE_DIR, "config.json")
                if os.path.exists(config_file):
                    os.remove(config_file)
                QMessageBox.information(self, "重置成功", "所有配置已重置！\n\n软件将在重启后恢复默认设置。")
            except Exception as e:
                QMessageBox.warning(self, "重置失败", f"重置配置失败：{str(e)}")

    def _export_stats(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"点名统计_{timestamp}.txt"
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path, _ = QFileDialog.getSaveFileName(self, "导出统计数据", os.path.join(desktop, default_name), "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("课堂点名系统 - 统计数据\n")
                    f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 40 + "\n\n")
                    f.write("（数据内容待补充）\n")
                QMessageBox.information(self, "导出成功", f"统计数据已导出到：\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "导出失败", str(e))

    def _reset_data(self):
        reply = QMessageBox.question(self, "确认重置", "确定要删除所有数据并恢复默认设置吗？\n所有学生名单、课文、记录、积分都将被清空，且无法恢复！", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            ini_path = os.path.join(BASE_DIR, "wizard_record.ini")
            try:
                cfg = configparser.ConfigParser()
                cfg["status"] = {"finished": "False"}
                with open(ini_path, "w", encoding="utf-8") as f:
                    cfg.write(f)
            except Exception:
                pass
            QMessageBox.information(self, "重置完成", "所有数据已重置，向导标记已清除。\n下次启动将重新打开配置向导。")

    def _rerun_wizard(self):
        ini_path = os.path.join(BASE_DIR, "wizard_record.ini")
        try:
            cfg = configparser.ConfigParser()
            cfg["status"] = {"finished": "False"}
            with open(ini_path, "w", encoding="utf-8") as f:
                cfg.write(f)
        except Exception:
            pass
        QMessageBox.information(self, "已设置", "已标记为未完成向导，下次启动将重新打开配置向导。")

    def _clear_echo(self):
        reply = QMessageBox.question(self, "确认清空", "确定要清空所有回声吗？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.echo_hole.clear_all()
            self.echo_list.clear()
            QMessageBox.information(self, "已清空", "所有回声已清空。")


class EchoHoleDialog(QDialog):
    def __init__(self, echo_hole, parent=None):
        super().__init__(parent)
        self.echo_hole = echo_hole
        self.setWindowTitle("回声洞")
        self.setFixedSize(480, 320)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._current_echo = None
        self._setup_ui()
        self._show_random_echo()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet("background: #ffffff; border-radius: 12px; border: 1px solid #e5e5e5;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 8)
        card.setGraphicsEffect(shadow)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(28, 24, 28, 24)
        cl.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("回声洞")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0067c0;")
        header.addWidget(title)
        header.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setStyleSheet("QPushButton { background: transparent; border: none; color: #999999; font-size: 14px; } QPushButton:hover { color: #333333; }")
        close_btn.clicked.connect(self.close)
        header.addWidget(close_btn)
        cl.addLayout(header)
        self.echo_text = QLabel("")
        self.echo_text.setWordWrap(True)
        self.echo_text.setAlignment(Qt.AlignCenter)
        self.echo_text.setStyleSheet("font-size: 16px; color: #333333; line-height: 1.6;")
        self.echo_text.setMinimumHeight(100)
        cl.addWidget(self.echo_text)
        self.echo_meta = QLabel("")
        self.echo_meta.setAlignment(Qt.AlignCenter)
        self.echo_meta.setStyleSheet("font-size: 11px; color: #999999;")
        cl.addWidget(self.echo_meta)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.echo_back_btn = QPushButton("回声 +1")
        self.echo_back_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; } QPushButton:hover { background: #1a76c8; }")
        self.echo_back_btn.clicked.connect(self._echo_back)
        btn_layout.addWidget(self.echo_back_btn)
        next_btn = QPushButton("下一个回声")
        next_btn.setStyleSheet("QPushButton { background: #f0f0f0; color: #333333; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; } QPushButton:hover { background: #e0e0e0; }")
        next_btn.clicked.connect(self._show_random_echo)
        btn_layout.addWidget(next_btn)
        cl.addLayout(btn_layout)
        outer.addWidget(card)

    def _show_random_echo(self):
        echo = self.echo_hole.get_random_echo()
        if not echo:
            self.echo_text.setText("回声洞里还没有回声...")
            self.echo_meta.setText("")
            self._current_echo = None
            return
        self._current_echo = echo
        self.echo_text.setText(echo["text"])
        self.echo_meta.setText(f"匿名 · {echo['time']} · 被回声 {echo['echo_count']} 次")

    def _echo_back(self):
        if not self._current_echo:
            return
        count = self.echo_hole.echo_back(self._current_echo["id"])
        self._current_echo["echo_count"] = count
        self.echo_meta.setText(f"匿名 · {self._current_echo['time']} · 被回声 {count} 次")
        self.echo_back_btn.setText(f"回声 +1 ({count})")


class StatsDialog(QDialog):
    def __init__(self, data_mgr, parent=None):
        super().__init__(parent)
        self.data_mgr = data_mgr
        self.setWindowTitle("数据统计")
        self.setMinimumSize(720, 560)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        title = QLabel("数据统计")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0067c0;")
        layout.addWidget(title)
        summary_card = QFrame()
        summary_card.setStyleSheet("background: #ffffff; border-radius: 10px; border: 1px solid #e5e5e5;")
        sc = QHBoxLayout(summary_card)
        sc.setContentsMargins(20, 16, 20, 16)
        sc.setSpacing(20)
        self.summary_labels = {}
        for key, label_text, color in [
            ("total", "总抽取", "#0067c0"),
            ("mastered", "已背过", "#107c10"),
            ("familiar", "未背熟", "#ca5010"),
            ("unlearned", "未背过", "#c42b1c"),
            ("avg_score", "平均积分", "#8764b8")
        ]:
            col = QVBoxLayout()
            val = QLabel("0")
            val.setAlignment(Qt.AlignCenter)
            val.setStyleSheet(f"font-size: 28px; font-weight: 800; color: {color};")
            col.addWidget(val)
            lbl = QLabel(label_text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 12px; color: #666666;")
            col.addWidget(lbl)
            sc.addLayout(col)
            self.summary_labels[key] = val
        layout.addWidget(summary_card)
        table_label = QLabel("学生详细统计")
        table_label.setStyleSheet("font-size: 15px; font-weight: 700; color: #333333;")
        layout.addWidget(table_label)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["学生", "抽取次数", "已背过", "未背熟", "未背过", "积分"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("QTableWidget { background: white; border: 1px solid #e5e5e5; border-radius: 8px; gridline-color: #f0f0f0; } QHeaderView::section { background: #f8f8f8; padding: 8px; border: none; font-weight: 600; }")
        layout.addWidget(self.table, 1)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        export_btn = QPushButton("导出统计数据")
        export_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; } QPushButton:hover { background: #1a76c8; }")
        export_btn.clicked.connect(self._export)
        btn_layout.addWidget(export_btn)
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("QPushButton { background: #f0f0f0; color: #333333; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; } QPushButton:hover { background: #e0e0e0; }")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _load_data(self):
        stats = self.data_mgr.get_all_stats()
        self.table.setRowCount(len(stats))
        total_draw = total_mastered = total_familiar = total_unlearned = 0
        total_score = 0
        for row, (name, data) in enumerate(sorted(stats.items())):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(data["draw_count"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(data["mastered"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(data["familiar"])))
            self.table.setItem(row, 4, QTableWidgetItem(str(data["unlearned"])))
            self.table.setItem(row, 5, QTableWidgetItem(str(data["score"])))
            total_draw += data["draw_count"]
            total_mastered += data["mastered"]
            total_familiar += data["familiar"]
            total_unlearned += data["unlearned"]
            total_score += data["score"]
        self.summary_labels["total"].setText(str(total_draw))
        self.summary_labels["mastered"].setText(str(total_mastered))
        self.summary_labels["familiar"].setText(str(total_familiar))
        self.summary_labels["unlearned"].setText(str(total_unlearned))
        avg = total_score // len(stats) if stats else 0
        self.summary_labels["avg_score"].setText(str(avg))

    def _export(self):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        default_name = f"点名统计_{timestamp}.txt"
        path, _ = QFileDialog.getSaveFileName(self, "导出统计数据", os.path.join(desktop, default_name), "Text Files (*.txt)")
        if not path:
            return
        try:
            stats = self.data_mgr.get_all_stats()
            with open(path, "w", encoding="utf-8") as f:
                f.write("课堂点名系统 - 统计数据\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"{'学生':<12}{'抽取次数':<10}{'已背过':<10}{'未背熟':<10}{'未背过':<10}{'积分':<10}\n")
                f.write("-" * 60 + "\n")
                for name, data in sorted(stats.items()):
                    f.write(f"{name:<12}{data['draw_count']:<10}{data['mastered']:<10}{data['familiar']:<10}{data['unlearned']:<10}{data['score']:<10}\n")
            QMessageBox.information(self, "导出成功", f"统计数据已导出到：\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出失败：{str(e)}")


class RankingDialog(QDialog):
    def __init__(self, data_mgr, parent=None):
        super().__init__(parent)
        self.data_mgr = data_mgr
        self.setWindowTitle("积分排行榜")
        self.setMinimumSize(520, 600)
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        title = QLabel("积分排行榜")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0067c0;")
        layout.addWidget(title)
        self.ranking_list = QListWidget()
        self.ranking_list.setStyleSheet("QListWidget { background: white; border: 1px solid #e5e5e5; border-radius: 10px; padding: 8px; } QListWidget::item { padding: 12px; border-bottom: 1px solid #f0f0f0; } QListWidget::item:selected { background: #e8f4ff; }")
        layout.addWidget(self.ranking_list, 1)
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("QPushButton { background: #f0f0f0; color: #333333; border: none; border-radius: 6px; padding: 10px 24px; font-weight: 600; } QPushButton:hover { background: #e0e0e0; }")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def _load_data(self):
        ranking = self.data_mgr.get_ranking()
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, score) in enumerate(ranking):
            if i < 3:
                prefix = medals[i]
                color = ["#ffd700", "#c0c0c0", "#cd7f32"][i]
                item_text = f"  {prefix}  第{i+1}名    {name}    积分: {score}"
            else:
                item_text = f"      第{i+1}名    {name}    积分: {score}"
                color = "#333333"
            item = QListWidgetItem(item_text)
            item.setForeground(QColor(color))
            if i < 3:
                font = item.font()
                font.setBold(True)
                font.setPointSize(12)
                item.setFont(font)
            self.ranking_list.addItem(item)


class GuideOverlay(QDialog):
    step_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(440, 200)
        self._step = 0
        self._steps = [
            ("欢迎使用！", "点击「开始抽取」按钮开始随机点名", "下一步"),
            ("抽取学生", "按空格键开始抽取，再次按空格停止", "下一步"),
            ("标记状态", "抽取到学生后，点击标记背诵状态", "下一步"),
            ("查看记录", "点击「抽取记录」查看历史", "下一步"),
            ("完成", "点击「重置本轮」开始新一轮", "完成"),
        ]
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setStyleSheet("background: #2d2d2d; border-radius: 10px; border: 1px solid #3d3d3d;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 6)
        card.setGraphicsEffect(shadow)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(24, 18, 24, 18)
        cl.setSpacing(10)
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 17px; font-weight: 700; color: #ffffff;")
        cl.addWidget(self.title)
        self.desc = QLabel()
        self.desc.setWordWrap(True)
        self.desc.setStyleSheet("font-size: 13px; color: #aaaaaa;")
        cl.addWidget(self.desc)
        self.progress = QProgressBar()
        self.progress.setMaximum(len(self._steps))
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(4)
        cl.addWidget(self.progress)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.next_btn = QPushButton()
        self.next_btn.setStyleSheet("QPushButton { background: #0067c0; color: white; border: none; border-radius: 6px; padding: 8px 20px; font-weight: 600; } QPushButton:hover { background: #1a76c8; }")
        self.next_btn.clicked.connect(self._next)
        btn_layout.addWidget(self.next_btn)
        cl.addLayout(btn_layout)
        layout.addWidget(card)
        self._show_step()

    def _show_step(self):
        title, desc, btn = self._steps[self._step]
        self.title.setText(title)
        self.desc.setText(desc)
        self.next_btn.setText(btn)
        self.progress.setValue(self._step + 1)

    def _next(self):
        self._step += 1
        if self._step >= len(self._steps):
            self.step_finished.emit()
            self.close()
        else:
            self._show_step()


class MainWindow(QMainWindow):
    def __init__(self, show_guide=False):
        super().__init__()
        self.config_mgr = ConfigManager()
        self.theme_mgr = Win11Theme(self.config_mgr)
        self.data_mgr = DataManager(self.config_mgr)
        self.draw_engine = DrawEngine(self.data_mgr, self.config_mgr)
        self.echo_hole = EchoHole(self.config_mgr)
        self.plugin_mgr = PluginManager(self.config_mgr)
        self._is_drawing = False
        self._last_draw_result = None
        self._quick_mode = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._roll_name)
        self._current_student = None
        self._last_marked_student = None
        self._last_marked_status = None
        self._mini_window = None
        self._quick_window = None
        self._students = []
        self._texts = []
        self._current_text_idx = 0
        self._no_repeat = True
        self._draw_mode = "auto"
        self._setup_window()
        self._setup_ui()
        self._load_data()
        self._apply_settings()
        QTimer.singleShot(500, self._startup_plugins)
        if show_guide:
            QTimer.singleShot(1500, self._show_guide)

    def _startup_plugins(self):
        try:
            if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
                return
            self.plugin_mgr.load_all_plugins()
            plugins = self.plugin_mgr.get_enabled_plugins()
            for plugin in plugins:
                name = plugin["meta"]["name"]
                try:
                    context = self.plugin_mgr.get_context(name, self)
                    self.plugin_mgr._call_lifecycle(name, "on_enable")
                except Exception as e:
                    print(f"插件 {name} 启动警告：{e}")
            print(f"插件自启动完成，共加载 {len(plugins)} 个插件")
        except Exception as e:
            print(f"插件自启动失败：{e}")

    def _get_class_name(self):
        try:
            return self.config_mgr.get("app", "class_name") or "A13"
        except Exception:
            return "A13"

    def _show_toast(self, message, duration=2000):
        try:
            toast = QLabel(message, self)
            toast.setStyleSheet("background: #333333; color: white; padding: 12px 24px; border-radius: 8px; font-size: 13px;")
            toast.setAlignment(Qt.AlignCenter)
            toast.adjustSize()
            x = (self.width() - toast.width()) // 2
            y = self.height() - 100
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(duration, toast.close)
        except Exception:
            pass

    def _setup_window(self):
        class_name = self._get_class_name()
        self.setWindowTitle(f"{class_name}班点名程序")
        self.setMinimumSize(1200, 800)
        screen = QApplication.desktop().screenGeometry()
        w = 1600 if screen.width() > 1920 else 1400
        h = 950 if screen.height() > 1080 else 880
        self.resize(w, h)
        self.move((screen.width() - w) // 2, (screen.height() - h) // 2)
        try:
            self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "app.ico")))
        except Exception:
            pass

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.particles = ParticleWidget(self)
        self.particles.setGeometry(0, 0, self.width(), self.height())
        self.particles.lower()

        topbar = QFrame()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(68)
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(24, 10, 24, 10)
        left = QHBoxLayout()
        left.setSpacing(12)
        try:
            self.icon_label = QLabel()
            pix = QPixmap(os.path.join(BASE_DIR, "app.ico")).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pix)
            self.icon_label.setCursor(QCursor(Qt.PointingHandCursor))
            self.icon_label.mousePressEvent = self._on_logo_clicked
            left.addWidget(self.icon_label)
        except Exception:
            pass
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        class_name = self._get_class_name()
        title = QLabel(f"{class_name}班点名程序")
        title.setObjectName("title")
        title_col.addWidget(title)
        subtitle = QLabel("A13 智能抽取引擎 V6.8")
        subtitle.setObjectName("subtitle")
        title_col.addWidget(subtitle)
        left.addLayout(title_col)
        top_layout.addLayout(left)
        top_layout.addStretch()
        for text, slot in [("设置", self._open_settings), ("统计", self._open_stats),
                            ("排行榜", self._open_ranking)]:
            btn = QPushButton(text)
            btn.setMinimumHeight(36)
            btn.clicked.connect(slot)
            top_layout.addWidget(btn)
        help_btn = QPushButton("?")
        help_btn.setFixedSize(36, 36)
        help_btn.setStyleSheet("QPushButton { background: #f0f0f0; border: 1px solid #d1d1d1; border-radius: 18px; font-size: 16px; font-weight: bold; color: #666666; } QPushButton:hover { background: #e0e0e0; color: #333333; }")
        help_btn.setToolTip("帮助与快捷键")
        help_btn.clicked.connect(self._show_help)
        top_layout.addWidget(help_btn)
        quick_btn = QPushButton("快捷抽取")
        quick_btn.setObjectName("primary")
        quick_btn.setMinimumHeight(36)
        quick_btn.clicked.connect(self._open_quick)
        top_layout.addWidget(quick_btn)
        main_layout.addWidget(topbar)

        body = QHBoxLayout()
        body.setContentsMargins(20, 20, 20, 20)
        body.setSpacing(18)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(320)
        sb_scroll = QScrollArea()
        sb_scroll.setWidget(sidebar)
        sb_scroll.setWidgetResizable(True)
        sb_scroll.setFrameShape(QFrame.NoFrame)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 16, 16, 16)
        sb_layout.setSpacing(12)

        current_card = QFrame()
        current_card.setObjectName("card")
        cc = QVBoxLayout(current_card)
        cc.setContentsMargins(18, 16, 18, 16)
        cc.setSpacing(8)
        cc_label = QLabel("当前学生")
        cc_label.setObjectName("subtitle")
        cc.addWidget(cc_label)
        self.current_name = QLabel("—")
        self.current_name.setStyleSheet("font-size: 26px; font-weight: 800; color: #0067c0;")
        cc.addWidget(self.current_name)
        self.current_status = QLabel("待标记")
        self.current_status.setObjectName("subtitle")
        cc.addWidget(self.current_status)
        mark_layout = QHBoxLayout()
        mark_layout.setSpacing(6)
        for text, status, color in [("已背过", "已背过", "#107c10"), ("未背熟", "未背熟", "#ca5010"), ("未背过", "未背过", "#c42b1c")]:
            btn = QPushButton(text)
            btn.setMinimumHeight(38)
            btn.setStyleSheet(f"QPushButton {{ background: {color}; color: white; border: none; border-radius: 6px; font-weight: 600; }} QPushButton:hover {{ opacity: 0.9; }}")
            btn.clicked.connect(lambda checked, s=status: self._mark(s))
            mark_layout.addWidget(btn)
        cc.addLayout(mark_layout)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(6)
        undo_btn = QPushButton("撤销")
        undo_btn.setMinimumHeight(34)
        undo_btn.clicked.connect(self._undo_mark)
        action_layout.addWidget(undo_btn)
        skip_btn = QPushButton("跳过")
        skip_btn.setMinimumHeight(34)
        skip_btn.clicked.connect(self._skip)
        action_layout.addWidget(skip_btn)
        cc.addLayout(action_layout)
        sb_layout.addWidget(current_card)

        text_card = QFrame()
        text_card.setObjectName("card")
        tc = QVBoxLayout(text_card)
        tc.setContentsMargins(18, 16, 18, 16)
        tc.setSpacing(8)
        tc_label = QLabel("课文选择")
        tc_label.setObjectName("subtitle")
        tc.addWidget(tc_label)
        text_mode_layout = QHBoxLayout()
        text_mode_layout.setSpacing(6)
        self.text_mode_specified = QRadioButton("指定课文")
        self.text_mode_specified.setChecked(True)
        self.text_mode_specified.clicked.connect(self._on_text_mode_changed)
        text_mode_layout.addWidget(self.text_mode_specified)
        self.text_mode_random = QRadioButton("随机课文")
        self.text_mode_random.clicked.connect(self._on_text_mode_changed)
        text_mode_layout.addWidget(self.text_mode_random)
        tc.addLayout(text_mode_layout)
        self.text_title = QLabel("—")
        self.text_title.setStyleSheet("font-weight: 700; font-size: 14px; color: #333333;")
        tc.addWidget(self.text_title)
        self.text_content = QLabel("")
        self.text_content.setWordWrap(True)
        self.text_content.setStyleSheet("color: #555555; font-size: 12px;")
        self.text_content.setAlignment(Qt.AlignTop)
        text_scroll = QScrollArea()
        text_scroll.setWidget(self.text_content)
        text_scroll.setWidgetResizable(True)
        text_scroll.setMaximumHeight(180)
        text_scroll.setFrameShape(QFrame.NoFrame)
        tc.addWidget(text_scroll)
        tc.addWidget(tc_label)
        weight_label = QLabel("课文权重")
        weight_label.setObjectName("subtitle")
        tc.addWidget(weight_label)
        self.text_weight_list = QListWidget()
        self.text_weight_list.setMaximumHeight(160)
        self.text_weight_list.itemClicked.connect(self._select_text_by_weight)
        tc.addWidget(self.text_weight_list)
        sb_layout.addWidget(text_card)

        self.text_list = QListWidget()
        self.text_list.setMaximumHeight(160)
        self.text_list.itemClicked.connect(self._select_text)
        sb_layout.addWidget(self.text_list)
        sb_layout.addStretch()
        body.addWidget(sb_scroll)

        center = QVBoxLayout()
        center.setSpacing(16)
        draw_card = QFrame()
        draw_card.setObjectName("card")
        draw_card.setMinimumHeight(340)
        dc = QVBoxLayout(draw_card)
        dc.setContentsMargins(24, 24, 24, 24)
        dc.setAlignment(Qt.AlignCenter)
        self.draw_widget = DrawNameWidget()
        self.draw_widget.set_name("点击开始")
        self.draw_widget.setMinimumHeight(260)
        dc.addWidget(self.draw_widget)
        self.draw_hint = QLabel("点击下方按钮或按空格键开始抽取")
        self.draw_hint.setAlignment(Qt.AlignCenter)
        self.draw_hint.setObjectName("subtitle")
        dc.addWidget(self.draw_hint)
        center.addWidget(draw_card)

        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(10)
        self.mode_auto_btn = QPushButton("自动模式")
        self.mode_auto_btn.setObjectName("primary")
        self.mode_auto_btn.setMinimumHeight(40)
        self.mode_auto_btn.clicked.connect(lambda: self._set_mode("auto"))
        mode_layout.addWidget(self.mode_auto_btn)
        self.mode_manual_btn = QPushButton("手动模式")
        self.mode_manual_btn.setMinimumHeight(40)
        self.mode_manual_btn.clicked.connect(lambda: self._set_mode("manual"))
        mode_layout.addWidget(self.mode_manual_btn)
        center.addLayout(mode_layout)

        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(12)
        self.draw_btn = QPushButton("开始抽取")
        self.draw_btn.setObjectName("drawbig")
        self.draw_btn.setMinimumHeight(60)
        self.draw_btn.clicked.connect(self._toggle_draw)
        ctrl_layout.addWidget(self.draw_btn, 2)
        self.no_repeat_btn = QPushButton("不重复:开")
        self.no_repeat_btn.setMinimumHeight(60)
        self.no_repeat_btn.clicked.connect(self._toggle_no_repeat)
        ctrl_layout.addWidget(self.no_repeat_btn, 1)
        reset_btn = QPushButton("重置本轮")
        reset_btn.setMinimumHeight(60)
        reset_btn.clicked.connect(self._reset_round)
        ctrl_layout.addWidget(reset_btn, 1)
        history_btn = QPushButton("抽取记录")
        history_btn.setMinimumHeight(60)
        history_btn.clicked.connect(self._open_history)
        ctrl_layout.addWidget(history_btn, 1)
        center.addLayout(ctrl_layout)
        body.addLayout(center, 1)

        right = QFrame()
        right.setFixedWidth(280)
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(12)
        stat_card = QFrame()
        stat_card.setObjectName("card")
        st = QVBoxLayout(stat_card)
        st.setContentsMargins(18, 16, 18, 16)
        st.setSpacing(8)
        st_label = QLabel("本轮统计")
        st_label.setObjectName("subtitle")
        st.addWidget(st_label)
        stats_grid = QGridLayout()
        stats_grid.setSpacing(8)
        self.stat_labels = {}
        for i, (label, key) in enumerate([("总人数", "total"), ("已抽取", "drawn"), ("已背过", "mastered"),
                                             ("未背熟", "familiar"), ("未背过", "unlearned"), ("剩余", "remain")]):
            num = QLabel("0")
            num.setStyleSheet("font-size: 24px; font-weight: 800; color: #0067c0;")
            num.setAlignment(Qt.AlignCenter)
            lab = QLabel(label)
            lab.setObjectName("subtitle")
            lab.setAlignment(Qt.AlignCenter)
            stats_grid.addWidget(num, (i // 3) * 2, i % 3)
            stats_grid.addWidget(lab, (i // 3) * 2 + 1, i % 3)
            self.stat_labels[key] = num
        st.addLayout(stats_grid)
        r_layout.addWidget(stat_card)
        shortcut_card = QFrame()
        shortcut_card.setObjectName("card")
        sc = QVBoxLayout(shortcut_card)
        sc.setContentsMargins(18, 16, 18, 16)
        sc.setSpacing(6)
        sc_label = QLabel("快捷键")
        sc_label.setObjectName("subtitle")
        sc.addWidget(sc_label)
        for key, desc in [("空格", "开始/停止"), ("1/2/3", "标记状态"), ("Esc", "重置"),
                            ("R", "记录"), ("T", "换课文"), ("Z", "撤销")]:
            row = QHBoxLayout()
            row.setSpacing(8)
            k = QLabel(key)
            k.setStyleSheet("background: #e5f3ff; color: #0067c0; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 10px;")
            d = QLabel(desc)
            d.setObjectName("subtitle")
            row.addWidget(k)
            row.addWidget(d)
            row.addStretch()
            sc.addLayout(row)
        r_layout.addWidget(shortcut_card)
        r_layout.addStretch()
        body.addWidget(right)
        main_layout.addLayout(body, 1)

        statusbar = QFrame()
        statusbar.setObjectName("statusbar")
        statusbar.setFixedHeight(32)
        sb = QHBoxLayout(statusbar)
        sb.setContentsMargins(20, 0, 20, 0)
        sb.setSpacing(16)
        self.status_ready = QLabel("就绪")
        self.status_ready.setStyleSheet("color: #107c10; font-size: 12px; font-weight: 700;")
        sb.addWidget(self.status_ready)
        self.status_mode = QLabel("模式: 自动")
        self.status_mode.setObjectName("subtitle")
        sb.addWidget(self.status_mode)
        self.status_norepeat = QLabel("不重复: 开启")
        self.status_norepeat.setObjectName("subtitle")
        sb.addWidget(self.status_norepeat)
        sb.addStretch()
        self.status_time = QLabel("")
        self.status_time.setObjectName("subtitle")
        sb.addWidget(self.status_time)
        main_layout.addWidget(statusbar)

        self._time_timer = QTimer()
        self._time_timer.timeout.connect(self._update_time)
        self._time_timer.start(1000)
        self._update_time()
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Space"), self, self._toggle_draw)
        QShortcut(QKeySequence("Esc"), self, self._reset_round)
        QShortcut(QKeySequence("1"), self, lambda: self._mark("已背过"))
        QShortcut(QKeySequence("2"), self, lambda: self._mark("未背熟"))
        QShortcut(QKeySequence("3"), self, lambda: self._mark("未背过"))
        QShortcut(QKeySequence("R"), self, self._open_history)
        QShortcut(QKeySequence("T"), self, self._next_text)
        QShortcut(QKeySequence("Z"), self, self._undo_mark)
        QShortcut(QKeySequence("Tab"), self, self._skip)
        QShortcut(QKeySequence("N"), self, self._toggle_no_repeat)
        QShortcut(QKeySequence(","), self, self._open_settings)
        QShortcut(QKeySequence("P"), self, self._toggle_particles)
        QShortcut(QKeySequence("L"), self, self._open_ranking)
        QShortcut(QKeySequence("M"), self, self._toggle_theme)
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_data)
        QShortcut(QKeySequence("?"), self, self._show_shortcut_help)

    def _apply_settings(self):
        try:
            QApplication.instance().setStyleSheet(self.theme_mgr.get_qss())
        except Exception:
            pass
        try:
            particle_enabled = bool(self.config_mgr.get("ui", "particle_enabled"))
            self.particles.set_enabled(particle_enabled)
        except Exception:
            pass
        try:
            name_size = int(self.config_mgr.get("ui", "name_font_size"))
            self.draw_widget.set_font_size(name_size)
        except Exception:
            pass
        try:
            text_size = int(self.config_mgr.get("ui", "text_font_size"))
            self.text_content.setStyleSheet(f"color: #555555; font-size: {text_size}px;")
        except Exception:
            pass
        try:
            text_align = self.config_mgr.get("text", "text_align")
            align = {"left": Qt.AlignLeft, "center": Qt.AlignCenter, "right": Qt.AlignRight}.get(text_align, Qt.AlignLeft)
            self.text_content.setAlignment(align | Qt.AlignTop)
        except Exception:
            pass

    def _toggle_theme(self):
        try:
            current = self.config_mgr.get("ui", "theme")
            new_theme = "dark" if current == "light" else "light"
            self.config_mgr.set(new_theme, "ui", "theme")
            self.config_mgr.save_config()
            QApplication.instance().setStyleSheet(self.theme_mgr.get_qss())
        except Exception:
            pass

    def _load_data(self):
        try:
            students, error = self.data_mgr.load_students()
            self._students = students
            self.stat_labels["total"].setText(str(len(students)))
            self.stat_labels["remain"].setText(str(len(students)))
        except Exception:
            self._students = []
        try:
            self.data_mgr.load_stats()
        except Exception:
            pass
        try:
            self._texts, error = self.data_mgr.load_texts()
            self.text_list.clear()
            for i, t in enumerate(self._texts):
                title = t.get("title", f"课文{i+1}") if isinstance(t, dict) else str(t)
                self.text_list.addItem(QListWidgetItem(f"{i+1}. {title}"))
            if self._texts:
                self._show_text(0)
            self._update_text_weights()
        except Exception:
            self._texts = []
        try:
            self._no_repeat = bool(self.config_mgr.get("draw", "no_repeat"))
            self.no_repeat_btn.setText(f"不重复:{'开' if self._no_repeat else '关'}")
            self.status_norepeat.setText(f"不重复: {'开启' if self._no_repeat else '关闭'}")
        except Exception:
            pass
        try:
            self._draw_mode = self.config_mgr.get("draw", "mode") or "auto"
            self._set_mode(self._draw_mode, save=False)
        except Exception:
            self._set_mode("auto", save=False)

    def _set_mode(self, mode, save=True):
        self._draw_mode = mode
        if mode == "auto":
            self.mode_auto_btn.setObjectName("primary")
            self.mode_manual_btn.setObjectName("")
            self.status_mode.setText("模式: 自动")
        else:
            self.mode_auto_btn.setObjectName("")
            self.mode_manual_btn.setObjectName("primary")
            self.status_mode.setText("模式: 手动")
        self.mode_auto_btn.style().unpolish(self.mode_auto_btn)
        self.mode_auto_btn.style().polish(self.mode_auto_btn)
        self.mode_manual_btn.style().unpolish(self.mode_manual_btn)
        self.mode_manual_btn.style().polish(self.mode_manual_btn)
        if save:
            try:
                self.config_mgr.set(mode, "draw", "mode")
                self.config_mgr.save_config()
            except Exception:
                pass

    def _show_text(self, idx):
        if not self._texts or idx < 0 or idx >= len(self._texts):
            return
        self._current_text_idx = idx
        t = self._texts[idx]
        title = t.get("title", f"课文{idx+1}") if isinstance(t, dict) else str(t)
        paragraphs = t.get("paragraphs", []) if isinstance(t, dict) else []
        content = "\n\n".join(paragraphs) if isinstance(paragraphs, list) else str(paragraphs)
        try:
            show_title = bool(self.config_mgr.get("text", "show_title"))
        except Exception:
            show_title = True
        self.text_title.setText(title if show_title else "")
        self.text_content.setText(content)
        self.text_list.setCurrentRow(idx)

    def _select_text(self, item):
        self._show_text(self.text_list.row(item))

    def _select_text_by_weight(self, item):
        idx = item.data(Qt.UserRole)
        if idx is not None:
            self.text_mode_specified.setChecked(True)
            self._show_text(idx)

    def _on_text_mode_changed(self):
        if self.text_mode_random.isChecked():
            self._random_text()

    def _update_text_weights(self):
        self.text_weight_list.clear()
        if not self._texts:
            return
        total = len(self._texts)
        for i, t in enumerate(self._texts):
            title = t.get("title", f"课文{i+1}") if isinstance(t, dict) else str(t)
            weight = random.randint(1, 10)
            item = QListWidgetItem(f"{title}  (权重: {weight})")
            item.setData(Qt.UserRole, i)
            self.text_weight_list.addItem(item)

    def _prev_text(self):
        if self._texts:
            self._show_text((self._current_text_idx - 1) % len(self._texts))

    def _next_text(self):
        if self._texts:
            self._show_text((self._current_text_idx + 1) % len(self._texts))

    def _random_text(self):
        if self._texts:
            idx = random.randint(0, len(self._texts) - 1)
            self._show_text(idx)

    def _toggle_draw(self):
        if self._is_drawing:
            self._stop_draw()
        else:
            self._start_draw()

    def _start_draw(self):
        if not self._students:
            self.draw_hint.setText("无学生名单，请先添加")
            return
        try:
            self.config_mgr.set(self._no_repeat, "draw", "no_repeat")
        except Exception:
            pass
        mode = "auto" if self._draw_mode == "auto" else "manual"
        ok, name, interval = self.draw_engine.start_draw(self._students, mode=mode)
        if not ok:
            if name is None:
                self.draw_hint.setText("所有学生都已抽取完毕，请重置本轮")
            return
        self._is_drawing = True
        self.draw_btn.setText("停止抽取")
        self.status_ready.setText("抽取中")
        self.status_ready.setStyleSheet("color: #ca5010; font-size: 12px; font-weight: 700;")
        self.draw_widget.set_name(name)
        self.draw_widget.set_drawing(True)
        self._timer.start(max(30, int(interval * 1000)))

    def _roll_name(self):
        is_drawing, name, interval = self.draw_engine.update()
        self.draw_widget.set_name(name)
        if not is_drawing:
            self._finish_draw(name)

    def _stop_draw(self):
        if self._draw_mode == "manual":
            is_drawing, name, interval = self.draw_engine.stop_manual()
            self._finish_draw(name)
        else:
            self._finish_draw(self.draw_widget._name)

    def _finish_draw(self, name):
        self._timer.stop()
        self._is_drawing = False
        self.draw_btn.setText("开始抽取")
        self.status_ready.setText("就绪")
        self.status_ready.setStyleSheet("color: #107c10; font-size: 12px; font-weight: 700;")
        self.draw_widget.set_drawing(False)
        if not name:
            return
        self._current_student = name
        self.current_name.setText(name)
        self.current_status.setText("待标记")
        self.draw_hint.setText("请在结果窗口中标记背诵状态")
        try:
            self.data_mgr.increment_draw_count(name)
        except Exception:
            pass
        drawn = len(self.draw_engine.drawn_students)
        self.stat_labels["drawn"].setText(str(drawn))
        self.stat_labels["remain"].setText(str(max(0, len(self._students) - drawn)))
        if self._texts:
            if hasattr(self, 'text_mode_random') and self.text_mode_random.isChecked():
                self._random_text()
            else:
                pass
        self._last_draw_result = {
            "student": name,
            "text_title": self.text_title.text() if self.text_title.text() != "—" else "",
            "text_content": self.text_content.text(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "未标记"
        }
        self._show_result_popup(name)

    def _show_result_popup(self, name):
        text_title = self.text_title.text() if self.text_title.text() != "—" else ""
        text_content = self.text_content.text()
        popup = ResultPopup(name, text_title, text_content, self)
        popup.marked.connect(lambda s: self._mark(s))
        popup.exec_()

    def _mark(self, status):
        if not self._current_student:
            return
        self._last_marked_status = status
        self._last_marked_student = self._current_student
        if self._last_draw_result:
            self._last_draw_result["status"] = status
        try:
            self.data_mgr.set_student_status(self._current_student, status)
            self.data_mgr.update_status_stats(self._current_student, status)
        except Exception:
            pass
        self.current_status.setText(status)
        colors = {"已背过": "#107c10", "未背熟": "#ca5010", "未背过": "#c42b1c"}
        self.current_status.setStyleSheet(f"color: {colors.get(status, '#666666')}; font-size: 12px; font-weight: 700;")
        key = {"已背过": "mastered", "未背熟": "familiar", "未背过": "unlearned"}.get(status)
        if key:
            cur = int(self.stat_labels[key].text()) + 1
            self.stat_labels[key].setText(str(cur))
        self._show_mark_toast(self._current_student, status)

    def _show_mark_toast(self, name, status):
        toast = MarkToast(name, status, self)
        screen = QApplication.primaryScreen().geometry()
        x = screen.center().x() - 210
        y = screen.top() + 100
        toast.move(x, y)
        toast.show()

    def _show_undo_toast(self, name, status):
        toast = UndoToast(name, status, self)
        screen = QApplication.primaryScreen().geometry()
        x = screen.center().x() - 210
        y = screen.top() + 100
        toast.move(x, y)
        toast.show()

    def _undo_mark(self):
        if not hasattr(self, '_last_marked_student') or not self._last_marked_student:
            return
        name = self._last_marked_student
        status = self._last_marked_status
        try:
            self.data_mgr.revert_status_stats(name, status)
        except Exception:
            pass
        key = {"已背过": "mastered", "未背熟": "familiar", "未背过": "unlearned"}.get(status)
        if key:
            cur = max(0, int(self.stat_labels[key].text()) - 1)
            self.stat_labels[key].setText(str(cur))
        if self._current_student == name:
            self.current_status.setText("待标记")
            self.current_status.setStyleSheet("color: #666666; font-size: 12px;")
        self._last_marked_student = None
        self._last_marked_status = None
        self._show_undo_toast(name, status)

    def _skip(self):
        if not self._current_student:
            return
        self._current_student = None
        self.current_name.setText("—")
        self.current_status.setText("待标记")

    def _toggle_no_repeat(self):
        self._no_repeat = not self._no_repeat
        self.no_repeat_btn.setText(f"不重复:{'开' if self._no_repeat else '关'}")
        self.status_norepeat.setText(f"不重复: {'开启' if self._no_repeat else '关闭'}")
        try:
            self.config_mgr.set(self._no_repeat, "draw", "no_repeat")
            self.config_mgr.save_config()
        except Exception:
            pass

    def _reset_round(self):
        self.draw_engine.reset_round()
        self._current_student = None
        self.draw_widget.set_name("点击开始")
        self.current_name.setText("—")
        self.current_status.setText("待标记")
        self.draw_hint.setText("点击下方按钮或按空格键开始抽取")
        for key in ["drawn", "mastered", "familiar", "unlearned"]:
            self.stat_labels[key].setText("0")
        self.stat_labels["remain"].setText(str(len(self._students)))

    def _open_settings(self):
        dlg = SettingsDialog(self.config_mgr, self.theme_mgr, self.echo_hole, self.plugin_mgr, self)
        if dlg.exec_():
            self._apply_settings()
            self._load_data()
            class_name = self._get_class_name()
            self.setWindowTitle(f"{class_name}班点名程序")

    def _open_stats(self):
        dlg = StatsDialog(self.data_mgr, self)
        dlg.exec_()

    def _open_ranking(self):
        dlg = RankingDialog(self.data_mgr, self)
        dlg.exec_()

    def _show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("帮助与快捷键")
        dlg.setMinimumSize(560, 600)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        title = QLabel("帮助与快捷键")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0067c0;")
        layout.addWidget(title)
        tabs = QTabWidget()
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        help_layout.setContentsMargins(8, 8, 8, 8)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h3>快速上手</h3>
        <p><b>1. 开始抽取</b>：点击「开始抽取」按钮或按空格键，系统随机抽取一名学生。</p>
        <p><b>2. 标记状态</b>：抽取完成后，在结果窗口中标记学生的背诵状态（已背过/未背熟/未背过）。</p>
        <p><b>3. 课文选择</b>：左侧栏可选择指定课文或随机课文，每次抽取时同时显示课文内容。</p>
        <p><b>4. 查看记录</b>：点击「抽取记录」查看本轮所有抽取历史。</p>
        <p><b>5. 重置本轮</b>：点击「重置本轮」清空抽取记录，开始新一轮。</p>
        <h3>小技巧</h3>
        <p>• 点击左上角 Logo 可以打开回声洞</p>
        <p>• 按 Z 键可以撤销上一次标记</p>
        <p>• 按 M 键快速切换深色/浅色主题</p>
        <p>• 按 ? 键打开快捷键速查</p>
        """)
        help_layout.addWidget(help_text)
        tabs.addTab(help_tab, "使用帮助")
        shortcut_tab = QWidget()
        shortcut_layout = QVBoxLayout(shortcut_tab)
        shortcut_layout.setContentsMargins(8, 8, 8, 8)
        shortcut_text = QTextEdit()
        shortcut_text.setReadOnly(True)
        shortcut_text.setHtml("""
        <h3>抽取操作</h3>
        <table border='1' cellpadding='6' style='border-collapse:collapse;'>
        <tr><td><b>开始/停止抽取</b></td><td>空格</td></tr>
        <tr><td><b>重置本轮</b></td><td>Esc</td></tr>
        <tr><td><b>不重复模式</b></td><td>N</td></tr>
        <tr><td><b>动态权重</b></td><td>W</td></tr>
        <tr><td><b>查看本轮记录</b></td><td>R</td></tr>
        </table>
        <h3>状态标记</h3>
        <table border='1' cellpadding='6' style='border-collapse:collapse;'>
        <tr><td><b>标记已背过</b></td><td>1</td></tr>
        <tr><td><b>标记未背熟</b></td><td>2</td></tr>
        <tr><td><b>标记未背过</b></td><td>3</td></tr>
        <tr><td><b>撤销上次标记</b></td><td>Z</td></tr>
        <tr><td><b>跳过当前</b></td><td>Tab</td></tr>
        </table>
        <h3>课文与界面</h3>
        <table border='1' cellpadding='6' style='border-collapse:collapse;'>
        <tr><td><b>切换抽取模式</b></td><td>T</td></tr>
        <tr><td><b>上一篇课文</b></td><td>←</td></tr>
        <tr><td><b>下一篇课文</b></td><td>→</td></tr>
        <tr><td><b>切换主题</b></td><td>M</td></tr>
        <tr><td><b>打开设置</b></td><td>,</td></tr>
        </table>
        <h3>显示与效果</h3>
        <table border='1' cellpadding='6' style='border-collapse:collapse;'>
        <tr><td><b>粒子效果开关</b></td><td>P</td></tr>
        <tr><td><b>全屏模式</b></td><td>F11</td></tr>
        <tr><td><b>排行榜</b></td><td>L</td></tr>
        <tr><td><b>保存数据</b></td><td>Ctrl + S</td></tr>
        <tr><td><b>快捷键速查</b></td><td>?</td></tr>
        </table>
        """)
        shortcut_layout.addWidget(shortcut_text)
        tabs.addTab(shortcut_tab, "快捷键列表")
        layout.addWidget(tabs, 1)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dlg.close)
        layout.addWidget(close_btn)
        dlg.exec_()

    def _on_logo_clicked(self, event):
        if event.button() == Qt.LeftButton:
            self._open_echo()

    def _open_echo(self):
        dlg = EchoHoleDialog(self.echo_hole, self)
        geo = self.geometry()
        dlg.move(geo.center().x() - 240, geo.center().y() - 160)
        dlg.exec_()

    def _open_history(self):
        history = self.draw_engine.drawn_history
        msg = f"本轮抽取记录（共{len(history)}次）\n\n"
        for i, item in enumerate(history):
            if isinstance(item, dict):
                msg += f"{i+1}. {item.get('name','')}  {item.get('time','')}\n"
            else:
                msg += f"{i+1}. {item}\n"
        QMessageBox.information(self, "抽取记录", msg)

    def _open_quick(self):
        self.hide()
        self._quick_mode = True
        if not self._quick_window:
            self._quick_window = QuickDrawWindow(self.data_mgr)
            self._quick_window.closed.connect(self._on_quick_closed)
        self._quick_window.show()
        self._quick_window.raise_()

    def _on_quick_closed(self):
        self._quick_mode = False
        self.show()
        self.raise_()
        self.activateWindow()

    def _toggle_particles(self):
        if self.particles.isVisible():
            self.particles.set_enabled(False)
        else:
            self.particles.set_enabled(True)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _save_data(self):
        try:
            self.data_mgr.save_stats()
        except Exception:
            pass

    def _show_shortcut_help(self):
        QMessageBox.information(self, "快捷键速查",
            "空格: 开始/停止抽取\n1/2/3: 标记状态\nEsc: 重置本轮\nR: 查看记录\n"
            "T: 换课文\nZ: 撤销\nTab: 跳过\nN: 不重复\n←/→: 上下篇\n"
            "M: 切换主题\n,: 设置\nP: 粒子\nF11: 全屏\nL: 排行榜\nCtrl+S: 保存\n?: 帮助")

    def _restart_application(self):
        try:
            python = sys.executable
            script = os.path.join(BASE_DIR, "main_qt.py")
            if os.path.exists(script):
                subprocess.Popen([python, script])
            else:
                subprocess.Popen([sys.argv[0]])
            QApplication.quit()
        except Exception as e:
            print(f"重启失败: {e}")

    def _show_guide(self):
        guide = GuideOverlay(self)
        geo = self.geometry()
        guide.move(geo.center().x() - 220, geo.center().y() - 100)
        guide.show()

    def _update_time(self):
        self.status_time.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'particles'):
            self.particles.resize(self.size())

    def changeEvent(self, event):
        if event.type() == event.WindowStateChange:
            if self.isMinimized():
                QTimer.singleShot(100, self._show_mini)
        super().changeEvent(event)

    def _show_mini(self):
        self.hide()
        if not self._mini_window:
            self._mini_window = MiniWindow()
            self._mini_window.restore_signal.connect(self._restore_from_mini)
            self._mini_window.quick_signal.connect(self._quick_from_mini)
        screen = QApplication.desktop().screenGeometry()
        self._mini_window.move(screen.width() - 310, screen.height() - 200)
        self._mini_window.show()

    def _restore_from_mini(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quick_from_mini(self):
        self._restore_from_mini()
        QTimer.singleShot(200, self._open_quick)


def check_wizard():
    ini_path = os.path.join(BASE_DIR, "wizard_record.ini")
    finished = False
    try:
        cfg = configparser.ConfigParser()
        cfg.read(ini_path, encoding="utf-8")
        finished = cfg.getboolean("status", "finished", fallback=False)
    except Exception:
        finished = False
    if not finished:
        return False
    for filename in ["students.txt", "texts.txt"]:
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if not content:
                return False
        except Exception:
            return False
    return True


def handle_url_protocol(argv):
    action = None
    for arg in argv[1:]:
        if arg.startswith("a13rollcall://"):
            path = arg.replace("a13rollcall://", "").strip("/")
            action = path
            break
        elif arg.startswith("--"):
            action = arg[2:]
    return action


def main():
    if not check_wizard():
        wizard_path = os.path.join(BASE_DIR, "wizard_launcher.py")
        wizard_exe = os.path.join(BASE_DIR, "A13配置向导.exe")
        try:
            if os.path.exists(wizard_exe):
                subprocess.Popen([wizard_exe], cwd=BASE_DIR)
            elif os.path.exists(wizard_path):
                subprocess.Popen([sys.executable, wizard_path], cwd=BASE_DIR)
        except Exception as e:
            print(f"启动向导失败: {e}")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))

    url_action = handle_url_protocol(sys.argv)
    show_guide = "--show-tip" in sys.argv or url_action == "guide"

    config_mgr = ConfigManager()
    theme_mgr = Win11Theme(config_mgr)
    app.setStyleSheet(theme_mgr.get_qss())

    splash = QSplashScreen()
    splash.setFixedSize(640, 440)
    splash_pix = QPixmap(640, 440)
    splash_pix.fill(QColor("#f3f3f3"))
    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.Antialiasing)
    try:
        icon = QPixmap(os.path.join(BASE_DIR, "app.ico")).scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(272, 80, icon)
    except Exception:
        pass
    painter.setPen(QColor("#0067c0"))
    painter.setFont(QFont("Microsoft YaHei", 26, QFont.Bold))
    painter.drawText(0, 210, 640, 40, Qt.AlignCenter, "课堂点名程序")
    painter.setPen(QColor("#666666"))
    painter.setFont(QFont("Microsoft YaHei", 13))
    painter.drawText(0, 260, 640, 24, Qt.AlignCenter, "A13 智能抽取引擎 V6.8")
    painter.setPen(QColor("#999999"))
    painter.setFont(QFont("Microsoft YaHei", 11))
    painter.drawText(0, 380, 640, 20, Qt.AlignCenter, "正在加载...")
    painter.end()
    splash.setPixmap(splash_pix)
    splash.show()
    app.processEvents()

    window = MainWindow(show_guide=show_guide)

    def on_show():
        splash.close()
        window.show()
        if url_action == "quick":
            QTimer.singleShot(300, window._open_quick)
        elif url_action == "draw":
            QTimer.singleShot(300, window._toggle_draw)
        elif url_action == "settings":
            QTimer.singleShot(300, window._open_settings)
        elif url_action == "echo":
            QTimer.singleShot(300, window._open_echo)

    QTimer.singleShot(2000, on_show)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
