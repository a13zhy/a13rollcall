import difflib
import json
import os
import re
import subprocess
import sys
import threading
import urllib.request

from PyQt5.QtCore import QEasingCurve, QSize, Qt, QTimer, QVariantAnimation, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QIcon, QKeySequence, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAbstractButton, QApplication, QCheckBox, QComboBox, QDialog, QFileDialog,
    QFontComboBox, QFrame, QGridLayout, QHBoxLayout, QKeySequenceEdit, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPlainTextEdit,
    QPushButton, QScrollArea, QSizePolicy, QSlider, QSpinBox, QDoubleSpinBox,
    QStackedWidget, QTabWidget, QTextBrowser, QVBoxLayout, QWidget,
)

import skin_engine as S

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "A13课堂点名系统"
VERSION = "6.8.2"
GITHUB_API = "https://api.github.com/repos/a13zhy/a13rollcall/releases/latest"
WEBSITE = "https://dkfile.istester.com/zhysppa13/a13callname.html"

NAV_WIDTH = 246


def _cfg_ensure(config_mgr):
    defaults = [
        ("ui", "skin", S.DEFAULT_SKIN),
        ("ui", "scale", 1.0),
        ("ui", "density", "normal"),
        ("ui", "settings_w", 1180),
        ("ui", "settings_h", 780),
        ("ui", "mark_toast", True),
        ("ui", "rounded_window", True),
        ("ui", "window_radius", 12),
        ("ui", "window_shadow", True),
        ("ui", "window_topmost", False),
        ("ui", "mini_on_minimize", False),
        ("ui", "echo_enabled", True),
        ("ui", "echo_confirm", True),
        ("ui", "echo_max", 120),
        ("animation", "draw_enabled", True),
        ("animation", "result_enabled", True),
        ("animation", "transition_enabled", True),
        ("animation", "duration_ms", 300),
        ("animation", "easing", "ease_out"),
        ("text", "auto_next", True),
        ("startup", "show_quick", True),
        ("startup", "remember_choice", True),
        ("startup", "countdown_sec", 3),
        ("startup", "force_wizard", True),
        ("ui", "particle_count", 30),
        ("ui", "particle_speed", 2),
        ("ui", "auto_save_interval", 300),
    ]
    for sec, key, val in defaults:
        if config_mgr.get(sec, key) is None:
            config_mgr.set(val, sec, key)


class ToggleSwitch(QAbstractButton):
    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self._pos = 1.0 if checked else 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.valueChanged.connect(self._on_anim)
        self.toggled.connect(self._start_anim)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(26)
        self.setFixedWidth(48)

    def _on_anim(self, v):
        self._pos = float(v)
        self.update()

    def _start_anim(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def paintEvent(self, e):
        sk = S.current()
        c = sk["c"]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = self.height()
        w = self.width()
        bar = QRectFix(0, 0, w, h)
        track_off = QColor(c["card3"])
        track_on = QColor(c["primary"])
        mix = QColor(
            int(track_off.red() + (track_on.red() - track_off.red()) * self._pos),
            int(track_off.green() + (track_on.green() - track_off.green()) * self._pos),
            int(track_off.blue() + (track_on.blue() - track_off.blue()) * self._pos),
        )
        p.setPen(QPen(QColor(c["border2"] if self._pos < 0.5 else c["primary"]), 1))
        p.setBrush(mix)
        p.drawRoundedRect(bar, h / 2, h / 2)
        knob = 4 + int((w - h) * self._pos)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffffff") if self._pos > 0.4 else QColor(c["text2"]))
        p.drawEllipse(QRectFix(knob, 3, h - 6, h - 6))
        p.end()

    def sizeHint(self):
        return QSize(48, 26)


def QRectFix(x, y, w, h):
    from PyQt5.QtCore import QRect
    return QRect(int(x), int(y), int(w), int(h))


class Segmented(QFrame):
    changed = pyqtSignal(str)

    def __init__(self, options, value=None, parent=None):
        super().__init__(parent)
        self.setObjectName("seg")
        self._options = options
        self._value = value if value is not None else options[0][0]
        self._buttons = []
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        for val, label in options:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda c=False, v=val: self.set_value(v, True))
            lay.addWidget(b)
            self._buttons.append((val, b))
        self._refresh()

    def set_value(self, val, emit=False):
        self._value = val
        self._refresh()
        if emit:
            self.changed.emit(val)

    def value(self):
        return self._value

    def _refresh(self):
        for val, b in self._buttons:
            b.setChecked(val == self._value)
        self.refresh_skin()

    def refresh_skin(self):
        sk = S.current()
        c = sk["c"]
        g = sk["g"]
        for val, b in self._buttons:
            active = val == self._value
            b.setStyleSheet(
                "QPushButton { border: 1px solid %s; border-radius: %dpx; padding: 5px 12px; "
                "font-size: 12px; background: %s; color: %s; }"
                % (
                    c["primary"] if active else c["border2"],
                    max(0, g["btn"] - 1),
                    c["primary"] if active else c["ghost"],
                    c["primary_text"] if active else c["text2"],
                )
            )


class SkinCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, skin, selected=False, parent=None):
        super().__init__(parent)
        self.skin = skin
        self.selected = selected
        self.setFixedSize(268, 192)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.skin["key"])

    def paintEvent(self, e):
        sk = self.skin
        c = sk["c"]
        g = sk["g"]
        f = sk["f"]
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        p.setBrush(QColor(c["bg"]))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(rect, 10, 10)
        card = QRectFix(10, 10, self.width() - 20, 100)
        p.setBrush(QColor(c["card"]))
        p.setPen(QPen(QColor(c["primary"] if self.selected else c["border"]), 2 if self.selected else 1))
        p.drawRoundedRect(card, max(0, min(14, g["card"])), max(0, min(14, g["card"])))
        p.setPen(QPen(QColor(c["text"])))
        font = QFont(f["family"], 11)
        font.setBold(True)
        p.setFont(font)
        p.drawText(QRectFix(22, 20, 160, 22), Qt.AlignLeft | Qt.AlignVCenter, sk["name"])
        p.setPen(QPen(QColor(c["text3"])))
        font2 = QFont(f["family"], 8)
        p.setFont(font2)
        p.drawText(QRectFix(22, 42, self.width() - 44, 18), Qt.AlignLeft | Qt.AlignVCenter, sk["tag"])
        btn = QRectFix(22, 68, 78, 26)
        p.setBrush(QColor(c["primary"]))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(btn, max(0, min(10, g["btn"])), max(0, min(10, g["btn"])))
        p.setPen(QPen(QColor(c["primary_text"])))
        p.setFont(QFont(f["family"], 8))
        p.drawText(btn, Qt.AlignCenter, "主按钮")
        chip = QRectFix(108, 68, 58, 26)
        p.setBrush(QColor(c["chip"]))
        p.setPen(QPen(QColor(c["border2"]), 1))
        p.drawRoundedRect(chip, 4, 4)
        p.setPen(QPen(QColor(c["sel_text"])))
        p.drawText(chip, Qt.AlignCenter, "标签")
        dots = [c["bg"], c["card"], c["primary"], c["accent"], c["text"], c["border2"]]
        x = 12
        y = 124
        for i, col in enumerate(dots):
            p.setBrush(QColor(col))
            p.setPen(QPen(QColor(c["border2"]), 1))
            p.drawRoundedRect(QRectFix(x + i * 25, y, 20, 20), 4, 4)
        p.setPen(QPen(QColor(c["text2"])))
        p.setFont(QFont(f["family"], 8))
        info = "圆角 %d · 描边 %d · 字号 %d · %s" % (
            g["card"], g["border"], f["size"], "深色" if sk["mode"] == "dark" else "浅色"
        )
        p.drawText(QRectFix(12, 152, self.width() - 24, 18), Qt.AlignLeft | Qt.AlignVCenter, info)
        if self.selected:
            p.setBrush(QColor(c["primary"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectFix(self.width() - 36, 18, 20, 20))
            p.setPen(QPen(QColor(c["primary_text"]), 2))
            p.setFont(QFont(f["family"], 10))
            p.drawText(QRectFix(self.width() - 36, 18, 20, 20), Qt.AlignCenter, "✓")
        p.end()


def row_frame():
    card = QFrame()
    card.setObjectName("settingcard")
    lay = QHBoxLayout(card)
    sk = S.current()
    g = sk["g"]
    pad = max(8, int(g["pad"] * 0.8))
    lay.setContentsMargins(pad, max(8, g["row"] - 4), pad, max(8, g["row"] - 4))
    lay.setSpacing(14)
    return card, lay


def add_row(layout, label, desc, widget, badge=None):
    card, lay = row_frame()
    left = QVBoxLayout()
    left.setSpacing(3)
    top = QHBoxLayout()
    top.setSpacing(8)
    lb = QLabel(label)
    lb.setObjectName("setting_label")
    lb.setWordWrap(False)
    lb.setMinimumWidth(150)
    top.addWidget(lb)
    if badge:
        b = QLabel(badge)
        b.setObjectName("badge")
        top.addWidget(b)
    top.addStretch()
    left.addLayout(top)
    if desc:
        d = QLabel(desc)
        d.setObjectName("setting_desc")
        d.setWordWrap(True)
        left.addWidget(d)
    lay.addLayout(left, 1)
    if widget is not None:
        widget.setMaximumWidth(340)
        widget.setMinimumWidth(120)
        lay.addWidget(widget, 0, Qt.AlignVCenter)
    layout.addWidget(card)
    S.card_shadow(card)
    return card


def section_label(text, sub=""):
    box = QWidget()
    lay = QVBoxLayout(box)
    lay.setContentsMargins(2, 8, 2, 0)
    lay.setSpacing(2)
    t = QLabel(text)
    t.setObjectName("section_title")
    lay.addWidget(t)
    if sub:
        s = QLabel(sub)
        s.setObjectName("muted")
        lay.addWidget(s)
    return box


class NavButton(QPushButton):
    def __init__(self, text, icon_name, parent=None):
        super().__init__(text, parent)
        self.setObjectName("navbtn")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("icon_name", icon_name)
        self.setIcon(S.svg_icon(icon_name, 17, S.current()["c"]["text"]))
        self.setIconSize(QSize(17, 17))
        self.setMinimumHeight(36)
        sk = S.current()
        self.setStyleSheet(
            "QPushButton { text-align: left; padding: 7px 12px; border: none; border-left: 3px solid transparent; border-radius: %dpx; background: transparent; color: %s; }"
            "QPushButton:hover { background: %s; border-left: 3px solid %s; }"
            "QPushButton:checked { background: %s; color: %s; font-weight: 700; border-left: 3px solid %s; }"
            % (sk["g"]["item"], sk["c"]["text"], sk["c"]["nav_hover"], sk["c"]["primary"],
               sk["c"]["nav_active"], sk["c"]["sel_text"], sk["c"]["primary"])
        )

    def refresh_skin(self):
        sk = S.current()
        self.setIcon(S.svg_icon(self.property("icon_name") or "settings", 17, sk["c"]["text"]))
        self.setStyleSheet(
            "QPushButton { text-align: left; padding: 7px 12px; border: none; border-left: 3px solid transparent; border-radius: %dpx; background: transparent; color: %s; }"
            "QPushButton:hover { background: %s; border-left: 3px solid %s; }"
            "QPushButton:checked { background: %s; color: %s; font-weight: 700; border-left: 3px solid %s; }"
            % (sk["g"]["item"], sk["c"]["text"], sk["c"]["nav_hover"], sk["c"]["primary"],
               sk["c"]["nav_active"], sk["c"]["sel_text"], sk["c"]["primary"])
        )


class SettingsDialog(QDialog):
    def __init__(self, config_mgr, theme_mgr=None, echo_hole=None, plugin_mgr=None, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.theme_mgr = theme_mgr
        self.echo_hole = echo_hole
        self.plugin_mgr = plugin_mgr
        self._cfg = config_mgr
        _cfg_ensure(config_mgr)
        self._bindings = []
        self._pages = {}
        self._nav_index = {}
        self._plugin_page_defs = []
        self._current_key = None
        self._restart_keys_changed = []
        self._dirty = False
        self._build_skin = S.resolve(config_mgr)
        self.setWindowTitle("设置")
        w = int(config_mgr.get("ui", "settings_w") or 1180)
        h = int(config_mgr.get("ui", "settings_h") or 780)
        self.setMinimumSize(960, 620)
        self.resize(w, h)
        self.setObjectName("settingsroot")
        self._build_ui()
        self._build_nav()
        self._build_pages()
        self._show_page("skin")
        try:
            self.config_mgr.backup_current()
        except Exception:
            pass

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        header = QFrame()
        header.setObjectName("topbar")
        header.setFixedHeight(66)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(22, 10, 18, 10)
        hl.setSpacing(10)
        logo = QLabel()
        logo.setPixmap(S.svg_icon("settings", 24).pixmap(24, 24))
        hl.addWidget(logo)
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        t = QLabel("设置")
        t.setObjectName("h1")
        title_box.addWidget(t)
        self.header_sub = QLabel("皮肤 · %s" % S.current()["name"])
        self.header_sub.setObjectName("muted")
        title_box.addWidget(self.header_sub)
        hl.addLayout(title_box)
        hl.addSpacing(18)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索设置项，支持同义词、首字母，例如：tk、字体、重启")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(300)
        self.search_input.setMaximumWidth(430)
        self.search_input.textChanged.connect(self._filter_nav)
        self.search_input.returnPressed.connect(self._jump_first_match)
        hl.addWidget(self.search_input, 1)
        self.skin_chip = QPushButton("皮肤：" + S.current()["name"])
        self.skin_chip.setObjectName("chip")
        self.skin_chip.setCursor(Qt.PointingHandCursor)
        self.skin_chip.clicked.connect(lambda: self._show_page("skin"))
        hl.addWidget(self.skin_chip)
        restart_btn = QPushButton("重启")
        restart_btn.setObjectName("chip")
        restart_btn.setCursor(Qt.PointingHandCursor)
        restart_btn.setToolTip("关闭并重新启动程序")
        restart_btn.clicked.connect(self._restart_now)
        hl.addWidget(restart_btn)
        root.addWidget(header)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(NAV_WIDTH)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(10, 10, 10, 10)
        sl.setSpacing(0)
        self.nav_scroll = QScrollArea()
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setFrameShape(QFrame.NoFrame)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_host = QWidget()
        self.nav_host.setObjectName("navhost")
        self.nav_layout = QVBoxLayout(self.nav_host)
        self.nav_layout.setContentsMargins(0, 0, 4, 12)
        self.nav_layout.setSpacing(4)
        self.nav_layout.addStretch()
        self.nav_scroll.setWidget(self.nav_host)
        sl.addWidget(self.nav_scroll, 1)
        foot = QLabel("v%s · 本地离线运行" % VERSION)
        foot.setObjectName("muted")
        foot.setAlignment(Qt.AlignCenter)
        foot.setMinimumHeight(26)
        sl.addWidget(foot)
        body.addWidget(side)
        content = QFrame()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        self.stack = QStackedWidget()
        cl.addWidget(self.stack, 1)
        bottom = QFrame()
        bottom.setObjectName("statusbar")
        bottom.setFixedHeight(68)
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(22, 12, 18, 12)
        bl.setSpacing(10)
        self.status_label = QLabel("所有修改即时预览，点击保存写入配置文件")
        self.status_label.setObjectName("muted")
        bl.addWidget(self.status_label)
        bl.addStretch()
        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.setObjectName("ghost")
        self.reset_btn.setFixedHeight(38)
        self.reset_btn.clicked.connect(self._reset_defaults)
        bl.addWidget(self.reset_btn)
        cancel = QPushButton("取消")
        cancel.setFixedHeight(38)
        cancel.setMinimumWidth(76)
        cancel.clicked.connect(self._cancel)
        bl.addWidget(cancel)
        save = QPushButton("保存")
        save.setObjectName("primary")
        save.setMinimumWidth(110)
        save.setFixedHeight(38)
        save.clicked.connect(self._save)
        bl.addWidget(save)
        cl.addWidget(bottom)
        body.addWidget(content, 1)
        root.addLayout(body, 1)

    def _nav_groups(self):
        return [
            ("系统", [
                ("class", "班级与身份", "user"),
                ("startup", "启动与引导", "restart"),
                ("info", "应用信息", "info"),
            ]),
            ("外观", [
                ("skin", "皮肤中心", "skin"),
                ("display", "显示与布局", "monitor"),
                ("font", "字体", "font"),
                ("animation", "动画与动效", "animation"),
                ("window", "窗口样式", "window"),
            ]),
            ("抽取", [
                ("mode", "抽取模式", "mode"),
                ("rules", "抽取规则", "rules"),
                ("params", "抽取参数", "sliders"),
                ("auto_draw", "自动抽取", "auto"),
                ("weight", "权重系统", "weight"),
                ("tts", "语音朗读", "speaker"),
            ]),
            ("课文", [
                ("text_extract", "课文抽取", "extract"),
                ("text_display", "课文显示", "display"),
                ("text_progress", "课文进度", "progress"),
            ]),
            ("标记", [
                ("mark", "背诵标记", "mark"),
                ("score", "积分体系", "score"),
            ]),
            ("快捷键", [
                ("shortcuts", "快捷键一览", "keyboard"),
                ("shortcut_settings", "自定义按键", "sliders"),
            ]),
            ("数据", [
                ("data_mgmt", "数据与文件", "database"),
                ("export", "统计导出", "export"),
                ("backup", "备份恢复", "backup"),
                ("echo", "回声洞", "echo"),
            ]),
            ("插件", [
                ("plugins", "插件中心", "plugin"),
                ("developer", "开发者支持", "developer"),
            ]),
            ("关于", [
                ("about", "关于本软件", "about"),
                ("update", "检查更新", "update"),
                ("help", "帮助与上手", "help"),
            ]),
        ]

    def _build_nav(self):
        self.nav_buttons = []
        groups = self._nav_groups()
        for gname, items in groups:
            gl = QLabel(gname)
            gl.setObjectName("navgroup")
            gl.setContentsMargins(12, 20, 6, 6)
            self.nav_layout.insertWidget(self.nav_layout.count() - 1, gl)
            for key, title, icon in items:
                btn = NavButton(title, icon)
                btn.setProperty("icon_name", icon)
                btn.setProperty("alias", self._page_alias(key))
                btn.clicked.connect(lambda c=False, k=key: self._show_page(k))
                self.nav_layout.insertWidget(self.nav_layout.count() - 1, btn)
                self.nav_buttons.append((key, title, btn))
                self._nav_index[key] = btn
        self._plugin_nav_start = self.nav_layout.count()

    def _page_alias(self, key):
        return {
            "class": "班级 班名 身份 名称 banji bj",
            "startup": "启动 引导 开机 向导 qidong qd",
            "info": "应用 信息 版本 路径 xinxi xx",
            "skin": "皮肤 主题 外观 配色 风格 pifu skin zhuti pf zt",
            "display": "显示 布局 状态栏 粒子 滚动 xianshi xs bj",
            "font": "字体 字号 字重 ziti zt zihao",
            "animation": "动画 动效 过渡 缓动 donghua dh",
            "window": "窗口 圆角 阴影 置顶 透明 chuangkou ck",
            "mode": "抽取 模式 点名 自动 chouqu cq moshi",
            "rules": "规则 去重 防作弊 轮次 guize gz",
            "params": "参数 时长 滚动 倒计时 canshu cs",
            "auto_draw": "自动 连续 定时 zidong zd",
            "weight": "权重 概率 动态 未背熟 quanzhong qz",
            "tts": "语音 朗读 发音 音量 yuyin yy tts",
            "text_extract": "课文 抽取 段落 随机 kewen kw",
            "text_display": "课文 显示 标题 对齐 xianshi",
            "text_progress": "课文 进度 重置 jindu jd",
            "mark": "标记 背过 熟练 提示 biaoji bj",
            "score": "积分 排行 分数 jifen jf",
            "shortcuts": "快捷键 热键 列表 kuaijie kjj",
            "shortcut_settings": "快捷键 自定义 按键 修改 zidingyi",
            "data_mgmt": "数据 文件 路径 名单 重置 shuju sj",
            "export": "导出 统计 报表 daochu dc",
            "backup": "备份 恢复 快照 beifen bf",
            "echo": "回声 树洞 留言 匿名 huisheng hs",
            "plugins": "插件 扩展 安装 示例 chajian cj plugin",
            "developer": "开发 调试 日志 协议 崩溃 kaifa kf",
            "about": "关于 信息 作者 版本 guanyu gy",
            "update": "更新 检查 GitHub 版本 gengxin gx",
            "help": "帮助 上手 教程 快捷键 bangzhu bz",
        }.get(key, key)

    def _page_pages_def(self):
        return PAGE_DEFS(self)

    def _build_pages(self):
        for key, group, title, icon, builder in PAGE_DEFS(self):
            page = self._make_page(builder, key)
            self._pages[key] = page
            self.stack.addWidget(page)
        self._build_plugin_pages()

    def _make_page(self, builder, key=None):
        self._building_key = key
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        host.setObjectName("pagehost")
        lay = QVBoxLayout(host)
        lay.setContentsMargins(26, 16, 26, 26)
        lay.setSpacing(6)
        try:
            builder(host, lay)
        except Exception as ex:
            err = QLabel("页面构建失败：%s" % ex)
            err.setObjectName("setting_desc")
            err.setWordWrap(True)
            lay.addWidget(err)
            import traceback
            traceback.print_exc()
        lay.addStretch()
        scroll.setWidget(host)
        return scroll

    def _show_page(self, key):
        if key not in self._pages:
            return
        self.stack.setCurrentWidget(self._pages[key])
        btn = self._nav_index.get(key)
        for k, t, b in self.nav_buttons:
            b.setChecked(b is btn)
        self._current_key = key
        title = dict((k, t) for k, t, b in self.nav_buttons).get(key, "")
        self.header_sub.setText("皮肤 · %s    |    %s" % (S.current()["name"], title))
        if btn:
            half = max(40, int(self.nav_scroll.viewport().height() / 2))
            self.nav_scroll.ensureWidgetVisible(btn, 0, half)

    def _filter_nav(self, text):
        text = (text or "").strip().lower()
        if not text:
            for k, t, b in self.nav_buttons:
                b.setVisible(True)
            return
        for k, t, b in self.nav_buttons:
            hay = (t + " " + b.property("alias") + " " + k).lower()
            hit = text in hay
            if not hit:
                for word in re.split(r"\s+", text):
                    if not word:
                        continue
                    if word in hay:
                        hit = True
                        break
                    ratio = difflib.SequenceMatcher(None, word, t.lower()).ratio()
                    if ratio >= 0.62:
                        hit = True
                        break
            b.setVisible(hit)

    def _jump_first_match(self):
        for k, t, b in self.nav_buttons:
            if b.isVisible():
                self._show_page(k)
                return

    def reg(self, path, reader, restart=False, live=False, label=""):
        self._bindings.append({
            "path": path,
            "reader": reader,
            "restart": restart,
            "live": live,
            "label": label,
            "page": getattr(self, "_building_key", None),
        })
        return reader

    def _collect(self):
        changed = []
        for b in self._bindings:
            try:
                val = b["reader"]()
            except Exception:
                continue
            old = self._cfg.get(*b["path"])
            if old != val:
                self._cfg.set(val, *b["path"])
                changed.append((b["path"], b["restart"], b["live"], b["label"]))
        return changed

    def _save(self):
        changed = self._collect()
        try:
            self._cfg.save_config()
        except Exception:
            pass
        restart_items = [c for c in changed if c[1]]
        self._apply_live(changed)
        if restart_items:
            self._ask_restart(restart_items)
            return
        n = len(changed)
        if n:
            self.status_label.setText("已保存 %d 项修改，主界面已同步" % n)
        else:
            self.status_label.setText("没有需要保存的新修改")
        self._notify_parent()
        try:
            self._cfg.backup_current()
        except Exception:
            pass
        QTimer.singleShot(450, self.accept)

    def _apply_live(self, changed):
        need_skin = any(c[0] == ("ui", "skin") or c[0] == ("ui", "scale") or c[0] == ("ui", "density") for c in changed)
        if need_skin:
            self._reload_skin()
        try:
            if self.parent() and hasattr(self.parent(), "_apply_settings"):
                self.parent()._apply_settings()
        except Exception:
            pass

    def _notify_parent(self):
        try:
            if self.parent() and hasattr(self.parent(), "_apply_settings"):
                self.parent()._apply_settings()
        except Exception:
            pass

    def _ask_restart(self, items):
        dlg = QDialog(self)
        dlg.setWindowTitle("需要重启")
        dlg.setMinimumWidth(520)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        head = QLabel("部分设置需要重启程序后生效")
        head.setObjectName("h1")
        lay.addWidget(head)
        names = [c[3] or "%s.%s" % c[0] for c in items] or ["窗口/主题相关设置"]
        body = QLabel("以下修改已保存，重新启动后生效：\n\n" + "\n".join(["· " + n for n in names]))
        body.setObjectName("setting_desc")
        body.setWordWrap(True)
        lay.addWidget(body)
        row = QHBoxLayout()
        row.addStretch()
        later = QPushButton("稍后手动重启")
        later.clicked.connect(lambda: (dlg.accept(), self.accept()))
        row.addWidget(later)
        now = QPushButton("立即重启")
        now.setObjectName("primary")
        now.clicked.connect(lambda: (dlg.accept(), self._restart_now()))
        row.addWidget(now)
        lay.addLayout(row)
        dlg.exec_()

    def _restart_now(self):
        try:
            self._notify_parent()
            self._cfg.save_config()
        except Exception:
            pass
        app = QApplication.instance()
        try:
            from PyQt5.QtWidgets import QApplication as QA
            QA.exit(0)
        except Exception:
            pass
        try:
            python = sys.executable
            main_py = os.path.join(BASE_DIR, "main_qt.py")
            if getattr(sys, "frozen", False):
                subprocess.Popen([sys.executable])
            else:
                subprocess.Popen([python, main_py], cwd=BASE_DIR)
        except Exception:
            pass

    def _cancel(self):
        try:
            if self.config_mgr.old_config is not None:
                self.config_mgr.config = self.config_mgr.old_config
            self._reload_skin()
        except Exception:
            pass
        self.reject()

    def _reset_defaults(self):
        r = QMessageBox.question(
            self, "恢复默认",
            "将当前页面的设置项恢复为出厂默认值？\n\n（只影响本页，保存后才写入配置文件）",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if r != QMessageBox.Yes:
            return
        import config_manager as CM
        defaults = getattr(CM, "DEFAULT_CONFIG", {})
        page_keys = [b["path"] for b in self._bindings if b.get("page") == self._current_key]
        if not page_keys:
            page_keys = [b["path"] for b in self._bindings]
        for path in page_keys:
            node = defaults
            ok = True
            for p in path:
                if isinstance(node, dict) and p in node:
                    node = node[p]
                else:
                    ok = False
                    break
            if ok and not isinstance(node, dict):
                try:
                    self._cfg.set(node, *path)
                except Exception:
                    continue
        self._reload_page(self._current_key)
        self.status_label.setText("已恢复本页默认值，点击保存后写入配置文件")

    def _reload_page(self, key):
        widget = self._pages.get(key)
        if not widget:
            return
        idx = self.stack.indexOf(widget)
        builder = dict((k, b) for k, g, t, i, b in PAGE_DEFS(self)).get(key)
        if builder is None:
            return
        self._bindings = [b for b in self._bindings if b.get("page") != key]
        old = self.stack.widget(idx)
        new_page = self._make_page(builder, key)
        self.stack.insertWidget(idx, new_page)
        self.stack.removeWidget(old)
        old.deleteLater()
        self._pages[key] = new_page
        self.stack.setCurrentWidget(new_page)
        self.status_label.setText("已重新加载本页，修改需点击保存")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        try:
            self._cfg.set(self.width(), "ui", "settings_w")
            self._cfg.set(self.height(), "ui", "settings_h")
        except Exception:
            pass

    def refresh_skin(self):
        for k, t, b in self.nav_buttons:
            b.refresh_skin()
        self.skin_chip.setText("皮肤：" + S.current()["name"])
        self.header_sub.setText("皮肤 · %s" % S.current()["name"])

    def _reload_skin(self):
        sk = S.resolve(self._cfg)
        S.set_current(sk["key"])
        try:
            scale = float(self._cfg.get("ui", "scale") or 1.0)
        except Exception:
            scale = 1.0
        density = self._cfg.get("ui", "density") or "normal"
        app = QApplication.instance()
        if app:
            S.apply_qss(app, sk, scale, density)
        for k, t, b in self.nav_buttons:
            b.refresh_skin()
        for w in self.findChildren(SkinCard):
            w.update()
        for w in self.findChildren(ToggleSwitch):
            w.update()
        for w in self.findChildren(Segmented):
            w.refresh_skin()
        self.refresh_skin()
        self.update()
        QTimer.singleShot(80, self._repaint_after_skin)

    def _repaint_after_skin(self):
        try:
            S.repaint_all_skins()
        except Exception:
            pass
        self.update()

    def _build_plugin_pages(self):
        if not self.plugin_mgr:
            return
        try:
            plugins = self.plugin_mgr.get_enabled_plugins()
        except Exception:
            plugins = []
        for plugin in plugins:
            name = plugin.get("meta", {}).get("name")
            if not name:
                continue
            try:
                pages = self.plugin_mgr.get_plugin_pages(name) or []
            except Exception:
                pages = []
            for info in pages:
                pkey = info.get("key", "settings")
                ptitle = info.get("title", pkey)
                icon = info.get("icon", "plugin")
                full = "plugin_%s_%s" % (name, pkey)
                page = self._make_plugin_page(name, pkey)
                self._pages[full] = page
                self.stack.addWidget(page)
                btn = NavButton(ptitle, icon)
                btn.setProperty("icon_name", icon)
                btn.setProperty("alias", (name + " " + ptitle).lower())
                btn.clicked.connect(lambda c=False, k=full: self._show_page(k))
                self.nav_layout.insertWidget(self.nav_layout.count() - 1, btn)
                self.nav_buttons.append((full, ptitle, btn))
                self._nav_index[full] = btn
                self._plugin_page_defs.append((full, name, pkey, ptitle))

    def _make_plugin_page(self, plugin_name, page_key):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        try:
            app_ref = self.parent() or self
            page = self.plugin_mgr.build_plugin_page(plugin_name, page_key, app_ref, self)
        except Exception as ex:
            page = None
            print("插件页面构建失败：%s" % ex)
        if page is None:
            host = QWidget()
            lay = QVBoxLayout(host)
            lay.setContentsMargins(26, 20, 26, 20)
            lb = QLabel("插件「%s」的页面「%s」构建失败，请查看插件日志。" % (plugin_name, page_key))
            lb.setWordWrap(True)
            lay.addWidget(lb)
            lay.addStretch()
            scroll.setWidget(host)
        else:
            scroll.setWidget(page)
        return scroll


def _line(value, width=300):
    w = QLineEdit(str(value if value is not None else ""))
    w.setMinimumWidth(width)
    return w


def _spin(value, lo, hi, step=1, suffix="", integer=True):
    w = QSpinBox() if integer else QDoubleSpinBox()
    w.setRange(lo, hi)
    w.setSingleStep(step)
    if suffix:
        w.setSuffix(" " + suffix)
    try:
        w.setValue(value if value is not None else lo)
    except Exception:
        w.setValue(lo)
    w.setMinimumWidth(150)
    return w


def _combo(pairs, value):
    w = QComboBox()
    for val, label in pairs:
        w.addItem(label, val)
    idx = w.findData(value)
    w.setCurrentIndex(idx if idx >= 0 else 0)
    w.setMinimumWidth(180)
    return w


def _toggle(value):
    return ToggleSwitch(bool(value))


def _slider(value, lo, hi, step=1, suffix="", integer=True):
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    s = QSlider(Qt.Horizontal)
    s.setRange(lo, hi)
    s.setSingleStep(step)
    s.setMinimumWidth(150)
    val_label = QLabel()
    val_label.setObjectName("mono")
    val_label.setMinimumWidth(58)

    def fmt(v):
        if integer:
            return "%d%s" % (v, (" " + suffix) if suffix else "")
        return "%.2f%s" % (v / 100.0, (" " + suffix) if suffix else "")

    if integer:
        s.setValue(int(value if value is not None else lo))
    else:
        s.setValue(int(float(value if value is not None else lo) * 100))
    val_label.setText(fmt(s.value()))
    s.valueChanged.connect(lambda v: val_label.setText(fmt(v)))
    lay.addWidget(s)
    lay.addWidget(val_label)
    box.value = lambda: (s.value() if integer else round(s.value() / 100.0, 2))
    box.setMinimumWidth(240)
    return box


def _path_row(dlg, path_value, kind="file"):
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    line = QLineEdit(str(path_value or ""))
    line.setMinimumWidth(190)
    btn = QPushButton("浏览")
    btn.setObjectName("chip")

    def browse():
        if kind == "dir":
            p = QFileDialog.getExistingDirectory(dlg, "选择文件夹", line.text() or BASE_DIR)
        else:
            p, _ = QFileDialog.getOpenFileName(dlg, "选择文件", line.text() or BASE_DIR, "数据文件 (*.txt *.json);;所有文件 (*.*)")
        if p:
            line.setText(os.path.relpath(p, BASE_DIR) if p.startswith(BASE_DIR) else p)

    btn.clicked.connect(browse)
    lay.addWidget(line, 1)
    lay.addWidget(btn)
    box.value = line.text
    box.setMinimumWidth(300)
    return box


def _button_row(buttons):
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    for text, fn, style in buttons:
        b = QPushButton(text)
        if style:
            b.setObjectName(style)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda c=False, f=fn: f())
        lay.addWidget(b)
    box.setMinimumWidth(300)
    return box


def _info_block(text, markdown=False):
    box = QFrame()
    box.setObjectName("settingcard")
    lay = QVBoxLayout(box)
    lay.setContentsMargins(14, 12, 14, 12)
    if markdown:
        tb = QTextBrowser()
        tb.setOpenExternalLinks(True)
        tb.setFrameShape(QFrame.NoFrame)
        tb.setMarkdown(text)
        tb.setMinimumHeight(160)
        lay.addWidget(tb)
    else:
        lb = QLabel(text)
        lb.setObjectName("setting_desc")
        lb.setWordWrap(True)
        lay.addWidget(lb)
    return box


def _page_class(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("身份", "用于主界面标题、记录与导出文件"))
    name = _line(cfg.get("app", "class_name") or "A13")
    dlg.reg(("app", "class_name"), lambda: name.text().strip() or "A13", label="班级名称")
    add_row(lay, "班级名称", "显示在主界面标题与统计数据里，例如「A13班」「初二(3)班」", name)
    appn = _line(cfg.get("app", "app_name") or "课堂点名程序")
    dlg.reg(("app", "app_name"), lambda: appn.text().strip() or "课堂点名程序", label="程序名称")
    add_row(lay, "程序名称", "窗口标题中显示的程序名，可改成自己习惯的叫法", appn)
    eng = _line(cfg.get("app", "engine_name") or "A13")
    dlg.reg(("app", "engine_name"), lambda: eng.text().strip() or "A13", label="引擎名称")
    add_row(lay, "抽签引擎名称", "主界面副标题显示的引擎代号，纯展示", eng)
    lay.addWidget(section_label("当前数据快照"))
    try:
        students = len([x for x in open(os.path.join(BASE_DIR, cfg.get("files", "students") or "students.txt"), encoding="utf-8") if x.strip()])
    except Exception:
        students = 0
    try:
        texts = len([x for x in open(os.path.join(BASE_DIR, cfg.get("files", "texts") or "texts.txt"), encoding="utf-8") if x.strip()])
    except Exception:
        texts = 0
    lay.addWidget(_info_block("学生 %d 人 · 课文条目 %d 条 · 配置文件 config.json\n程序目录：%s" % (students, texts, BASE_DIR)))


def _page_startup(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("启动行为"))
    q = _toggle(cfg.get("startup", "show_quick") if cfg.get("startup", "show_quick") is not None else True)
    dlg.reg(("startup", "show_quick"), q.isChecked, label="启动显示快捷面板")
    add_row(lay, "启动时显示快捷抽取面板", "开启后启动直接进入小窗模式，适合上课随用随点", q)
    r = _toggle(cfg.get("startup", "remember_choice") if cfg.get("startup", "remember_choice") is not None else True)
    dlg.reg(("startup", "remember_choice"), r.isChecked, label="记住上次选择")
    add_row(lay, "记住上次选择的模式", "下次启动沿用上次的抽取模式与课文选择", r)
    c = _spin(int(cfg.get("startup", "countdown_sec") or 3), 0, 10, 1, "秒")
    dlg.reg(("startup", "countdown_sec"), c.value, label="启动倒计时")
    add_row(lay, "启动倒计时", "0 表示不等待直接进入；大于 0 时启动页倒计时后自动关闭", c)
    w = _toggle(cfg.get("startup", "force_wizard") if cfg.get("startup", "force_wizard") is not None else True)
    dlg.reg(("startup", "force_wizard"), w.isChecked, label="首次启动强制向导")
    add_row(lay, "未配置时强制进入向导", "名单或课文为空时，启动先进入配置向导，避免空班级直接抽取", w)
    lay.addWidget(section_label("开场动画"))
    sa = _toggle(cfg.get("ui", "start_animation") if cfg.get("ui", "start_animation") is not None else True)
    dlg.reg(("ui", "start_animation"), sa.isChecked, label="开场动画")
    add_row(lay, "启动开场动画", "关闭可让程序打开更快，低配电脑建议关闭", sa)
    sd = _spin(int(cfg.get("ui", "start_anim_duration") or 2500), 600, 6000, 100, "毫秒")
    dlg.reg(("ui", "start_anim_duration"), sd.value, label="开场动画时长")
    add_row(lay, "开场动画时长", "600~6000 毫秒，越长越有仪式感", sd)
    lay.addWidget(section_label("向导"))
    add_row(
        lay, "重新运行配置向导",
        "把向导标记改为未完成，下次启动重新进入配置向导（不会清空现有数据）",
        _button_row([("标记为未完成", lambda: _rerun_wizard(dlg), "primary")]),
    )


def _rerun_wizard(dlg):
    try:
        import configparser
        cfg = configparser.ConfigParser()
        cfg["status"] = {"finished": "False"}
        with open(os.path.join(BASE_DIR, "wizard_record.ini"), "w", encoding="utf-8") as f:
            cfg.write(f)
        QMessageBox.information(dlg, "已设置", "下次启动将重新进入配置向导。")
    except Exception as ex:
        QMessageBox.warning(dlg, "设置失败", str(ex))


def _page_info(dlg, host, lay):
    lay.addWidget(section_label("应用信息"))
    ver = "6.8.2"
    rows = [
        ("版本", "V%s" % ver),
        ("运行时", "Python %d.%d · PyQt5" % (sys.version_info[0], sys.version_info[1])),
        ("程序目录", BASE_DIR),
        ("配置文件", os.path.join(BASE_DIR, "config.json")),
        ("数据库文件", "students.txt / texts.txt / records.txt / stats.txt"),
        ("运行模式", "完全本地离线，无网络请求（除手动检查更新）"),
    ]
    for k, v in rows:
        val = QLabel(v)
        val.setObjectName("mono")
        val.setWordWrap(True)
        add_row(lay, k, "", val)
    lay.addWidget(section_label("快捷入口"))
    add_row(lay, "程序目录", "打开软件所在文件夹，便于备份名单与配置", _button_row([
        ("打开程序目录", lambda: _open_dir(BASE_DIR), ""),
        ("打开配置", lambda: _open_file(os.path.join(BASE_DIR, "config.json")), ""),
    ]))


def _open_dir(path):
    try:
        os.startfile(path)
    except Exception:
        try:
            subprocess.Popen(["explorer", path])
        except Exception:
            pass


def _open_file(path):
    try:
        os.startfile(path)
    except Exception:
        pass


def _page_skin(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("皮肤", "一套皮肤会同时改变配色、圆角、描边、字体、阴影、背景纹理、控件形态与动效速度，不只是换颜色"))
    grid_host = QWidget()
    grid = QGridLayout(grid_host)
    grid.setContentsMargins(0, 4, 0, 4)
    grid.setSpacing(12)
    cur = S.resolve(cfg)["key"]
    cards = []

    def select(key):
        cfg.set(key, "ui", "skin")
        cfg.set("dark" if S.SKIN_INDEX[key]["mode"] == "dark" else "light", "ui", "theme")
        S.set_current(key)
        dlg.selected_skin_key = key
        for c in cards:
            c.selected = (c.skin["key"] == key)
            c.update()
        dlg.status_label.setText("已切换到「%s」皮肤，可继续微调下方参数" % S.SKIN_INDEX[key]["name"])
        dlg.skin_chip.setText("皮肤：" + S.SKIN_INDEX[key]["name"])
        QTimer.singleShot(0, dlg._reload_skin)

    cols = 3
    for i, sk in enumerate(S.all_skins()):
        card = SkinCard(sk, sk["key"] == cur)
        card.clicked.connect(select)
        cards.append(card)
        grid.addWidget(card, i // cols, i % cols)
    dlg.skin_cards = cards
    lay.addWidget(grid_host)
    lay.addWidget(section_label("个性化微调", "在当前皮肤基础上叠加缩放与密度，不改动预设本身"))
    scale = _slider(cfg.get("ui", "scale") or 1.0, 80, 140, 1, "%", integer=True)
    dlg.reg(("ui", "scale"), lambda: round(scale.value() / 100.0, 2), live=True, label="界面缩放")
    add_row(lay, "界面缩放", "整体字号与控件尺寸按比例缩放，教室投影建议 110%~125%", scale, "需保存")
    dens = Segmented([("compact", "紧凑"), ("normal", "标准"), ("loose", "宽松")], cfg.get("ui", "density") or "normal")
    dlg.reg(("ui", "density"), dens.value, live=True, label="界面密度")
    add_row(lay, "界面密度", "紧凑减少留白适合大名单，宽松适合大屏展示", dens)
    lay.addWidget(section_label("皮肤覆盖范围"))
    lay.addWidget(_info_block(
        "皮肤同时作用于：主窗口顶栏与侧栏、抽取结果区、所有按钮与输入框、滚动条、统计窗口、设置窗口本身、"
        "以及插件页面中使用标准 objectName 的控件。第三方插件若写死了颜色，仍会保留自己的样式。"
    ))


def _page_display(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("状态栏与信息"))
    sb = _toggle(cfg.get("ui", "show_status_bar") if cfg.get("ui", "show_status_bar") is not None else True)
    dlg.reg(("ui", "show_status_bar"), sb.isChecked, label="状态栏")
    add_row(lay, "显示底部状态栏", "展示人数、课文数、当前轮次等概要信息", sb)
    lay.addWidget(section_label("背景与粒子"))
    pe = _toggle(cfg.get("ui", "particle_enabled") if cfg.get("ui", "particle_enabled") is not None else True)
    dlg.reg(("ui", "particle_enabled"), pe.isChecked, label="背景粒子")
    add_row(lay, "背景粒子动画", "关闭可明显降低 CPU 占用，低配电脑建议关闭", pe)
    pc = _spin(int(cfg.get("ui", "particle_count") or 30), 0, 120, 5, "个")
    dlg.reg(("ui", "particle_count"), pc.value, label="粒子数量")
    add_row(lay, "粒子数量", "0 表示不绘制粒子；30~60 比较自然", pc)
    ps = _spin(int(cfg.get("ui", "particle_speed") or 2), 1, 6, 1, "档")
    dlg.reg(("ui", "particle_speed"), ps.value, label="粒子速度")
    add_row(lay, "粒子速度", "1 最慢 6 最快", ps)
    lay.addWidget(section_label("滚动与布局"))
    sc = _slider(float(cfg.get("ui", "scroll_speed") or 1.0), 30, 300, 5, "x", integer=True)
    dlg.reg(("ui", "scroll_speed"), lambda: round(sc.value() / 100.0, 2), label="滚动速度")
    add_row(lay, "名单与课文滚动速度", "抽取时名单滚动的基础速度，1.0 为标准", sc)
    add_row(lay, "配置项一致性修复", "历史版本中 show_status_bar 与 status_bar 两个键可能不一致，保存时会自动同步为同一值",
            _button_row([("立即同步", lambda: _sync_status_keys(dlg), "")]))


def _sync_status_keys(dlg):
    val = bool(dlg.config_mgr.get("ui", "show_status_bar"))
    dlg.config_mgr.set(val, "ui", "status_bar")
    dlg.config_mgr.set(val, "ui", "show_status_bar")
    dlg.config_mgr.save_config()
    QMessageBox.information(dlg, "已同步", "状态栏配置已统一为：%s" % ("显示" if val else "隐藏"))


def _page_font(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("字体"))
    fam = QFontComboBox()
    fam.setCurrentFont(QFont(cfg.get("ui", "font_family") or "微软雅黑"))
    fam.setMinimumWidth(220)
    dlg.reg(("ui", "font_family"), lambda: fam.currentFont().family(), label="全局字体")
    add_row(lay, "全局字体", "界面正文与标题使用的主字体，皮肤预设字体会被这里覆盖", fam)
    fs = _spin(int(cfg.get("ui", "font_size") or 12), 9, 20, 1, "px")
    dlg.reg(("ui", "font_size"), fs.value, label="正文字号")
    add_row(lay, "正文字号", "9~20，设置窗口与主界面正文跟随", fs)
    nfs = _spin(int(cfg.get("ui", "name_font_size") or 50), 24, 120, 2, "px")
    dlg.reg(("ui", "name_font_size"), nfs.value, label="抽取姓名字号")
    add_row(lay, "抽取结果姓名字号", "主界面被抽中姓名的字号，教室大屏建议 80 以上", nfs)
    tfs = _spin(int(cfg.get("ui", "text_font_size") or 14), 9, 40, 1, "px")
    dlg.reg(("ui", "text_font_size"), tfs.value, label="课文正文字号")
    add_row(lay, "课文正文字号", "右侧课文面板的字号", tfs)
    wgt = Segmented([("normal", "常规"), ("bold", "加粗"), ("black", "特粗")], cfg.get("ui", "name_font_weight") or "bold")
    dlg.reg(("ui", "name_font_weight"), wgt.value, label="姓名字重")
    add_row(lay, "姓名字重", "被抽中姓名的粗细，大屏建议加粗或特粗", wgt)


def _page_animation(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("抽取动画"))
    da = _toggle(cfg.get("animation", "draw_enabled") if cfg.get("animation", "draw_enabled") is not None else True)
    dlg.reg(("animation", "draw_enabled"), da.isChecked, label="抽取动画")
    add_row(lay, "抽取过程动画", "关闭后点抽取立即出结果，不滚动", da)
    ra = _toggle(cfg.get("animation", "result_enabled") if cfg.get("animation", "result_enabled") is not None else True)
    dlg.reg(("animation", "result_enabled"), ra.isChecked, label="结果动画")
    add_row(lay, "结果弹出动画", "被抽中姓名的放大、发光、抖动等效果", ra)
    ta = _toggle(cfg.get("animation", "transition_enabled") if cfg.get("animation", "transition_enabled") is not None else True)
    dlg.reg(("animation", "transition_enabled"), ta.isChecked, label="过渡动画")
    add_row(lay, "界面过渡动画", "页面切换、面板展开、弹窗淡入", ta)
    dur = _spin(int(cfg.get("animation", "duration_ms") or 300), 0, 1200, 20, "毫秒")
    dlg.reg(("animation", "duration_ms"), dur.value, label="控件动画时长")
    add_row(lay, "控件动画时长", "按钮、开关、弹窗的过渡时长；0 表示瞬变", dur)
    ease = _combo([("linear", "线性"), ("ease_in", "缓入"), ("ease_out", "缓出"), ("ease_in_out", "缓入缓出"), ("elastic", "弹性")], cfg.get("animation", "easing") or "ease_out")
    dlg.reg(("animation", "easing"), ease.currentData, label="控件缓动")
    add_row(lay, "控件缓动曲线", "缓出最自然，弹性适合整活", ease)
    lay.addWidget(section_label("抽取节奏"))
    ad = _slider(float(cfg.get("draw", "auto_duration") or 4.0), 100, 1200, 10, "秒", integer=True)
    dlg.reg(("draw", "auto_duration"), lambda: round(ad.value() / 100.0, 2), label="抽取滚动时长")
    add_row(lay, "抽取滚动时长", "0.1~12 秒，越长越吊胃口", ad)
    es = _slider(float(cfg.get("ui", "ease_strength") or 0.92), 10, 100, 1, "%", integer=True)
    dlg.reg(("ui", "ease_strength"), lambda: round(es.value() / 100.0, 2), label="缓动强度")
    add_row(lay, "名字滚动缓动强度", "越大末尾减速越明显，0.9 左右最自然", es)
    curve = _combo([("ease_out", "缓出（推荐）"), ("ease_in", "缓入"), ("ease_in_out", "缓入缓出"), ("linear", "匀速"), ("elastic", "回弹")], cfg.get("ui", "animation_curve") or "ease_out")
    dlg.reg(("ui", "animation_curve"), curve.currentData, label="抽取缓动曲线")
    add_row(lay, "抽取缓动曲线", "决定名字滚动末尾的手感", curve)


def _page_window(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("窗口外观", "带「需重启」标记的项目保存后会提示重启"))
    rw = _toggle(cfg.get("ui", "rounded_window") if cfg.get("ui", "rounded_window") is not None else True)
    dlg.reg(("ui", "rounded_window"), rw.isChecked, restart=True, label="圆角窗口")
    add_row(lay, "圆角窗口", "关闭后使用系统标准直角窗框", rw, "需重启")
    rr = _spin(int(cfg.get("ui", "window_radius") or 12), 0, 32, 1, "px")
    dlg.reg(("ui", "window_radius"), rr.value, restart=True, label="窗口圆角")
    add_row(lay, "窗口圆角半径", "0~32，仅圆角窗口开启时生效", rr, "需重启")
    ws = _toggle(cfg.get("ui", "window_shadow") if cfg.get("ui", "window_shadow") is not None else True)
    dlg.reg(("ui", "window_shadow"), ws.isChecked, restart=True, label="窗口阴影")
    add_row(lay, "窗口阴影", "关闭可减少低配电脑的合成开销", ws, "需重启")
    wt = _toggle(cfg.get("ui", "window_topmost") if cfg.get("ui", "window_topmost") is not None else False)
    dlg.reg(("ui", "window_topmost"), wt.isChecked, label="窗口置顶")
    add_row(lay, "主窗口始终置顶", "开启后主窗口盖在其它程序上方；子窗口与插件窗口会同步跟随层级", wt)
    mm = _toggle(cfg.get("ui", "mini_on_minimize") if cfg.get("ui", "mini_on_minimize") is not None else False)
    dlg.reg(("ui", "mini_on_minimize"), mm.isChecked, label="最小化到小窗")
    add_row(lay, "最小化时切换为快捷小窗", "点最小化不隐藏，而是缩成悬浮小窗", mm)
    op = _slider(float(cfg.get("ui", "window_opacity") or 1.0), 60, 100, 1, "%", integer=True)
    dlg.reg(("ui", "window_opacity"), lambda: round(op.value() / 100.0, 2), restart=True, label="窗口透明度")
    add_row(lay, "窗口透明度", "60%~100%，半透明便于看穿到课件", op, "需重启")
    sw = _spin(int(cfg.get("ui", "sidebar_width") or 300), 220, 520, 10, "px")
    dlg.reg(("ui", "sidebar_width"), sw.value, restart=True, label="侧栏宽度")
    add_row(lay, "主界面侧栏宽度", "220~520，宽侧栏方便看课文全文", sw, "需重启")


def _page_mode(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("抽取方式"))
    mode = Segmented([("auto", "自动模式"), ("manual", "手动模式")], cfg.get("draw", "mode") or "auto")
    dlg.reg(("draw", "mode"), mode.value, label="抽取模式")
    add_row(lay, "抽取模式", "自动模式按权重随机；手动模式由老师逐一点名后记录", mode)
    lay.addWidget(_info_block("自动模式：算法按权重与去重规则随机选人，适合常规提问。\n手动模式：老师自己点人，程序只负责记录与标记，适合观察课。"))


def _page_rules(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("公平性"))
    nr = _toggle(cfg.get("draw", "no_repeat") if cfg.get("draw", "no_repeat") is not None else True)
    dlg.reg(("draw", "no_repeat"), nr.isChecked, label="本轮去重")
    add_row(lay, "本轮不重复抽取", "同一轮内已抽过的学生不再出现，保证雨露均沾", nr)
    ac = _toggle(cfg.get("draw", "anti_cheat") if cfg.get("draw", "anti_cheat") is not None else False)
    dlg.reg(("draw", "anti_cheat"), ac.isChecked, label="防作弊")
    add_row(lay, "防作弊模式", "检测到频繁切屏或外部工具热键时暂缓抽取（实验特性）", ac)
    hl = _spin(int(cfg.get("draw", "history_limit") or 50), 20, 500, 10, "条")
    dlg.reg(("draw", "history_limit"), hl.value, label="历史保留")
    add_row(lay, "抽取历史保留条数", "只保留最近 N 条，避免记录文件无限增长", hl)
    lay.addWidget(section_label("轮次"))
    ar = _toggle(cfg.get("draw", "auto_reset_round") if cfg.get("draw", "auto_reset_round") is not None else True)
    dlg.reg(("draw", "auto_reset_round"), ar.isChecked, label="自动开启新轮")
    add_row(lay, "全班抽完后自动开启新一轮", "关闭则需手动点「新建轮次」", ar)


def _page_params(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("抽取节奏"))
    cd = _toggle(cfg.get("ui", "draw_countdown") if cfg.get("ui", "draw_countdown") is not None else False)
    dlg.reg(("ui", "draw_countdown"), cd.isChecked, label="抽取倒计时")
    add_row(lay, "抽取前倒计时", "点抽取后先倒数几秒再开始滚名字，制造紧张感", cd)
    cn = _spin(int(cfg.get("ui", "countdown_number") or 3), 1, 10, 1, "秒")
    dlg.reg(("ui", "countdown_number"), cn.value, label="倒计时秒数")
    add_row(lay, "倒计时秒数", "1~10 秒", cn)
    sc = _slider(float(cfg.get("ui", "scroll_speed") or 1.0), 30, 300, 5, "x", integer=True)
    dlg.reg(("ui", "scroll_speed"), lambda: round(sc.value() / 100.0, 2), label="滚动速度")
    add_row(lay, "名字滚动速度", "1.0 标准，2.0 极速", sc)


def _page_auto_draw(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("结果展示"))
    rp = _toggle(cfg.get("ui", "result_popup") if cfg.get("ui", "result_popup") is not None else False)
    dlg.reg(("ui", "result_popup"), rp.isChecked, label="结果大窗")
    add_row(lay, "抽取结果弹出大窗口", "全屏级别的大字结果窗，适合教室大屏", rp)
    pd = _spin(int(cfg.get("ui", "popup_duration") or 2000), 500, 8000, 100, "毫秒")
    dlg.reg(("ui", "popup_duration"), pd.value, label="结果窗停留")
    add_row(lay, "结果大窗停留时长", "500~8000 毫秒，到时自动关闭", pd)
    lay.addWidget(section_label("数据安全"))
    asi = _spin(int(cfg.get("ui", "auto_save_interval") or 300), 30, 1800, 30, "秒")
    dlg.reg(("ui", "auto_save_interval"), asi.value, label="自动保存间隔")
    add_row(lay, "自动保存间隔", "每隔 N 秒把名单、记录、积分写盘，防断电丢失", asi)
    add_row(lay, "立即保存一次", "手动触发一次全量保存", _button_row([("立即保存", lambda: _save_data_now(dlg), "primary")]))


def _save_data_now(dlg):
    try:
        parent = dlg.parent()
        if parent and hasattr(parent, "_save_data"):
            parent._save_data()
        dlg.config_mgr.save_config()
        QMessageBox.information(dlg, "保存完成", "配置与课堂数据已写入磁盘。")
    except Exception as ex:
        QMessageBox.warning(dlg, "保存失败", str(ex))


def _page_weight(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("动态权重", "权重越高越容易被抽到"))
    we = _toggle(cfg.get("draw", "dynamic_weight") if cfg.get("draw", "dynamic_weight") is not None else True)
    dlg.reg(("draw", "dynamic_weight"), we.isChecked, label="动态权重")
    add_row(lay, "启用动态权重", "按背诵状态动态调整被抽中的概率", we)
    df = _toggle(cfg.get("draw", "dynamic_focus") if cfg.get("draw", "dynamic_focus") is not None else True)
    dlg.reg(("draw", "dynamic_focus"), df.isChecked, label="关注薄弱学生")
    add_row(lay, "优先关注薄弱学生", "未背过的学生权重更高，避免总是抽到同一批人", df)
    lay.addWidget(section_label("状态倍率"))
    un = _spin(int(float(cfg.get("draw", "rate_unlearned") or 3)), 1, 10, 1, "倍")
    dlg.reg(("draw", "rate_unlearned"), un.value, label="未背过倍率")
    add_row(lay, "未背过", "未背过学生的抽取倍率，建议 3", un)
    fa = _spin(int(float(cfg.get("draw", "rate_familiar") or 2)), 1, 10, 1, "倍")
    dlg.reg(("draw", "rate_familiar"), fa.value, label="未背熟倍率")
    add_row(lay, "未背熟", "半熟状态学生的倍率，建议 2", fa)
    ma = _spin(int(float(cfg.get("draw", "rate_mastered") or 1)), 1, 10, 1, "倍")
    dlg.reg(("draw", "rate_mastered"), ma.value, label="已背过倍率")
    add_row(lay, "已背过", "已掌握学生的倍率，建议 1", ma)
    add_row(lay, "权重可视化", "查看每个学生当前的权重条与分布", _button_row([
        ("查看权重分布", lambda: _open_weight_view(dlg), "primary"),
    ]))


def _open_weight_view(dlg):
    parent = dlg.parent()
    if parent and hasattr(parent, "_show_weight_visualization"):
        parent._show_weight_visualization()
    else:
        QMessageBox.information(dlg, "提示", "请在主界面菜单中打开权重可视化。")


def _page_tts(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("语音朗读", "离线朗读，不联网，不上传任何内容"))
    te = _toggle(cfg.get("tts", "enabled") if cfg.get("tts", "enabled") is not None else False)
    dlg.reg(("tts", "enabled"), te.isChecked, label="语音朗读")
    add_row(lay, "抽取结果语音播报", "抽中后朗读姓名与课文标题", te)
    tt = _toggle(cfg.get("tts", "speak_text") if cfg.get("tts", "speak_text") is not None else True)
    dlg.reg(("tts", "speak_text"), tt.isChecked, label="朗读课文")
    add_row(lay, "同时朗读课文", "关闭则只念姓名", tt)
    rate = _spin(int(cfg.get("tts", "rate") or 150), 80, 300, 5, "字/分")
    dlg.reg(("tts", "rate"), rate.value, label="语速")
    add_row(lay, "语速", "80~300，160 左右接近正常讲课速度", rate)
    vol = _slider(float(cfg.get("tts", "volume") or 1.0), 10, 100, 5, "%", integer=True)
    dlg.reg(("tts", "volume"), lambda: round(vol.value() / 100.0, 2), label="音量")
    add_row(lay, "音量", "10%~100%", vol)
    add_row(lay, "试听", "用当前设置朗读一句示例", _button_row([("播放示例", lambda: _tts_test(dlg), "primary")]))
    lay.addWidget(_info_block(
        "朗读依赖系统自带语音引擎（Windows SAPI / pyttsx3）。若未安装 pyttsx3，程序不会报错，只在状态栏提示一次，"
        "其余功能不受影响。安装命令：pip install pyttsx3"
    ))


def _tts_test(dlg):
    cfg = dlg.config_mgr
    parent = dlg.parent()
    try:
        if parent and hasattr(parent, "_speak_result"):
            parent._speak_result("A13班，朗读测试，当前课文第一课")
        else:
            raise RuntimeError("no speaker")
    except Exception:
        QMessageBox.information(dlg, "提示", "主界面未启用语音模块，或未安装 pyttsx3。\n安装后即可离线朗读。")


def _page_text_extract(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("课文抽取"))
    mode = Segmented(
        [("段落抽取", "段落抽取"), ("随机抽取", "随机抽取"), ("不抽取课文", "不抽课文")],
        cfg.get("text", "extract_mode") or "段落抽取",
    )
    dlg.reg(("text", "extract_mode"), mode.value, label="课文抽取模式")
    add_row(lay, "课文抽取模式", "段落抽取：按段落定位；随机抽取：整篇随机；不抽课文：只点名", mode)
    pr = _toggle(cfg.get("text", "paragraph_random") if cfg.get("text", "paragraph_random") is not None else True)
    dlg.reg(("text", "paragraph_random"), pr.isChecked, label="段落随机")
    add_row(lay, "段落在课文内随机", "一篇课文分多段时随机定位到某一段", pr)


def _page_text_display(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("课文展示"))
    st = _toggle(cfg.get("text", "show_title") if cfg.get("text", "show_title") is not None else True)
    dlg.reg(("text", "show_title"), st.isChecked, label="显示课文标题")
    add_row(lay, "显示课文标题", "在课文面板顶部显示「第X课 标题」", st)
    al = Segmented([("left", "左对齐"), ("center", "居中"), ("right", "右对齐")], cfg.get("text", "text_align") or "left")
    dlg.reg(("text", "text_align"), al.value, label="课文对齐")
    add_row(lay, "课文正文对齐", "长课文建议左对齐，短句可居中", al)
    an = _toggle(cfg.get("text", "auto_next") if cfg.get("text", "auto_next") is not None else True)
    dlg.reg(("text", "auto_next"), an.isChecked, label="自动切换下一课")
    add_row(lay, "抽完自动切下一篇", "关闭则同一课文可反复抽", an)


def _page_text_progress(dlg, host, lay):
    lay.addWidget(section_label("课文进度"))
    add_row(lay, "重置课文进度", "清除所有课文的背诵进度标记，不可撤销", _button_row([
        ("重置进度", lambda: _reset_text_progress(dlg), "danger"),
    ]))
    add_row(lay, "查看进度文件", "打开课文进度保存位置", _button_row([
        ("打开程序目录", lambda: _open_dir(BASE_DIR), ""),
    ]))
    lay.addWidget(_info_block("课文进度保存在 text_progress.json，与轮次记录相互独立。重置进度不会删除抽取历史。"))


def _reset_text_progress(dlg):
    r = QMessageBox.question(dlg, "确认重置", "确定重置所有课文进度？此操作不可撤销。", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if r != QMessageBox.Yes:
        return
    try:
        p = os.path.join(BASE_DIR, "text_progress.json")
        if os.path.exists(p):
            os.remove(p)
        QMessageBox.information(dlg, "已重置", "课文进度已清空。")
    except Exception as ex:
        QMessageBox.warning(dlg, "重置失败", str(ex))


def _page_mark(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("标记反馈"))
    mt = _toggle(cfg.get("ui", "mark_toast") if cfg.get("ui", "mark_toast") is not None else True)
    dlg.reg(("ui", "mark_toast"), mt.isChecked, label="标记提示")
    add_row(lay, "标记后弹出提示", "标记「已背过/未背熟/未背过」后弹出轻提示", mt)
    lay.addWidget(section_label("标记与统计的关系"))
    lay.addWidget(_info_block(
        "每次标记都会写入当前轮次记录，并同步更新右侧面板与积分榜。\n"
        "标记选错时，先点撤销（Ctrl+Z）回退标记，再重新选择；撤销会同步回退统计与积分，不会出现「面板已加、积分未减」的不一致。\n"
        "如果没有撤销而是重新标记，则以最后一次标记为准，统计只保留一条最终状态。"
    ))
    add_row(lay, "撤销上一步", "等价于 Ctrl+Z，回退最近一次标记或抽取", _button_row([
        ("撤销", lambda: _undo(dlg), "primary"),
        ("重做", lambda: _redo(dlg), ""),
    ]))


def _undo(dlg):
    parent = dlg.parent()
    if parent and hasattr(parent, "_undo"):
        parent._undo()
    else:
        QMessageBox.information(dlg, "提示", "请在主界面使用 Ctrl+Z 撤销。")


def _redo(dlg):
    parent = dlg.parent()
    if parent and hasattr(parent, "_redo"):
        parent._redo()
    else:
        QMessageBox.information(dlg, "提示", "请在主界面使用 Ctrl+Y 重做。")


def _page_score(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("积分"))
    lay.addWidget(_info_block(
        "积分规则由「已背过 +2 / 未背熟 +1 / 未背过 0」组成，并随撤销同步回退。\n"
        "积分榜按轮次累计，切换轮次不会改变历史积分。"
    ))
    add_row(lay, "查看积分排行榜", "打开当前班级的积分排行窗口", _button_row([
        ("打开排行榜", lambda: _ranking(dlg), "primary"),
    ]))
    add_row(lay, "清零积分", "把全班积分归零，历史抽取记录保留", _button_row([
        ("清零", lambda: _clear_score(dlg), "danger"),
    ]))


def _ranking(dlg):
    parent = dlg.parent()
    if parent and hasattr(parent, "_show_ranking"):
        parent._show_ranking()
    else:
        QMessageBox.information(dlg, "提示", "请从主界面打开排行榜。")


def _clear_score(dlg):
    r = QMessageBox.question(dlg, "确认清零", "确定把全班积分清零？抽取记录会保留。", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if r != QMessageBox.Yes:
        return
    parent = dlg.parent()
    try:
        if parent and hasattr(parent, "data_mgr"):
            dmg = parent.data_mgr
            for name in list(dmg.students):
                dmg.set_student_status(name, dmg.get_student_status(name))
            dlg.config_mgr.save_config()
        QMessageBox.information(dlg, "完成", "积分已清零。")
    except Exception as ex:
        QMessageBox.warning(dlg, "失败", str(ex))


SHORTCUT_ROWS = [
    ("开始抽取", "空格", "space"),
    ("已背过", "1", "1"),
    ("未背熟", "2", "2"),
    ("未背过", "3", "3"),
    ("隐藏面板", "Esc", "Escape"),
    ("重置本轮", "R", "r"),
    ("撤销", "Ctrl+Z", "Ctrl+Z"),
    ("重做", "Ctrl+Y", "Ctrl+Y"),
    ("保存", "Ctrl+S", "Ctrl+S"),
    ("放大界面", "Ctrl+=", "Ctrl+="),
    ("缩小界面", "Ctrl+-", "Ctrl+-"),
    ("切换权重", "W", "w"),
    ("上一篇课文", "←", "Left"),
    ("下一篇课文", "→", "Right"),
    ("打开设置", "Ctrl+,", "Ctrl+,"),
]


def _page_shortcuts(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("快捷键一览", "以下为当前生效的按键，可在「自定义按键」页修改"))
    enabled = cfg.get("shortcut", "enabled")
    cur = {
        "space": cfg.get("shortcut", "key_draw") or "space",
        "1": cfg.get("shortcut", "key_mastered") or "1",
        "2": cfg.get("shortcut", "key_familiar") or "2",
        "3": cfg.get("shortcut", "key_unlearned") or "3",
        "Escape": cfg.get("shortcut", "key_hide_panel") or "Escape",
        "r": cfg.get("shortcut", "key_reset_round") or "r",
    }
    for label, display, key in SHORTCUT_ROWS:
        actual = cur.get(key, display)
        val = QLabel(actual)
        val.setObjectName("mono")
        add_row(lay, label, "", val)
    if enabled is False:
        lay.addWidget(_info_block("注意：快捷键总开关当前为关闭状态，以上按键不会触发。"))


def _page_shortcut_settings(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("快捷键开关"))
    en = _toggle(cfg.get("shortcut", "enabled") if cfg.get("shortcut", "enabled") is not None else True)
    dlg.reg(("shortcut", "enabled"), en.isChecked, restart=True, label="快捷键总开关")
    add_row(lay, "启用全局快捷键", "关闭后所有单键快捷键失效（Ctrl 组合仍可用）", en, "需重启")
    lay.addWidget(section_label("按键绑定", "点输入框后按下新按键，Esc 可清空"))
    for label, sec_key, default in [
        ("开始抽取", "key_draw", "space"),
        ("标记已背过", "key_mastered", "1"),
        ("标记未背熟", "key_familiar", "2"),
        ("标记未背过", "key_unlearned", "3"),
        ("隐藏面板", "key_hide_panel", "Escape"),
        ("重置本轮", "key_reset_round", "r"),
    ]:
        ed = QKeySequenceEdit(QKeySequence(cfg.get("shortcut", sec_key) or default))
        ed.setMinimumWidth(180)
        dlg.reg(("shortcut", sec_key), lambda e=ed: e.keySequence().toString() or default, restart=True, label=label)
        add_row(lay, label, "默认：%s" % default, ed, "需重启")


def _page_data_mgmt(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("数据文件"))
    for label, sec_key, default, kind in [
        ("学生名单", "students", "students.txt", "file"),
        ("课文题库", "texts", "texts.txt", "file"),
        ("抽取记录", "records", "records.txt", "file"),
        ("统计数据", "stats", "stats.txt", "file"),
    ]:
        row = _path_row(dlg, cfg.get("files", sec_key) or default, kind)
        dlg.reg(("files", sec_key), row.value, label=label)
        add_row(lay, label, "相对路径以程序目录为基准，可指向任意 txt", row)
    lay.addWidget(section_label("维护"))
    add_row(lay, "打开数据目录", "在资源管理器中查看全部数据文件", _button_row([
        ("打开目录", lambda: _open_dir(BASE_DIR), ""),
    ]))
    add_row(lay, "重置全部数据", "清空名单、课文、记录、积分并重新进入向导（不可恢复）", _button_row([
        ("重置", lambda: _reset_all(dlg), "danger"),
    ]))


def _reset_all(dlg):
    r = QMessageBox.question(
        dlg, "危险操作",
        "将清空学生名单、课文、抽取记录、积分，并把向导标记改为未完成。\n\n此操作不可恢复，确定继续？",
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
    )
    if r != QMessageBox.Yes:
        return
    try:
        for name in ["students.txt", "texts.txt", "records.txt", "stats.txt"]:
            p = os.path.join(BASE_DIR, name)
            if os.path.exists(p):
                os.remove(p)
        import configparser
        c = configparser.ConfigParser()
        c["status"] = {"finished": "False"}
        with open(os.path.join(BASE_DIR, "wizard_record.ini"), "w", encoding="utf-8") as f:
            c.write(f)
        QMessageBox.information(dlg, "已重置", "数据已清空，下次启动进入配置向导。")
    except Exception as ex:
        QMessageBox.warning(dlg, "重置失败", str(ex))


def _page_export(dlg, host, lay):
    lay.addWidget(section_label("导出统计"))
    add_row(lay, "导出为 CSV", "表格软件可直接打开，含每人的抽取次数与三种标记次数", _button_row([
        ("导出 CSV", lambda: _export(dlg, "csv"), "primary"),
    ]))
    add_row(lay, "导出为 TXT", "纯文本报表，便于打印与贴到群里", _button_row([
        ("导出 TXT", lambda: _export(dlg, "txt"), ""),
    ]))
    add_row(lay, "导出轮次记录", "把每一轮的明细导出为 CSV", _button_row([
        ("导出轮次", lambda: _export_rounds(dlg), ""),
    ]))
    lay.addWidget(_info_block("导出文件默认保存到桌面，文件名带时间戳，不会覆盖历史导出。"))


def _stats_rows(dlg):
    parent = dlg.parent()
    try:
        if parent and hasattr(parent, "data_mgr"):
            return parent.data_mgr.get_all_stats()
    except Exception:
        pass
    return {}


def _export(dlg, fmt):
    stats = _stats_rows(dlg)
    if not stats:
        QMessageBox.information(dlg, "没有数据", "当前还没有可导出的统计数据。")
        return
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    default = os.path.join(desktop, "点名统计_%s.%s" % (ts, fmt))
    path, _ = QFileDialog.getSaveFileName(dlg, "导出统计", default, "CSV (*.csv);;文本 (*.txt)")
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8-sig" if fmt == "csv" else "utf-8") as f:
            sep = "," if fmt == "csv" else "\t"
            f.write(sep.join(["学生", "抽取次数", "已背过", "未背熟", "未背过", "积分"]) + "\n")
            for name, d in sorted(stats.items()):
                f.write(sep.join([str(name), str(d.get("draw_count", 0)), str(d.get("mastered", 0)),
                                  str(d.get("familiar", 0)), str(d.get("unlearned", 0)), str(d.get("score", 0))]) + "\n")
        QMessageBox.information(dlg, "导出完成", path)
    except Exception as ex:
        QMessageBox.warning(dlg, "导出失败", str(ex))


def _export_rounds(dlg):
    from datetime import datetime
    parent = dlg.parent()
    rounds = []
    try:
        if parent and hasattr(parent, "data_mgr"):
            rounds = parent.data_mgr.get_all_rounds()
    except Exception:
        rounds = []
    if not rounds:
        QMessageBox.information(dlg, "没有记录", "当前还没有轮次记录。")
        return
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    default = os.path.join(os.path.expanduser("~"), "Desktop", "轮次记录_%s.csv" % ts)
    path, _ = QFileDialog.getSaveFileName(dlg, "导出轮次", default, "CSV (*.csv)")
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8-sig") as f:
            f.write("轮次,时间,学生,课文,状态\n")
            for r in rounds:
                for rec in (r.get("records") or []):
                    f.write("%s,%s,%s,%s,%s\n" % (
                        r.get("id", ""), r.get("time", ""), rec.get("student", ""),
                        (rec.get("text") or "").replace(",", "，"), rec.get("status", ""),
                    ))
        QMessageBox.information(dlg, "导出完成", path)
    except Exception as ex:
        QMessageBox.warning(dlg, "导出失败", str(ex))


def _page_backup(dlg, host, lay):
    lay.addWidget(section_label("备份"))
    add_row(lay, "立即备份", "把配置、名单、课文、向导标记复制到 backup 目录", _button_row([
        ("备份", lambda: _backup(dlg), "primary"),
    ]))
    add_row(lay, "恢复最新备份", "用最近一次备份覆盖当前配置与名单", _button_row([
        ("恢复", lambda: _restore(dlg), ""),
    ]))
    add_row(lay, "打开备份目录", "查看历史备份，可手动删除旧备份", _button_row([
        ("打开", lambda: _open_dir(os.path.join(BASE_DIR, "backup")), ""),
    ]))


def _backup(dlg):
    try:
        import shutil
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        d = os.path.join(BASE_DIR, "backup", "backup_%s" % ts)
        os.makedirs(d, exist_ok=True)
        n = 0
        for name in ["config.json", "students.txt", "texts.txt", "wizard_record.ini"]:
            src = os.path.join(BASE_DIR, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(d, name))
                n += 1
        QMessageBox.information(dlg, "备份完成", "已备份 %d 个文件到：\n%s" % (n, d))
    except Exception as ex:
        QMessageBox.warning(dlg, "备份失败", str(ex))


def _restore(dlg):
    try:
        import shutil
        bdir = os.path.join(BASE_DIR, "backup")
        if not os.path.isdir(bdir):
            QMessageBox.information(dlg, "无备份", "还没有任何备份。")
            return
        items = sorted([x for x in os.listdir(bdir) if os.path.isdir(os.path.join(bdir, x))], reverse=True)
        if not items:
            QMessageBox.information(dlg, "无备份", "还没有任何备份。")
            return
        r = QMessageBox.question(dlg, "确认恢复", "将用最新备份「%s」覆盖当前配置与名单，继续？" % items[0], QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if r != QMessageBox.Yes:
            return
        src = os.path.join(bdir, items[0])
        for name in os.listdir(src):
            sp = os.path.join(src, name)
            if os.path.isfile(sp):
                shutil.copy2(sp, os.path.join(BASE_DIR, name))
        QMessageBox.information(dlg, "恢复完成", "已恢复，建议重启软件。")
    except Exception as ex:
        QMessageBox.warning(dlg, "恢复失败", str(ex))


def _page_echo(dlg, host, lay):
    cfg = dlg.config_mgr
    lay.addWidget(section_label("回声洞", "本地内容，不上传，不联网"))
    ee = _toggle(cfg.get("ui", "echo_enabled") if cfg.get("ui", "echo_enabled") is not None else True)
    dlg.reg(("ui", "echo_enabled"), ee.isChecked, label="回声洞")
    add_row(lay, "启用回声洞", "关闭后主界面不再出现回声入口", ee)
    ec = _toggle(cfg.get("ui", "echo_confirm") if cfg.get("ui", "echo_confirm") is not None else True)
    dlg.reg(("ui", "echo_confirm"), ec.isChecked, label="写前确认")
    add_row(lay, "写入前确认", "每次写入回声前弹一次确认，防止误触", ec)
    em = _spin(int(cfg.get("ui", "echo_max") or 120), 20, 500, 10, "条")
    dlg.reg(("ui", "echo_max"), em.value, label="回声上限")
    add_row(lay, "保留上限", "超过上限自动删除最旧的一条", em)
    lay.addWidget(section_label("管理"))
    try:
        count = len(dlg.echo_hole.get_all()) if dlg.echo_hole else 0
    except Exception:
        count = 0
    add_row(lay, "当前回声数量", "全部保存在程序目录的本地 txt 中", QLabel("%d 条" % count))
    add_row(lay, "清空回声", "删除全部回声内容，不可撤销", _button_row([
        ("清空", lambda: _clear_echo(dlg), "danger"),
        ("打开目录", lambda: _open_dir(BASE_DIR), ""),
    ]))


def _clear_echo(dlg):
    r = QMessageBox.question(dlg, "确认清空", "确定清空所有回声？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if r != QMessageBox.Yes:
        return
    try:
        if dlg.echo_hole:
            dlg.echo_hole.clear_all()
        QMessageBox.information(dlg, "已清空", "回声已清空。")
    except Exception as ex:
        QMessageBox.warning(dlg, "失败", str(ex))


def _page_plugins(dlg, host, lay):
    import plugin_market as PM
    pm = dlg.plugin_mgr
    lay.addWidget(section_label("插件中心", "与 ClassIsland 相同的组织方式：每个插件一个目录、一份 manifest.json；卡片可直接启用、设置、卸载，市场可检查更新"))

    bar = QWidget()
    bl = QHBoxLayout(bar)
    bl.setContentsMargins(0, 0, 0, 0)
    bl.setSpacing(8)
    for text, fn, style in [
        ("刷新列表", lambda: _reload_plugins(dlg), "primary"),
        ("安装本地插件", lambda: _install_plugin(dlg), ""),
        ("检查更新", lambda: _refresh_market(dlg), ""),
        ("打开插件目录", lambda: _open_plugin_dir(dlg), ""),
        ("开发工具", lambda: _open_tool("arcx_packager.py"), ""),
        ("查看日志", lambda: _plugin_logs(dlg), ""),
    ]:
        b = QPushButton(text)
        b.setObjectName(style)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda c=False, f=fn: f())
        bl.addWidget(b)
    bl.addStretch()
    lay.addWidget(bar)

    tabs = QTabWidget()
    tabs.setObjectName("settings_tabs")
    dlg._plugin_tabs = tabs

    installed_host = QWidget()
    grid = QGridLayout(installed_host)
    grid.setContentsMargins(0, 10, 0, 0)
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(10)
    try:
        items = PM.installed_plugins(pm)
    except Exception:
        items = []
    if not items:
        empty = QFrame()
        empty.setObjectName("settingcard")
        el = QVBoxLayout(empty)
        el.setContentsMargins(16, 20, 16, 20)
        t = QLabel("还没有安装任何插件")
        t.setObjectName("setting_title")
        el.addWidget(t)
        d = QLabel("点「安装本地插件」选择插件目录或压缩包；插件目录里需要一份 manifest.json。")
        d.setObjectName("setting_desc")
        d.setWordWrap(True)
        el.addWidget(d)
        grid.addWidget(empty, 0, 0, 1, 2)
        grid.setRowStretch(1, 1)
    else:
        single = len(items) == 1
        for index, item in enumerate(items):
            grid.addWidget(_plugin_card(dlg, item), index // 2, index % 2, 1, 2 if single else 1)
        grid.setRowStretch((len(items) + 1) // 2, 1)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    tabs.addTab(installed_host, "已安装")

    market_host = QWidget()
    market_lay = QVBoxLayout(market_host)
    market_lay.setContentsMargins(0, 10, 0, 0)
    market_lay.setSpacing(8)
    dlg._market_host_lay = market_lay
    market_lay.addWidget(_market_body(dlg))
    tabs.addTab(market_host, "插件市场")

    lay.addWidget(tabs, 1)


def _market_body(dlg):
    import plugin_market as PM
    host = QWidget()
    grid = QGridLayout(host)
    grid.setContentsMargins(0, 0, 0, 0)
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(10)
    try:
        cards, source, error = PM.market_plugins(dlg.plugin_mgr, remote=bool(getattr(dlg, "_market_remote", False)))
    except Exception:
        cards, source, error = [], "", "读取索引失败"
    if not cards:
        empty = QFrame()
        empty.setObjectName("settingcard")
        el = QVBoxLayout(empty)
        el.setContentsMargins(16, 20, 16, 20)
        t = QLabel("市场里还没有可安装的插件")
        t.setObjectName("setting_title")
        el.addWidget(t)
        msg = "把插件放成文件夹并生成 market_index 后，或点「检查更新」联网拉取索引。"
        if error:
            msg = "暂时连不上在线索引，已按离线模式显示。"
        d = QLabel(msg)
        d.setObjectName("setting_desc")
        d.setWordWrap(True)
        el.addWidget(d)
        grid.addWidget(empty, 0, 0, 1, 2)
        grid.setRowStretch(1, 1)
    else:
        single = len(cards) == 1
        for index, item in enumerate(cards):
            grid.addWidget(_market_card(dlg, item), index // 2, index % 2, 1, 2 if single else 1)
        grid.setRowStretch((len(cards) + 1) // 2, 1)
    grid.setColumnStretch(0, 1)
    grid.setColumnStretch(1, 1)
    return host


def _plugin_icon_label(item, size=42):
    icon_path = ""
    if item.get("_folder"):
        icon_name = item.get("icon", "")
        if icon_name:
            icon_path = os.path.join(item["_folder"], icon_name)
    if icon_path and os.path.exists(icon_path):
        pmap = QPixmap(icon_path).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label = QLabel()
        label.setPixmap(pmap)
        label.setFixedSize(size, size)
        label.setAlignment(Qt.AlignCenter)
        return label
    icon = QIcon(S.svg_icon("plugin", size - 12, S.current()["c"]["text2"]))
    label = QLabel()
    label.setPixmap(icon.pixmap(size, size))
    label.setFixedSize(size, size)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("background: %s; border-radius: 8px;" % S.current()["c"]["card2"])
    return label


def _set_plugin_enabled(dlg, item, checked):
    import plugin_market as PM
    key = item.get("id") or item.get("name")
    name = item.get("name")
    PM.save_state(key, checked)
    try:
        if checked:
            dlg.plugin_mgr.enable_plugin(name)
        else:
            dlg.plugin_mgr.disable_plugin(name)
    except Exception:
        pass
    dlg.status_label.setText("插件「%s」已%s，重启后完全生效" % (name, "启用" if checked else "禁用"))


def _plugin_card(dlg, item):
    card = QFrame()
    card.setObjectName("settingcard")
    card.setMinimumHeight(132)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(8)

    top = QHBoxLayout()
    top.setSpacing(10)
    top.addWidget(_plugin_icon_label(item, 34))

    col = QVBoxLayout()
    col.setSpacing(3)
    line = QHBoxLayout()
    line.setSpacing(8)
    n = QLabel(item.get("name", "未命名"))
    n.setObjectName("setting_label")
    line.addWidget(n)
    v = QLabel("v%s" % item.get("version", "1.0.0"))
    v.setObjectName("badge")
    line.addWidget(v)
    dot = QLabel()
    dot.setFixedSize(7, 7)
    dot.setStyleSheet("background: %s; border-radius: 3px;" % (
        S.current()["c"]["success"] if item.get("enabled", True) else S.current()["c"]["text3"]
    ))
    line.addWidget(dot)
    line.addStretch()
    col.addLayout(line)
    a = QLabel("作者 %s" % item.get("author", "未知"))
    a.setObjectName("setting_desc")
    col.addWidget(a)
    top.addLayout(col, 1)

    enabled = bool(item.get("enabled", True))
    sw = QPushButton("已启用" if enabled else "已禁用")
    if enabled:
        sw.setObjectName("primary")
    sw.setCursor(Qt.PointingHandCursor)

    def _flip(checked=False, b=sw, i=item):
        new_state = not bool(i.get("enabled", True))
        i["enabled"] = new_state
        b.setText("已启用" if new_state else "已禁用")
        b.setObjectName("primary" if new_state else "")
        b.style().unpolish(b)
        b.style().polish(b)
        _set_plugin_enabled(dlg, i, new_state)

    sw.clicked.connect(_flip)
    top.addWidget(sw, 0, Qt.AlignTop)
    lay.addLayout(top)

    desc = item.get("description", "")
    if desc:
        d = QLabel(desc)
        d.setObjectName("setting_desc")
        d.setWordWrap(True)
        d.setMinimumHeight(32)
        lay.addWidget(d)
    lay.addStretch()

    actions = QHBoxLayout()
    actions.setSpacing(8)
    sid = item.get("id") or item.get("name")
    name = item.get("name", "")
    b = QPushButton("设置")
    b.clicked.connect(lambda c=False, nm=name: _open_plugin_setting(dlg, nm))
    actions.addWidget(b)
    if item.get("kind") == "folder":
        b = QPushButton("打开目录")
        b.clicked.connect(lambda c=False, i=item: _open_folder_path(i.get("_folder", "")))
        actions.addWidget(b)
    else:
        b = QPushButton("运行")
        b.clicked.connect(lambda c=False, nm=name: _run_plugin(dlg, nm))
        actions.addWidget(b)
    actions.addStretch()
    b = QPushButton("卸载")
    b.setObjectName("danger")
    b.clicked.connect(lambda c=False, i=sid, nm=name: _uninstall_plugin_v2(dlg, i, nm))
    actions.addWidget(b)
    lay.addLayout(actions)
    return card


def _market_card(dlg, item):
    card = QFrame()
    card.setObjectName("settingcard")
    card.setMinimumHeight(132)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(8)

    top = QHBoxLayout()
    top.setSpacing(10)
    top.addWidget(_plugin_icon_label(item, 34))
    col = QVBoxLayout()
    col.setSpacing(3)
    line = QHBoxLayout()
    line.setSpacing(8)
    n = QLabel(item.get("name", "未命名"))
    n.setObjectName("setting_label")
    line.addWidget(n)
    v = QLabel("v%s" % item.get("version", "1.0.0"))
    v.setObjectName("badge")
    line.addWidget(v)
    if item.get("update_available"):
        u = QLabel("可更新")
        u.setObjectName("badge")
        line.addWidget(u)
    line.addStretch()
    col.addLayout(line)
    a = QLabel("作者 %s" % item.get("author", "未知"))
    a.setObjectName("setting_desc")
    col.addWidget(a)
    top.addLayout(col, 1)
    lay.addLayout(top)

    desc = item.get("description", "")
    d = QLabel(desc if desc else "该插件没有填写说明")
    d.setObjectName("setting_desc")
    d.setWordWrap(True)
    d.setMinimumHeight(32)
    lay.addWidget(d)
    lay.addStretch()

    actions = QHBoxLayout()
    actions.setSpacing(8)
    actions.addStretch()
    if item.get("installed"):
        b = QPushButton("更新" if item.get("update_available") else "已安装")
        b.setEnabled(bool(item.get("update_available")))
        b.clicked.connect(lambda c=False, i=item: _market_install(dlg, i))
        actions.addWidget(b)
    else:
        b = QPushButton("安装")
        b.setObjectName("primary")
        b.setEnabled(bool(item.get("download_url")))
        b.clicked.connect(lambda c=False, i=item: _market_install(dlg, i))
        actions.addWidget(b)
    lay.addLayout(actions)
    return card


def _toggle_plugin_switch(dlg, plugin_id, checked):
    import plugin_market as PM
    PM.save_state(plugin_id, checked)
    if checked:
        try:
            dlg.plugin_mgr.enable_plugin(plugin_id)
        except Exception:
            pass
    else:
        try:
            dlg.plugin_mgr.disable_plugin(plugin_id)
        except Exception:
            pass
    dlg.status_label.setText("插件「%s」已%s，重启后完全生效" % (plugin_id, "启用" if checked else "禁用"))


def _uninstall_plugin_v2(dlg, plugin_id, name):
    import plugin_market as PM
    r = QMessageBox.question(
        dlg, "确认卸载", "卸载「%s」？插件目录与插件数据都会被删除。" % (name or plugin_id),
        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
    )
    if r != QMessageBox.Yes:
        return
    ok, msg = PM.remove_plugin(plugin_id, dlg.plugin_mgr)
    try:
        dlg.plugin_mgr.load_all_plugins()
    except Exception:
        pass
    dlg._reload_page("plugins")
    dlg.status_label.setText(msg if ok else ("卸载失败：" + msg))


def _open_folder_path(path):
    if not path or not os.path.isdir(path):
        return
    try:
        import cross_platform
        cross_platform.open_folder(path)
    except Exception:
        try:
            os.startfile(path)
        except Exception:
            pass


def _open_plugin_dir(dlg):
    import plugin_market as PM
    folder = PM.plugins_dir()
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except Exception:
            return
    _open_folder_path(folder)
    dlg.status_label.setText("插件目录：%s" % folder)


def _refresh_market(dlg):
    import plugin_market as PM
    dlg._market_remote = True
    try:
        cards, source, error = PM.market_plugins(dlg.plugin_mgr, remote=True)
    except Exception as exc:
        QMessageBox.warning(dlg, "检查更新失败", str(exc))
        return
    if dlg._market_host_lay is not None:
        while dlg._market_host_lay.count():
            item = dlg._market_host_lay.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        dlg._market_host_lay.addWidget(_market_body(dlg))
    if error:
        dlg.status_label.setText("连不上在线索引，已按离线模式显示本地插件")
    else:
        dlg.status_label.setText("市场已刷新，共 %d 个插件" % len(cards))


def _market_install(dlg, item):
    import plugin_market as PM
    url = item.get("download_url", "")
    if not url:
        QMessageBox.warning(dlg, "无法安装", "该插件没有提供下载地址")
        return
    dlg.status_label.setText("正在下载 %s ..." % item.get("name", ""))
    QApplication.processEvents()
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "A13Rollcall"})
        with urllib.request.urlopen(request, timeout=12) as resp:
            payload = resp.read()
    except Exception as exc:
        QMessageBox.warning(dlg, "下载失败", "网络不可用或地址失效：%s" % exc)
        dlg.status_label.setText("下载失败")
        return
    temp_dir = os.path.join(PM.plugins_dir(), "_downloads")
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
    suffix = ".zip" if url.lower().endswith(".zip") else ".arcx"
    path = os.path.join(temp_dir, "%s%s" % (item["id"].replace("/", "_"), suffix))
    try:
        with open(path, "wb") as f:
            f.write(payload)
    except Exception as exc:
        QMessageBox.warning(dlg, "保存失败", str(exc))
        return
    ok, msg = PM.install_archive(path, PM.plugins_dir())
    try:
        os.remove(path)
    except Exception:
        pass
    try:
        dlg.plugin_mgr.load_all_plugins()
    except Exception:
        pass
    if ok:
        dlg._reload_page("plugins")
        dlg.status_label.setText(msg)
    else:
        QMessageBox.warning(dlg, "安装失败", msg)
        dlg.status_label.setText("安装失败：" + msg)


def _reload_plugins(dlg):
    try:
        dlg.plugin_mgr.load_all_plugins()
        _rebuild_plugin_nav(dlg)
        dlg._reload_page("plugins")
        dlg.status_label.setText("插件已重新加载，左侧导航已更新")
    except Exception as ex:
        QMessageBox.warning(dlg, "重新加载失败", str(ex))


def _rebuild_plugin_nav(dlg):
    for full, name, pkey, title in list(dlg._plugin_page_defs):
        page = dlg._pages.get(full)
        if page:
            dlg.stack.removeWidget(page)
            page.deleteLater()
        dlg._pages.pop(full, None)
        btn = dlg._nav_index.pop(full, None)
        if btn:
            dlg.nav_layout.removeWidget(btn)
            btn.deleteLater()
            dlg.nav_buttons = [x for x in dlg.nav_buttons if x[2] is not btn]
    dlg._plugin_page_defs = []
    dlg._build_plugin_pages()


def _install_plugin(dlg):
    import plugin_market as PM
    path, _ = QFileDialog.getOpenFileName(
        dlg, "选择插件", "", "插件 (*.arcx *.arcxpkg *.zip);;所有文件 (*.*)"
    )
    if not path:
        return
    try:
        ok, msg = PM.install_archive(path, PM.plugins_dir())
        if ok:
            try:
                dlg.plugin_mgr.install_plugin(path)
            except Exception:
                pass
            dlg.plugin_mgr.load_all_plugins()
            _rebuild_plugin_nav(dlg)
            dlg._reload_page("plugins")
            dlg.status_label.setText(msg)
            QMessageBox.information(dlg, "安装成功", msg + "\n\n请重启软件以完全加载插件。")
        else:
            QMessageBox.warning(dlg, "安装失败", msg)
    except Exception as ex:
        QMessageBox.warning(dlg, "安装失败", str(ex))


def _open_tool(script):
    p = os.path.join(BASE_DIR, script)
    if not os.path.exists(p):
        QMessageBox.warning(None, "未找到", "工具不存在：\n%s" % p)
        return
    try:
        subprocess.Popen([sys.executable, p], cwd=BASE_DIR)
    except Exception as ex:
        QMessageBox.warning(None, "启动失败", str(ex))


def _plugin_logs(dlg):
    if not dlg.plugin_mgr:
        return
    d = QDialog(dlg)
    d.setWindowTitle("插件日志")
    d.resize(720, 520)
    lay = QVBoxLayout(d)
    lay.setContentsMargins(16, 16, 16, 16)
    lay.setSpacing(8)
    top = QHBoxLayout()
    combo = QComboBox()
    combo.addItem("全部插件")
    for p in dlg.plugin_mgr.get_all_plugins():
        combo.addItem(p.get("meta", {}).get("name", "?"))
    top.addWidget(combo)
    top.addStretch()
    refresh = QPushButton("刷新")
    top.addWidget(refresh)
    lay.addLayout(top)
    view = QPlainTextEdit()
    view.setReadOnly(True)
    lay.addWidget(view, 1)

    def load():
        cur = combo.currentText()
        lines = []
        for nm, ctx in getattr(dlg.plugin_mgr, "contexts", {}).items():
            if cur != "全部插件" and nm != cur:
                continue
            try:
                for line in ctx.get_logs(200):
                    lines.append("[%s] %s" % (nm, line))
            except Exception:
                continue
        view.setPlainText("".join(lines) if lines else "暂无日志")
        view.verticalScrollBar().setValue(view.verticalScrollBar().maximum())

    refresh.clicked.connect(load)
    combo.currentIndexChanged.connect(lambda i: load())
    load()
    close = QPushButton("关闭")
    close.clicked.connect(d.close)
    lay.addWidget(close)
    d.exec_()


def _open_plugin_setting(dlg, name):
    for full, pname, pkey, title in dlg._plugin_page_defs:
        if pname == name:
            dlg._show_page(full)
            return
    QMessageBox.information(dlg, "提示", "该插件没有独立设置页，可在插件卡片上直接运行。")


def _run_plugin(dlg, name):
    try:
        result, error = dlg.plugin_mgr.execute_plugin(name, dlg.parent())
        if error:
            QMessageBox.warning(dlg, "插件错误", str(error))
        elif result:
            QMessageBox.information(dlg, "插件完成", str(result))
    except Exception as ex:
        QMessageBox.warning(dlg, "插件错误", str(ex))


def _toggle_plugin(dlg, name):
    p = dlg.plugin_mgr.get_plugin(name)
    if not p:
        return
    try:
        if p.get("enabled", True):
            dlg.plugin_mgr.disable_plugin(name)
        else:
            dlg.plugin_mgr.enable_plugin(name)
        dlg.plugin_mgr._save_plugin_state(name, not p.get("enabled", True))
        _reload_plugins(dlg)
    except Exception as ex:
        QMessageBox.warning(dlg, "切换失败", str(ex))


def _uninstall_plugin(dlg, name):
    r = QMessageBox.question(dlg, "确认卸载", "卸载「%s」？插件数据也会删除。" % name, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if r != QMessageBox.Yes:
        return
    try:
        ok, msg = dlg.plugin_mgr.uninstall_plugin(name)
        _reload_plugins(dlg)
        QMessageBox.information(dlg, "卸载" if ok else "失败", msg)
    except Exception as ex:
        QMessageBox.warning(dlg, "失败", str(ex))


def _page_developer(dlg, host, lay):
    lay.addWidget(section_label("开发者支持"))
    entries = [
        ("插件开发工具", "可视化搭建插件设置页，产出 .arcx / .arcxpkg", "arcx_packager.py"),
        ("插件安装器", "安装带依赖的 .arcxpkg 插件包", "plugin_installer.py"),
        ("可视化页面编辑器", "拖拽模块生成插件页面 JSON", "visual_page_editor.py"),
    ]
    for label, desc, script in entries:
        add_row(lay, label, desc, _button_row([("打开", (lambda s=script: _open_tool(s)), "")]))
    add_row(lay, "插件目录", "查看已安装插件与插件数据（每个插件一个文件夹，内含 settings.json 与日志）",
            _button_row([("打开", lambda: _open_dir(os.path.join(BASE_DIR, "plugins")), "")]))
    add_row(lay, "崩溃报告", "程序异常时生成的报告保存在 crash 目录",
            _button_row([("打开", lambda: _open_dir(os.path.join(BASE_DIR, "crash")), "")]))
    add_row(lay, "配置文件", "直接查看 config.json 的完整结构",
            _button_row([("打开", lambda: _open_file(os.path.join(BASE_DIR, "config.json")), "")]))
    lay.addWidget(section_label("a13rollcall:// 协议"))
    lay.addWidget(_info_block(
        "支持通过浏览器或快捷方式唤起程序：\n"
        "a13rollcall://quick    快速抽取\n"
        "a13rollcall://draw     主界面抽取\n"
        "a13rollcall://settings 打开设置\n"
        "a13rollcall://guide    首次教学浮窗\n"
        "a13rollcall://echo     回声洞\n"
        "a13rollcall://last     载入最后一次抽取结果\n"
        "a13rollcall://about    关于信息"
    ))
    lay.addWidget(section_label("插件能力边界"))
    lay.addWidget(_info_block(
        "可以：加按钮、加独立设置页、读写自己的 JSON、读名单、触发抽取、显示对话框、写日志、注册钩子。\n"
        "不可以：修改主程序内部控件、替换核心抽取算法、访问未公开的内部对象。\n"
        "插件异常会被隔离，不会导致主程序闪退；出错细节写入 plugins/logs 与插件自己的日志。"
    ))


def _page_about(dlg, host, lay):
    md = """# A13 课堂点名系统 V%s

第六代 A13 抽签引擎 · 本地离线 · 零广告 · 零捆绑

## 作者
**a13zhy**

## 项目地址
- GitHub：<https://github.com/a13zhy/a13rollcall>
- 官网：<%s>

## 数据与隐私
所有学生名单、课文、抽取记录、积分、回声内容都保存在本机程序目录，不上传任何服务器。
除手动点击「检查更新」外，程序不发起任何网络请求。

## 许可
仅供教育学习与个人教学使用，禁止倒卖与商业二次封装。二创请标注原作者。

## 版本信息
- 版本号：%s
- 构建：PyQt5
- 配置目录：%s
""" % (VERSION, WEBSITE, VERSION, BASE_DIR)
    view = QTextBrowser()
    view.setOpenExternalLinks(True)
    view.setFrameShape(QFrame.NoFrame)
    view.setMarkdown(md)
    view.setMinimumHeight(560)
    lay.addWidget(view)


class UpdateWorker(threading.Thread):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.daemon = True

    def run(self):
        try:
            req = urllib.request.Request(GITHUB_API, headers={"User-Agent": "A13Rollcall", "Accept": "application/vnd.github.v3+json"})
            data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode("utf-8"))
            self.signal.emit(True, data)
        except Exception as ex:
            self.signal.emit(False, str(ex))


def _page_update(dlg, host, lay):
    lay.addWidget(section_label("版本"))
    add_row(lay, "当前版本", "本地程序版本号", QLabel("V%s" % VERSION))
    add_row(lay, "远程仓库", "GitHub Releases 最新版本", QLabel("a13zhy/a13rollcall"))
    result = QLabel("尚未检查")
    result.setObjectName("setting_desc")
    result.setWordWrap(True)
    holder = QFrame()
    holder.setObjectName("settingcard")
    hl = QVBoxLayout(holder)
    hl.setContentsMargins(16, 14, 16, 14)
    hl.addWidget(result)
    lay.addWidget(holder)

    def show(ok, payload):
        if not ok:
            result.setText("检查失败：%s\n（可能是网络不可用，稍后再试）" % payload)
            return
        tag = payload.get("tag_name") or ""
        body = payload.get("body") or ""
        published = payload.get("published_at") or ""
        author = (payload.get("author") or {}).get("login", "a13zhy")
        nums = re.findall(r"\d+", tag)
        try:
            remote = ".".join(nums[:3]) if nums else tag
        except Exception:
            remote = tag
        try:
            local_nums = [int(x) for x in VERSION.split(".")]
            remote_nums = [int(x) for x in remote.split(".")][:3]
            newer = remote_nums > local_nums
        except Exception:
            newer = True
        head = "发现新版本 V%s（当前 V%s）" % (remote, VERSION) if newer else "已是最新版本（V%s）" % VERSION
        extra = "\n\n作者：%s\n发布：%s\n\n%s" % (author, published, body[:1500]) if body else "\n\n作者：%s\n发布：%s" % (author, published)
        result.setText(head + extra)

    btn_row = _button_row([
        ("检查更新", lambda: _check_update(dlg, show), "primary"),
        ("打开 Releases", lambda: _open_url("https://github.com/a13zhy/a13rollcall/releases"), ""),
        ("前往官网", lambda: _open_url(WEBSITE), ""),
    ])
    add_row(lay, "检查与下载", "从 GitHub 读取最新发布信息（需要联网）", btn_row)
    lay.addWidget(_info_block("检查更新只读取公开的发布信息，不上传任何本地数据。"))


def _check_update(dlg, cb):
    class Sig:
        pass
    from PyQt5.QtCore import QObject
    class Bridge(QObject):
        done = pyqtSignal(bool, object)
    bridge = Bridge()
    bridge.done.connect(cb)
    w = UpdateWorker(bridge.done)
    w.start()


def _open_url(url):
    try:
        from PyQt5.QtGui import QDesktopServices
        from PyQt5.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))
    except Exception:
        pass


def _page_help(dlg, host, lay):
    md = """# 快速上手

## 第一次使用
1. 启动后若进入配置向导，填写班级名称并导入名单（每行一个姓名）。
2. 在「课文」区粘贴课文或导入 texts.txt。
3. 回到主界面，点「新建轮次」开始课堂记录。
4. 点「开始抽取」，姓名滚动后出结果，按 1/2/3 标记背诵状态。

## 轮次是什么
每一轮代表一次完整的课堂抽查。统计、积分、历史都挂在轮次上，切换轮次查看时互不干扰。
没有轮次时抽取按钮会保持在禁用状态，避免记录无处归属。

## 标记错了怎么办
按 Ctrl+Z 撤销，统计面板与积分榜会同步回退；也可以重新标记，以最后一次为准。

## 快捷键
- 空格：开始抽取
- 1 / 2 / 3：已背过 / 未背熟 / 未背过
- Ctrl+Z / Ctrl+Y：撤销 / 重做
- Ctrl+S：保存
- Ctrl+,：打开设置

## 皮肤怎么换
设置 → 皮肤中心。切换皮肤会同时改变配色、圆角、字体、阴影、背景纹理与控件形态；可在下方微调缩放与密度。

## 插件
设置 → 插件中心可安装 .arcx / .arcxpkg；开发者支持页提供打包工具、安装器与协议说明。
"""
    view = QTextBrowser()
    view.setOpenExternalLinks(True)
    view.setFrameShape(QFrame.NoFrame)
    view.setMarkdown(md)
    view.setMinimumHeight(560)
    lay.addWidget(view)


def PAGE_DEFS(dlg):
    return [
        ("class", "系统", "班级与身份", "user", lambda h, l: _page_class(dlg, h, l)),
        ("startup", "系统", "启动与引导", "restart", lambda h, l: _page_startup(dlg, h, l)),
        ("info", "系统", "应用信息", "info", lambda h, l: _page_info(dlg, h, l)),
        ("skin", "外观", "皮肤中心", "skin", lambda h, l: _page_skin(dlg, h, l)),
        ("display", "外观", "显示与布局", "monitor", lambda h, l: _page_display(dlg, h, l)),
        ("font", "外观", "字体", "font", lambda h, l: _page_font(dlg, h, l)),
        ("animation", "外观", "动画与动效", "animation", lambda h, l: _page_animation(dlg, h, l)),
        ("window", "外观", "窗口样式", "window", lambda h, l: _page_window(dlg, h, l)),
        ("mode", "抽取", "抽取模式", "mode", lambda h, l: _page_mode(dlg, h, l)),
        ("rules", "抽取", "抽取规则", "rules", lambda h, l: _page_rules(dlg, h, l)),
        ("params", "抽取", "抽取参数", "sliders", lambda h, l: _page_params(dlg, h, l)),
        ("auto_draw", "抽取", "自动抽取", "auto", lambda h, l: _page_auto_draw(dlg, h, l)),
        ("weight", "抽取", "权重系统", "weight", lambda h, l: _page_weight(dlg, h, l)),
        ("tts", "抽取", "语音朗读", "speaker", lambda h, l: _page_tts(dlg, h, l)),
        ("text_extract", "课文", "课文抽取", "extract", lambda h, l: _page_text_extract(dlg, h, l)),
        ("text_display", "课文", "课文显示", "display", lambda h, l: _page_text_display(dlg, h, l)),
        ("text_progress", "课文", "课文进度", "progress", lambda h, l: _page_text_progress(dlg, h, l)),
        ("mark", "标记", "背诵标记", "mark", lambda h, l: _page_mark(dlg, h, l)),
        ("score", "标记", "积分体系", "score", lambda h, l: _page_score(dlg, h, l)),
        ("shortcuts", "快捷键", "快捷键一览", "keyboard", lambda h, l: _page_shortcuts(dlg, h, l)),
        ("shortcut_settings", "快捷键", "自定义按键", "sliders", lambda h, l: _page_shortcut_settings(dlg, h, l)),
        ("data_mgmt", "数据", "数据与文件", "database", lambda h, l: _page_data_mgmt(dlg, h, l)),
        ("export", "数据", "统计导出", "export", lambda h, l: _page_export(dlg, h, l)),
        ("backup", "数据", "备份恢复", "backup", lambda h, l: _page_backup(dlg, h, l)),
        ("echo", "数据", "回声洞", "echo", lambda h, l: _page_echo(dlg, h, l)),
        ("plugins", "插件", "插件中心", "plugin", lambda h, l: _page_plugins(dlg, h, l)),
        ("developer", "插件", "开发者支持", "developer", lambda h, l: _page_developer(dlg, h, l)),
        ("about", "关于", "关于本软件", "about", lambda h, l: _page_about(dlg, h, l)),
        ("update", "关于", "检查更新", "update", lambda h, l: _page_update(dlg, h, l)),
        ("help", "关于", "帮助与上手", "help", lambda h, l: _page_help(dlg, h, l)),
    ]
