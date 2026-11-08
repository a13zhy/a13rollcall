import sys
import os
import random
import subprocess
import configparser
import math
import traceback
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

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, "icons")
sys.path.insert(0, BASE_DIR)

from config_manager import ConfigManager
from data_manager import DataManager
from draw_engine import DrawEngine
from echo_hole import EchoHole
from plugin_manager import PluginManager
import skin_engine as S
from settings_window import SettingsDialog

S.patch_stylesheet()

WEBSITE_URL = "https://dkfile.istester.com/zhysppa13/a13callname.html"


def sk_c(key, fallback="#0067c0", alpha=None):
    try:
        col = QColor(S.current()["c"][key])
    except Exception:
        col = QColor(fallback)
    if alpha is not None:
        col.setAlpha(alpha)
    return col


def sk_family():
    try:
        return S.current()["f"]["family"]
    except Exception:
        return "Microsoft YaHei"


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
            sk = S.resolve(self.config)
            S.set_current(sk["key"])
            self.is_dark = (sk["mode"] == "dark")
            scale = float(self.config.get("ui", "scale") or 1.0)
            density = self.config.get("ui", "density") or "normal"
            return S.apply_qss(QApplication.instance(), sk, scale, density)
        except Exception:
            self.is_dark = False
            return S.build_qss()

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
        center = int(self._size / 2)
        radius = int(self._size / 2 - 4)
        painter.setPen(QPen(QColor("#e5e5e5"), 3, Qt.SolidLine, Qt.RoundCap))
        painter.drawEllipse(center - radius, center - radius, radius * 2, radius * 2)
        for i in range(3):
            start_angle = (self._angle + i * 120) * 16
            span_angle = 60 * 16
            color = sk_c("primary")
            color.setAlpha(255 - i * 60)
            painter.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap))
            painter.drawArc(center - radius, center - radius, radius * 2, radius * 2, start_angle, span_angle)
        painter.end()


class ParticleWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(Qt.NoFocus)
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
            color = sk_c("primary", alpha=alpha)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(x, y, r, r)
        painter.end()


class DrawNameWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._name = "点击开始"
        self._is_drawing = False
        self._scale = 1.0
        self._target_scale = 1.0
        self._font_size = 96
        self._gradient_offset = 0
        self._particles = []
        self._easing_progress = 0
        self._is_finishing = False
        self._finish_start_time = 0
        self._animation_enabled = True
        self._animation_duration = 300
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._update_animation)
        self._anim_timer.start(16)

    def set_animation_enabled(self, enabled):
        self._animation_enabled = enabled
        if not enabled:
            self._is_drawing = False
            self._particles = []
            self._scale = 1.0
            self._target_scale = 1.0
        self.update()

    def set_animation_duration(self, ms):
        self._animation_duration = ms

    def _update_animation(self):
        if not self._animation_enabled:
            self.update()
            return
        if self._is_drawing:
            self._gradient_offset = (self._gradient_offset + 2) % 100
        scale_diff = self._target_scale - self._scale
        if abs(scale_diff) > 0.001:
            self._scale += scale_diff * 0.15
        else:
            self._scale = self._target_scale
        self._particles = [(x, y + vy, vx, vy, life - 1, size)
                           for x, y, vx, vy, life, size in self._particles
                           if life > 0]
        self.update()

    def _spawn_particles(self, count=5):
        import random
        for _ in range(count):
            x = random.randint(50, self.width() - 50)
            y = random.randint(50, self.height() - 50)
            vx = random.uniform(-1, 1)
            vy = random.uniform(-2, -0.5)
            life = random.randint(20, 40)
            size = random.randint(2, 5)
            self._particles.append((x, y, vx, vy, life, size))

    def set_name(self, name):
        self._name = name
        self.update()

    def set_font_size(self, size):
        self._font_size = size
        self.update()

    def set_drawing(self, drawing):
        self._is_drawing = drawing
        if drawing:
            self._target_scale = 1.08
            self._is_finishing = False
        else:
            self._target_scale = 1.0
            self._is_finishing = True
            self._spawn_particles(20)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        w = self.width()
        h = self.height()
        name = self._name
        font_size = self._font_size

        for px, py, pvx, pvy, plife, psize in self._particles:
            alpha = int(255 * (plife / 40))
            color = sk_c("primary", alpha=alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            px_int = int(px)
            py_int = int(py)
            psize_int = int(max(1, psize))
            painter.drawEllipse(px_int - psize_int, py_int - psize_int, psize_int * 2, psize_int * 2)

        font = QFont(sk_family(), int(font_size * self._scale), QFont.Bold)
        painter.setFont(font)
        text_width = painter.fontMetrics().horizontalAdvance(name)
        while text_width > w - 60 and font_size > 36:
            font_size -= 2
            font = QFont(sk_family(), int(font_size * self._scale), QFont.Bold)
            painter.setFont(font)
            text_width = painter.fontMetrics().horizontalAdvance(name)

        if self._is_drawing:
            gradient = QLinearGradient(0, 0, w, 0)
            offset = self._gradient_offset / 100.0
            gradient.setColorAt(max(0, offset - 0.3), sk_c("primary_d"))
            gradient.setColorAt(max(0, offset - 0.15), sk_c("primary"))
            gradient.setColorAt(offset, sk_c("primary_h"))
            gradient.setColorAt(min(1, offset + 0.15), sk_c("primary"))
            gradient.setColorAt(min(1, offset + 0.3), sk_c("primary_d"))
            painter.setPen(QPen(gradient, 1))
        else:
            if self._is_finishing and self._scale > 1.02:
                glow_color = sk_c("primary", alpha=80)
                painter.setPen(QPen(glow_color, 8))
                painter.drawText(QRectF(0, 0, w, h - 20), Qt.AlignCenter, name)
            painter.setPen(sk_c("primary"))

        painter.drawText(QRectF(0, 0, w, h - 20), Qt.AlignCenter, name)

        if self._is_drawing:
            painter.setPen(sk_c("primary"))
            painter.setFont(QFont(sk_family(), 13, QFont.Bold))
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


from stats_dialog import StatsDialog


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
        from operation_history import OperationHistoryManager, MarkOperation
        self.history_mgr = OperationHistoryManager(max_history=50)
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
        self._ui_scale = float(self.config_mgr.get("ui", "scale") or 1.0)
        self._min_scale = 0.7
        self._max_scale = 1.5
        self._scale_step = 0.1
        self._round_active = False
        self._round_id = None
        self._round_records = []
        self._round_start_time = None
        self._setup_window()
        self._setup_ui()
        self._load_data()
        self._apply_settings()
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start(30000)
        self._last_autosave_time = None
        QTimer.singleShot(500, self._startup_plugins)
        if show_guide:
            QTimer.singleShot(1500, self._show_guide)

    def _startup_plugins(self):
        try:
            if not hasattr(self, 'plugin_mgr') or not self.plugin_mgr:
                return
            self.plugin_mgr.load_all_plugins()
            plugins = self.plugin_mgr.get_enabled_plugins()
            loaded_count = 0
            error_plugins = []
            for plugin in plugins:
                name = plugin["meta"]["name"]
                try:
                    context = self.plugin_mgr.get_context(name, self)
                    self.plugin_mgr._call_lifecycle(name, "on_enable")
                    result, error = self.plugin_mgr.execute_plugin(name, self, "main")
                    if error:
                        print(f"插件 {name} 执行警告：{error}")
                        error_plugins.append((name, error))
                    else:
                        loaded_count += 1
                except Exception as e:
                    print(f"插件 {name} 启动警告：{e}")
                    import traceback
                    traceback.print_exc()
                    error_plugins.append((name, str(e)))
            print(f"插件自启动完成，共加载 {loaded_count}/{len(plugins)} 个插件")
            if error_plugins:
                error_msg = "\n".join([f"• {name}: {err[:100]}" for name, err in error_plugins])
                self._show_toast(f"⚠️ {len(error_plugins)} 个插件启动失败，详情请查看日志", 4000)
        except Exception as e:
            print(f"插件自启动失败：{e}")
            import traceback
            traceback.print_exc()

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
        import display_fit
        min_w, min_h = display_fit.minimum_size()
        self.setMinimumSize(min_w, min_h)
        w, h = display_fit.window_size()
        self.resize(w, h)
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.x() + (screen.width() - w) // 2, screen.y() + (screen.height() - h) // 2)
        try:
            self.setWindowIcon(QIcon(os.path.join(BASE_DIR, "app.ico")))
        except Exception:
            pass
        try:
            if self.config_mgr.get("ui", "window_topmost"):
                self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
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
        subtitle = QLabel("A13 智能抽取引擎 V6.8.2")
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

        import display_fit
        tokens = display_fit.layout_tokens()
        body = QHBoxLayout()
        body.setContentsMargins(tokens["page_pad"], tokens["page_pad"], tokens["page_pad"], tokens["page_pad"])
        body.setSpacing(tokens["gap"])

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(tokens["sidebar"])
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
        self.text_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_list.customContextMenuRequested.connect(self._show_text_context_menu)
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
        self.new_round_btn = QPushButton("新建轮次")
        self.new_round_btn.setObjectName("primary")
        self.new_round_btn.setMinimumHeight(60)
        self.new_round_btn.setStyleSheet("QPushButton#primary { background: #107c10; color: white; border: none; border-radius: 10px; font-size: 15px; font-weight: 700; } QPushButton#primary:hover { background: #0e6c0e; }")
        self.new_round_btn.clicked.connect(self._start_new_round)
        ctrl_layout.addWidget(self.new_round_btn, 1)
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
        right.setFixedWidth(tokens["right"])
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(12)
        stat_card = QFrame()
        stat_card.setObjectName("card")
        st = QVBoxLayout(stat_card)
        st.setContentsMargins(18, 16, 18, 16)
        st.setSpacing(8)
        st_header = QHBoxLayout()
        st_label = QLabel("本轮统计")
        st_label.setObjectName("subtitle")
        st_header.addWidget(st_label)
        st_header.addStretch()
        self.round_title_label = QLabel("未开始")
        self.round_title_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #c42b1c;")
        st_header.addWidget(self.round_title_label)
        st.addLayout(st_header)
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

        from weight_visualization import WeightVisualizationWidget
        weight_card = QFrame()
        weight_card.setObjectName("card")
        wc = QVBoxLayout(weight_card)
        wc.setContentsMargins(18, 16, 18, 16)
        wc.setSpacing(8)
        wc_header = QHBoxLayout()
        wc_label = QLabel("权重分布")
        wc_label.setObjectName("subtitle")
        wc_header.addWidget(wc_label)
        wc_header.addStretch()
        wc_detail_btn = QPushButton("详情")
        wc_detail_btn.setStyleSheet("background: transparent; color: #0067c0; border: none; font-size: 10px; font-weight: 600;")
        wc_detail_btn.setCursor(QCursor(Qt.PointingHandCursor))
        wc_detail_btn.clicked.connect(self._show_weight_detail)
        wc_header.addWidget(wc_detail_btn)
        wc.addLayout(wc_header)
        self.weight_viz = WeightVisualizationWidget()
        self.weight_viz.setMaximumHeight(180)
        wc.addWidget(self.weight_viz)
        r_layout.addWidget(weight_card)
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
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_mark)
        QShortcut(QKeySequence("Ctrl+Y"), self, self._redo_mark)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._redo_mark)
        QShortcut(QKeySequence("Tab"), self, self._skip)
        QShortcut(QKeySequence("N"), self, self._toggle_no_repeat)
        QShortcut(QKeySequence("W"), self, self._toggle_weight)
        QShortcut(QKeySequence(","), self, self._open_settings)
        QShortcut(QKeySequence("P"), self, self._toggle_particles)
        QShortcut(QKeySequence("L"), self, self._open_ranking)
        QShortcut(QKeySequence("M"), self, self._toggle_theme)
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_data)
        QShortcut(QKeySequence("?"), self, self._show_shortcut_help)
        QShortcut(QKeySequence("Left"), self, self._prev_text)
        QShortcut(QKeySequence("Right"), self, self._next_text)
        QShortcut(QKeySequence("Ctrl+="), self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl++"), self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self._reset_zoom)

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
        try:
            anim_draw = bool(self.config_mgr.get("animation", "draw_enabled"))
            if hasattr(self, 'draw_widget'):
                self.draw_widget.set_animation_enabled(anim_draw)
        except Exception:
            pass
        try:
            anim_duration = int(self.config_mgr.get("animation", "duration_ms"))
            if hasattr(self, 'draw_widget'):
                self.draw_widget.set_animation_duration(anim_duration)
        except Exception:
            pass
        try:
            topmost = bool(self.config_mgr.get("ui", "window_topmost"))
            on_top = bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
            if topmost != on_top and self.isVisible():
                self.setWindowFlag(Qt.WindowStaysOnTopHint, topmost)
                self.show()
                self.activateWindow()
                if hasattr(self, 'particles'):
                    self.particles.lower()
        except Exception:
            pass
        try:
            QTimer.singleShot(80, S.repaint_all_skins)
        except Exception:
            pass
        try:
            if hasattr(self, 'draw_widget'):
                self.draw_widget.update()
            if hasattr(self, 'particles'):
                self.particles.update()
            if hasattr(self, 'weight_viz'):
                self.weight_viz.refresh_skin()
                if self._students:
                    self.weight_viz.update_weights(self._students, self._calculate_all_weights())
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
        QTimer.singleShot(100, self._update_weight_visualization)
        try:
            self.draw_btn.setEnabled(False)
            self.draw_hint.setText("请点击绿色「新建轮次」按钮开始新一轮")
        except Exception:
            pass

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

    def _show_text_context_menu(self, pos):
        item = self.text_list.itemAt(pos)
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: white; border: 1px solid #ddd; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 8px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #e5f1fb; }
        """)
        if item:
            idx = self.text_list.row(item)
            action_open = menu.addAction("打开此课文")
            action_edit = menu.addAction("编辑课文内容")
            menu.addSeparator()
            action_up = menu.addAction("上移")
            action_down = menu.addAction("下移")
            menu.addSeparator()
            action_delete = menu.addAction("删除此课文")
            action = menu.exec_(self.text_list.mapToGlobal(pos))
            if action == action_open:
                self._show_text(idx)
            elif action == action_edit:
                self._edit_text(idx)
            elif action == action_up:
                self._move_text(idx, -1)
            elif action == action_down:
                self._move_text(idx, 1)
            elif action == action_delete:
                self._delete_text(idx)
        else:
            action_add = menu.addAction("添加新课文")
            action_import = menu.addAction("从文件导入")
            action = menu.exec_(self.text_list.mapToGlobal(pos))
            if action == action_add:
                self._add_new_text()
            elif action == action_import:
                self._import_texts()

    def _select_text_by_weight(self, item):
        idx = item.data(Qt.UserRole)
        if idx is not None:
            self.text_mode_specified.setChecked(True)
            self._show_text(idx)

    def _edit_text(self, idx):
        if idx < 0 or idx >= len(self._texts):
            return
        text = self._texts[idx]
        title = text.get("title", f"课文{idx+1}") if isinstance(text, dict) else str(text)
        content = text.get("content", "") if isinstance(text, dict) else ""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"编辑课文：{title}")
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)
        title_input = QLineEdit(title)
        layout.addWidget(QLabel("课文标题："))
        layout.addWidget(title_input)
        content_input = QTextEdit(content)
        layout.addWidget(QLabel("课文内容："))
        layout.addWidget(content_input)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("保存")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        ok_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        if dlg.exec_():
            new_title = title_input.text().strip()
            new_content = content_input.toPlainText().strip()
            if new_title and new_content:
                self._texts[idx] = {"title": new_title, "content": new_content}
                self._reload_text_list()
                self._show_toast("课文已更新", 1500)

    def _move_text(self, idx, direction):
        if idx < 0 or idx >= len(self._texts):
            return
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._texts):
            return
        self._texts[idx], self._texts[new_idx] = self._texts[new_idx], self._texts[idx]
        self._reload_text_list()
        self.text_list.setCurrentRow(new_idx)

    def _delete_text(self, idx):
        if idx < 0 or idx >= len(self._texts):
            return
        reply = QMessageBox.question(self, "确认删除", "确定要删除这篇课文吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self._texts[idx]
            self._reload_text_list()
            self._show_toast("课文已删除", 1500)

    def _add_new_text(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("添加新课文")
        dlg.setMinimumSize(500, 400)
        layout = QVBoxLayout(dlg)
        title_input = QLineEdit()
        title_input.setPlaceholderText("请输入课文标题")
        layout.addWidget(QLabel("课文标题："))
        layout.addWidget(title_input)
        content_input = QTextEdit()
        content_input.setPlaceholderText("请输入课文内容")
        layout.addWidget(QLabel("课文内容："))
        layout.addWidget(content_input)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("添加")
        ok_btn.setObjectName("primary")
        cancel_btn = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        ok_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        if dlg.exec_():
            title = title_input.text().strip()
            content = content_input.toPlainText().strip()
            if title and content:
                self._texts.append({"title": title, "content": content})
                self._reload_text_list()
                self._show_toast("课文已添加", 1500)

    def _import_texts(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入课文文件", "", "文本文件 (*.txt);;所有文件 (*.*)")
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if content.strip():
                    self._texts.append({"title": os.path.basename(file_path), "content": content})
                    self._reload_text_list()
                    self._show_toast("课文已导入", 1500)
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"导入课文失败：{str(e)}")

    def _reload_text_list(self):
        self.text_list.clear()
        for i, t in enumerate(self._texts):
            title = t.get("title", f"课文{i+1}") if isinstance(t, dict) else str(t)
            self.text_list.addItem(QListWidgetItem(f"{i+1}. {title}"))

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

    def _start_new_round(self):
        if self._round_active:
            reply = QMessageBox.question(self, "开始新轮次",
                f"当前第 {self._round_id} 轮已进行中（已抽取 {len(self._round_records)} 人）。\n"
                "开始新轮次将自动结束并保存当前轮次，确定继续吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply != QMessageBox.Yes:
                return
            self._finish_round_to_storage()
        if not self._students:
            self.draw_hint.setText("无学生名单，请先添加")
            return
        self._round_id = self.data_mgr.next_round_id()
        self._round_records = []
        self._round_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._round_active = True
        self.draw_engine.reset_round()
        self.draw_widget.set_name("点击开始")
        self.current_name.setText("—")
        self.current_status.setText("待标记")
        self.draw_hint.setText(f"第 {self._round_id} 轮已就绪，点击开始抽取")
        for key in ["drawn", "mastered", "familiar", "unlearned"]:
            self.stat_labels[key].setText("0")
        self.stat_labels["remain"].setText(str(len(self._students)))
        self.round_title_label.setText(f"第 {self._round_id} 轮")
        self.round_title_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #107c10;")
        self.draw_btn.setEnabled(True)
        self.draw_btn.setStyleSheet("")
        self._show_toast(f"已开始第 {self._round_id} 轮", 2000)

    def _finish_round_to_storage(self):
        if not self._round_active:
            return
        records = []
        for rec in self._round_records:
            records.append({
                "student": rec.get("student", ""),
                "text": rec.get("text", ""),
                "paragraph": rec.get("paragraph", ""),
                "status": rec.get("status", "未标记"),
                "time": rec.get("time", ""),
            })
        mastered = sum(1 for r in records if r["status"] == "已背过")
        familiar = sum(1 for r in records if r["status"] == "未背熟")
        unlearned = sum(1 for r in records if r["status"] == "未背过")
        round_data = {
            "round_id": self._round_id,
            "start_time": self._round_start_time,
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "records": records,
            "summary": {"total": len(records), "mastered": mastered,
                        "familiar": familiar, "unlearned": unlearned},
        }
        try:
            self.data_mgr.save_round(round_data)
        except Exception as e:
            print(f"保存轮次失败: {e}")
        self._round_active = False
        self._round_id = None
        self._round_records = []

    def _start_draw(self):
        if not self._round_active:
            self.draw_hint.setText("请先点击「新建轮次」开始一轮点名")
            QMessageBox.information(self, "尚未开始轮次",
                "请先点击左上角绿色「新建轮次」按钮，开始一轮点名后再抽取学生。")
            return
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
        if self._round_active:
            self._round_records.append({
                "student": name,
                "text": self.text_title.text() if self.text_title.text() != "—" else "",
                "paragraph": "",
                "status": "未标记",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
        QTimer.singleShot(100, self._update_weight_visualization)
        self._speak_result(name)
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
        student_name = self._current_student
        self._last_marked_status = status
        self._last_marked_student = student_name
        if self._last_draw_result:
            self._last_draw_result["status"] = status
        if self._round_active:
            for rec in reversed(self._round_records):
                if rec.get("student") == student_name and rec.get("status") == "未标记":
                    rec["status"] = status
                    break
        try:
            self.data_mgr.set_student_status(student_name, status)
            self.data_mgr.update_status_stats(student_name, status)
        except Exception:
            pass
        self.current_status.setText(status)
        colors = {"已背过": "#107c10", "未背熟": "#ca5010", "未背过": "#c42b1c"}
        self.current_status.setStyleSheet(f"color: {colors.get(status, '#666666')}; font-size: 12px; font-weight: 700;")
        key = {"已背过": "mastered", "未背熟": "familiar", "未背过": "unlearned"}.get(status)
        if key:
            cur = int(self.stat_labels[key].text()) + 1
            self.stat_labels[key].setText(str(cur))
        self._show_mark_toast(student_name, status)

        def undo_mark():
            try:
                self.data_mgr.revert_status_stats(student_name, status)
            except Exception:
                pass
            k = {"已背过": "mastered", "未背熟": "familiar", "未背过": "unlearned"}.get(status)
            if k:
                c = max(0, int(self.stat_labels[k].text()) - 1)
                self.stat_labels[k].setText(str(c))
            if self._current_student == student_name:
                self.current_status.setText("待标记")
                self.current_status.setStyleSheet("color: #666666; font-size: 12px;")
            self._show_undo_toast(student_name, status)

        def redo_mark():
            try:
                self.data_mgr.set_student_status(student_name, status)
                self.data_mgr.update_status_stats(student_name, status)
            except Exception:
                pass
            k = {"已背过": "mastered", "未背熟": "familiar", "未背过": "unlearned"}.get(status)
            if k:
                c = int(self.stat_labels[k].text()) + 1
                self.stat_labels[k].setText(str(c))
            if self._current_student == student_name:
                self.current_status.setText(status)
                self.current_status.setStyleSheet(f"color: {colors.get(status, '#666666')}; font-size: 12px; font-weight: 700;")
            self._show_mark_toast(student_name, status)

        from operation_history import MarkOperation
        operation = MarkOperation(student_name, status, undo_mark, redo_mark)
        self.history_mgr.add_operation(operation)

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
        if not hasattr(self, 'history_mgr') or not self.history_mgr.can_undo():
            self._show_toast("没有可撤销的操作", 1500)
            return
        operation = self.history_mgr.undo()
        if operation:
            self._last_marked_student = None
            self._last_marked_status = None
            self._show_toast(f"已撤销：{operation.description}", 2000)

    def _redo_mark(self):
        if not hasattr(self, 'history_mgr') or not self.history_mgr.can_redo():
            self._show_toast("没有可重做的操作", 1500)
            return
        operation = self.history_mgr.redo()
        if operation:
            self._show_toast(f"已重做：{operation.description}", 2000)

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

    def _toggle_weight(self):
        try:
            current = self.config_mgr.get("draw", "weighted", False)
            new_value = not current
            self.config_mgr.set(new_value, "draw", "weighted")
            self.config_mgr.save_config()
            if hasattr(self, 'weight_btn'):
                self.weight_btn.setText(f"权重:{'开' if new_value else '关'}")
            self._show_toast(f"动态权重已{'开启' if new_value else '关闭'}", 1500)
            self._update_weight_visualization()
        except Exception as e:
            print(f"切换权重模式失败: {e}")
            self._show_toast("动态权重切换失败", 1500)

    def _show_weight_detail(self):
        try:
            from weight_visualization import WeightDistributionDialog
            weights = self._calculate_all_weights()
            dlg = WeightDistributionDialog(self._students, weights, self)
            dlg.exec_()
        except Exception as e:
            print(f"显示权重详情失败: {e}")

    def _calculate_all_weights(self):
        weights = {}
        try:
            for student in self._students:
                try:
                    weight = self.draw_engine._calculate_weight(student)
                    weights[student] = weight
                except Exception:
                    weights[student] = 1.0
        except Exception:
            pass
        return weights

    def _update_weight_visualization(self):
        try:
            if hasattr(self, 'weight_viz') and self._students:
                weights = self._calculate_all_weights()
                self.weight_viz.update_weights(self._students, weights)
        except Exception as e:
            print(f"更新权重可视化失败: {e}")

    def _reset_round(self):
        if self._round_active:
            n = len(self._round_records)
            reply = QMessageBox.question(self, "结束本轮",
                f"结束并保存第 {self._round_id} 轮（共抽取 {n} 人）？\n\n"
                "保存后可在「数据统计」中查看与恢复本轮记录。",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply != QMessageBox.Yes:
                return
            saved_id = self._round_id
            self._finish_round_to_storage()
            self._show_toast(f"第 {saved_id} 轮已保存，共 {n} 条记录", 3000)
        self.draw_engine.reset_round()
        self._current_student = None
        self.draw_widget.set_name("点击新建轮次")
        self.current_name.setText("—")
        self.current_status.setText("待开始")
        self.draw_hint.setText("请点击绿色「新建轮次」按钮开始新一轮")
        for key in ["drawn", "mastered", "familiar", "unlearned"]:
            self.stat_labels[key].setText("0")
        self.stat_labels["remain"].setText(str(len(self._students)))
        self.round_title_label.setText("未开始")
        self.round_title_label.setStyleSheet("font-size: 12px; font-weight: 700; color: #c42b1c;")
        self.draw_btn.setEnabled(False)

    def _open_settings(self):
        dlg = SettingsDialog(self.config_mgr, self.theme_mgr, self.echo_hole, self.plugin_mgr, self)
        if dlg.exec_():
            self._apply_settings()
            self._load_data()
            class_name = self._get_class_name()
            self.setWindowTitle(f"{class_name}班点名程序")
            try:
                if self._round_active:
                    self.round_label.setText(self._round_display_name())
            except Exception:
                pass

    def _open_stats(self):
        dlg = StatsDialog(self.data_mgr, self)
        dlg.exec_()

    def closeEvent(self, event):
        try:
            if self._round_active and self._round_records:
                self._finish_round_to_storage()
        except Exception:
            pass
        super().closeEvent(event)

    def _get_tts_engine(self):
        try:
            if getattr(self, "_tts", None) is None:
                import pyttsx3
                self._tts = pyttsx3.init()
            return self._tts
        except Exception:
            self._tts = None
            return None

    def _speak_result(self, name):
        try:
            if not self.config_mgr.get("tts", "enabled"):
                return
        except Exception:
            return
        try:
            engine = self._get_tts_engine()
            if engine is None:
                return
            rate = self.config_mgr.get("tts", "rate") or 150
            engine.setProperty("rate", int(rate))
            text_title = ""
            try:
                if self.config_mgr.get("tts", "speak_text") and self.text_title.text() not in ("—", ""):
                    text_title = f"，背诵 {self.text_title.text()}"
            except Exception:
                pass
            engine.say(f"{name}同学{text_title}")
            engine.runAndWait()
        except Exception:
            pass

    def _open_ranking(self):
        dlg = RankingDialog(self.data_mgr, self)
        dlg.exec_()


    def _show_restart_required(self, message="部分设置需要重启后生效"):
        self.restart_btn.show()
        self.restart_btn.setToolTip(message)
        self._show_toast(message, 3000)

    def _restart_app(self):
        reply = QMessageBox.question(self, "重启确认",
            "确定要立即重启程序吗？\n\n未保存的数据可能会丢失。",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            import sys
            QApplication.quit()
            import subprocess
            subprocess.Popen([sys.executable] + sys.argv)

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
            self.config_mgr.save_config()
            self._last_autosave_time = datetime.now().strftime("%H:%M:%S")
        except Exception:
            pass

    def _autosave(self):
        try:
            self.data_mgr.save_stats()
            self.config_mgr.save_config()
            self._last_autosave_time = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            print(f"自动保存失败: {e}")

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

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    def _zoom_in(self):
        new_scale = min(self._max_scale, self._ui_scale + self._scale_step)
        if new_scale != self._ui_scale:
            self._ui_scale = new_scale
            self._apply_zoom()
            self._show_toast(f"界面缩放: {int(self._ui_scale * 100)}%", 1000)

    def _zoom_out(self):
        new_scale = max(self._min_scale, self._ui_scale - self._scale_step)
        if new_scale != self._ui_scale:
            self._ui_scale = new_scale
            self._apply_zoom()
            self._show_toast(f"界面缩放: {int(self._ui_scale * 100)}%", 1000)

    def _reset_zoom(self):
        if self._ui_scale != 1.0:
            self._ui_scale = 1.0
            self._apply_zoom()
            self._show_toast("界面缩放已重置为 100%", 1000)

    def _apply_zoom(self):
        try:
            self.config_mgr.set(self._ui_scale, "ui", "scale")
            app = QApplication.instance()
            if app:
                self.theme_mgr.get_qss()
            if hasattr(self, "weight_viz"):
                self.weight_viz.refresh_skin()
                if self._students:
                    self.weight_viz.update_weights(self._students, self._calculate_all_weights())
            self.update()
        except Exception as e:
            print(f"应用缩放失败: {e}")

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
        cfg.read(ini_path, encoding="utf-8-sig")
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


# ==================== 全局异常处理 ====================
_crash_report_dir = os.path.join(BASE_DIR, "crash_reports")
_last_crash_file = os.path.join(BASE_DIR, "last_crash.json")


def _ensure_crash_dir():
    try:
        os.makedirs(_crash_report_dir, exist_ok=True)
    except Exception:
        pass


def _generate_crash_report(exc_type, exc_value, exc_tb):
    _ensure_crash_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(_crash_report_dir, f"crash_{timestamp}.txt")

    try:
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    except Exception:
        tb_str = str(exc_value)

    report_content = f"""A13课堂点名系统 - 崩溃报告
========================================
崩溃时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
程序版本: 6.8.0
Python版本: {sys.version}
操作系统: {sys.platform}
工作目录: {BASE_DIR}

异常类型: {exc_type.__name__}
异常信息: {str(exc_value)}

完整堆栈跟踪:
{tb_str}

系统信息:
- 可执行文件: {sys.executable}
- 命令行参数: {sys.argv}
- 已加载模块数: {len(sys.modules)}

========================================
此报告自动生成，可用于技术支持排查问题
"""

    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
    except Exception:
        pass

    try:
        import json
        crash_info = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": exc_type.__name__,
            "message": str(exc_value),
            "report_file": report_file,
        }
        with open(_last_crash_file, "w", encoding="utf-8") as f:
            json.dump(crash_info, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return report_file


def _global_exception_hook(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return

    report_file = _generate_crash_report(exc_type, exc_value, exc_tb)

    print(f"\n{'='*60}")
    print(f"程序发生未捕获异常！")
    print(f"异常类型: {exc_type.__name__}")
    print(f"异常信息: {str(exc_value)}")
    print(f"崩溃报告已保存: {report_file}")
    print(f"{'='*60}\n")
    traceback.print_exception(exc_type, exc_value, exc_tb)

    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            try:
                from error_dialog import ModernErrorDialog
                details = traceback.format_exception(exc_type, exc_value, exc_tb)
                details_str = "".join(details)
                error_msg = (
                    f"程序发生未捕获异常，即将退出。\n\n"
                    f"异常类型: {exc_type.__name__}\n"
                    f"异常信息: {str(exc_value)[:200]}\n\n"
                    f"崩溃报告已保存到:\n{report_file}\n\n"
                    f"建议:\n"
                    f"1. 查看崩溃报告了解详细信息\n"
                    f"2. 重启程序，系统将尝试恢复上次状态\n"
                    f"3. 如问题持续存在，请联系技术支持"
                )
                dialog = ModernErrorDialog(
                    title="程序异常",
                    message=error_msg,
                    details=details_str,
                    error_type="error",
                    parent=None
                )
                dialog.exec_()
            except Exception as dialog_error:
                print(f"显示错误对话框失败: {dialog_error}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(None, "程序异常", f"程序发生异常：{str(exc_value)}")
    except Exception:
        pass


def _check_last_crash():
    try:
        if not os.path.exists(_last_crash_file):
            return None
        import json
        with open(_last_crash_file, "r", encoding="utf-8") as f:
            crash_info = json.load(f)
        return crash_info
    except Exception:
        return None


def _show_crash_recovery_dialog(crash_info):
    try:
        from PyQt5.QtWidgets import QMessageBox, QCheckBox
        from PyQt5.QtCore import Qt

        msg_box = QMessageBox()
        msg_box.setWindowTitle("检测到上次异常退出")
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(
            f"检测到程序上次运行时发生异常退出。\n\n"
            f"异常时间: {crash_info.get('time', '未知')}\n"
            f"异常类型: {crash_info.get('type', '未知')}\n"
            f"异常信息: {crash_info.get('message', '未知')[:100]}\n\n"
            f"是否需要查看崩溃报告？"
        )
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        result = msg_box.exec_()
        if result == QMessageBox.Yes:
            report_file = crash_info.get('report_file', '')
            if report_file and os.path.exists(report_file):
                try:
                    import cross_platform
                    cross_platform.open_file(report_file)
                except Exception:
                    pass

        try:
            os.remove(_last_crash_file)
        except Exception:
            pass

        return True
    except Exception:
        return False


def main():
    sys.excepthook = _global_exception_hook

    import display_fit
    display_fit.enable_high_dpi()

    crash_info = _check_last_crash()

    if not check_wizard():
        import cross_platform
        wizard_proc = cross_platform.launch_wizard(BASE_DIR)
        if wizard_proc is None:
            try:
                from PyQt5.QtWidgets import QMessageBox as _QMB, QApplication as _QApp
                _qa = _QApp(sys.argv)
                _QMB.warning(None, "配置向导未找到",
                    "未找到配置向导程序（向导启动器）。\n\n"
                    "请确认它和本程序放在同一个文件夹中，或手动编辑名单和课文文件后重新启动。")
            except Exception:
                pass
        sys.exit(0)

    app = QApplication(sys.argv)

    url_action = handle_url_protocol(sys.argv)
    show_guide = "--show-tip" in sys.argv or url_action == "guide"

    config_mgr = ConfigManager()
    try:
        display_fit.apply(app, config_mgr)
    except Exception:
        app.setFont(QFont("Microsoft YaHei", 10))
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
    painter.drawText(0, 260, 640, 24, Qt.AlignCenter, "A13 智能抽取引擎 V6.8.2")
    painter.setPen(QColor("#999999"))
    painter.setFont(QFont("Microsoft YaHei", 11))
    painter.drawText(0, 380, 640, 20, Qt.AlignCenter, "正在加载...")
    painter.end()
    splash.setPixmap(splash_pix)
    splash.show()
    app.processEvents()

    window = MainWindow(show_guide=show_guide)

    if crash_info:
        QTimer.singleShot(500, lambda: _show_crash_recovery_dialog(crash_info))

    app.setQuitOnLastWindowClosed(False)
    window.show()
    splash.finish(window)
    app.setQuitOnLastWindowClosed(True)

    if url_action == "quick":
        QTimer.singleShot(300, window._open_quick)
    elif url_action == "draw":
        QTimer.singleShot(300, window._toggle_draw)
    elif url_action == "settings":
        QTimer.singleShot(300, window._open_settings)
    elif url_action == "echo":
        QTimer.singleShot(300, window._open_echo)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()









