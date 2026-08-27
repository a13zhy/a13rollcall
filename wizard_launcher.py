import os
import sys
import subprocess
import configparser
import tkinter as tk
from tkinter import messagebox
from tkinter import Tk, Frame, Label
from tkinter.font import Font

# ========== 文件名配置区，可根据实际打包名称修改 ==========
APP_EXE = "A13课堂点名系统.exe"
WIZARD_INI = "wizard_record.ini"
STUDENT_FILE = "students.txt"
TEXT_FILE = "texts.txt"
MAIN_PY = "main.py"
# ========================================================

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INI_PATH = os.path.join(BASE_DIR, WIZARD_INI)
STUDENT_PATH = os.path.join(BASE_DIR, STUDENT_FILE)
TEXT_PATH = os.path.join(BASE_DIR, TEXT_FILE)
APP_EXE_PATH = os.path.join(BASE_DIR, APP_EXE)
MAIN_PY_PATH = os.path.join(BASE_DIR, MAIN_PY)

# 配色方案 - 现代蓝白风格
COLORS = {
    "bg": "#f5f7fa",
    "header_bg": "#2563eb",
    "header_bg2": "#1d4ed8",
    "card_bg": "#ffffff",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "text_hint": "#94a3b8",
    "text_light": "#ffffff",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "primary_pressed": "#1e40af",
    "primary_light": "#dbeafe",
    "success": "#10b981",
    "success_hover": "#059669",
    "success_light": "#d1fae5",
    "warning": "#f59e0b",
    "warning_light": "#fef3c7",
    "danger": "#ef4444",
    "danger_light": "#fee2e2",
    "border": "#e2e8f0",
    "step_active": "#2563eb",
    "step_done": "#10b981",
    "step_inactive": "#cbd5e1",
    "btn_secondary": "#f1f5f9",
    "btn_secondary_hover": "#e2e8f0",
    "btn_secondary_text": "#475569",
}


def apply_round_corner(window, radius=16):
    """给Windows窗口设置圆角区域（仅overrideredirect窗口有效）"""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        window.update_idletasks()
        w = window.winfo_width()
        h = window.winfo_height()
        if w <= 1 or h <= 1:
            return
        hrgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w, h, radius * 2, radius * 2)
        ctypes.windll.user32.SetWindowRgn(hwnd, hrgn, True)
    except Exception:
        pass


def check_file_status(filepath):
    """检测文件状态，返回 (是否存在, 是否有内容, 行数)"""
    if not os.path.exists(filepath):
        return False, False, 0
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        return True, len(lines) > 0, len(lines)
    except Exception:
        return True, False, 0


class RoundedButton(tk.Canvas):
    """自定义圆角按钮"""

    def __init__(self, master, text="", width=120, height=38, radius=8,
                 bg=None, hover_bg=None, pressed_bg=None, fg=None, font=None,
                 command=None):
        super().__init__(master, width=width, height=height, bg=master["bg"],
                         highlightthickness=0, bd=0)
        self.master_bg = master["bg"]
        self.text = text
        self.width = width
        self.height = height
        self.radius = radius
        self.command = command
        self.disabled = False
        self.normal_bg = bg or COLORS["primary"]
        self.hover_bg = hover_bg or COLORS["primary_hover"]
        self.pressed_bg = pressed_bg or COLORS["primary_pressed"]
        self.fg = fg or COLORS["text_light"]
        self.font = font or ("微软雅黑", 11, "normal")
        self._draw(self.normal_bg)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, color):
        self.delete("all")
        r = self.radius
        w = self.width
        h = self.height
        self.create_arc((0, 0, 2 * r, 2 * r), start=90, extent=90, fill=color, outline=color)
        self.create_arc((w - 2 * r, 0, w, 2 * r), start=0, extent=90, fill=color, outline=color)
        self.create_arc((0, h - 2 * r, 2 * r, h), start=180, extent=90, fill=color, outline=color)
        self.create_arc((w - 2 * r, h - 2 * r, w, h), start=270, extent=90, fill=color, outline=color)
        self.create_rectangle((r, 0, w - r, h), fill=color, outline=color)
        self.create_rectangle((0, r, w, h - r), fill=color, outline=color)
        self.create_text(w / 2, h / 2, text=self.text, fill=self.fg, font=self.font)

    def _on_enter(self, e):
        if not self.disabled:
            self._draw(self.hover_bg)

    def _on_leave(self, e):
        if not self.disabled:
            self._draw(self.normal_bg)

    def _on_click(self, e):
        if not self.disabled:
            self._draw(self.pressed_bg)

    def _on_release(self, e):
        if not self.disabled:
            self._draw(self.hover_bg)
            if self.command:
                self.command()

    def set_disabled(self, disabled):
        self.disabled = disabled
        if disabled:
            self._draw("#cbd5e1")
        else:
            self._draw(self.normal_bg)

    def set_text(self, text):
        self.text = text
        self._draw(self.normal_bg if not self.disabled else "#cbd5e1")


class StepIndicator(Frame):
    """步骤进度指示器"""

    def __init__(self, master, total_steps, current_step=0):
        super().__init__(master, bg=COLORS["card_bg"])
        self.total_steps = total_steps
        self.current_step = current_step
        self.dots = []
        self.labels = []
        self._build()

    def _build(self):
        container = Frame(self, bg=COLORS["card_bg"])
        container.pack(pady=8)
        for i in range(self.total_steps):
            dot_frame = Frame(container, bg=COLORS["card_bg"])
            dot_frame.pack(side="left", padx=10)
            dot = tk.Canvas(dot_frame, width=28, height=28, bg=COLORS["card_bg"],
                            highlightthickness=0, bd=0)
            dot.pack()
            self.dots.append(dot)
            lbl = Label(dot_frame, text=f"步骤{i + 1}", bg=COLORS["card_bg"],
                       fg=COLORS["text_hint"], font=("微软雅黑", 9))
            lbl.pack(pady=(2, 0))
            self.labels.append(lbl)
            if i < self.total_steps - 1:
                line = Frame(container, bg=COLORS["border"], width=36, height=2)
                line.pack(side="left", pady=(0, 20))
        self._update()

    def _update(self):
        for i in range(self.total_steps):
            dot = self.dots[i]
            dot.delete("all")
            if i < self.current_step:
                color = COLORS["step_done"]
                dot.create_oval(2, 2, 26, 26, fill=color, outline=color)
                dot.create_text(14, 14, text="✓", fill="white", font=("微软雅黑", 10, "bold"))
                self.labels[i].config(fg=COLORS["step_done"])
            elif i == self.current_step:
                color = COLORS["step_active"]
                dot.create_oval(2, 2, 26, 26, fill=color, outline=color)
                dot.create_text(14, 14, text=str(i + 1), fill="white", font=("微软雅黑", 11, "bold"))
                self.labels[i].config(fg=COLORS["step_active"], font=("微软雅黑", 9, "bold"))
            else:
                color = COLORS["step_inactive"]
                dot.create_oval(2, 2, 26, 26, fill=color, outline=color)
                dot.create_text(14, 14, text=str(i + 1), fill="white", font=("微软雅黑", 11, "bold"))
                self.labels[i].config(fg=COLORS["text_hint"])

    def set_step(self, step):
        self.current_step = step
        self._update()


class ModernWizard(Tk):
    def __init__(self):
        super().__init__()
        self.title("课堂点名抽背系统 - 首次使用向导")
        self.geometry("880x980")
        self.minsize(820, 620)
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.overrideredirect(True)

        self.current_page = 0
        self.confirm_edit_done = False

        self.title_font = Font(family="Microsoft YaHei", size=18, weight="bold")
        self.subtitle_font = Font(family="Microsoft YaHei", size=11)
        self.content_font = Font(family="Microsoft YaHei", size=11)
        self.hint_font = Font(family="Microsoft YaHei", size=10)
        self.small_font = Font(family="Microsoft YaHei", size=9)

        self.pages_content = [
            {
                "icon": "👋",
                "title": "欢迎使用 课堂点名抽背系统",
                "subtitle": "专为课堂教学设计的随机点名与背诵抽查工具 · V6.2",
                "text": """本软件用于课堂随机点名、抽查学生背诵，支持名单导入、课文分段抽查、点名记录保存与积分统计。

本向导将带你完成初始配置，只需简单几步即可开始使用：

  ①  了解数据源文件格式
  ②  编辑学生名单与课文库
  ③  熟悉软件主要功能（含快捷抽取模式）
  ④  完成配置，启动软件

📌 核心亮点：
  • 第六代A13智能抽取引擎，支持动态权重
  • 交互式新手引导，手把手教你每个按钮
  • 快捷抽取模式，极简界面一键点名
  • 积分排行榜 + 数据导出，课堂管理更高效
  • 明暗双主题 + 粒子动效，视觉体验出众

点击右下角【下一步】按钮继续，或点击左下角【跳过向导】直接进入软件。""",
                "need_confirm": False,
                "show_skip": True,
            },
            {
                "icon": "📋",
                "title": "数据源文件格式说明",
                "subtitle": "正确的文件格式是软件正常运行的基础",
                "text": """【students.txt 学生名单】
  • 每行写 1 位学生姓名，不要表头
  • 支持带序号格式（如：1 张三），程序会自动去除序号
  • 空行会被自动忽略

  示例：
  张三
  李四
  王五

【texts.txt 课文库】
  • 使用【课文标题】标记新一篇课文，符号必须是中文方括号【】
  • 空行作为段落分隔，两个空行之间的文字算作 1 个段落
  • 连续多行文字会自动合并为同一个段落

  格式样例：
  【岳阳楼记】
      第一段正文……

      第二段正文……
  【醉翁亭记】
      第一段正文……

⚠ 重要提醒（请务必注意）：
  1. 文件必须为 UTF-8 编码的 .txt 文件，禁止使用 Word 文档
  2. 修改完毕务必按 Ctrl+S 保存文件
  3. 保存完成后再回到向导点击【我已编辑完成】
  4. 软件运行中修改txt后，需点击「刷新名单」重载数据

💡 小技巧：可以先用记事本打开样例文件，直接在上面修改，格式不会出错！""",
                "need_confirm": True,
                "show_skip": False,
            },
            {
                "icon": "🔧",
                "title": "软件主要功能介绍",
                "subtitle": "了解核心功能，快速上手课堂点名",
                "text": """🎯 核心功能

  1. 随机点名：点击中间画布或按空格键，启动随机抽取滚动
  2. 状态标记：抽取完成后标记「已背过 / 未背熟 / 未背过」，自动记录积分
  3. 分段抽查：课文库按空行拆分为多个段落，支持随机抽段、顺序推进
  4. 数据统计：自动保存抽查记录，支持积分排行榜和数据导出到桌面
  5. 丰富设置：支持动态权重、明暗主题、快捷键、粒子动效等功能

⚡ 快捷抽取模式（新增！）

  主界面右下角有「⚡ 快捷抽取」按钮，点击后：
  • 隐藏主界面，打开极简抽取窗口
  • 只抽取学生名字，不抽取课文
  • 有独立的设置按钮（置顶/动画/不重复等）
  • 一键「返回主界面」恢复完整功能
  • 记录为临时文件（日期+时间.txt），关闭后自动删除

  ⚠ 注意：快捷抽取的记录不会保存到主程序，关闭即删除，适合临时快速点名！

⌨️ 快捷键

  空格键 — 开始 / 停止抽取
  数字 1  — 标记为「已背过」（+10分）
  数字 2  — 标记为「未背熟」（-5分）
  数字 3  — 标记为「未背过」（-15分）
  R 键    — 重置本轮抽取记录

💡 使用小提示

  • 修改外部 txt 后，需在软件内点击「刷新名单」重载数据
  • 不建议手动修改 records.txt、stats.txt，会破坏统计数据
  • 底部状态栏实时显示名单状态、本轮进度与权重提示
  • 首次进入主界面会有交互式引导，带你熟悉每个按钮
  • 统计数据可一键导出为带时间戳的txt文件，自动保存到桌面""",
                "need_confirm": False,
                "show_skip": False,
            },
            {
                "icon": "✅",
                "title": "向导完成！",
                "subtitle": "配置已就绪，即将启动课堂点名抽背系统",
                "text": """全部引导介绍完毕！

向导记录已写入本地，下次启动将直接进入主程序，不再弹出向导。

你现在可以：

  🚀  点击【完成并启动】按钮，立即开始使用
  📖  首次进入主界面会弹出交互式操作引导，高亮每个按钮
  ⚙️  随时可以在软件内点击「设置」修改各项配置
  🌐  在「设置 → 关于」中可访问产品官网及定制班级专属版本
  ⚡  主界面右下角「快捷抽取」按钮，体验极简点名模式

📌 温馨提示：
  • 如果数据源文件为空或损坏，下次启动会自动重新打开向导
  • 重置数据后，ini标记会被修改，可重新运行向导和界面教学
  • 统计导出文件会自动加上时间戳，并保存到桌面，方便查找

祝你使用愉快，课堂点名高效顺畅！🎓""",
                "need_confirm": False,
                "show_skip": False,
            },
        ]

        self._build_ui()
        self._update_page()
        self._center_window()
        self.after(80, lambda: apply_round_corner(self, 18))

    def _center_window(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # ===== 顶部标题栏 =====
        header = Frame(self, bg=COLORS["header_bg"], height=72)
        header.pack(fill="x")
        header.pack_propagate(False)

        header_inner = Frame(header, bg=COLORS["header_bg"])
        header_inner.pack(fill="both", expand=True, padx=28)

        icon_label = Label(header_inner, text="📚", bg=COLORS["header_bg"],
                           fg="white", font=("微软雅黑", 24))
        icon_label.pack(side="left", padx=(0, 14))

        title_frame = Frame(header_inner, bg=COLORS["header_bg"])
        title_frame.pack(side="left")
        Label(title_frame, text="课堂点名抽背系统", bg=COLORS["header_bg"],
              fg="white", font=("微软雅黑", 16, "bold")).pack(anchor="w")
        Label(title_frame, text="首次使用配置向导", bg=COLORS["header_bg"],
              fg="#bfdbfe", font=("微软雅黑", 10)).pack(anchor="w")

        close_btn = RoundedButton(header_inner, text="✕", width=32, height=32, radius=16,
                                   bg=COLORS["header_bg"], hover_bg="#1e40af",
                                   pressed_bg="#1e3a8a", fg="white",
                                   font=("微软雅黑", 12, "bold"), command=self._on_close)
        close_btn.pack(side="right")

        # ===== 步骤指示器 =====
        step_container = Frame(self, bg=COLORS["card_bg"])
        step_container.pack(fill="x", padx=20, pady=(16, 0))
        self.step_indicator = StepIndicator(step_container, len(self.pages_content), 0)
        self.step_indicator.pack()

        Frame(self, bg=COLORS["border"], height=1).pack(fill="x", padx=40, pady=(8, 0))

        # ===== 内容卡片 =====
        content_wrapper = Frame(self, bg=COLORS["bg"])
        content_wrapper.pack(fill="both", expand=True, padx=20, pady=16)

        shadow = Frame(content_wrapper, bg="#cbd5e1")
        shadow.pack(fill="both", expand=True, padx=4, pady=4)

        self.card = Frame(shadow, bg=COLORS["card_bg"],
                          highlightbackground=COLORS["border"], highlightthickness=1)
        self.card.pack(fill="both", expand=True, padx=(0, 2), pady=(0, 2))

        self.card_inner = Frame(self.card, bg=COLORS["card_bg"])
        self.card_inner.pack(fill="both", expand=True, padx=32, pady=24)

        # 标题区
        title_area = Frame(self.card_inner, bg=COLORS["card_bg"])
        title_area.pack(fill="x")

        self.page_icon = Label(title_area, text="", bg=COLORS["card_bg"],
                               font=("微软雅黑", 28))
        self.page_icon.pack(side="left", padx=(0, 14))

        title_text_frame = Frame(title_area, bg=COLORS["card_bg"])
        title_text_frame.pack(side="left", fill="x", expand=True)
        self.page_title = Label(title_text_frame, text="", bg=COLORS["card_bg"],
                                fg=COLORS["text_primary"], font=self.title_font, anchor="w")
        self.page_title.pack(fill="x")
        self.page_subtitle = Label(title_text_frame, text="", bg=COLORS["card_bg"],
                                    fg=COLORS["text_secondary"], font=self.subtitle_font, anchor="w")
        self.page_subtitle.pack(fill="x", pady=(2, 0))

        Frame(self.card_inner, bg=COLORS["border"], height=1).pack(fill="x", pady=(16, 14))

        # 正文内容区（可滚动）
        self.content_scroll = Frame(self.card_inner, bg=COLORS["card_bg"])
        self.content_scroll.pack(fill="both", expand=True)

        self.content_canvas = tk.Canvas(self.content_scroll, bg=COLORS["card_bg"],
                                         highlightthickness=0, bd=0)
        self.content_scrollbar = tk.Scrollbar(self.content_scroll, orient="vertical",
                                                command=self.content_canvas.yview)
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)
        self.content_canvas.pack(side="left", fill="both", expand=True)
        self.content_scrollbar.pack(side="right", fill="y")

        self.content_frame = Frame(self.content_canvas, bg=COLORS["card_bg"])
        self.content_window = self.content_canvas.create_window((0, 0), window=self.content_frame,
                                                                  anchor="nw")
        self.content_frame.bind("<Configure>", self._on_content_configure)
        self.content_canvas.bind("<Configure>", self._on_canvas_configure)

        self.content_label = Label(self.content_frame, text="", bg=COLORS["card_bg"],
                                   fg=COLORS["text_primary"], font=self.content_font,
                                   justify="left", anchor="nw", wraplength=700)
        self.content_label.pack(fill="both", expand=True, padx=4)

        # 文件操作按钮区
        self.file_btn_frame = Frame(self.card_inner, bg=COLORS["card_bg"])
        self.btn_open_student = RoundedButton(
            self.file_btn_frame, text="📄 打开 students.txt",
            width=180, height=36, radius=8,
            bg="#eff6ff", hover_bg="#dbeafe", pressed_bg="#bfdbfe",
            fg="#1d4ed8", font=("微软雅黑", 10, "bold"),
            command=lambda: open_file_with_notepad(STUDENT_FILE))
        self.btn_open_text = RoundedButton(
            self.file_btn_frame, text="📃 打开 texts.txt（课文）",
            width=200, height=36, radius=8,
            bg="#eff6ff", hover_bg="#dbeafe", pressed_bg="#bfdbfe",
            fg="#1d4ed8", font=("微软雅黑", 10, "bold"),
            command=lambda: open_file_with_notepad(TEXT_FILE))
        self.btn_refresh_status = RoundedButton(
            self.file_btn_frame, text="🔄 刷新检测",
            width=100, height=36, radius=8,
            bg=COLORS["btn_secondary"], hover_bg=COLORS["btn_secondary_hover"],
            pressed_bg="#cbd5e1", fg=COLORS["btn_secondary_text"],
            font=("微软雅黑", 10), command=self._refresh_file_status)

        # 文件状态显示区
        self.status_frame = Frame(self.card_inner, bg=COLORS["card_bg"])
        self.student_status_label = Label(self.status_frame, text="", bg=COLORS["card_bg"],
                                           font=("微软雅黑", 10))
        self.text_status_label = Label(self.status_frame, text="", bg=COLORS["card_bg"],
                                        font=("微软雅黑", 10))

        self.hint_label = Label(
            self.file_btn_frame,
            text="💡 编辑完成后记得按 Ctrl+S 保存，再点击「刷新检测」确认",
            bg=COLORS["card_bg"], fg=COLORS["warning"], font=self.hint_font, anchor="w")

        # ===== 底部按钮栏 =====
        bottom_bar = Frame(self, bg=COLORS["bg"], height=76)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)

        # 进度条
        progress_bg = Frame(bottom_bar, bg=COLORS["border"], height=3)
        progress_bg.pack(fill="x", side="top")
        progress_bg.pack_propagate(False)
        self.progress_fill = Frame(progress_bg, bg=COLORS["primary"], height=3, width=0)
        self.progress_fill.pack(side="left")

        bottom_inner = Frame(bottom_bar, bg=COLORS["bg"])
        bottom_inner.pack(fill="both", expand=True, padx=28)

        self.btn_skip = RoundedButton(
            bottom_inner, text="跳过向导 →", width=110, height=40, radius=8,
            bg=COLORS["bg"], hover_bg=COLORS["btn_secondary"],
            pressed_bg=COLORS["btn_secondary_hover"], fg=COLORS["text_hint"],
            font=("微软雅黑", 10), command=self._skip_wizard)

        self.scroll_hint = Label(bottom_inner, text="⬇  内容较多，鼠标滚轮下滑查看更多  ⬇",
                                  bg=COLORS["bg"], fg="#2563eb", font=("微软雅黑", 10, "bold"))

        self.btn_back = RoundedButton(
            bottom_inner, text="← 上一步", width=110, height=40, radius=8,
            bg=COLORS["btn_secondary"], hover_bg=COLORS["btn_secondary_hover"],
            pressed_bg="#cbd5e1", fg=COLORS["btn_secondary_text"],
            font=("微软雅黑", 11, "bold"), command=self.page_back)
        self.btn_back.pack(side="left", pady=18)

        self.btn_next = RoundedButton(
            bottom_inner, text="下一步 →", width=140, height=40, radius=8,
            bg=COLORS["primary"], hover_bg=COLORS["primary_hover"],
            pressed_bg=COLORS["primary_pressed"], fg="white",
            font=("微软雅黑", 11, "bold"), command=self.page_next)

        self.btn_confirm = RoundedButton(
            bottom_inner, text="✓ 我已编辑完成", width=170, height=40, radius=8,
            bg=COLORS["success"], hover_bg=COLORS["success_hover"],
            pressed_bg="#047857", fg="white",
            font=("微软雅黑", 11, "bold"), command=self.on_confirm_done)

    def _on_content_configure(self, event):
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.content_canvas.itemconfig(self.content_window, width=event.width)

    def _refresh_file_status(self):
        stu_exists, stu_has_content, stu_lines = check_file_status(STUDENT_PATH)
        txt_exists, txt_has_content, txt_lines = check_file_status(TEXT_PATH)

        if stu_has_content:
            self.student_status_label.config(
                text=f"  ✓ students.txt：已就绪（{stu_lines} 行）",
                fg=COLORS["success"])
        else:
            self.student_status_label.config(
                text="  ✗ students.txt：为空或不存在",
                fg=COLORS["danger"])

        if txt_has_content:
            self.text_status_label.config(
                text=f"  ✓ texts.txt：已就绪（{txt_lines} 行）",
                fg=COLORS["success"])
        else:
            self.text_status_label.config(
                text="  ✗ texts.txt：为空或不存在",
                fg=COLORS["danger"])

    def _update_page(self):
        page = self.pages_content[self.current_page]
        self.page_icon.config(text=page["icon"])
        self.page_title.config(text=page["title"])
        self.page_subtitle.config(text=page["subtitle"])
        self.content_label.config(text=page["text"])
        self.confirm_edit_done = False
        self.step_indicator.set_step(self.current_page)

        # 更新进度条
        progress = (self.current_page + 1) / len(self.pages_content) * 100
        self.progress_fill.config(width=int(progress * 8.8))

        # 重置文件按钮区
        self.file_btn_frame.pack_forget()
        self.btn_open_student.pack_forget()
        self.btn_open_text.pack_forget()
        self.btn_refresh_status.pack_forget()
        self.status_frame.pack_forget()
        self.student_status_label.pack_forget()
        self.text_status_label.pack_forget()
        self.hint_label.pack_forget()
        self.btn_confirm.pack_forget()
        self.btn_next.pack_forget()
        self.btn_skip.pack_forget()

        # 上一步按钮
        if self.current_page == 0:
            self.btn_back.set_disabled(True)
        else:
            self.btn_back.set_disabled(False)

        # 跳过按钮（仅第一页显示）
        if page.get("show_skip"):
            self.btn_skip.pack(side="left", pady=18, padx=(16, 0))

        # 下滑提示（中间位置）
        self.scroll_hint.pack(side="left", expand=True, pady=18)

        if page["need_confirm"]:
            self.file_btn_frame.pack(fill="x", pady=(12, 0))
            self.btn_open_student.pack(side="left", padx=(0, 10))
            self.btn_open_text.pack(side="left", padx=(0, 10))
            self.btn_refresh_status.pack(side="left")
            self.hint_label.pack(fill="x", pady=(10, 0))

            # 文件状态
            self.status_frame.pack(fill="x", pady=(8, 0))
            self.student_status_label.pack(anchor="w", pady=1)
            self.text_status_label.pack(anchor="w", pady=1)
            self._refresh_file_status()

            self.btn_confirm.pack(side="right", pady=18)
        else:
            self.btn_next.pack(side="right", pady=18)
            if self.current_page == len(self.pages_content) - 1:
                self.btn_next.set_text("完成并启动 🚀")
            else:
                self.btn_next.set_text("下一步 →")

        self.content_canvas.yview_moveto(0)

    def _skip_wizard(self):
        result = messagebox.askyesno("跳过向导", "确定要跳过向导直接进入软件吗？\n\n建议完成向导以确保数据源配置正确。")
        if result:
            set_wizard_finished()
            self.destroy()
            launch_main_app()
            sys.exit(0)

    def on_confirm_done(self):
        stu_exists, stu_has_content, _ = check_file_status(STUDENT_PATH)
        txt_exists, txt_has_content, _ = check_file_status(TEXT_PATH)
        if not stu_has_content or not txt_has_content:
            result = messagebox.askyesno("文件未就绪",
                                          "检测到学生名单或课文库为空，确定要继续吗？\n\n软件启动后可能无法正常使用点名功能。")
            if not result:
                return
        self.confirm_edit_done = True
        self.page_next()

    def page_next(self):
        if self.current_page < len(self.pages_content) - 1:
            self.current_page += 1
            self._update_page()
        else:
            set_wizard_finished()
            self.destroy()
            launch_main_app()
            sys.exit(0)

    def page_back(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()

    def _on_close(self):
        result = messagebox.askyesno("确认退出", "确定要退出向导吗？\n\n退出后下次启动仍会重新打开向导。")
        if result:
            self.destroy()
            sys.exit(0)


def kill_target_exe():
    try:
        subprocess.run(["taskkill", "/F", "/IM", APP_EXE], shell=True, capture_output=True)
    except Exception:
        pass


def launch_main_app():
    exe_path = os.path.join(BASE_DIR, APP_EXE)
    py_path = os.path.join(BASE_DIR, MAIN_PY)

    if os.path.exists(exe_path):
        subprocess.Popen([exe_path, "--show-tip"], cwd=BASE_DIR)
        return True

    if os.path.exists(py_path):
        subprocess.Popen([sys.executable, py_path, "--show-tip"], cwd=BASE_DIR)
        return True

    messagebox.showerror(
        "启动失败",
        f"找不到主程序文件！\n\n请确保同目录下存在：\n• {APP_EXE}（打包版）\n• 或 {MAIN_PY}（源码版）"
    )
    return False


def is_wizard_finished():
    cfg = configparser.ConfigParser()
    if os.path.exists(INI_PATH):
        try:
            cfg.read(INI_PATH, encoding="utf-8")
            return cfg.getboolean("status", "finished")
        except Exception:
            return False
    return False


def set_wizard_finished():
    cfg = configparser.ConfigParser()
    cfg["status"] = {"finished": "True"}
    try:
        with open(INI_PATH, "w", encoding="utf-8") as f:
            cfg.write(f)
    except Exception as e:
        print(f"写入ini失败: {e}")


def build_sample_files():
    if not os.path.exists(STUDENT_PATH):
        sample_students = """张三
李四
王五
赵六
小明
小红
小华
小刚
小美
小强
"""
        with open(STUDENT_PATH, "w", encoding="utf-8") as f:
            f.write(sample_students)

    if not os.path.exists(TEXT_PATH):
        sample_texts = """【岳阳楼记】
庆历四年春，滕子京谪守巴陵郡。越明年，政通人和，百废具兴。乃重修岳阳楼，增其旧制，刻唐贤今人诗赋于其上。属予作文以记之。

予观夫巴陵胜状，在洞庭一湖。衔远山，吞长江，浩浩汤汤，横无际涯；朝晖夕阴，气象万千。此则岳阳楼之大观也，前人之述备矣。然则北通巫峡，南极潇湘，迁客骚人，多会于此，览物之情，得无异乎？

若夫霪雨霏霏，连月不开，阴风怒号，浊浪排空；日星隐耀，山岳潜形；商旅不行，樯倾楫摧；薄暮冥冥，虎啸猿啼。登斯楼也，则有去国怀乡，忧谗畏讥，满目萧然，感极而悲者矣。

至若春和景明，波澜不惊，上下天光，一碧万顷；沙鸥翔集，锦鳞游泳；岸芷汀兰，郁郁青青。而或长烟一空，皓月千里，浮光跃金，静影沉璧，渔歌互答，此乐何极！登斯楼也，则有心旷神怡，宠辱偕忘，把酒临风，其喜洋洋者矣。

嗟夫！予尝求古仁人之心，或异二者之为，何哉？不以物喜，不以己悲；居庙堂之高则忧其民；处江湖之远则忧其君。是进亦忧，退亦忧。然则何时而乐耶？其必曰"先天下之忧而忧，后天下之乐而乐"乎。噫！微斯人，吾谁与归？

时六年九月十五日。

【醉翁亭记】
环滁皆山也。其西南诸峰，林壑尤美，望之蔚然而深秀者，琅琊也。山行六七里，渐闻水声潺潺而泻出于两峰之间者，酿泉也。峰回路转，有亭翼然临于泉上者，醉翁亭也。作亭者谁？山之僧智仙也。名之者谁？太守自谓也。太守与客来饮于此，饮少辄醉，而年又最高，故自号曰醉翁也。醉翁之意不在酒，在乎山水之间也。山水之乐，得之心而寓之酒也。

若夫日出而林霏开，云归而岩穴暝，晦明变化者，山间之朝暮也。野芳发而幽香，佳木秀而繁阴，风霜高洁，水落而石出者，山间之四时也。朝而往，暮而归，四时之景不同，而乐亦无穷也。

至于负者歌于途，行者休于树，前者呼，后者应，伛偻提携，往来而不绝者，滁人游也。临溪而渔，溪深而鱼肥。酿泉为酒，泉香而酒洌；山肴野蔌，杂然而前陈者，太守宴也。宴酣之乐，非丝非竹，射者中，弈者胜，觥筹交错，起坐而喧哗者，众宾欢也。苍颜白发，颓然乎其间者，太守醉也。

已而夕阳在山，人影散乱，太守归而宾客从也。树林阴翳，鸣声上下，游人去而禽鸟乐也。然而禽鸟知山林之乐，而不知人之乐；人知从太守游而乐，而不知太守之乐其乐也。醉能同其乐，醒能述以文者，太守也。太守谓谁？庐陵欧阳修也。
"""
        with open(TEXT_PATH, "w", encoding="utf-8") as f:
            f.write(sample_texts)


def open_file_with_notepad(filename):
    fullpath = os.path.join(BASE_DIR, filename)
    if os.path.exists(fullpath):
        subprocess.Popen(["notepad.exe", fullpath])
    else:
        messagebox.showerror("错误", f"文件 {filename} 不存在！")


def main():
    os.chdir(BASE_DIR)
    kill_target_exe()

    if is_wizard_finished():
        if launch_main_app():
            sys.exit(0)

    build_sample_files()
    app = ModernWizard()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        root = Tk()
        root.withdraw()
        messagebox.showerror("程序异常", f"向导运行出错：{str(e)}")
        root.destroy()
        sys.exit(1)
