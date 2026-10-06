# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 现代化UI组件库
包含统一的按钮、卡片、加载动画等组件，提供一致的视觉风格和微交互
"""

from PyQt5.QtWidgets import (
    QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QFrame, QSizePolicy
)
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize, pyqtSignal,
    QPointF
)
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen, QRadialGradient,
    QLinearGradient, QPainterPath, QCursor
)
import math


# ==================== 颜色主题 ====================
class ThemeColors:
    PRIMARY = "#0067c0"
    PRIMARY_HOVER = "#106ebe"
    PRIMARY_PRESSED = "#005a9e"
    PRIMARY_LIGHT = "#0078d4"

    SUCCESS = "#107c10"
    SUCCESS_HOVER = "#0e6c0e"
    SUCCESS_PRESSED = "#0b5a0b"

    WARNING = "#ca5010"
    WARNING_HOVER = "#b04810"
    WARNING_PRESSED = "#963d0e"

    DANGER = "#c42b1c"
    DANGER_HOVER = "#a52517"
    DANGER_PRESSED = "#8a1f13"

    GHOST_BG = "transparent"
    GHOST_BORDER = "#0067c0"
    GHOST_HOVER_BG = "#e5f1fb"

    WHITE = "#ffffff"
    TEXT_PRIMARY = "#1a1a1a"
    TEXT_SECONDARY = "#666666"
    TEXT_DISABLED = "#999999"
    BG_HOVER = "#f0f0f0"
    BG_PRESSED = "#e0e0e0"

    DARK_BG = "#2d2d2d"
    DARK_TEXT = "#ffffff"
    DARK_BORDER = "#404040"


# ==================== 现代化按钮 ====================
class ModernButton(QPushButton):
    """
    现代化按钮组件
    支持悬停缩放、阴影、渐变背景等微交互效果
    """

    STYLE_PRIMARY = "primary"
    STYLE_SUCCESS = "success"
    STYLE_WARNING = "warning"
    STYLE_DANGER = "danger"
    STYLE_GHOST = "ghost"
    STYLE_NEUTRAL = "neutral"

    def __init__(self, text="", style_type=STYLE_PRIMARY, parent=None):
        super().__init__(text, parent)
        self.style_type = style_type
        self._hover_animation = None
        self._press_animation = None
        self._shadow_effect = None
        self._original_height = None
        self._setup_style()
        self._setup_animations()

    def _setup_style(self):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMinimumHeight(36)
        self.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        self._update_style()

    def _setup_animations(self):
        self._shadow_effect = QGraphicsDropShadowEffect(self)
        self._shadow_effect.setBlurRadius(0)
        self._shadow_effect.setOffset(0, 0)
        self._shadow_effect.setColor(QColor(0, 0, 0, 0))
        self.setGraphicsEffect(self._shadow_effect)

    def _get_colors(self):
        styles = {
            self.STYLE_PRIMARY: (
                ThemeColors.PRIMARY, ThemeColors.PRIMARY_HOVER,
                ThemeColors.PRIMARY_PRESSED, ThemeColors.WHITE
            ),
            self.STYLE_SUCCESS: (
                ThemeColors.SUCCESS, ThemeColors.SUCCESS_HOVER,
                ThemeColors.SUCCESS_PRESSED, ThemeColors.WHITE
            ),
            self.STYLE_WARNING: (
                ThemeColors.WARNING, ThemeColors.WARNING_HOVER,
                ThemeColors.WARNING_PRESSED, ThemeColors.WHITE
            ),
            self.STYLE_DANGER: (
                ThemeColors.DANGER, ThemeColors.DANGER_HOVER,
                ThemeColors.DANGER_PRESSED, ThemeColors.WHITE
            ),
            self.STYLE_GHOST: (
                "transparent", ThemeColors.GHOST_HOVER_BG,
                ThemeColors.BG_PRESSED, ThemeColors.PRIMARY
            ),
            self.STYLE_NEUTRAL: (
                "#f5f5f5", ThemeColors.BG_HOVER,
                ThemeColors.BG_PRESSED, ThemeColors.TEXT_PRIMARY
            ),
        }
        return styles.get(self.style_type, styles[self.STYLE_PRIMARY])

    def _update_style(self):
        normal, hover, pressed, text_color = self._get_colors()
        border = f"border: 1px solid {ThemeColors.GHOST_BORDER};" if self.style_type == self.STYLE_GHOST else "border: none;"

        self.setStyleSheet(f"""
            QPushButton {{
                background: {normal};
                color: {text_color};
                {border}
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 600;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
            QPushButton:pressed {{
                background: {pressed};
            }}
            QPushButton:disabled {{
                background: #e0e0e0;
                color: #999999;
                border: none;
            }}
        """)

    def enterEvent(self, event):
        super().enterEvent(event)
        if self.isEnabled():
            self._start_hover_animation(True)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._start_hover_animation(False)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self.isEnabled():
            self._start_press_animation(True)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._start_press_animation(False)

    def _start_hover_animation(self, is_hover):
        try:
            if self._hover_animation and self._hover_animation.state() == QPropertyAnimation.Running:
                self._hover_animation.stop()

            self._hover_animation = QPropertyAnimation(self._shadow_effect, b"blurRadius")
            self._hover_animation.setDuration(200)
            self._hover_animation.setStartValue(self._shadow_effect.blurRadius())
            self._hover_animation.setEndValue(15 if is_hover else 0)
            self._hover_animation.setEasingCurve(QEasingCurve.OutCubic)
            self._hover_animation.start()

            offset_anim = QPropertyAnimation(self._shadow_effect, b"offset")
            offset_anim.setDuration(200)
            offset_anim.setStartValue(self._shadow_effect.offset())
            offset_anim.setEndValue(QPointF(0, 4 if is_hover else 0))
            offset_anim.setEasingCurve(QEasingCurve.OutCubic)
            offset_anim.start()

            color = QColor(0, 103, 192, 80 if is_hover else 0)
            self._shadow_effect.setColor(color)
        except Exception:
            pass

    def _start_press_animation(self, is_pressed):
        try:
            if self._press_animation and self._press_animation.state() == QPropertyAnimation.Running:
                self._press_animation.stop()

            self._press_animation = QPropertyAnimation(self, b"minimumHeight")
            self._press_animation.setDuration(100)
            current_height = self.height() if self.height() > 0 else 36
            self._press_animation.setStartValue(current_height)
            self._press_animation.setEndValue(34 if is_pressed else 36)
            self._press_animation.setEasingCurve(QEasingCurve.OutCubic)
            self._press_animation.start()
        except Exception:
            pass

    def set_style_type(self, style_type):
        self.style_type = style_type
        self._update_style()


# ==================== 大按钮（用于主操作） ====================
class LargeButton(ModernButton):
    """大按钮，用于主要操作，如开始抽取"""

    def __init__(self, text="", style_type=ModernButton.STYLE_PRIMARY, parent=None):
        super().__init__(text, style_type, parent)
        self.setMinimumHeight(52)
        self.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.setStyleSheet(self.styleSheet().replace("padding: 8px 20px;", "padding: 12px 32px;"))


# ==================== 图标按钮 ====================
class IconButton(QPushButton):
    """图标按钮，仅显示图标，用于工具栏等"""

    def __init__(self, icon_path="", tooltip="", parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self._setup_style()
        if tooltip:
            self.setToolTip(tooltip)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedSize(36, 36)

    def _setup_style(self):
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
            QPushButton:pressed {
                background: #e0e0e0;
            }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.icon_path and self.icon_path.endswith('.svg'):
            try:
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                from PyQt5.QtSvg import QSvgRenderer
                renderer = QSvgRenderer(self.icon_path)
                renderer.render(painter, self.rect().adjusted(8, 8, -8, -8))
                painter.end()
            except Exception:
                pass


# ==================== 现代化卡片 ====================
class ModernCard(QFrame):
    """现代化卡片组件，带圆角和阴影"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_style()
        self._setup_shadow()
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._layout.setSpacing(12)

    def _setup_style(self):
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        self.setFrameShape(QFrame.StyledPanel)

    def _setup_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

    def add_widget(self, widget):
        self._layout.addWidget(widget)

    def add_layout(self, layout):
        self._layout.addLayout(layout)

    def add_stretch(self):
        self._layout.addStretch()


# ==================== Windows风格加载动画 ====================
class WindowsLoader(QWidget):
    """
    Windows 11风格加载动画
    六个点依次亮起，形成流动效果
    """

    def __init__(self, parent=None, size=40, color="#0067c0"):
        super().__init__(parent)
        self.size = size
        self.color = color
        self._timer = None
        self._current_dot = 0
        self._dots = 6
        self.setFixedSize(size, size)
        self._start_animation()

    def _start_animation(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_animation)
        self._timer.start(80)

    def _update_animation(self):
        self._current_dot = (self._current_dot + 1) % self._dots
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = self.width() * 0.35
        dot_radius = self.width() * 0.08

        for i in range(self._dots):
            angle = (i / self._dots) * 2 * math.pi - math.pi / 2
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))

            offset = (i - self._current_dot) % self._dots
            if offset == 0:
                alpha = 255
                scale = 1.3
            elif offset == 1:
                alpha = 180
                scale = 1.1
            elif offset == 2:
                alpha = 120
                scale = 1.0
            else:
                alpha = 60
                scale = 0.9

            color = QColor(self.color)
            color.setAlpha(alpha)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            dot_size = int(max(1, dot_radius * scale))
            painter.drawEllipse(x - dot_size, y - dot_size, dot_size * 2, dot_size * 2)

        painter.end()

    def stop(self):
        if self._timer:
            self._timer.stop()

    def start(self):
        if self._timer:
            self._timer.start()


# ==================== 进度条加载动画 ====================
class ProgressLoader(QWidget):
    """
    进度条样式加载动画
    显示不确定进度的流动效果
    """

    def __init__(self, parent=None, width=200, height=6, color="#0067c0"):
        super().__init__(parent)
        self.color = color
        self._progress = 0
        self._timer = None
        self.setFixedSize(width, height)
        self._start_animation()

    def _start_animation(self):
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_progress)
        self._timer.start(30)

    def _update_progress(self):
        self._progress = (self._progress + 2) % 100
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        bg_color = QColor("#e0e0e0")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, w, h, 3, 3)

        bar_width = int(w * 0.3)
        x = int((self._progress / 100) * (w - bar_width))

        gradient = QLinearGradient(x, 0, x + bar_width, 0)
        gradient.setColorAt(0, QColor(self.color, 100))
        gradient.setColorAt(0.5, QColor(self.color, 255))
        gradient.setColorAt(1, QColor(self.color, 100))

        painter.setBrush(QBrush(gradient))
        painter.drawRoundedRect(x, 0, bar_width, h, 3, 3)

        painter.end()

    def stop(self):
        if self._timer:
            self._timer.stop()

    def start(self):
        if self._timer:
            self._timer.start()


# ==================== 加载遮罩 ====================
class LoadingOverlay(QWidget):
    """加载遮罩，覆盖在父窗口上显示加载动画"""

    def __init__(self, parent=None, text="加载中..."):
        super().__init__(parent)
        self.text = text
        self._setup_ui()
        self.hide()

    def _setup_ui(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        self.loader = WindowsLoader(size=60)
        layout.addWidget(self.loader, 0, Qt.AlignCenter)

        self.label = QLabel(self.text)
        self.label.setStyleSheet("""
            color: #0067c0;
            font-size: 14px;
            font-weight: 600;
            background: transparent;
        """)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

    def showEvent(self, event):
        super().showEvent(event)
        if self.parent():
            self.setGeometry(self.parent().rect())

    def set_text(self, text):
        self.text = text
        self.label.setText(text)

    def start(self):
        self.show()
        self.loader.start()

    def stop(self):
        self.loader.stop()
        self.hide()


# ==================== 状态标签 ====================
class StatusBadge(QLabel):
    """状态标签，用于显示各种状态"""

    TYPE_SUCCESS = "success"
    TYPE_WARNING = "warning"
    TYPE_ERROR = "error"
    TYPE_INFO = "info"
    TYPE_NEUTRAL = "neutral"

    def __init__(self, text="", badge_type=TYPE_INFO, parent=None):
        super().__init__(text, parent)
        self.badge_type = badge_type
        self._setup_style()

    def _setup_style(self):
        colors = {
            self.TYPE_SUCCESS: ("#107c10", "#e8f5e9"),
            self.TYPE_WARNING: ("#ca5010", "#fff3e0"),
            self.TYPE_ERROR: ("#c42b1c", "#ffebee"),
            self.TYPE_INFO: ("#0067c0", "#e3f2fd"),
            self.TYPE_NEUTRAL: ("#666666", "#f5f5f5"),
        }
        text_color, bg_color = colors.get(self.badge_type, colors[self.TYPE_INFO])

        self.setStyleSheet(f"""
            QLabel {{
                background: {bg_color};
                color: {text_color};
                border: 1px solid {text_color};
                border-radius: 10px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)

    def set_type(self, badge_type):
        self.badge_type = badge_type
        self._setup_style()


# ==================== 分割线 ====================
class Divider(QFrame):
    """分割线组件"""

    HORIZONTAL = 0
    VERTICAL = 1

    def __init__(self, orientation=HORIZONTAL, parent=None):
        super().__init__(parent)
        if orientation == self.HORIZONTAL:
            self.setFrameShape(QFrame.HLine)
            self.setFixedHeight(1)
        else:
            self.setFrameShape(QFrame.VLine)
            self.setFixedWidth(1)
        self.setStyleSheet("background: #e0e0e0; border: none;")
        self.setFrameShadow(QFrame.Plain)


# ==================== 工具函数 ====================
def create_primary_button(text, parent=None):
    """创建主按钮"""
    return ModernButton(text, ModernButton.STYLE_PRIMARY, parent)


def create_success_button(text, parent=None):
    """创建成功按钮"""
    return ModernButton(text, ModernButton.STYLE_SUCCESS, parent)


def create_warning_button(text, parent=None):
    """创建警告按钮"""
    return ModernButton(text, ModernButton.STYLE_WARNING, parent)


def create_danger_button(text, parent=None):
    """创建危险按钮"""
    return ModernButton(text, ModernButton.STYLE_DANGER, parent)


def create_ghost_button(text, parent=None):
    """创建幽灵按钮"""
    return ModernButton(text, ModernButton.STYLE_GHOST, parent)


def create_neutral_button(text, parent=None):
    """创建中性按钮"""
    return ModernButton(text, ModernButton.STYLE_NEUTRAL, parent)


def create_large_button(text, parent=None):
    """创建大按钮"""
    return LargeButton(text, ModernButton.STYLE_PRIMARY, parent)
