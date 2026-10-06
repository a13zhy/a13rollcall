# -*- coding: utf-8 -*-
import os, sys, zipfile, shutil, traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QLineEdit, QFileDialog, QStackedWidget,
                             QProgressBar, QFrame, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QLinearGradient, QColor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "A13课堂点名系统"
VERSION = "V6.8"
EXE_NAME = "A13课堂点名程序.exe"


def _resource_path(name):
    if getattr(sys, "frozen", False):
        return os.path.join(getattr(sys, "_MEIPASS", BASE_DIR), name)
    return os.path.join(BASE_DIR, name)


PAYLOAD = _resource_path("payload.zip")

SLIDES = [
    {"title": "第六代 A13 抽签引擎", "desc": "会话防重复、动态权重、概率均衡\n把命运交给算法，告别点名偏心"},
    {"title": "大屏课堂适配", "desc": "超大姓名展示、粒子动画、圆角窗口\n支持 3000+ 分辨率班级大屏"},
    {"title": "悬浮快捷抽取", "desc": "上课缩成右上角小浮窗，不挡课件\n一键抽人，快速扫荡全班"},
    {"title": "完整插件生态", "desc": "自研 .arcx 插件格式，支持 UI 注入\n事件总线、HTTP、数据库、自定义快捷键"},
    {"title": "统计与导出", "desc": "按轮次统计背诵进度、权重分布\n一键导出到桌面，纯本地离线运行"},
]


class WelcomeSlide(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._idx = 0
        lay = QVBoxLayout(self)
        lay.setContentsMargins(60, 50, 60, 50)
        lay.setSpacing(18)
        self.logo = QLabel("A13")
        self.logo.setAlignment(Qt.AlignCenter)
        self.logo.setStyleSheet("font-size: 64px; font-weight: 900; color: #0067c0;")
        lay.addWidget(self.logo)
        self.sub = QLabel("课堂点名抽背神器  " + VERSION)
        self.sub.setAlignment(Qt.AlignCenter)
        self.sub.setStyleSheet("font-size: 15px; color: #666;")
        lay.addWidget(self.sub)
        lay.addSpacing(20)
        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 26px; font-weight: 800; color: #1a1a1a;")
        self.desc = QLabel()
        self.desc.setAlignment(Qt.AlignCenter)
        self.desc.setWordWrap(True)
        self.desc.setStyleSheet("font-size: 15px; color: #555; line-height: 160%;")
        lay.addWidget(self.title)
        lay.addWidget(self.desc)
        lay.addStretch()
        self.dots = QHBoxLayout()
        self.dots.setAlignment(Qt.AlignCenter)
        self.dot_labels = []
        for i in range(len(SLIDES)):
            d = QLabel("●")
            d.setStyleSheet("font-size: 14px; color: #cccccc;")
            self.dot_labels.append(d)
            self.dots.addWidget(d)
        lay.addLayout(self.dots)
        self._update_slide()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next)
        self.timer.start(3500)

    def _update_slide(self):
        s = SLIDES[self._idx]
        self.title.setText(s["title"])
        self.desc.setText(s["desc"])
        for i, d in enumerate(self.dot_labels):
            d.setStyleSheet("font-size: 14px; color: #0067c0;" if i == self._idx else "font-size: 14px; color: #cccccc;")

    def _next(self):
        self._idx = (self._idx + 1) % len(SLIDES)
        self._update_slide()


class Installer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} 安装程序")
        self.setWindowIcon(QIcon(_resource_path("app.ico")))
        self.resize(760, 560)
        self.setStyleSheet("QMainWindow{background:#f0f4f9;} QWidget{font-family:'Microsoft YaHei';}")
        self.target = os.path.join(os.path.expanduser("~"), "A13Rollcall")
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self._build_welcome()
        self._build_path()
        self._build_progress()
        self._build_done()
        self.stack.setCurrentIndex(0)

    def _nav(self, back_text, next_text, on_back=None, on_next=None, hide_back=False):
        bar = QHBoxLayout()
        bar.addStretch()
        back = QPushButton(back_text)
        back.setStyleSheet("QPushbutton{background:white;color:#0067c0;border:1px solid #0067c0;border-radius:6px;padding:8px 22px;}")
        back.setMinimumHeight(38)
        if hide_back:
            back.hide()
        else:
            back.clicked.connect(on_back or (lambda: self.stack.setCurrentIndex(self.stack.currentIndex()-1)))
        nxt = QPushButton(next_text)
        nxt.setStyleSheet("QPushButton{background:#0067c0;color:white;border:none;border-radius:6px;padding:8px 26px;font-weight:600;} QPushButton:hover{background:#005a9e;}")
        nxt.setMinimumHeight(38)
        nxt.clicked.connect(on_next)
        bar.addWidget(back)
        bar.addSpacing(10)
        bar.addWidget(nxt)
        return bar, back, nxt

    def _build_welcome(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0,0,0,0)
        lay.addWidget(WelcomeSlide(), 1)
        bar = QHBoxLayout(); bar.addStretch()
        nxt = QPushButton("开始安装"); nxt.setStyleSheet("QPushButton{background:#0067c0;color:white;border:none;border-radius:6px;padding:10px 30px;font-weight:700;font-size:14px;}")
        nxt.clicked.connect(lambda: self.stack.setCurrentIndex(1)); bar.addWidget(nxt)
        row = QWidget(); row.setLayout(bar); row.setStyleSheet("background:#e8eef7;")
        lay.addWidget(row)
        self.stack.addWidget(w)

    def _build_path(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(40,30,40,20); lay.setSpacing(16)
        t = QLabel("选择安装位置"); t.setStyleSheet("font-size:22px;font-weight:800;color:#1a1a1a;"); lay.addWidget(t)
        d = QLabel("建议使用默认路径。安装完成后可从开始菜单和桌面快捷方式启动。"); d.setStyleSheet("color:#666;"); lay.addWidget(d)
        row = QHBoxLayout()
        self.path_edit = QLineEdit(self.target)
        self.path_edit.setStyleSheet("padding:8px;border:1px solid #ccc;border-radius:6px;")
        browse = QPushButton("浏览..."); browse.setStyleSheet("background:#0067c0;color:white;border:none;border-radius:6px;padding:8px 16px;")
        browse.clicked.connect(self._pick_dir)
        row.addWidget(self.path_edit,1); row.addWidget(browse)
        lay.addLayout(row)
        lay.addStretch()
        bar, back, nxt = self._nav("上一步", "开始安装", on_next=self._start)
        nxt.setText("开始安装")
        lay.addLayout(bar)
        self.stack.addWidget(w)

    def _pick_dir(self):
        d = QFileDialog.getExistingDirectory(self, "选择安装目录", self.path_edit.text())
        if d:
            self.path_edit.setText(d)

    def _build_progress(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(40,40,40,20); lay.setSpacing(16)
        t = QLabel("正在安装"); t.setStyleSheet("font-size:22px;font-weight:800;"); lay.addWidget(t)
        self.status = QLabel("准备中..."); self.status.setStyleSheet("color:#666;"); lay.addWidget(self.status)
        self.bar = QProgressBar(); self.bar.setValue(0); self.bar.setTextVisible(True)
        self.bar.setStyleSheet("QProgressBar{border:1px solid #ccc;border-radius:6px;height:22px;background:white;} QProgressBar::chunk{background:#0067c0;border-radius:5px;}")
        lay.addWidget(self.bar)
        lay.addStretch()
        self.stack.addWidget(w)

    def _build_done(self):
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(40,40,40,20); lay.setSpacing(14)
        t = QLabel("安装完成"); t.setStyleSheet("font-size:26px;font-weight:800;color:#107c10;"); t.setAlignment(Qt.AlignCenter)
        lay.addWidget(t)
        d = QLabel(f"{APP_NAME} {VERSION} 已成功安装到你选择的目录。\n首次启动会引导你配置班级名单和课文。")
        d.setAlignment(Qt.AlignCenter); d.setStyleSheet("color:#555;font-size:14px;"); lay.addWidget(d)
        lay.addStretch()
        bar = QHBoxLayout(); bar.addStretch()
        run = QPushButton("立即启动"); run.setStyleSheet("QPushButton{background:#0067c0;color:white;border:none;border-radius:6px;padding:10px 28px;font-weight:700;}")
        run.clicked.connect(self._launch)
        close = QPushButton("退出"); close.setStyleSheet("background:white;color:#333;border:1px solid #ccc;border-radius:6px;padding:10px 24px;")
        close.clicked.connect(self.close)
        bar.addWidget(close); bar.addSpacing(10); bar.addWidget(run)
        lay.addLayout(bar)
        self.stack.addWidget(w)

    def _start(self):
        self.target = self.path_edit.text().strip()
        if not self.target:
            self.target = os.path.join(os.path.expanduser("~"), "A13Rollcall")
        self.target = os.path.abspath(os.path.normpath(self.target))
        self.stack.setCurrentIndex(2)
        QTimer.singleShot(200, self._extract)

    def _safe_extract(self, zf, member, dest):
        name = member.filename.replace("\\", "/")
        while name.startswith("/"):
            name = name[1:]
        parts = [p for p in name.split("/") if p and p not in (".", "..")]
        safe = os.path.join(dest, *parts)
        if not os.path.abspath(safe).startswith(os.path.abspath(dest)):
            raise RuntimeError(f"非法路径：{member.filename}")
        if member.is_dir():
            os.makedirs(safe, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(safe), exist_ok=True)
            with zf.open(member) as src, open(safe, "wb") as out:
                shutil.copyfileobj(src, out)

    def _extract(self):
        try:
            if not os.path.exists(PAYLOAD):
                self.status.setText("错误：找不到 payload.zip")
                return
            os.makedirs(self.target, exist_ok=True)
            with zipfile.ZipFile(PAYLOAD) as zf:
                names = zf.namelist()
                total = len(names)
                for i, name in enumerate(names):
                    self._safe_extract(zf, zf.getinfo(name), self.target)
                    self.bar.setValue(int((i+1)/total*95))
                    self.status.setText(f"正在释放文件：{os.path.basename(name)}")
                    QApplication.processEvents()
            self._create_shortcut()
            self._mark_wizard_pending()
            self.bar.setValue(100)
            self.status.setText("完成！")
            self.stack.setCurrentIndex(3)
        except PermissionError:
            self.status.setText("安装失败：没有该目录的写入权限，请更换安装目录（如 D 盘或桌面）后重试。")
        except Exception as e:
            self.status.setText(f"安装失败：{e}")
            traceback.print_exc()

    def _mark_wizard_pending(self):
        try:
            import configparser
            ini = os.path.join(self.target, "wizard_record.ini")
            cfg = configparser.ConfigParser()
            cfg.read(ini, encoding="utf-8-sig")
            if not cfg.has_section("status"):
                cfg["status"] = {}
            cfg["status"]["finished"] = "False"
            if not cfg.has_section("app"):
                cfg["app"] = {}
            if not cfg.has_option("app", "class_name"):
                cfg["app"]["class_name"] = "A13"
            with open(ini, "w", encoding="utf-8") as f:
                cfg.write(f)
        except Exception:
            pass

    def _create_shortcut(self):
        try:
            exe = os.path.join(self.target, EXE_NAME)
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            lnk = os.path.join(desktop, f"{APP_NAME}.lnk")
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                s = shell.CreateShortCut(lnk)
                s.Targetpath = exe
                s.WorkingDirectory = self.target
                s.IconLocation = exe
                s.save()
            except Exception:
                shutil.copy2(exe, os.path.join(desktop, f"{APP_NAME}.exe"))
        except Exception:
            pass

    def _launch(self):
        try:
            os.startfile(os.path.join(self.target, EXE_NAME))
        except Exception as e:
            self.status.setText(str(e))
        self.close()


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    w = Installer()
    w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
