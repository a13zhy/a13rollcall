import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import os
import sys
import subprocess
import random
import time
import copy
import configparser
from config_manager import ConfigManager
from data_manager import DataManager
from draw_engine import DrawEngine

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WIZARD_EXE = "向导启动器.exe"
WIZARD_PY_CANDIDATES = ["wizard_launcher.py"]
RECORD_FILE = os.path.join(BASE_DIR, "wizard_record.ini")
WEBSITE_URL = "https://dkfile.istester.com/zhysppa13/a13callname.html"


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


def apply_dwm_round_corner(window):
    """通过DWM API给普通窗口（含系统标题栏）设置圆角，Windows 11+有效，Win10自动忽略"""
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()
        # 尝试多种圆角属性值以兼容不同Windows版本
        for attr_id in (33, 34):
            try:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr_id,
                    ctypes.byref(ctypes.c_int(2)), ctypes.sizeof(ctypes.c_int)
                )
            except Exception:
                continue
        # 刷新窗口使圆角生效
        try:
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
        except Exception:
            pass
    except Exception:
        pass

LIGHT_THEME = {
    "bg": "#f0f4f8",
    "card_bg": "#ffffff",
    "card_hover": "#f8fafc",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "text_hint": "#94a3b8",
    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "primary_light": "#dbeafe",
    "primary_super_light": "#eff6ff",
    "danger": "#ef4444",
    "danger_light": "#fee2e2",
    "warning": "#f59e0b",
    "warning_light": "#fef3c7",
    "success": "#10b981",
    "success_light": "#d1fae5",
    "border": "#e2e8f0",
    "border_light": "#f1f5f9",
    "canvas_bg": "#ffffff",
    "sidebar_bg": "#f8fafc",
    "status_bar_bg": "#e2e8f0"
}

DARK_THEME = {
    "bg": "#0f172a",
    "card_bg": "#1e293b",
    "card_hover": "#334155",
    "text_primary": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_hint": "#64748b",
    "primary": "#60a5fa",
    "primary_hover": "#3b82f6",
    "primary_light": "#1e3a8a",
    "primary_super_light": "#172554",
    "danger": "#f87171",
    "danger_light": "#7f1d1d",
    "warning": "#fbbf24",
    "warning_light": "#78350f",
    "success": "#34d399",
    "success_light": "#064e3b",
    "border": "#334155",
    "border_light": "#1e293b",
    "canvas_bg": "#1e293b",
    "sidebar_bg": "#1e293b",
    "status_bar_bg": "#1e293b"
}


def is_wizard_finished():
    cfg = configparser.ConfigParser()
    if os.path.exists(RECORD_FILE):
        try:
            cfg.read(RECORD_FILE, encoding="utf-8")
            return cfg.getboolean("status", "finished")
        except Exception:
            return False
    return False


def set_wizard_unfinished():
    cfg = configparser.ConfigParser()
    cfg["status"] = {"finished": "False"}
    try:
        with open(RECORD_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)
    except Exception:
        pass


def validate_students_file(file_path):
    """校验学生名单文件，返回 (是否有效, 错误信息, 有效学生数)"""
    if not os.path.exists(file_path):
        return False, "学生名单文件不存在", 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return False, "学生名单文件编码错误，请使用 UTF-8 编码", 0
    except Exception as e:
        return False, f"学生名单文件读取失败：{str(e)}", 0

    valid_names = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[0].isdigit():
            name = parts[1].strip()
        else:
            name = line
        if name and not name.isdigit():
            valid_names.append(name)

    if not valid_names:
        return False, "学生名单为空或格式不正确，请每行填写一个学生姓名", 0
    if len(valid_names) < 1:
        return False, "学生名单至少需要 1 名学生", 0
    return True, "", len(valid_names)


def validate_texts_file(file_path):
    """校验课文库文件，返回 (是否有效, 错误信息, 课文篇数, 段落总数)"""
    if not os.path.exists(file_path):
        return False, "课文库文件不存在", 0, 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return False, "课文库文件编码错误，请使用 UTF-8 编码", 0, 0
    except Exception as e:
        return False, f"课文库文件读取失败：{str(e)}", 0, 0

    if not content.strip():
        return False, "课文库文件为空，请添加课文内容", 0, 0

    # 检查是否有【】标题
    import re
    titles = re.findall(r'【([^】]+)】', content)
    if not titles:
        return False, "课文库格式不正确：未找到【课文标题】标记，请使用中文方括号【】标记标题", 0, 0

    # 统计段落数
    text_count = len(titles)
    paragraph_count = 0
    for title in titles:
        # 简单统计：每篇课文至少有内容
        pass
    # 按标题分割，统计每篇的段落
    sections = re.split(r'【[^】]+】', content)
    for section in sections[1:]:  # 跳过第一个（标题前的内容）
        paragraphs = [p.strip() for p in section.split('\n\n') if p.strip()]
        paragraph_count += len(paragraphs)

    if paragraph_count == 0:
        return False, "课文库中没有有效段落内容，请在标题下添加课文正文", text_count, 0

    return True, "", text_count, paragraph_count

def launch_wizard_and_exit(reason=""):
    wizard_path = None
    launch_args = None

    exe_path = os.path.join(BASE_DIR, WIZARD_EXE)
    if os.path.exists(exe_path):
        wizard_path = exe_path
        launch_args = [exe_path]

    if not wizard_path:
        for py_name in WIZARD_PY_CANDIDATES:
            py_path = os.path.join(BASE_DIR, py_name)
            if os.path.exists(py_path):
                wizard_path = py_path
                launch_args = [sys.executable, py_path]
                break

    if not wizard_path:
        root = tk.Tk()
        root.withdraw()
        msg = f"找不到配置向导程序！\n\n请确保同目录下存在：\n• {WIZARD_EXE}（打包版）\n• 或 {WIZARD_PY_CANDIDATES[0]}（源码版）"
        if reason:
            msg = f"检测到数据源问题：{reason}\n\n" + msg
        messagebox.showerror("启动错误", msg)
        root.destroy()
        sys.exit(1)

    try:
        subprocess.Popen(launch_args, cwd=BASE_DIR)
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动失败", f"无法启动配置向导：{str(e)}")
        root.destroy()
        sys.exit(1)

    sys.exit(0)

class RoundedButton(tk.Canvas):
    def __init__(self, master, text="", bg=None, hover_bg=None, fg=None,
                 width=100, height=32, radius=8, style="default", command=None,
                 font=None, icon=None, **kwargs):
        bg = bg or master["bg"]
        super().__init__(master, width=width, height=height, bg=master["bg"],
                         highlightthickness=0, bd=0, **kwargs)
        self.master_bg = master["bg"]
        self.text = text
        self.icon = icon
        self.width = width
        self.height = height
        self.radius = radius
        self.command = command
        self.disabled = False
        self.font = font or ("微软雅黑", 10, "normal")
        if style == "primary":
            self.normal_bg = "#3b82f6"
            self.hover_bg = "#2563eb"
            self.pressed_bg = "#1d4ed8"
            self.fg = "#ffffff"
        elif style == "danger":
            self.normal_bg = "#ef4444"
            self.hover_bg = "#dc2626"
            self.pressed_bg = "#b91c1c"
            self.fg = "#ffffff"
        elif style == "success":
            self.normal_bg = "#10b981"
            self.hover_bg = "#059669"
            self.pressed_bg = "#047857"
            self.fg = "#ffffff"
        elif style == "warning":
            self.normal_bg = "#f59e0b"
            self.hover_bg = "#d97706"
            self.pressed_bg = "#b45309"
            self.fg = "#ffffff"
        elif style == "ghost":
            self.normal_bg = "transparent"
            self.hover_bg = "#f1f5f9"
            self.pressed_bg = "#e2e8f0"
            self.fg = "#475569"
        else:
            self.normal_bg = bg or "#ffffff"
            self.hover_bg = hover_bg or "#f1f5f9"
            self.pressed_bg = "#e2e8f0"
            self.fg = fg or "#1e293b"
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
        if color == "transparent":
            color = self.master_bg
        self.create_arc((0, 0, 2*r, 2*r), start=90, extent=90, fill=color, outline=color)
        self.create_arc((w-2*r, 0, w, 2*r), start=0, extent=90, fill=color, outline=color)
        self.create_arc((0, h-2*r, 2*r, h), start=180, extent=90, fill=color, outline=color)
        self.create_arc((w-2*r, h-2*r, w, h), start=270, extent=90, fill=color, outline=color)
        self.create_rectangle((r, 0, w-r, h), fill=color, outline=color)
        self.create_rectangle((0, r, w, h-r), fill=color, outline=color)
        if self.icon:
            display_text = f"{self.icon}  {self.text}" if self.text else self.icon
        else:
            display_text = self.text
        self.create_text(w/2, h/2, text=display_text, fill=self.fg, font=self.font)

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
        if self.disabled:
            self._draw("#cbd5e1")
        else:
            self._draw(self.normal_bg)


class ToggleSwitch(tk.Canvas):
    def __init__(self, master, variable=None, on_color="#2563eb", off_color="#cbd5e1",
                 width=52, height=28, command=None):
        super().__init__(master, width=width, height=height, bg=master["bg"],
                         highlightthickness=0, bd=0)
        self.variable = variable or tk.BooleanVar(value=False)
        self.on_color = on_color
        self.off_color = off_color
        self.sw = width
        self.sh = height
        self.command = command
        self._draw()
        self.bind("<Button-1>", self._toggle)

    def _draw(self):
        self.delete("all")
        r = self.sh // 2
        on = self.variable.get()
        bg_color = self.on_color if on else self.off_color
        self.create_oval(0, 0, self.sh, self.sh, fill=bg_color, outline=bg_color)
        self.create_oval(self.sw - self.sh, 0, self.sw, self.sh, fill=bg_color, outline=bg_color)
        self.create_rectangle(r, 0, self.sw - r, self.sh, fill=bg_color, outline=bg_color)
        knob_r = self.sh // 2 - 3
        if on:
            kx = self.sw - knob_r - 3
        else:
            kx = knob_r + 3
        ky = self.sh // 2
        self.create_oval(kx - knob_r, ky - knob_r, kx + knob_r, ky + knob_r,
                         fill="white", outline="white")

    def _toggle(self, e=None):
        self.variable.set(not self.variable.get())
        self._draw()
        if self.command:
            self.command()

    def get(self):
        return self.variable.get()

    def set(self, value):
        self.variable.set(bool(value))
        self._draw()


class SpotlightGuide:
    def __init__(self, master, theme, steps, on_finish=None):
        self.master = master
        self.theme = theme
        self.steps = steps
        self.current = 0
        self.on_finish = on_finish
        self.tip_card = None
        self.master.after(200, self._show_step)

    def _get_widget_geometry(self, widget):
        try:
            widget.update_idletasks()
            x = widget.winfo_rootx()
            y = widget.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            if w <= 1 or h <= 1:
                return None
            return (x, y, w, h)
        except Exception:
            return None

    def _clear(self):
        if self.tip_card:
            try:
                self.tip_card.destroy()
            except Exception:
                pass
            self.tip_card = None

    def _show_step(self):
        self._clear()
        if self.current >= len(self.steps):
            self._finish()
            return
        step = self.steps[self.current]
        target_widget = step.get("widget")
        geo = None
        if target_widget is not None:
            geo = self._get_widget_geometry(target_widget)
        self._create_tip_card(geo, step)

    def _create_tip_card(self, geo, step):
        title = step.get("title", "")
        text = step.get("text", "")
        cards = step.get("cards", [])
        highlight = step.get("highlight", "")
        tip = tk.Toplevel(self.master)
        tip.overrideredirect(True)
        tip.attributes("-topmost", True)
        tip.config(bg="#1d4ed8")
        tip_width = 480
        tip_height = 620
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        if geo:
            gx, gy, gw, gh = geo
            tx = gx + gw + 20
            ty = gy - 40
            if tx + tip_width > sw - 10:
                tx = gx - tip_width - 20
            if tx < 10:
                tx = 10
            if ty < 10:
                ty = 10
            if ty + tip_height > sh - 10:
                ty = sh - tip_height - 10
        else:
            tx = (sw - tip_width) // 2
            ty = (sh - tip_height) // 2
        tip.geometry(f"{tip_width}x{tip_height}+{tx}+{ty}")
        tip.minsize(tip_width, 480)

        header = tk.Frame(tip, bg="#2563eb", height=56)
        header.pack(fill="x", padx=2, pady=(2, 0))
        header.pack_propagate(False)
        tk.Label(header, text=f"第 {self.current + 1} / {len(self.steps)} 步",
                bg="#2563eb", fg="#93c5fd",
                font=("微软雅黑", 9, "bold")).pack(side="left", padx=(20, 0))
        tk.Label(header, text=title, bg="#2563eb", fg="white",
                font=("微软雅黑", 16, "bold")).pack(side="left", padx=(12, 0))
        close_btn = tk.Button(header, text="✕", bg="#2563eb", fg="white",
                              activebackground="#dc2626", activeforeground="white",
                              bd=0, font=("微软雅黑", 13, "bold"), cursor="hand2",
                              padx=10, pady=4, command=self._finish)
        close_btn.pack(side="right", padx=(0, 8))

        btn_frame = tk.Frame(tip, bg="#f1f5f9")
        btn_frame.pack(fill="x", side="bottom", padx=2, pady=(0, 2))
        btn_inner = tk.Frame(btn_frame, bg="#f1f5f9")
        btn_inner.pack(fill="x", padx=20, pady=12)
        tk.Button(btn_inner, text="跳过引导", bg="#f1f5f9",
                  fg="#64748b", activebackground="#e2e8f0",
                  activeforeground="#475569", bd=0, font=("微软雅黑", 10),
                  cursor="hand2", padx=10, pady=6, command=self._finish).pack(side="left")
        nav_frame = tk.Frame(btn_inner, bg="#f1f5f9")
        nav_frame.pack(side="right")
        if self.current > 0:
            tk.Button(nav_frame, text="← 上一步", bg="#e2e8f0",
                     fg="#334155", activebackground="#cbd5e1",
                     activeforeground="#1e293b", bd=0, font=("微软雅黑", 10),
                     cursor="hand2", padx=16, pady=6, command=self._prev).pack(side="left", padx=5)
        if self.current < len(self.steps) - 1:
            tk.Button(nav_frame, text="下一步 →", bg="#2563eb",
                     fg="white", activebackground="#1d4ed8",
                     activeforeground="white", bd=0, font=("微软雅黑", 10, "bold"),
                     cursor="hand2", padx=18, pady=6, command=self._next).pack(side="left", padx=5)
        else:
            tk.Button(nav_frame, text="✓ 完成", bg="#10b981",
                     fg="white", activebackground="#059669",
                     activeforeground="white", bd=0, font=("微软雅黑", 11, "bold"),
                     cursor="hand2", padx=24, pady=7, command=self._finish).pack(side="left", padx=5)

        content_frame = tk.Frame(tip, bg="#f8fafc")
        content_frame.pack(fill="both", expand=True, padx=2, pady=0)

        inner_content = tk.Frame(content_frame, bg="#f8fafc")
        inner_content.pack(fill="both", expand=True, padx=20, pady=16)

        if text:
            tk.Label(inner_content, text=text, bg="#f8fafc",
                    fg="#1e293b", font=("微软雅黑", 11),
                    wraplength=tip_width - 60, justify="left").pack(anchor="w", pady=(0, 12))

        if highlight:
            hl_frame = tk.Frame(inner_content, bg="#fef3c7", bd=0)
            hl_frame.pack(fill="x", pady=(0, 12))
            tk.Label(hl_frame, text="💡 " + highlight, bg="#fef3c7", fg="#92400e",
                    font=("微软雅黑", 10, "bold"), wraplength=tip_width - 76,
                    justify="left").pack(padx=14, pady=10, anchor="w")

        for card in cards:
            card_frame = tk.Frame(inner_content, bg="#e2e8f0", bd=0)
            card_frame.pack(fill="x", pady=5)
            inner = tk.Frame(card_frame, bg="white")
            inner.pack(fill="x", padx=1, pady=1)
            if card.get("title"):
                tk.Label(inner, text=card["title"], bg="white",
                        fg="#2563eb", font=("微软雅黑", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 4))
            if card.get("content"):
                tk.Label(inner, text=card["content"], bg="white",
                        fg="#64748b", font=("微软雅黑", 10),
                        wraplength=tip_width - 84, justify="left").pack(anchor="w", padx=14, pady=(0, 10))

        self.tip_card = tip
        tip.update()
        tip.update_idletasks()

    def _next(self):
        step = self.steps[self.current]
        check = step.get("check")
        if check and not check():
            msg = step.get("check_msg", "请先完成当前步骤的操作后再继续")
            try:
                from tkinter import messagebox
                messagebox.showinfo("操作提示", msg)
            except Exception:
                pass
            return
        self.current += 1
        self._show_step()

    def _prev(self):
        if self.current > 0:
            self.current -= 1
            self._show_step()

    def _finish(self):
        self._clear()
        if self.on_finish:
            self.on_finish()


class Card(tk.Frame):
    def __init__(self, master, theme, padding=12, **kwargs):
        super().__init__(master, bg=theme["card_bg"], bd=0, highlightthickness=0, **kwargs)
        self.theme = theme
        self.padding = padding
        self.inner = tk.Frame(self, bg=theme["card_bg"])
        self.inner.pack(fill="both", expand=True, padx=padding, pady=padding)


class SettingItem(tk.Frame):
    def __init__(self, master, theme, label, hint="", **kwargs):
        super().__init__(master, bg=theme["card_bg"], **kwargs)
        self.theme = theme
        tk.Label(self, text=label, bg=theme["card_bg"], fg=theme["text_primary"],
                font=("微软雅黑", 11)).pack(anchor="w")
        if hint:
            tk.Label(self, text=hint, bg=theme["card_bg"], fg=theme["text_hint"],
                    font=("微软雅黑", 9)).pack(anchor="w", pady=(2, 0))


class ScrollableFrame(tk.Frame):
    def __init__(self, master, theme, **kwargs):
        super().__init__(master, bg=theme["bg"], **kwargs)
        self.theme = theme
        self.canvas = tk.Canvas(self, bg=theme["bg"], highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=theme["bg"])
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")


class ParticleSystem:
    def __init__(self, canvas, theme, count=30):
        self.canvas = canvas
        self.theme = theme
        self.count = count
        self.particles = []
        self.active = False
        self.speed = 2

    def start(self):
        self.active = True
        self.particles = []
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1: w = 800
        if h <= 1: h = 500
        for _ in range(self.count // 2):
            self.particles.append(self._create_particle(50, h - 50, -1, -1))
        for _ in range(self.count // 2):
            self.particles.append(self._create_particle(w - 50, 50, 1, 1))
        self._update()

    def _create_particle(self, x, y, dx_dir, dy_dir):
        return {
            "x": x + random.randint(-30, 30),
            "y": y + random.randint(-30, 30),
            "dx": random.uniform(0.5, 2) * dx_dir * self.speed,
            "dy": random.uniform(0.5, 2) * dy_dir * self.speed,
            "size": random.randint(2, 6),
            "alpha": random.uniform(0.3, 0.8),
            "id": None
        }

    def _update(self):
        if not self.active:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        for p in self.particles:
            if p["id"]:
                self.canvas.delete(p["id"])
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            p["alpha"] -= 0.005
            if p["alpha"] <= 0 or p["x"] < 0 or p["x"] > w or p["y"] < 0 or p["y"] > h:
                if p["dx"] < 0:
                    p["x"] = 50 + random.randint(-30, 30)
                    p["y"] = h - 50 + random.randint(-30, 30)
                else:
                    p["x"] = w - 50 + random.randint(-30, 30)
                    p["y"] = 50 + random.randint(-30, 30)
                p["alpha"] = random.uniform(0.3, 0.8)
            color = self._hex_with_alpha(self.theme["primary"], p["alpha"])
            p["id"] = self.canvas.create_oval(
                p["x"] - p["size"], p["y"] - p["size"],
                p["x"] + p["size"], p["y"] + p["size"],
                fill=color, outline=color
            )
        self.canvas.after(30, self._update)

    def stop(self):
        self.active = False
        for p in self.particles:
            if p["id"]:
                self.canvas.delete(p["id"])
        self.particles = []

    def _hex_with_alpha(self, hex_color, alpha):
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'#{int(r):02x}{int(g):02x}{int(b):02x}'


class DrawCanvas(tk.Canvas):
    def __init__(self, master, theme, **kwargs):
        super().__init__(master, bg=theme["canvas_bg"], highlightthickness=0, bd=0, **kwargs)
        self.theme = theme
        self.current_text = "点击开始抽取"
        self.name_size = 50
        self.particles = ParticleSystem(self, theme, count=30)
        self.bind("<Configure>", lambda e: self._redraw())

    def set_name_size(self, size):
        self.name_size = size
        self._redraw()

    def update_name(self, name):
        self.current_text = name
        self._redraw()

    def reset(self):
        self.current_text = "点击开始抽取"
        self.particles.stop()
        self._redraw()

    def start_particles(self):
        self.particles.start()

    def stop_particles(self):
        self.particles.stop()

    def _redraw(self):
        self.delete("text_layer")
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1: w = 600
        if h <= 1: h = 280
        self.create_text(w/2, h/2, text=self.current_text,
                        fill=self.theme["text_primary"],
                        font=("微软雅黑", self.name_size, "bold"),
                        tags="text_layer")

    def set_theme(self, theme):
        self.theme = theme
        self.config(bg=theme["canvas_bg"])
        self.particles.theme = theme
        self._redraw()


class SplashScreen(tk.Toplevel):
    def __init__(self, master, theme, duration=2500):
        super().__init__(master)
        self.theme = theme
        self.duration = duration
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.0)
        w, h = 560, 400
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.config(bg="#0f172a")

        main = tk.Frame(self, bg="#0f172a")
        main.pack(fill="both", expand=True, padx=2, pady=2)

        tk.Frame(main, bg="#2563eb", height=3).pack(fill="x")

        logo_frame = tk.Frame(main, bg="#0f172a")
        logo_frame.pack(pady=(40, 16))
        logo_bg = tk.Frame(logo_frame, bg="#1e40af", width=80, height=80)
        logo_bg.pack()
        logo_bg.pack_propagate(False)
        tk.Label(logo_bg, text="📚", bg="#1e40af", fg="white",
                font=("微软雅黑", 36)).pack(expand=True)

        tk.Label(main, text="A13 课堂背诵点名系统", font=("微软雅黑", 20, "bold"),
                bg="#0f172a", fg="white").pack()
        tk.Label(main, text="V6.2  ·  第六代A13智能抽取引擎", font=("微软雅黑", 10),
                bg="#0f172a", fg="#64748b").pack(pady=(4, 0))

        self.loading_frame = tk.Frame(main, bg="#0f172a")
        self.loading_frame.pack(pady=(24, 8))
        self.dot_labels = []
        for i in range(3):
            dot = tk.Label(self.loading_frame, text="●", bg="#0f172a",
                           fg="#3b82f6", font=("微软雅黑", 14))
            dot.pack(side="left", padx=4)
            self.dot_labels.append(dot)
        self._dot_index = 0
        self._animate_dots()

        progress_wrap = tk.Frame(main, bg="#1e293b", width=360, height=6)
        progress_wrap.pack(pady=(16, 8))
        progress_wrap.pack_propagate(False)
        self.progress_bar = tk.Frame(progress_wrap, bg="#3b82f6", width=0, height=6)
        self.progress_bar.pack(side="left")

        self.status_label = tk.Label(main, text="正在初始化...",
                                    font=("微软雅黑", 10),
                                    bg="#0f172a", fg="#94a3b8")
        self.status_label.pack()

        tk.Label(main, text="© 2026 A13 Classroom  ·   Powered by A13 Engine v6.2",
                bg="#0f172a", fg="#475569", font=("微软雅黑", 8)).pack(side="bottom", pady=12)

        self.update()
        self._fade_in()
        self.after(150, self._start_progress)
        self.after(100, lambda: apply_round_corner(self, 16))

    def _animate_dots(self):
        colors = ["#3b82f6", "#60a5fa", "#93c5fd"]
        for i, dot in enumerate(self.dot_labels):
            idx = (i + self._dot_index) % 3
            dot.config(fg=colors[idx])
        self._dot_index = (self._dot_index + 1) % 3
        self.after(300, self._animate_dots)

    def _fade_in(self):
        alpha = self.attributes("-alpha")
        if alpha < 1.0:
            self.attributes("-alpha", min(alpha + 0.05, 1.0))
            self.after(20, self._fade_in)

    def _start_progress(self):
        self._progress = 0
        self._update_progress()

    def _update_progress(self):
        if self._progress < 100:
            self._progress += 2
            self.progress_bar.config(width=3.6 * self._progress)
            self.after(self.duration // 50, self._update_progress)

    def set_status(self, text):
        self.status_label.config(text=text)
        self.update()

    def show_launch_choices(self, on_main=None, on_quick=None, config_mgr=None):
        self._on_main = on_main
        self._on_quick = on_quick
        self._config_mgr = config_mgr
        self._countdown_active = False
        self._countdown_value = 3
        for dot in self.dot_labels:
            dot.config(fg="#1e293b")
        self.loading_frame.pack_forget()
        self.progress_bar.master.pack_forget()
        self.status_label.config(text="加载完成，请选择启动模式")
        self.choice_frame = tk.Frame(self, bg="#0f172a")
        self.choice_frame.pack(pady=(16, 8))
        btn_container = tk.Frame(self.choice_frame, bg="#0f172a")
        btn_container.pack()
        self.main_btn = tk.Button(btn_container, text="🚀 启动主界面", bg="#2563eb", fg="white",
                                   activebackground="#1d4ed8", activeforeground="white",
                                   bd=0, font=("微软雅黑", 13, "bold"), cursor="hand2",
                                   padx=28, pady=12, command=self._launch_main)
        self.main_btn.pack(side="left", padx=8)
        self.quick_btn = tk.Button(btn_container, text="⚡ 快速抽取", bg="#f59e0b", fg="white",
                                    activebackground="#d97706", activeforeground="white",
                                    bd=0, font=("微软雅黑", 13, "bold"), cursor="hand2",
                                    padx=28, pady=12, command=self._launch_quick)
        self.quick_btn.pack(side="left", padx=8)
        self.remember_var = tk.BooleanVar(value=False)
        remember_frame = tk.Frame(self.choice_frame, bg="#0f172a")
        remember_frame.pack(pady=(12, 0))
        self.remember_check = tk.Checkbutton(remember_frame, text="总是保持此选择", variable=self.remember_var,
                                              bg="#0f172a", fg="#94a3b8", selectcolor="#1e293b",
                                              activebackground="#0f172a", activeforeground="#94a3b8",
                                              font=("微软雅黑", 10), cursor="hand2")
        self.remember_check.pack()
        self.countdown_label = tk.Label(self.choice_frame, text="", bg="#0f172a", fg="#f59e0b",
                                         font=("微软雅黑", 11, "bold"))
        self.countdown_label.pack(pady=(8, 0))
        for w in (self, self.main_btn, self.quick_btn, self.remember_check):
            w.bind("<Button-1>", self._stop_countdown, add="+")
            w.bind("<Key>", self._stop_countdown, add="+")
            w.bind("<Motion>", self._stop_countdown, add="+")
        saved_mode = config_mgr.get("startup", "default_mode") if config_mgr else None
        if saved_mode in ("main", "quick"):
            self.remember_var.set(True)
            self._start_countdown(saved_mode)

    def _start_countdown(self, mode):
        self._countdown_mode = mode
        self._countdown_value = 3
        self._countdown_active = True
        label = "主界面" if mode == "main" else "快速抽取"
        self.countdown_label.config(text=f"{self._countdown_value} 秒后自动打开{label}（移动鼠标或点击取消）")
        self._tick_countdown()

    def _tick_countdown(self):
        if not self._countdown_active:
            return
        self._countdown_value -= 1
        if self._countdown_value <= 0:
            self._countdown_active = False
            if self._countdown_mode == "main":
                self._launch_main()
            else:
                self._launch_quick()
            return
        label = "主界面" if self._countdown_mode == "main" else "快速抽取"
        self.countdown_label.config(text=f"{self._countdown_value} 秒后自动打开{label}（移动鼠标或点击取消）")
        self.after(1000, self._tick_countdown)

    def _stop_countdown(self, event=None):
        if self._countdown_active:
            self._countdown_active = False
            self.countdown_label.config(text="")

    def _launch_main(self):
        self._stop_countdown()
        if self.remember_var.get() and self._config_mgr:
            self._config_mgr.set("main", "startup", "default_mode")
            self._config_mgr.save_config()
        self.close(self._on_main)

    def _launch_quick(self):
        self._stop_countdown()
        if self.remember_var.get() and self._config_mgr:
            self._config_mgr.set("quick", "startup", "default_mode")
            self._config_mgr.save_config()
        self.close(self._on_quick)

    def close(self, callback=None):
        self._fade_out(callback)

    def _fade_out(self, callback=None):
        alpha = self.attributes("-alpha")
        if alpha > 0:
            self.attributes("-alpha", max(alpha - 0.06, 0))
            self.after(20, lambda: self._fade_out(callback))
        else:
            self.destroy()
            if callback:
                callback()


def _center_window(win):
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"+{x}+{y}")


class DrawnHistoryWindow(tk.Toplevel):
    def __init__(self, master, draw_engine, theme):
        super().__init__(master)
        self.draw_engine = draw_engine
        self.theme = theme
        self.overrideredirect(True)
        self.geometry("500x540")
        self.minsize(440, 440)
        self.config(bg=theme["bg"])
        outer = tk.Frame(self, bg=theme["card_bg"], highlightbackground=theme["border"],
                         highlightthickness=1)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=theme["primary"], height=46)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="📋", bg=theme["primary"], fg="white",
                font=("微软雅黑", 14)).pack(side="left", padx=(16, 6))
        tk.Label(header, text="本轮抽取记录", bg=theme["primary"], fg="white",
                font=("微软雅黑", 13, "bold")).pack(side="left")
        RoundedButton(header, text="×", bg=theme["primary"], hover_bg=theme["primary_hover"],
                     fg="white", width=32, height=32, radius=16,
                     font=("微软雅黑", 12, "bold"), command=self.destroy).pack(side="right", padx=12, pady=7)
        content = tk.Frame(outer, bg=theme["card_bg"])
        content.pack(fill="both", expand=True, padx=16, pady=16)
        columns = ("index", "name", "time", "status")
        self.tree = ttk.Treeview(content, columns=columns, show="headings", height=16)
        self.tree.heading("index", text="序号")
        self.tree.heading("name", text="学生姓名")
        self.tree.heading("time", text="抽取时间")
        self.tree.heading("status", text="状态")
        self.tree.column("index", width=60, anchor="center")
        self.tree.column("name", width=160, anchor="center")
        self.tree.column("time", width=120, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.empty_label = tk.Label(content, text="暂无抽取记录\n点击画布开始抽取",
                                    bg=theme["card_bg"], fg=theme["text_hint"],
                                    font=("微软雅黑", 12), justify="center")
        self._populate()
        _center_window(self)
        self.after(60, lambda: apply_round_corner(self, 14))

    def _populate(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        records = self.draw_engine.drawn_history
        if not records:
            self.tree.pack_forget()
            self.empty_label.pack(expand=True)
            return
        self.empty_label.pack_forget()
        self.tree.pack(side="left", fill="both", expand=True)
        for i, record in enumerate(records, 1):
            self.tree.insert("", "end", values=(i, record["name"], record["time"], record["status"]))


class InternalTextEditor(tk.Toplevel):
    def __init__(self, master, theme, file_path):
        super().__init__(master)
        self.master_win = master
        self.theme = theme
        self.file_path = file_path
        filename = os.path.basename(file_path)
        self.overrideredirect(True)
        self.geometry("800x600")
        self.minsize(600, 450)
        self.config(bg=theme["bg"])
        header = tk.Frame(self, bg=theme["primary"], height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"编辑 - {filename}", bg=theme["primary"], fg="white",
                font=("微软雅黑", 12, "bold")).pack(side="left", padx=15)
        RoundedButton(header, text="×", bg=theme["primary"], hover_bg=theme["primary_hover"],
                     fg="white", width=30, height=30, radius=15,
                     command=self.on_cancel).pack(side="right", padx=10, pady=5)
        self.original_content, error = self._read_file()
        if error:
            CustomMessageBox(self, self.theme, "错误", error, "error")
            self.destroy()
            return
        if len(self.original_content) > 30000:
            CustomMessageBox(self, self.theme, "提示", "文件内容较大，内置编辑器可能卡顿，建议使用外部编辑器", "warning")
        if filename in ("records.txt", "stats.txt"):
            warn_frame = tk.Frame(self, bg=theme["danger_light"])
            warn_frame.pack(fill="x", padx=15, pady=(15, 0))
            tk.Label(warn_frame, text="⚠ 警告：此文件由程序自动维护，手动修改可能破坏统计数据与抽查记录，修改风险自负",
                    fg=theme["danger"], bg=theme["danger_light"],
                    font=("微软雅黑", 10)).pack(padx=12, pady=8)
        toolbar = tk.Frame(self, bg=theme["card_bg"])
        toolbar.pack(fill="x", padx=15, pady=(10, 0))
        RoundedButton(toolbar, text="保存", style="primary", width=90, height=32,
                     command=self.on_save).pack(side="right", padx=4, pady=8)
        RoundedButton(toolbar, text="重载原始", style="ghost", width=90, height=32,
                     command=self.on_revert_original).pack(side="right", padx=4, pady=8)
        RoundedButton(toolbar, text="取消", style="ghost", width=90, height=32,
                     command=self.on_cancel).pack(side="right", padx=4, pady=8)
        tk.Label(toolbar, text=filename, bg=theme["card_bg"],
                fg=theme["text_secondary"], font=("微软雅黑", 10)).pack(side="left", padx=12)
        edit_frame = tk.Frame(self, bg=theme["card_bg"])
        edit_frame.pack(fill="both", expand=True, padx=15, pady=10)
        self.text_widget = tk.Text(edit_frame, bg=theme["card_bg"], fg=theme["text_primary"],
                                  insertbackground=theme["primary"],
                                  font=("微软雅黑", 11), wrap="word",
                                  relief="flat", padx=12, pady=12, undo=True)
        scrollbar = ttk.Scrollbar(edit_frame, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        self.text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.text_widget.insert("1.0", self.original_content)
        status_bar = tk.Frame(self, bg=theme["border_light"], height=24)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        self.char_label = tk.Label(status_bar, text=f"字符数：{len(self.original_content)}",
                                  bg=theme["border_light"], fg=theme["text_hint"],
                                  font=("微软雅黑", 9))
        self.char_label.pack(side="right", padx=10)
        self.text_widget.bind("<KeyRelease>", self._update_char_count)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        _center_window(self)
        self.after(60, lambda: apply_round_corner(self, 14))

    def _update_char_count(self, e=None):
        content = self.text_widget.get("1.0", tk.END)
        self.char_label.config(text=f"字符数：{len(content)}")

    def _read_file(self):
        if not os.path.exists(self.file_path):
            return "", ""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return content, ""
        except IOError as e:
            return "", f"读取文件失败：{str(e)}"
        except UnicodeDecodeError:
            return "", "文件编码错误，请使用UTF-8编码"

    def _write_file(self, content):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, ""
        except IOError as e:
            return False, f"写入文件失败：{str(e)}"

    def _get_main_app(self):
        app = self.master_win
        while not hasattr(app, "_refresh_students"):
            app = app.master
            if app is None:
                break
        return app

    def on_save(self):
        content = self.text_widget.get("1.0", tk.END)
        ok, error = self._write_file(content)
        if not ok:
            CustomMessageBox(self, self.theme, "保存失败", error, "error")
            return
        filename = os.path.basename(self.file_path)
        main_app = self._get_main_app()
        if main_app:
            if filename == "students.txt":
                main_app._refresh_students()
            elif filename == "texts.txt":
                main_app._load_texts()
                main_app._populate_text_tree()
        self.original_content = content
        CustomMessageBox(self, self.theme, "保存成功", "文件已保存", "info")
        self.destroy()

    def on_revert_original(self):
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", self.original_content)
        self._update_char_count()
        CustomMessageBox(self, self.theme, "已恢复", "已恢复打开时的原始文件内容", "info")

    def on_cancel(self):
        current = self.text_widget.get("1.0", tk.END)
        if current != self.original_content:
            result = CustomMessageBox(self, self.theme, "未保存修改",
                                     "存在未保存修改，关闭将丢弃改动，确认继续？", "confirm")
            if not result:
                return
        self.destroy()


class CustomMessageBox(tk.Toplevel):
    def __init__(self, master, theme, title, message, mtype="info"):
        super().__init__(master)
        self.theme = theme
        self.result = False
        self.overrideredirect(True)
        self.config(bg=theme["bg"])
        if mtype == "error":
            icon_text = "✕"
            icon_color = theme["danger"]
            icon_bg = theme["danger_light"]
        elif mtype == "warning":
            icon_text = "⚠"
            icon_color = theme["warning"]
            icon_bg = theme["warning_light"]
        elif mtype == "confirm":
            icon_text = "?"
            icon_color = theme["primary"]
            icon_bg = theme["primary_light"]
        else:
            icon_text = "✓"
            icon_color = theme["success"]
            icon_bg = theme["success_light"]

        outer = tk.Frame(self, bg=theme["card_bg"], highlightbackground=theme["border"],
                         highlightthickness=1)
        outer.pack(fill="both", expand=True, padx=0, pady=0)

        header = tk.Frame(outer, bg=theme["card_bg"], height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, bg=theme["card_bg"], fg=theme["text_primary"],
                font=("微软雅黑", 12, "bold")).pack(side="left", padx=18)
        RoundedButton(header, text="×", style="ghost", width=30, height=30, radius=15,
                     font=("微软雅黑", 11, "bold"), command=self._on_close).pack(side="right", padx=10, pady=7)

        content = tk.Frame(outer, bg=theme["card_bg"])
        content.pack(fill="both", expand=True, padx=24, pady=(8, 16))

        icon_frame = tk.Frame(content, bg=theme["card_bg"])
        icon_frame.pack(pady=(4, 14))
        icon_canvas = tk.Canvas(icon_frame, width=56, height=56, bg=theme["card_bg"],
                                highlightthickness=0, bd=0)
        icon_canvas.pack()
        icon_canvas.create_oval(4, 4, 52, 52, fill=icon_bg, outline=icon_bg)
        icon_canvas.create_text(28, 28, text=icon_text, fill=icon_color,
                                font=("微软雅黑", 22, "bold"))

        tk.Label(content, text=message, bg=theme["card_bg"], fg=theme["text_primary"],
                font=("微软雅黑", 11), wraplength=320, justify="center").pack()

        btn_frame = tk.Frame(outer, bg=theme["card_bg"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 18))
        if mtype == "confirm":
            RoundedButton(btn_frame, text="取消", style="ghost", width=90, height=36,
                         font=("微软雅黑", 10), command=self._on_close).pack(side="right", padx=6)
            RoundedButton(btn_frame, text="确定", style="primary", width=90, height=36,
                         font=("微软雅黑", 10, "bold"), command=self._on_confirm).pack(side="right", padx=6)
        else:
            RoundedButton(btn_frame, text="确定", style="primary", width=110, height=36,
                         font=("微软雅黑", 10, "bold"), command=self._on_confirm).pack()

        _center_window(self)
        self.after(50, lambda: apply_round_corner(self, 16))
        self.grab_set()
        self.wait_window()

    def _on_confirm(self):
        self.result = True
        self.grab_release()
        self.destroy()

    def _on_close(self):
        self.result = False
        self.grab_release()
        self.destroy()

    def __bool__(self):
        return self.result


class ResultPopup(tk.Toplevel):
    def __init__(self, master, name, text_title, text_content, theme):
        super().__init__(master)
        self.theme = theme
        self.overrideredirect(True)
        self.geometry("600x440")
        self.resizable(False, False)
        self.config(bg=theme["bg"])
        self.attributes("-topmost", True)
        outer = tk.Frame(self, bg=theme["card_bg"], highlightbackground=theme["border"],
                         highlightthickness=1)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=theme["primary"], height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🎉 抽取结果", bg=theme["primary"], fg="white",
                font=("微软雅黑", 14, "bold")).pack(side="left", padx=20)
        RoundedButton(header, text="×", bg=theme["primary"], hover_bg=theme["primary_hover"],
                     fg="white", width=32, height=32, radius=16,
                     font=("微软雅黑", 12, "bold"), command=self.destroy).pack(side="right", padx=15, pady=8)
        content = tk.Frame(outer, bg=theme["card_bg"])
        content.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(content, text="抽中同学", bg=theme["card_bg"], fg=theme["text_secondary"],
                font=("微软雅黑", 11)).pack(pady=(2, 4))
        name_frame = tk.Frame(content, bg=theme["primary_super_light"])
        name_frame.pack(fill="x", pady=(0, 14))
        tk.Label(name_frame, text=name, bg=theme["primary_super_light"], fg=theme["primary"],
                font=("微软雅黑", 30, "bold")).pack(pady=10)
        if text_title:
            tk.Label(content, text=text_title, bg=theme["card_bg"], fg=theme["text_secondary"],
                    font=("微软雅黑", 11)).pack(pady=(0, 8), anchor="w")
        text_frame = tk.Frame(content, bg=theme["border_light"])
        text_frame.pack(fill="both", expand=True, pady=(0, 14))
        text_display = tk.Text(text_frame, bg=theme["card_bg"], fg=theme["text_primary"],
                              font=("微软雅黑", 12), wrap="word", relief="flat",
                              padx=15, pady=10, spacing1=3, spacing2=2)
        text_display.pack(fill="both", expand=True)
        text_display.insert("1.0", text_content)
        text_display.config(state="disabled")
        btn_frame = tk.Frame(outer, bg=theme["card_bg"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 18))
        RoundedButton(btn_frame, text="知道了", style="primary", width=130, height=38,
                     font=("微软雅黑", 11, "bold"), command=self.destroy).pack()
        duration = master.config_mgr.get("ui", "popup_duration") or 3000
        self.after(duration, self.destroy)
        _center_window(self)
        self.after(50, lambda: apply_round_corner(self, 16))


class SettingsWindow(tk.Toplevel):
    def __init__(self, master, config_mgr, theme):
        super().__init__(master)
        self.master_app = master
        self.config_mgr = config_mgr
        self.theme = theme
        self.overrideredirect(True)
        self.geometry("960x720")
        self.minsize(860, 620)
        self.resizable(True, True)
        self.config(bg=theme["primary"])
        outer = tk.Frame(self, bg=theme["bg"])
        outer.pack(fill="both", expand=True, padx=2, pady=2)
        header = tk.Frame(outer, bg=theme["primary"], height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⚙ 系统设置", bg=theme["primary"], fg="white",
                font=("微软雅黑", 14, "bold")).pack(side="left", padx=20)
        RoundedButton(header, text="×", bg=theme["primary"], hover_bg=theme["primary_hover"],
                     fg="white", width=32, height=32, radius=16,
                     font=("微软雅黑", 12, "bold"), command=self.on_cancel).pack(side="right", padx=12, pady=8)
        # 定制班级版横幅
        banner = tk.Frame(outer, bg="#fef3c7", height=42, cursor="hand2")
        banner.pack(fill="x")
        banner.pack_propagate(False)
        banner_inner = tk.Frame(banner, bg="#fef3c7")
        banner_inner.pack(fill="both", expand=True, padx=20)
        tk.Label(banner_inner, text="🎨 定制属于你们班的课堂点名程序",
                bg="#fef3c7", fg="#92400e", font=("微软雅黑", 11, "bold")).pack(side="left")
        tag = tk.Label(banner_inner, text="限时免费", bg="#dc2626", fg="white",
                       font=("微软雅黑", 9, "bold"), padx=8, pady=1)
        tag.pack(side="left", padx=10)
        tk.Label(banner_inner, text="点击前往官网定制 →", bg="#fef3c7", fg="#b45309",
                font=("微软雅黑", 10, "bold")).pack(side="right")
        for w in (banner, banner_inner):
            w.bind("<Button-1>", lambda e: self.master_app._open_website())
        for child in banner_inner.winfo_children():
            child.bind("<Button-1>", lambda e: self.master_app._open_website())

        self.config_mgr.backup_current()
        self._setup_ttk_style()
        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=12)
        self._build_ui_tab()
        self._build_draw_tab()
        self._build_text_tab()
        self._build_weight_tab()
        self._build_shortcut_tab()
        self._build_files_tab()
        self._build_experimental_tab()
        self._build_danger_tab()
        self._build_about_tab()
        btn_frame = tk.Frame(outer, bg=theme["bg"])
        btn_frame.pack(fill="x", padx=16, pady=(0, 14))
        # 醒目的下滑提示
        scroll_hint = tk.Frame(btn_frame, bg="#eff6ff", cursor="hand2",
                                highlightbackground="#3b82f6", highlightthickness=1)
        scroll_hint.pack(side="left", padx=(0, 12))
        hint_inner = tk.Frame(scroll_hint, bg="#eff6ff")
        hint_inner.pack(padx=14, pady=6)
        tk.Label(hint_inner, text="⬇", bg="#eff6ff", fg="#2563eb",
                font=("微软雅黑", 14, "bold")).pack(side="left", padx=(0, 6))
        tk.Label(hint_inner, text="鼠标滚轮下滑查看更多设置选项",
                bg="#eff6ff", fg="#1d4ed8", font=("微软雅黑", 10, "bold")).pack(side="left")
        RoundedButton(btn_frame, text="保存设置", style="primary", width=130, height=38,
                     font=("微软雅黑", 10, "bold"), command=self.on_save).pack(side="right", padx=6)
        RoundedButton(btn_frame, text="取消", style="ghost", width=100, height=38,
                     command=self.on_cancel).pack(side="right", padx=6)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        _center_window(self)
        self.after(80, lambda: apply_round_corner(self, 16))

    def _setup_ttk_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TNotebook", background=self.theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(20, 10), font=("微软雅黑", 10),
                       background=self.theme["card_bg"], foreground=self.theme["text_secondary"])
        style.map("TNotebook.Tab",
                 background=[("selected", self.theme["primary_super_light"])],
                 foreground=[("selected", self.theme["primary"])])
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28,
                       background=self.theme["card_bg"], foreground=self.theme["text_primary"],
                       fieldbackground=self.theme["card_bg"], borderwidth=0)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"),
                       background=self.theme["border_light"], foreground=self.theme["text_primary"])
        style.map("Treeview", background=[("selected", self.theme["primary_light"])])

    def _add_section(self, parent, title):
        frame = tk.Frame(parent, bg=self.theme["card_bg"])
        frame.pack(fill="x", pady=8)
        tk.Label(frame, text=title, font=("微软雅黑", 12, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w", pady=(10, 12), padx=16)
        content = tk.Frame(frame, bg=self.theme["card_bg"])
        content.pack(fill="x", padx=16, pady=(0, 14))
        return content

    def _add_checkbox_item(self, parent, label, hint, value):
        var = tk.BooleanVar(value=value)
        item = SettingItem(parent, self.theme, label, hint)
        item.pack(fill="x", pady=6)
        sw = ToggleSwitch(item, variable=var, on_color=self.theme["primary"],
                          off_color="#cbd5e1", width=52, height=28)
        sw.place(relx=1.0, rely=0, anchor="ne")
        return var

    def _add_slider_item(self, parent, label, hint, value, min_val, max_val, step=1):
        item = SettingItem(parent, self.theme, label, hint)
        item.pack(fill="x", pady=6)
        var = tk.DoubleVar(value=value)
        slider_frame = tk.Frame(item, bg=self.theme["card_bg"])
        slider_frame.pack(fill="x", pady=(6, 0))
        scale = tk.Scale(slider_frame, from_=min_val, to=max_val, resolution=step,
                        orient="horizontal", variable=var,
                        bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                        troughcolor=self.theme["border_light"],
                        activebackground=self.theme["primary"],
                        highlightthickness=0, showvalue=False, length=200)
        scale.pack(side="left", fill="x", expand=True)
        val_label = tk.Label(slider_frame, text=f"{value:g}", bg=self.theme["card_bg"],
                            fg=self.theme["primary"], width=6, anchor="e")
        val_label.pack(side="right", padx=(10, 0))
        def on_change(e):
            val_label.config(text=f"{var.get():g}")
        scale.bind("<Motion>", on_change)
        return var

    def _add_spin_item(self, parent, label, hint, value, min_val, max_val, step=1):
        item = SettingItem(parent, self.theme, label, hint)
        item.pack(fill="x", pady=6)
        var = tk.IntVar(value=value)
        spin = tk.Spinbox(item, from_=min_val, to=max_val, increment=step,
                         textvariable=var, width=10,
                         bg=self.theme["card_bg"], fg=self.theme["text_primary"],
                         buttonbackground=self.theme["border_light"])
        spin.place(relx=1.0, rely=0, anchor="ne")
        return var

    def _add_combo_item(self, parent, label, hint, value, options):
        item = SettingItem(parent, self.theme, label, hint)
        item.pack(fill="x", pady=6)
        var = tk.StringVar(value=value)
        combo = ttk.Combobox(item, textvariable=var, values=options, state="readonly", width=15)
        combo.place(relx=1.0, rely=0, anchor="ne")
        return var

    def _build_ui_tab(self):
        frame = ScrollableFrame(self.notebook, self.theme)
        self.notebook.add(frame, text="  界面外观  ")
        scroll = frame.scrollable_frame
        sec = self._add_section(scroll, "主题与基础")
        self.theme_var = self._add_checkbox_item(sec, "深色模式", "切换明暗主题，暗色主题更有专业性，明亮主题更有轻量化。⚠需重启完全生效",
                                                self.config_mgr.get("ui", "theme") == "dark")
        self.dpi_var = self._add_checkbox_item(sec, "DPI高清优化", "针对大屏的分辨率优化，解决高分辨率下的文字不清晰问题，提升界面清晰度，⚠需重启生效",
                                              self.config_mgr.get("experimental", "dpi_optimization"))
        sec = self._add_section(scroll, "字体与字号")
        self.font_size_var = self._add_slider_item(sec, "界面字号", "界面中文字大小，此大小将被应用于全局",
                                                  self.config_mgr.get("ui", "font_size"), 10, 18, 1)
        self.name_size_var = self._add_slider_item(sec, "抽取名字字号", "抽取画布中央名字的大小",
                                                  self.config_mgr.get("ui", "name_font_size"), 30, 80, 2)
        self.text_size_var = self._add_slider_item(sec, "课文显示字号", "课文内容显示字体大小",
                                                  self.config_mgr.get("ui", "text_font_size"), 12, 28, 1)
        sec = self._add_section(scroll, "动画与动效")
        self.anim_duration_var = self._add_slider_item(sec, "自动抽取时长", "自动模式下滚动动画持续秒数",
                                                       self.config_mgr.get("ui", "animation_duration"), 1, 10, 0.5)
        self.ease_var = self._add_slider_item(sec, "减速强度", "数值越大结尾减速越明显",
                                             self.config_mgr.get("ui", "ease_strength"), 0.5, 1.0, 0.01)
        self.curve_var = self._add_combo_item(sec, "动画曲线", "抽取滚动的速度变化模式",
                                              self.config_mgr.get("ui", "animation_curve"),
                                              ["ease_out", "linear", "ease_in"])
        self.particle_var = self._add_checkbox_item(sec, "抽取动画", "抽取时角落显示粒子动效，表示正在抽取",
                                                    self.config_mgr.get("ui", "particle_enabled"))
        self.particle_count_var = self._add_slider_item(sec, "粒子数量", "抽取动画中特效的粒子数量",
                                                        self.config_mgr.get("ui", "particle_count"), 10, 80, 5)
        self.start_anim_var = self._add_checkbox_item(sec, "启动加载界面", "程序启动时显示开屏动画，不需要可关闭",
                                                      self.config_mgr.get("ui", "start_animation"))
        self.start_anim_dur_var = self._add_slider_item(sec, "启动窗口持续时长", "开屏加载窗口持续毫秒数",
                                                        self.config_mgr.get("ui", "start_anim_duration"), 1000, 5000, 100)
        sec = self._add_section(scroll, "界面元素")
        self.status_bar_var = self._add_checkbox_item(sec, "底部状态栏", "显示底部状态信息栏，实时展示名单状态、本轮进度与权重提示",
                                                      self.config_mgr.get("ui", "show_status_bar"))
        self.result_popup_var = self._add_checkbox_item(sec, "结果放大弹窗", "抽取完成弹出放大结果窗口，可自动关闭",
                                                        self.config_mgr.get("ui", "result_popup"))
        self.popup_dur_var = self._add_slider_item(sec, "弹窗自动关闭时长", "结果放大弹窗自动关闭毫秒数",
                                                   self.config_mgr.get("ui", "popup_duration"), 1000, 5000, 100)
        self.countdown_var = self._add_checkbox_item(sec, "抽取前准备倒计时", "点击抽取后先进行倒计时以进行准备",
                                                     self.config_mgr.get("ui", "draw_countdown"))
        self.countdown_num_var = self._add_spin_item(sec, "倒计时秒数", "抽取前准备倒计时的秒数设置",
                                                     self.config_mgr.get("ui", "countdown_number"), 1, 10, 1)
        self.border_width_var = self._add_slider_item(sec, "边框宽度", "界面元素边框粗细",
                                                      self.config_mgr.get("ui", "border_width"), 0, 3, 1)
        self.button_radius_var = self._add_slider_item(sec, "按钮圆角", "所有按钮圆角半径",
                                                       self.config_mgr.get("ui", "button_radius"), 0, 20, 1)

    def _build_draw_tab(self):
        frame = ScrollableFrame(self.notebook, self.theme)
        self.notebook.add(frame, text="  抽取规则  ")
        scroll = frame.scrollable_frame
        sec = self._add_section(scroll, "基础模式")
        self.draw_mode_var = self._add_combo_item(sec, "抽取模式", "自动滚动停止或手动点击停止",
                                                  self.config_mgr.get("draw", "mode"),
                                                  ["auto", "manual"])
        self.no_repeat_var = self._add_checkbox_item(sec, "不重复抽取", "本轮已抽中的学生不再进行抽取",
                                                     self.config_mgr.get("draw", "no_repeat"))
        self.auto_reset_var = self._add_checkbox_item(sec, "全部抽完自动重置", "所有学生抽完后自动重置本轮",
                                                      self.config_mgr.get("draw", "auto_reset_round"))
        self.auto_duration_var = self._add_slider_item(sec, "自动模式时长", "自动抽取持续秒数",
                                                       self.config_mgr.get("draw", "auto_duration"), 1, 15, 0.5)
        sec = self._add_section(scroll, "动态权重")
        self.dynamic_focus_var = self._add_checkbox_item(sec, "启用动态权重", "根据背诵状态调整抽取概率",
                                                         self.config_mgr.get("draw", "dynamic_focus"))
        self.rate_mastered_var = self._add_slider_item(sec, "已背过 倍率", "已背过学生的抽取概率倍率",
                                                       self.config_mgr.get("draw", "rate_mastered"), 0.1, 5, 0.1)
        self.rate_familiar_var = self._add_slider_item(sec, "未背熟 倍率", "未背熟学生的抽取概率倍率",
                                                       self.config_mgr.get("draw", "rate_familiar"), 0.1, 5, 0.1)
        self.rate_unlearned_var = self._add_slider_item(sec, "未背过 倍率", "未背过学生的抽取概率倍率",
                                                        self.config_mgr.get("draw", "rate_unlearned"), 0.1, 5, 0.1)
        self.dynamic_weight_var = self._add_checkbox_item(sec, "动态权重总开关", "启用状态加权抽取机制",
                                                          self.config_mgr.get("draw", "dynamic_weight"))
        sec = self._add_section(scroll, "高级选项")
        self.history_limit_var = self._add_spin_item(sec, "历史记录上限", "本轮抽取历史保留条数",
                                                     self.config_mgr.get("draw", "history_limit"), 10, 200, 10)
        self.anti_cheat_var = self._add_checkbox_item(sec, "防作弊模式2.0", "增强抽取结果不可预测性",
                                                      self.config_mgr.get("draw", "anti_cheat"))

    def _build_text_tab(self):
        frame = ScrollableFrame(self.notebook, self.theme)
        self.notebook.add(frame, text="  课文抽取  ")
        scroll = frame.scrollable_frame
        sec = self._add_section(scroll, "抽取模式")
        self.extract_mode_var = self._add_combo_item(sec, "课文抽取模式", "选择课文内容的抽取方式",
                                                     self.config_mgr.get("text", "extract_mode"),
                                                     ["整篇抽取", "段落抽取", "分段抽取"])
        self.paragraph_random_var = self._add_checkbox_item(sec, "段落随机抽取", "段落模式下随机选择段落，关闭则按顺序抽取",
                                                            self.config_mgr.get("text", "paragraph_random"))
        sec = self._add_section(scroll, "显示设置")
        self.show_title_var = self._add_checkbox_item(sec, "显示课文标题", "课文内容区显示标题",
                                                      self.config_mgr.get("text", "show_title"))
        self.text_align_var = self._add_combo_item(sec, "文本对齐方式", "课文内容的对齐方式",
                                                   self.config_mgr.get("text", "text_align"),
                                                   ["left", "center", "right"])
        tk.Label(scroll, text="说明：\n- 整篇抽取：选中课文后显示全文\n- 段落抽取：随机抽取课文中的一个段落\n- 分段抽取：按顺序依次抽取段落，记录进度",
                bg=self.theme["bg"], fg=self.theme["text_hint"],
                justify="left", font=("微软雅黑", 9)).pack(anchor="w", padx=20, pady=10)

    def _build_weight_tab(self):
        frame = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(frame, text="  学生权重  ")
        list_frame = tk.Frame(frame, bg=self.theme["bg"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=15)
        columns = ("name", "weight")
        self.weight_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        self.weight_tree.heading("name", text="学生姓名")
        self.weight_tree.heading("weight", text="基础权重")
        self.weight_tree.column("name", width=250, anchor="center")
        self.weight_tree.column("weight", width=150, anchor="center")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.weight_tree.yview)
        self.weight_tree.configure(yscrollcommand=scrollbar.set)
        self.weight_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for name in self.master_app.students:
            weight = self.master_app.data_mgr.get_student_weight(name)
            self.weight_tree.insert("", "end", values=(name, weight))
        btn_frame = tk.Frame(frame, bg=self.theme["bg"])
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))
        tk.Label(btn_frame, text="设置权重：", bg=self.theme["bg"],
                fg=self.theme["text_primary"]).pack(side="left")
        self.weight_set_var = tk.IntVar(value=1)
        tk.Spinbox(btn_frame, from_=0, to=10, textvariable=self.weight_set_var, width=8,
                  bg=self.theme["card_bg"]).pack(side="left", padx=8)
        RoundedButton(btn_frame, text="应用选中", style="primary", width=100, height=32,
                     command=self._set_selected_weight).pack(side="left", padx=10)
        RoundedButton(btn_frame, text="全部重置为1", style="warning", width=120, height=32,
                     command=self._reset_all_weights).pack(side="left", padx=10)

    def _set_selected_weight(self):
        selected = self.weight_tree.selection()
        if not selected:
            CustomMessageBox(self, self.theme, "提示", "请先选中学生", "warning")
            return
        weight = self.weight_set_var.get()
        for item in selected:
            name = self.weight_tree.item(item, "values")[0]
            self.master_app.data_mgr.set_student_weight(name, weight, skip_save=True)
            self.weight_tree.item(item, values=(name, weight))
        self.master_app.config_mgr.save_config()
        self.master_app._update_weight_tip()
        CustomMessageBox(self, self.theme, "成功", "权重已更新", "info")

    def _reset_all_weights(self):
        result = CustomMessageBox(self, self.theme, "确认", "确定要将所有学生权重重置为1吗？", "confirm")
        if not result:
            return
        self.master_app.data_mgr.reset_all_weights(self.master_app.students)
        for item in self.weight_tree.get_children():
            self.weight_tree.delete(item)
        for name in self.master_app.students:
            self.weight_tree.insert("", "end", values=(name, 1))
        self.master_app._update_weight_tip()

    def _build_shortcut_tab(self):
        frame = ScrollableFrame(self.notebook, self.theme)
        self.notebook.add(frame, text="  快捷键  ")
        scroll = frame.scrollable_frame
        sec = self._add_section(scroll, "全局设置")
        self.shortcut_enabled_var = self._add_checkbox_item(sec, "启用全局快捷键", "关闭后所有快捷键失效，按 ? 可查看速查表",
                                                            self.config_mgr.get("shortcut", "enabled"))
        btn_row = tk.Frame(sec, bg=self.theme["card_bg"])
        btn_row.pack(fill="x", pady=(8, 0))
        RoundedButton(btn_row, text="⌨ 打开快捷键速查表", style="primary", width=180, height=34,
                     font=("微软雅黑", 10, "bold"),
                     command=lambda: self.master_app._show_shortcut_help()).pack(side="left")

        groups = [
            ("🎯 抽取操作", [
                ("开始 / 停止抽取", "空格"),
                ("重置本轮", "Esc"),
                ("切换不重复模式", "N"),
                ("切换动态权重", "W"),
                ("查看本轮记录", "R"),
            ]),
            ("✅ 状态标记", [
                ("标记已背过", "1"),
                ("标记未背熟", "2"),
                ("标记未背过", "3"),
                ("撤销上次标记", "Z"),
                ("跳过当前", "Tab"),
            ]),
            ("📄 课文与界面", [
                ("切换抽取模式", "T"),
                ("上一篇课文", "←"),
                ("下一篇课文", "→"),
                ("切换主题", "M"),
                ("打开设置", ","),
            ]),
            ("✨ 显示与效果", [
                ("粒子效果开关", "P"),
                ("全屏模式", "F11"),
                ("排行榜", "L"),
                ("保存数据", "Ctrl+S"),
                ("快捷键速查", "? / /"),
            ]),
        ]

        for group_title, items in groups:
            sec = self._add_section(scroll, group_title)
            for name, key in items:
                item = SettingItem(sec, self.theme, name, "")
                item.pack(fill="x", pady=3)
                key_label = tk.Label(item, text=key, bg=self.theme["primary_super_light"],
                                    fg=self.theme["primary"], padx=10, pady=3,
                                    font=("Consolas", 9, "bold"))
                key_label.pack(side="right")

        tk.Label(scroll, text="提示：快捷键全局生效，即使焦点在按钮或列表上也能触发。按 ? 随时打开浮动速查表。",
                bg=self.theme["bg"], fg=self.theme["text_hint"],
                font=("微软雅黑", 9), wraplength=800, justify="left").pack(anchor="w", padx=20, pady=10)

    def _build_files_tab(self):
        frame = ScrollableFrame(self.notebook, self.theme)
        self.notebook.add(frame, text="  数据文件  ")
        scroll = frame.scrollable_frame
        sec = self._add_section(scroll, "文件管理")
        files = [
            ("学生名单", self.config_mgr.get("files", "students")),
            ("课文库", self.config_mgr.get("files", "texts")),
            ("抽查记录", self.config_mgr.get("files", "records")),
            ("统计积分", self.config_mgr.get("files", "stats")),
            ("配置文件", "config.json")
        ]
        for label, file_path in files:
            row = tk.Frame(sec, bg=self.theme["bg"])
            row.pack(fill="x", pady=8)
            info_frame = tk.Frame(row, bg=self.theme["bg"])
            info_frame.pack(side="left", fill="x", expand=True)
            tk.Label(info_frame, text=label, bg=self.theme["bg"],
                    fg=self.theme["text_primary"], font=("微软雅黑", 11)).pack(anchor="w")
            tk.Label(info_frame, text=file_path, bg=self.theme["bg"],
                    fg=self.theme["text_hint"], font=("微软雅黑", 9)).pack(anchor="w")
            btn_frame = tk.Frame(row, bg=self.theme["bg"])
            btn_frame.pack(side="right")
            if file_path.endswith(".txt"):
                RoundedButton(btn_frame, text="内置编辑", style="primary", width=90, height=32,
                             command=lambda p=file_path: InternalTextEditor(self, self.theme, p)).pack(side="left", padx=4)
            RoundedButton(btn_frame, text="外部打开", style="ghost", width=90, height=32,
                         command=lambda p=file_path: open_external_file(p)).pack(side="left", padx=4)

    def _build_experimental_tab(self):
        frame = ScrollableFrame(self.notebook, self.theme)
        self.notebook.add(frame, text="  实验功能  ")
        scroll = frame.scrollable_frame
        sec = self._add_section(scroll, "显示效果")
        self.smooth_scroll_var = self._add_checkbox_item(sec, "平滑滚动", "列表和文本平滑滚动，需重启",
                                                         self.config_mgr.get("experimental", "smooth_scroll"))
        self.shadow_var = self._add_checkbox_item(sec, "卡片阴影效果", "界面卡片显示阴影增强层次感",
                                                  self.config_mgr.get("ui", "shadow_enabled"))
        self.blur_bg_var = self._add_checkbox_item(sec, "毛玻璃背景", "弹窗背景模糊效果（仅Win11+）",
                                                   self.config_mgr.get("experimental", "blur_background"))
        sec = self._add_section(scroll, "交互体验")
        self.sound_var = self._add_checkbox_item(sec, "抽取音效", "抽取完成播放提示音（需系统音频支持）",
                                                 self.config_mgr.get("experimental", "sound_effect"))
        self.voice_var = self._add_checkbox_item(sec, "语音播报", "抽取结果语音播报学生姓名",
                                                 self.config_mgr.get("experimental", "voice_broadcast"))
        self.history_recall_var = self._add_checkbox_item(sec, "历史回溯", "支持撤回上一次抽取结果",
                                                          self.config_mgr.get("experimental", "history_recall"))
        self.anti_cheat_mode_var = self._add_checkbox_item(sec, "防篡改模式", "增强抽取结果不可预测性",
                                                           self.config_mgr.get("experimental", "anti_cheat_mode"))
        tk.Label(scroll, text="实验性功能可能存在不稳定，部分功能依赖系统环境",
                bg=self.theme["bg"], fg=self.theme["text_hint"],
                font=("微软雅黑", 9)).pack(anchor="w", padx=20, pady=10)

    def _build_danger_tab(self):
        frame = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(frame, text="  危险操作  ")

        scroll = ScrollableFrame(frame, self.theme)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        content = scroll.scrollable_frame

        # 数据重置
        sec = Card(content, self.theme, padding=20)
        sec.pack(fill="x", pady=(0, 16))
        tk.Label(sec.inner, text="⚠ 恢复所有默认设置", font=("微软雅黑", 13, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["danger"]).pack(anchor="w")
        tk.Label(sec.inner, text="此操作将清空所有学生名单、课文库、抽查记录、统计积分和配置文件，恢复为初始状态。\n同时会重置向导标记，下次启动将重新打开配置向导。\n数据删除后无法恢复，请谨慎操作！",
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                justify="left", wraplength=600).pack(anchor="w", pady=(8, 14))
        RoundedButton(sec.inner, text="恢复所有默认设置", style="danger", width=180, height=38,
                     font=("微软雅黑", 10, "bold"), command=self._reset_all_data).pack(anchor="w")

        # 重新运行向导
        sec2 = Card(content, self.theme, padding=20)
        sec2.pack(fill="x")
        tk.Label(sec2.inner, text="🔧 重新运行配置向导", font=("微软雅黑", 13, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["warning"]).pack(anchor="w")
        tk.Label(sec2.inner, text="重置向导完成标记，程序重启后将重新打开首次配置向导。\n不会删除现有学生名单和课文库数据。",
                bg=self.theme["card_bg"], fg=self.theme["text_secondary"],
                justify="left", wraplength=600).pack(anchor="w", pady=(8, 14))
        RoundedButton(sec2.inner, text="重新运行向导", style="warning", width=160, height=38,
                     font=("微软雅黑", 10, "bold"), command=self.master_app._rerun_wizard).pack(anchor="w")

    def _reset_all_data(self):
        r1 = CustomMessageBox(self, self.theme, "危险操作确认",
                             "确定要删除所有数据并恢复默认设置吗？\n\n所有学生名单、课文、记录、积分都将被清空，且无法恢复！\n向导标记也将被重置，下次启动会重新打开配置向导。",
                             "confirm")
        if not r1:
            return
        r2 = CustomMessageBox(self, self.theme, "二次确认",
                             "真的确定要清空所有数据吗？此操作不可逆！", "confirm")
        if not r2:
            return
        self.config_mgr.reset_all_files()
        set_wizard_unfinished()
        CustomMessageBox(self, self.theme, "操作完成", "所有数据已清空，向导标记已重置，程序将自动重启", "info")
        restart_application()

    def _build_about_tab(self):
        frame = tk.Frame(self.notebook, bg=self.theme["bg"])
        self.notebook.add(frame, text="  关于  ")

        scroll = ScrollableFrame(frame, self.theme)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        content = scroll.scrollable_frame

        # Logo 区域
        logo_card = Card(content, self.theme, padding=24)
        logo_card.pack(fill="x", pady=(0, 16))
        logo_inner = tk.Frame(logo_card.inner, bg=self.theme["card_bg"])
        logo_inner.pack()
        tk.Label(logo_inner, text="📚", bg=self.theme["card_bg"],
                font=("微软雅黑", 40)).pack(pady=(0, 8))
        tk.Label(logo_inner, text="A13 课堂背诵点名系统", font=("微软雅黑", 20, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack()
        tk.Label(logo_inner, text="版本 V6.2 专业版  ·  [20260820]", bg=self.theme["card_bg"],
                fg=self.theme["text_secondary"], font=("微软雅黑", 11)).pack(pady=6)
        tk.Label(logo_inner, text="纯 Python + Tkinter 实现 · 无第三方依赖 · 本地离线运行",
                bg=self.theme["card_bg"], fg=self.theme["text_hint"],
                font=("微软雅黑", 10)).pack(pady=(4, 0))

        # 功能特性
        feat_card = Card(content, self.theme, padding=20)
        feat_card.pack(fill="x", pady=(0, 16))
        tk.Label(feat_card.inner, text="核心特性", font=("微软雅黑", 13, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w", pady=(0, 12))
        features = [
            "✓ 四层架构设计，业务与界面完全解耦",
            "✓ 第六代A13抽取引擎，公平防篡改",
            "✓ 加权随机抽取，支持动态状态权重",
            "✓ 三种课文抽取模式，适配不同教学场景",
            "✓ 完整积分统计与排行榜",
            "✓ 内置文本编辑器，无需外部程序",
            "✓ 粒子动效，提升抽取仪式感",
            "✓ 明暗双主题，现代化圆角界面",
            "✓ 交互式新手引导，逐一点亮核心功能"
        ]
        for f in features:
            tk.Label(feat_card.inner, text=f, bg=self.theme["card_bg"],
                    fg=self.theme["text_secondary"], anchor="w",
                    font=("微软雅黑", 10)).pack(anchor="w", pady=2)

        # 操作按钮区
        action_card = Card(content, self.theme, padding=20)
        action_card.pack(fill="x", pady=(0, 16))
        tk.Label(action_card.inner, text="快捷操作", font=("微软雅黑", 13, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w", pady=(0, 14))

        btn_grid = tk.Frame(action_card.inner, bg=self.theme["card_bg"])
        btn_grid.pack(fill="x")

        # 官网按钮
        col1 = tk.Frame(btn_grid, bg=self.theme["card_bg"])
        col1.pack(side="left", expand=True, fill="x", padx=4)
        RoundedButton(col1, text="🌐 访问官网", style="primary", width=160, height=40,
                     font=("微软雅黑", 10, "bold"),
                     command=self.master_app._open_website).pack(pady=4)
        tk.Label(col1, text="打开产品官方网站", bg=self.theme["card_bg"],
                fg=self.theme["text_hint"], font=("微软雅黑", 9)).pack()

        # 界面教学按钮
        col2 = tk.Frame(btn_grid, bg=self.theme["card_bg"])
        col2.pack(side="left", expand=True, fill="x", padx=4)
        RoundedButton(col2, text="📖 界面教学", style="success", width=160, height=40,
                     font=("微软雅黑", 10, "bold"),
                     command=self.master_app._rerun_tutorial).pack(pady=4)
        tk.Label(col2, text="重新运行交互式操作引导", bg=self.theme["card_bg"],
                fg=self.theme["text_hint"], font=("微软雅黑", 9)).pack()

        # 重新运行向导按钮
        col3 = tk.Frame(btn_grid, bg=self.theme["card_bg"])
        col3.pack(side="left", expand=True, fill="x", padx=4)
        RoundedButton(col3, text="🔧 重新运行向导", style="warning", width=160, height=40,
                     font=("微软雅黑", 10, "bold"),
                     command=self.master_app._rerun_wizard).pack(pady=4)
        tk.Label(col3, text="重置配置并重新打开首次向导", bg=self.theme["card_bg"],
                fg=self.theme["text_hint"], font=("微软雅黑", 9)).pack()

        # 技术信息
        tech_card = Card(content, self.theme, padding=16)
        tech_card.pack(fill="x")
        tk.Label(tech_card.inner, text="技术信息", font=("微软雅黑", 11, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w", pady=(0, 8))
        tech_info = [
            f"官网地址：{WEBSITE_URL}",
            "开发语言：Python 3 + Tkinter",
            "数据存储：本地 JSON / TXT 文件",
            "运行环境：Windows 7 及以上",
            "开源协议：个人免费使用"
        ]
        for info in tech_info:
            tk.Label(tech_card.inner, text=info, bg=self.theme["card_bg"],
                    fg=self.theme["text_secondary"], anchor="w",
                    font=("微软雅黑", 9)).pack(anchor="w", pady=1)

    def on_save(self):
        self.config_mgr.set("dark" if self.theme_var.get() else "light", "ui", "theme")
        self.config_mgr.set(int(self.font_size_var.get()), "ui", "font_size")
        self.config_mgr.set(int(self.name_size_var.get()), "ui", "name_font_size")
        self.config_mgr.set(int(self.text_size_var.get()), "ui", "text_font_size")
        self.config_mgr.set(float(self.anim_duration_var.get()), "ui", "animation_duration")
        self.config_mgr.set(float(self.ease_var.get()), "ui", "ease_strength")
        self.config_mgr.set(self.curve_var.get(), "ui", "animation_curve")
        self.config_mgr.set(self.particle_var.get(), "ui", "particle_enabled")
        self.config_mgr.set(int(self.particle_count_var.get()), "ui", "particle_count")
        self.config_mgr.set(self.start_anim_var.get(), "ui", "start_animation")
        self.config_mgr.set(int(self.start_anim_dur_var.get()), "ui", "start_anim_duration")
        self.config_mgr.set(self.status_bar_var.get(), "ui", "show_status_bar")
        self.config_mgr.set(self.result_popup_var.get(), "ui", "result_popup")
        self.config_mgr.set(int(self.popup_dur_var.get()), "ui", "popup_duration")
        self.config_mgr.set(self.countdown_var.get(), "ui", "draw_countdown")
        self.config_mgr.set(int(self.countdown_num_var.get()), "ui", "countdown_number")
        self.config_mgr.set(int(self.border_width_var.get()), "ui", "border_width")
        self.config_mgr.set(int(self.button_radius_var.get()), "ui", "button_radius")
        self.config_mgr.set(self.shadow_var.get(), "ui", "shadow_enabled")
        self.config_mgr.set(self.draw_mode_var.get(), "draw", "mode")
        self.config_mgr.set(self.no_repeat_var.get(), "draw", "no_repeat")
        self.config_mgr.set(self.auto_reset_var.get(), "draw", "auto_reset_round")
        self.config_mgr.set(float(self.auto_duration_var.get()), "draw", "auto_duration")
        self.config_mgr.set(self.dynamic_focus_var.get(), "draw", "dynamic_focus")
        self.config_mgr.set(self.dynamic_weight_var.get(), "draw", "dynamic_weight")
        self.config_mgr.set(float(self.rate_mastered_var.get()), "draw", "rate_mastered")
        self.config_mgr.set(float(self.rate_familiar_var.get()), "draw", "rate_familiar")
        self.config_mgr.set(float(self.rate_unlearned_var.get()), "draw", "rate_unlearned")
        self.config_mgr.set(int(self.history_limit_var.get()), "draw", "history_limit")
        self.config_mgr.set(self.anti_cheat_var.get(), "draw", "anti_cheat")
        self.config_mgr.set(self.extract_mode_var.get(), "text", "extract_mode")
        self.config_mgr.set(self.paragraph_random_var.get(), "text", "paragraph_random")
        self.config_mgr.set(self.show_title_var.get(), "text", "show_title")
        self.config_mgr.set(self.text_align_var.get(), "text", "text_align")
        self.config_mgr.set(self.shortcut_enabled_var.get(), "shortcut", "enabled")
        self.config_mgr.set(self.dpi_var.get(), "experimental", "dpi_optimization")
        self.config_mgr.set(self.smooth_scroll_var.get(), "experimental", "smooth_scroll")
        self.config_mgr.set(self.blur_bg_var.get(), "experimental", "blur_background")
        self.config_mgr.set(self.sound_var.get(), "experimental", "sound_effect")
        self.config_mgr.set(self.voice_var.get(), "experimental", "voice_broadcast")
        self.config_mgr.set(self.history_recall_var.get(), "experimental", "history_recall")
        self.config_mgr.set(self.anti_cheat_mode_var.get(), "experimental", "anti_cheat_mode")
        self.config_mgr.save_config()
        need_restart = self.config_mgr.check_restart_required()
        if need_restart:
            self.config_mgr.config = copy.deepcopy(self.config_mgr.old_config)
            if CustomMessageBox(self, self.theme, "需要重启",
                               "部分设置需要重启程序才能生效，是否立即重启？", "confirm"):
                self.destroy()
                restart_application()
            else:
                CustomMessageBox(self, self.theme, "提示", "设置已保存，下次启动程序时生效", "info")
                self.destroy()
        else:
            self.master_app._reload_settings()
            CustomMessageBox(self, self.theme, "成功", "设置已保存并生效", "info")
            self.destroy()

    def on_cancel(self):
        self.config_mgr.config = copy.deepcopy(self.config_mgr.old_config)
        self.destroy()


class StatsWindow(tk.Toplevel):
    def __init__(self, master, data_mgr, theme):
        super().__init__(master)
        self.data_mgr = data_mgr
        self.theme = theme
        self.overrideredirect(True)
        self.geometry("780x560")
        self.minsize(680, 460)
        self.config(bg=theme["bg"])
        outer = tk.Frame(self, bg=theme["card_bg"], highlightbackground=theme["border"],
                         highlightthickness=1)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=theme["primary"], height=46)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="📊", bg=theme["primary"], fg="white",
                font=("微软雅黑", 14)).pack(side="left", padx=(16, 6))
        tk.Label(header, text="抽取统计", bg=theme["primary"], fg="white",
                font=("微软雅黑", 13, "bold")).pack(side="left")
        RoundedButton(header, text="×", bg=theme["primary"], hover_bg=theme["primary_hover"],
                     fg="white", width=32, height=32, radius=16,
                     font=("微软雅黑", 12, "bold"), command=self.destroy).pack(side="right", padx=12, pady=7)
        toolbar = tk.Frame(outer, bg=theme["card_bg"])
        toolbar.pack(fill="x", padx=16, pady=(14, 10))
        tk.Label(toolbar, text="学生抽取统计", font=("微软雅黑", 14, "bold"),
                bg=theme["card_bg"], fg=theme["text_primary"]).pack(side="left")
        RoundedButton(toolbar, text="导出统计", style="primary", width=110, height=34,
                     font=("微软雅黑", 10, "bold"), command=self.export_stats).pack(side="right")
        table_frame = tk.Frame(outer, bg=theme["card_bg"])
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        columns = ("name", "draw_count", "mastered", "familiar", "unlearned", "score")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("name", text="学生姓名")
        self.tree.heading("draw_count", text="抽取次数")
        self.tree.heading("mastered", text="已背过")
        self.tree.heading("familiar", text="未背熟")
        self.tree.heading("unlearned", text="未背过")
        self.tree.heading("score", text="积分")
        for col in columns:
            self.tree.column(col, width=100, anchor="center")
        self.tree.column("name", width=180, anchor="center")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._populate_data()
        _center_window(self)
        self.after(60, lambda: apply_round_corner(self, 14))

    def _populate_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        stats = self.data_mgr.get_all_stats()
        for name, data in stats.items():
            try:
                self.tree.insert("", "end", values=(
                    name, data.get("draw_count", 0), data.get("mastered", 0),
                    data.get("familiar", 0), data.get("unlearned", 0), data.get("score", 0)
                ))
            except Exception:
                continue

    def export_stats(self):
        stats = self.data_mgr.get_all_stats()
        try:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.join(os.path.expanduser("~"), "桌面")
            if not os.path.exists(desktop):
                desktop = BASE_DIR
            filename = f"课堂点名统计_{ts}.txt"
            filepath = os.path.join(desktop, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=" * 50 + "\n")
                f.write("  A13 课堂点名系统 - 学生抽取统计报表\n")
                f.write(f"  导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"{'学生姓名':<12}{'抽取次数':<10}{'已背过':<8}{'未背熟':<8}{'未背过':<8}{'积分':<8}\n")
                f.write("-" * 50 + "\n")
                for name, data in stats.items():
                    f.write(f"{name:<12}{data.get('draw_count',0):<10}{data.get('mastered',0):<8}{data.get('familiar',0):<8}{data.get('unlearned',0):<8}{data.get('score',0):<8}\n")
                f.write("\n" + "=" * 50 + "\n")
                f.write(f"  共 {len(stats)} 名学生  |  A13 Engine V6.2\n")
            CustomMessageBox(self, self.theme, "导出成功",
                           f"统计文件已导出到桌面！\n\n文件名：{filename}\n保存位置：{desktop}\n\n可在桌面找到该文件。", "info")
        except Exception as e:
            CustomMessageBox(self, self.theme, "导出失败", str(e), "error")


class RankingWindow(tk.Toplevel):
    def __init__(self, master, data_mgr, theme):
        super().__init__(master)
        self.data_mgr = data_mgr
        self.theme = theme
        self.overrideredirect(True)
        self.geometry("440x580")
        self.minsize(400, 480)
        self.config(bg=theme["bg"])
        outer = tk.Frame(self, bg=theme["card_bg"], highlightbackground=theme["border"],
                         highlightthickness=1)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=theme["primary"], height=46)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🏆", bg=theme["primary"], fg="white",
                font=("微软雅黑", 14)).pack(side="left", padx=(16, 6))
        tk.Label(header, text="积分排行榜", bg=theme["primary"], fg="white",
                font=("微软雅黑", 13, "bold")).pack(side="left")
        RoundedButton(header, text="×", bg=theme["primary"], hover_bg=theme["primary_hover"],
                     fg="white", width=32, height=32, radius=16,
                     font=("微软雅黑", 12, "bold"), command=self.destroy).pack(side="right", padx=12, pady=7)
        scroll = ScrollableFrame(outer, theme)
        scroll.pack(fill="both", expand=True, padx=16, pady=16)
        content = scroll.scrollable_frame
        ranking = self.data_mgr.get_ranking()
        if not ranking:
            tk.Label(content, text="暂无积分数据\n抽取学生后自动统计",
                    bg=theme["card_bg"], fg=theme["text_hint"],
                    font=("微软雅黑", 12), justify="center").pack(pady=40)
        else:
            for i, (name, score) in enumerate(ranking[:30], 1):
                row = tk.Frame(content, bg=theme["card_bg"])
                row.pack(fill="x", pady=3)
                if i == 1:
                    medal = "🥇"
                    row_bg = "#fef3c7"
                    rank_fg = "#92400e"
                elif i == 2:
                    medal = "🥈"
                    row_bg = "#f1f5f9"
                    rank_fg = "#475569"
                elif i == 3:
                    medal = "🥉"
                    row_bg = "#fed7aa"
                    rank_fg = "#9a3412"
                else:
                    medal = f" {i} "
                    row_bg = theme["border_light"]
                    rank_fg = theme["text_secondary"]
                rank_label = tk.Label(row, text=medal, bg=row_bg, fg=rank_fg,
                                     font=("微软雅黑", 11, "bold"), width=4)
                rank_label.pack(side="left")
                name_frame = tk.Frame(row, bg=theme["card_bg"])
                name_frame.pack(side="left", fill="x", expand=True, padx=10)
                tk.Label(name_frame, text=name, font=("微软雅黑", 11),
                        bg=theme["card_bg"], fg=theme["text_primary"], anchor="w").pack(fill="x")
                tk.Label(row, text=f"{score} 分", font=("微软雅黑", 11, "bold"),
                        bg=theme["card_bg"], fg=theme["primary"]).pack(side="right")
        _center_window(self)
        self.after(60, lambda: apply_round_corner(self, 14))


class QuickDrawSettingsWindow(tk.Toplevel):
    def __init__(self, master, config_mgr, theme, on_save=None):
        super().__init__(master)
        self.config_mgr = config_mgr
        self.theme = theme
        self.on_save = on_save
        self.overrideredirect(True)
        self.title("快捷抽取设置")
        w, h = 460, 580
        self.geometry(f"{w}x{h}")
        self.minsize(w, h)
        self.config(bg="#1d4ed8")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
        self.attributes("-topmost", True)

        outer = tk.Frame(self, bg=theme["card_bg"])
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        header = tk.Frame(outer, bg="#2563eb", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⚡ 快捷抽取设置", bg="#2563eb", fg="white",
                font=("微软雅黑", 14, "bold")).pack(side="left", padx=18)
        tk.Button(header, text="✕", bg="#2563eb", fg="white", activebackground="#dc2626",
                  activeforeground="white", bd=0, font=("微软雅黑", 12, "bold"),
                  cursor="hand2", padx=10, command=self.destroy).pack(side="right", padx=(0, 10))

        body = tk.Frame(outer, bg=theme["card_bg"])
        body.pack(fill="both", expand=True, padx=20, pady=16)

        canvas = tk.Canvas(body, bg=theme["card_bg"], highlightthickness=0, bd=0)
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=theme["card_bg"])
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=w - 60)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.vars = {}

        def add_section(title):
            tk.Label(scroll_frame, text=title, bg=theme["card_bg"], fg=theme["primary"],
                    font=("微软雅黑", 11, "bold")).pack(anchor="w", pady=(12, 6))

        def add_check(key, label, default=True):
            var = tk.BooleanVar(value=self.config_mgr.get("quick_draw", key) if self.config_mgr.get("quick_draw", key) is not None else default)
            self.vars[key] = var
            row = tk.Frame(scroll_frame, bg=theme["card_bg"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=theme["card_bg"], fg=theme["text_primary"],
                    font=("微软雅黑", 10)).pack(side="left")
            ToggleSwitch(row, variable=var, on_color=theme["primary"],
                         off_color="#cbd5e1", width=48, height=26).pack(side="right")

        def add_spin(key, label, from_, to, default):
            val = self.config_mgr.get("quick_draw", key)
            if val is None:
                val = default
            var = tk.IntVar(value=val)
            self.vars[key] = var
            row = tk.Frame(scroll_frame, bg=theme["card_bg"])
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=theme["card_bg"], fg=theme["text_primary"],
                    font=("微软雅黑", 10)).pack(side="left")
            tk.Spinbox(row, from_=from_, to=to, textvariable=var, width=6,
                      font=("微软雅黑", 10)).pack(side="right")

        add_section("窗口行为")
        add_check("always_on_top", "窗口始终置顶", True)
        add_check("auto_hide", "抽取后自动隐藏窗口", False)
        add_check("confirm_on_close", "关闭时确认提示", True)

        add_section("抽取规则")
        add_check("no_repeat", "不重复抽取（本轮）", True)
        add_check("show_count", "显示已抽取人数", True)
        add_spin("animation_duration", "滚动动画时长（秒）", 1, 6, 2)
        add_spin("name_font_size", "名字字体大小", 24, 72, 48)

        add_section("其他")
        add_check("show_history", "显示抽取历史列表", True)
        add_check("sound_enabled", "抽取完成提示音", False)

        btn_frame = tk.Frame(outer, bg="#f1f5f9")
        btn_frame.pack(fill="x")
        tk.Button(btn_frame, text="取消", bg="#f1f5f9", fg="#64748b",
                  activebackground="#e2e8f0", bd=0, font=("微软雅黑", 10),
                  cursor="hand2", padx=20, pady=8, command=self.destroy).pack(side="right", padx=8, pady=12)
        tk.Button(btn_frame, text="保存设置", bg="#2563eb", fg="white",
                  activebackground="#1d4ed8", bd=0, font=("微软雅黑", 10, "bold"),
                  cursor="hand2", padx=20, pady=8, command=self._save).pack(side="right", pady=12)

        self.after(50, lambda: apply_round_corner(self, 12))

    def _save(self):
        for key, var in self.vars.items():
            self.config_mgr.set(var.get(), "quick_draw", key)
        self.config_mgr.save_config()
        if self.on_save:
            self.on_save()
        self.destroy()


class QuickDrawWindow(tk.Toplevel):
    def __init__(self, master, config_mgr, data_mgr, theme, on_return=None):
        super().__init__(master)
        self.master_app = master
        self.config_mgr = config_mgr
        self.data_mgr = data_mgr
        self.theme = theme
        self.on_return = on_return
        self.drawn_names = []
        self.is_rolling = False
        self._roll_job = None
        self._temp_file = None

        qd = self.config_mgr.get("quick_draw") or {}
        w = qd.get("window_width", 420)
        h = qd.get("window_height", 520)
        self.overrideredirect(True)
        self.title("快捷抽取")
        self.geometry(f"{w}x{h}")
        self.minsize(380, 460)
        self.config(bg="#1d4ed8")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
        if qd.get("always_on_top", True):
            self.attributes("-topmost", True)

        self._create_temp_file()

        outer = tk.Frame(self, bg=theme["card_bg"])
        outer.pack(fill="both", expand=True, padx=2, pady=2)

        header = tk.Frame(outer, bg="#2563eb", height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._drag_x = 0
        self._drag_y = 0
        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)
        tk.Label(header, text="⚡ 快捷抽取", bg="#2563eb", fg="white",
                font=("微软雅黑", 13, "bold")).pack(side="left", padx=16)
        tk.Button(header, text="⚙", bg="#2563eb", fg="white", activebackground="#1d4ed8",
                  activeforeground="white", bd=0, font=("微软雅黑", 13),
                  cursor="hand2", padx=8, command=self._open_settings).pack(side="right", padx=(0, 4))
        tk.Button(header, text="—", bg="#2563eb", fg="white", activebackground="#1d4ed8",
                  activeforeground="white", bd=0, font=("微软雅黑", 14),
                  cursor="hand2", padx=8, command=self._minimize).pack(side="right")
        tk.Button(header, text="✕", bg="#2563eb", fg="white", activebackground="#dc2626",
                  activeforeground="white", bd=0, font=("微软雅黑", 11, "bold"),
                  cursor="hand2", padx=8, command=self._on_close).pack(side="right", padx=(0, 8))

        self.count_label = tk.Label(outer, text="已抽取：0 人", bg=theme["card_bg"],
                                    fg=theme["primary"], font=("微软雅黑", 10, "bold"))
        if qd.get("show_count", True):
            self.count_label.pack(pady=(10, 0))

        self.status_label = tk.Label(outer, text="● 就绪", bg=theme["card_bg"],
                                     fg="#10b981", font=("微软雅黑", 10, "bold"))
        self.status_label.pack(pady=(4, 0))

        self.draw_area = tk.Frame(outer, bg=theme["bg"])
        self.draw_area.pack(fill="both", expand=True, padx=20, pady=12)

        self.name_label = tk.Label(self.draw_area, text="点击下方按钮\n开始抽取",
                                   bg=theme["bg"], fg=theme["text_hint"],
                                   font=("微软雅黑", qd.get("name_font_size", 48), "bold"),
                                   justify="center")
        self.name_label.pack(expand=True)

        self.draw_btn = tk.Button(outer, text="🎲  点击抽取  🎲", bg="#f59e0b", fg="white",
                                  activebackground="#d97706", activeforeground="white",
                                  bd=0, font=("微软雅黑", 16, "bold"), cursor="hand2",
                                  padx=50, pady=14, command=self._do_draw)
        self.draw_btn.pack(pady=(0, 12))

        if qd.get("show_history", True):
            hist_frame = tk.Frame(outer, bg=theme["card_bg"])
            hist_frame.pack(fill="x", padx=20, pady=(0, 8))
            tk.Label(hist_frame, text="📋 本次抽取记录", bg=theme["card_bg"],
                    fg=theme["text_secondary"], font=("微软雅黑", 9, "bold")).pack(anchor="w")
            self.history_list = tk.Listbox(hist_frame, height=4, bg=theme["bg"],
                                            fg=theme["text_primary"], font=("微软雅黑", 9),
                                            bd=0, highlightthickness=1,
                                            highlightcolor=theme["border"],
                                            highlightbackground=theme["border"])
            self.history_list.pack(fill="x", pady=(4, 0))

        bottom = tk.Frame(outer, bg="#f1f5f9")
        bottom.pack(fill="x")
        tk.Button(bottom, text="↩ 返回主界面", bg="#f1f5f9", fg="#2563eb",
                  activebackground="#e2e8f0", bd=0, font=("微软雅黑", 10, "bold"),
                  cursor="hand2", padx=16, pady=8, command=self._return_main).pack(side="left", padx=16, pady=10)
        tk.Button(bottom, text="🔄 重置本轮", bg="#f1f5f9", fg="#ef4444",
                  activebackground="#e2e8f0", bd=0, font=("微软雅黑", 10),
                  cursor="hand2", padx=16, pady=8, command=self._reset_round).pack(side="right", padx=16, pady=10)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Map>", self._on_window_map)
        self.update_idletasks()
        self.after(100, lambda: apply_round_corner(self, 12))
        self.after(300, lambda: apply_round_corner(self, 12))
        self.after(600, lambda: apply_round_corner(self, 12))

    def _create_temp_file(self):
        try:
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._temp_file = os.path.join(BASE_DIR, f"quick_draw_{ts}.txt")
            with open(self._temp_file, "w", encoding="utf-8") as f:
                f.write(f"快捷抽取临时记录 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 40 + "\n\n")
        except Exception:
            self._temp_file = None

    def _do_draw(self):
        try:
            if self.is_rolling:
                return
            students, error = self.data_mgr.load_students()
            if not students:
                self.name_label.config(text="名单为空\n请先添加学生", fg="#ef4444")
                return
            qd = self.config_mgr.get("quick_draw") or {}
            no_repeat = qd.get("no_repeat", True)
            available = [s for s in students if s not in self.drawn_names] if no_repeat else list(students)
            if not available:
                self.name_label.config(text="本轮已全部抽完\n请重置本轮", fg="#f59e0b")
                return
            self.is_rolling = True
            self.draw_btn.config(state="disabled", bg="#94a3b8")
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.config(text="● 抽取中...", fg="#f59e0b")
            duration = qd.get("animation_duration", 2)
            import random
            import time
            start = time.time()
            def roll():
                try:
                    if not self.winfo_exists():
                        return
                    if time.time() - start < duration:
                        name = random.choice(available)
                        self.name_label.config(text=name, fg=self.theme["primary"])
                        self._roll_job = self.after(50, roll)
                    else:
                        cname = random.choice(available)
                        self.name_label.config(text=cname, fg="#10b981")
                        self.drawn_names.append(cname)
                        if hasattr(self, 'count_label') and self.count_label.winfo_exists():
                            self.count_label.config(text=f"已抽取：{len(self.drawn_names)} 人")
                        if hasattr(self, 'history_list') and self.history_list.winfo_exists():
                            self.history_list.insert(tk.END, f"{len(self.drawn_names)}. {cname}")
                            self.history_list.see(tk.END)
                        self._append_temp(cname)
                        self.is_rolling = False
                        if self.draw_btn.winfo_exists():
                            self.draw_btn.config(state="normal", bg="#f59e0b")
                        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                            self.status_label.config(text="● 就绪", fg="#10b981")
                        if qd.get("auto_hide", False):
                            self.after(1500, self._minimize)
                except Exception:
                    self.is_rolling = False
                    try:
                        if self.draw_btn.winfo_exists():
                            self.draw_btn.config(state="normal", bg="#f59e0b")
                    except Exception:
                        pass
            roll()
        except Exception as e:
            self.is_rolling = False
            try:
                if self.draw_btn.winfo_exists():
                    self.draw_btn.config(state="normal", bg="#f59e0b")
                self.name_label.config(text=f"抽取出错\n{str(e)[:20]}", fg="#ef4444")
            except Exception:
                pass

    def _append_temp(self, name):
        if not self._temp_file:
            return
        try:
            from datetime import datetime
            with open(self._temp_file, "a", encoding="utf-8") as f:
                f.write(f"{datetime.now().strftime('%H:%M:%S')}  {name}\n")
        except Exception:
            pass

    def _reset_round(self):
        try:
            self.drawn_names = []
            if self.name_label.winfo_exists():
                self.name_label.config(text="点击下方按钮\n开始抽取", fg=self.theme["text_hint"])
            if hasattr(self, 'count_label') and self.count_label.winfo_exists():
                self.count_label.config(text="已抽取：0 人")
            if hasattr(self, 'history_list') and self.history_list.winfo_exists():
                self.history_list.delete(0, tk.END)
        except Exception:
            pass

    def _open_settings(self):
        QuickDrawSettingsWindow(self, self.config_mgr, self.theme, on_save=self._apply_settings)

    def _apply_settings(self):
        try:
            qd = self.config_mgr.get("quick_draw") or {}
            if self.name_label.winfo_exists():
                self.name_label.config(font=("微软雅黑", qd.get("name_font_size", 48), "bold"))
            if qd.get("always_on_top", True):
                self.attributes("-topmost", True)
            else:
                self.attributes("-topmost", False)
            if qd.get("show_count", True):
                if self.count_label.winfo_exists():
                    self.count_label.pack(pady=(10, 0))
            else:
                if self.count_label.winfo_exists():
                    self.count_label.pack_forget()
        except Exception:
            pass

    def _minimize(self):
        try:
            self.update_idletasks()
            self.overrideredirect(False)
            self.iconify()
        except Exception:
            pass

    def _on_window_map(self, event=None):
        try:
            if not self.overrideredirect():
                self.overrideredirect(True)
                self.after(30, lambda: apply_round_corner(self, 12))
        except Exception:
            pass

    def _start_drag(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _return_main(self):
        if self.on_return:
            self.on_return()
        self._cleanup_temp()
        self.destroy()

    def _on_close(self):
        qd = self.config_mgr.get("quick_draw") or {}
        if qd.get("confirm_on_close", True):
            result = CustomMessageBox(self, self.theme, "关闭快捷抽取",
                f"本次共抽取 {len(self.drawn_names)} 人。\n\n"
                "⚠ 快捷抽取的记录为临时文件，关闭后将自动删除，\n"
                "如需保留请先复制记录内容。\n\n"
                "确定关闭吗？", "confirm")
            if not result:
                return
        if self.on_return:
            self.on_return()
        self._cleanup_temp()
        self.destroy()

    def _cleanup_temp(self):
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except Exception:
                pass
        if self._roll_job:
            try:
                self.after_cancel(self._roll_job)
            except Exception:
                pass


class ShortcutHelpWindow(tk.Toplevel):
    def __init__(self, master, theme, on_close=None):
        super().__init__(master)
        self.theme = theme
        self.on_close = on_close
        self.title("快捷键速查")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.config(bg="#1d4ed8")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 560, 640
        x = (sw - w) // 2
        y = max(40, (sh - h) // 3)
        self.geometry(f"{w}x{h}+{x}+{y}")

        header = tk.Frame(self, bg="#2563eb", height=52)
        header.pack(fill="x", padx=2, pady=(2, 0))
        header.pack_propagate(False)
        self._drag_x = 0
        self._drag_y = 0
        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)
        tk.Label(header, text="⌨ 快捷键速查", bg="#2563eb", fg="white",
                font=("微软雅黑", 15, "bold")).pack(side="left", padx=20)
        tk.Button(header, text="✕", bg="#2563eb", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, font=("微软雅黑", 13, "bold"), cursor="hand2",
                  padx=10, pady=4, command=self._close).pack(side="right", padx=(0, 8))

        body = tk.Frame(self, bg="#f8fafc")
        body.pack(fill="both", expand=True, padx=2, pady=0)

        canvas = tk.Canvas(body, bg="#f8fafc", highlightthickness=0)
        scrollbar = tk.Scrollbar(body, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#f8fafc")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=w - 20)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        groups = [
            ("🎯 抽取操作", [
                ("空格", "开始 / 停止抽取"),
                ("Esc", "重置本轮"),
                ("N", "切换不重复模式"),
                ("W", "切换动态权重"),
                ("R", "查看本轮记录"),
            ]),
            ("✅ 状态标记", [
                ("1", "标记已背过"),
                ("2", "标记未背熟"),
                ("3", "标记未背过"),
                ("Z", "撤销上次标记"),
                ("Tab", "跳过当前"),
            ]),
            ("📄 课文与界面", [
                ("T", "切换抽取模式"),
                ("←", "上一篇课文"),
                ("→", "下一篇课文"),
                ("M", "切换主题"),
                (",", "打开设置"),
            ]),
            ("✨ 显示与效果", [
                ("P", "粒子效果开关"),
                ("F11", "全屏模式"),
                ("L", "排行榜"),
                ("Ctrl+S", "保存数据"),
                ("?", "快捷键速查"),
            ]),
        ]

        for group_title, items in groups:
            g_frame = tk.Frame(scroll_frame, bg="#e2e8f0")
            g_frame.pack(fill="x", pady=6, padx=4)
            g_inner = tk.Frame(g_frame, bg="white")
            g_inner.pack(fill="x", padx=1, pady=1)
            tk.Label(g_inner, text=group_title, bg="white", fg="#2563eb",
                    font=("微软雅黑", 11, "bold")).pack(anchor="w", padx=14, pady=(10, 6))
            for key, desc in items:
                row = tk.Frame(g_inner, bg="white")
                row.pack(fill="x", padx=14, pady=2)
                key_label = tk.Label(row, text=key, bg="#eff6ff", fg="#2563eb",
                                     font=("Consolas", 10, "bold"), padx=8, pady=2)
                key_label.pack(side="left")
                tk.Label(row, text=desc, bg="white", fg="#475569",
                        font=("微软雅黑", 10)).pack(side="left", padx=12)
            tk.Frame(g_inner, bg="white", height=6).pack()

        footer = tk.Frame(self, bg="#f1f5f9")
        footer.pack(fill="x", side="bottom", padx=2, pady=(0, 2))
        tk.Label(footer, text="按 ? 或 / 可随时打开此窗口", bg="#f1f5f9", fg="#94a3b8",
                font=("微软雅黑", 9)).pack(pady=8)

        self.update_idletasks()
        self.after(50, lambda: apply_round_corner(self, 14))
        self.after(200, lambda: apply_round_corner(self, 14))
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _start_drag(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _close(self):
        if self.on_close:
            self.on_close()
        self.destroy()


class MainApp(tk.Tk):
    def __init__(self, show_first_tip=False):
        super().__init__()
        self.show_first_tip = show_first_tip
        self.title("A13 课堂背诵点名系统 V6.2")
        self.geometry("1280x1100")
        self.minsize(1000, 700)
        self.overrideredirect(True)
        self._is_maximized = False
        self._normal_geometry = ""
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        cx = (sw - 1280) // 2
        cy = max(0, (sh - 1100) // 2)
        self.geometry(f"1280x1100+{cx}+{cy}")
        icon_path = os.path.join(BASE_DIR, "app.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        self.config_mgr = ConfigManager()
        self.data_mgr = DataManager(self.config_mgr)
        self.draw_engine = DrawEngine(self.data_mgr, self.config_mgr)
        theme_name = self.config_mgr.get("ui", "theme")
        self.theme = DARK_THEME if theme_name == "dark" else LIGHT_THEME
        self.config(bg=self.theme["bg"])
        if self.config_mgr.get("experimental", "dpi_optimization"):
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass
        opacity = self.config_mgr.get("ui", "window_opacity")
        if opacity and opacity < 1.0:
            self.attributes("-alpha", opacity)
        self.students = []
        self.texts = []
        self.current_text = None
        self.current_paragraph = ""
        self.current_paragraph_info = ""
        self.selected_text_index = 0
        self.selected_paragraph_index = None
        self.text_mode = "random"
        self._countdown_active = False
        self._weight_tip_index = 0
        self._weight_tip_text = ""
        self._mark_history = []
        self._is_fullscreen = False
        self._shortcut_help_open = False
        self._current_marked = False
        self.withdraw()
        self.splash = None
        if self.config_mgr.get("ui", "start_animation"):
            duration = self.config_mgr.get("ui", "start_anim_duration") or 2500
            self.splash = SplashScreen(self, self.theme, duration)
            self.splash.set_status("加载配置...")
        self._load_all_data()
        self._init_stats()
        self._setup_ttk_style()
        self._build_ui()
        self._bind_shortcuts()
        self._update_weight_tip()
        self._start_weight_scroll()
        if self.splash:
            self.splash.set_status("初始化完成")
            self.after(800, lambda: self.splash.show_launch_choices(
                on_main=self._show_main_window,
                on_quick=self._show_main_and_quick_draw,
                config_mgr=self.config_mgr
            ))
        else:
            self._show_main_window()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Map>", self._on_window_map)

    def _on_window_map(self, event):
        try:
            if not self.overrideredirect():
                self.overrideredirect(True)
                self.after(30, self._apply_window_round)
        except Exception:
            pass

    def _show_main_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.update_idletasks()
        self.after(100, self._apply_window_round)
        self.after(300, self._apply_window_round)
        self.after(600, self._apply_window_round)
        if self.show_first_tip:
            self.after(800, self._show_floating_guide)

    def _show_main_and_quick_draw(self):
        self.update_idletasks()
        self._open_quick_draw()

    def _show_floating_guide(self):
        steps = [
            {
                "title": "欢迎使用",
                "text": "欢迎来到 A13 课堂点名系统 V6.2！\n\n接下来带你亲手操作一遍核心流程，跟着提示点击对应按钮即可。",
                "cards": [
                    {"title": "本次引导流程", "content": "① 抽取学生 → ② 标记状态 → ③ 再抽取 → ④ 再标记 → ⑤ 查看记录 → ⑥ 重置本轮 → ⑦ 快捷抽取"},
                ],
                "widget": None,
            },
            {
                "title": "第1次抽取",
                "text": "点击中间的大画布（或按空格键），启动随机点名滚动。\n\n滚动停止后会显示抽中的学生姓名。",
                "highlight": "请现在点击画布完成第一次抽取",
                "widget": self.draw_canvas,
                "check": lambda: len(self.draw_engine.drawn_history) >= 1,
                "check_msg": "请先点击画布完成第一次抽取，再点击下一步",
            },
            {
                "title": "标记背诵状态",
                "text": "抽取完成后，在左侧「状态标记」区点击对应按钮记录背诵情况：",
                "cards": [
                    {"title": "✅ 已背过", "content": "绿色按钮，加 10 分，快捷键 1"},
                    {"title": "⚠️ 未背熟", "content": "黄色按钮，扣 5 分，快捷键 2"},
                    {"title": "❌ 未背过", "content": "红色按钮，扣 15 分，快捷键 3"},
                ],
                "highlight": "请点击「已背过」标记第一位学生",
                "widget": self.btn_mastered,
                "check": lambda: len(self.draw_engine.drawn_history) >= 1 and self.draw_engine.drawn_history[0].get("status", "") != "未标记",
                "check_msg": "请先点击状态按钮标记第一位学生的背诵情况，再点击下一步",
            },
            {
                "title": "第2次抽取",
                "text": "再次点击画布（或按空格键）抽取第二位学生。\n\n开启「不重复抽取」后，已抽过的学生本轮不会再被抽到。",
                "highlight": "请再次点击画布抽取第二位学生",
                "widget": self.draw_canvas,
                "check": lambda: len(self.draw_engine.drawn_history) >= 2,
                "check_msg": "请先点击画布完成第二次抽取，再点击下一步",
            },
            {
                "title": "再次标记状态",
                "text": "第二位学生抽取完成后，根据实际背诵情况选择标记。\n\n这次试试点击「未背熟」（黄色按钮）。",
                "highlight": "请点击「未背熟」标记第二位学生",
                "widget": self.btn_familiar,
                "check": lambda: len(self.draw_engine.drawn_history) >= 2 and self.draw_engine.drawn_history[1].get("status", "") != "未标记",
                "check_msg": "请先点击状态按钮标记第二位学生的背诵情况，再点击下一步",
            },
            {
                "title": "查看本轮记录",
                "text": "点击左侧「本轮记录」按钮，可以查看本次所有抽取结果和对应状态，方便课后回顾。",
                "cards": [
                    {"title": "记录内容", "content": "序号、学生姓名、抽取时间、背诵状态，一目了然"},
                ],
                "widget": self.btn_history,
            },
            {
                "title": "重置本轮",
                "text": "点击「重置本轮」清空当前所有已抽记录，所有学生重新进入抽取池，开始新一轮点名。",
                "highlight": "重置后历史记录不会丢失，仅清空本轮抽取队列",
                "widget": self.btn_reset,
            },
            {
                "title": "系统设置",
                "text": "点击右上角「设置」打开系统设置面板，可调整各项参数。",
                "cards": [
                    {"title": "设置面板包含", "content": "界面外观 / 抽取规则 / 课文抽取 / 学生权重 / 快捷键 / 数据文件 / 实验功能 / 危险操作 / 关于"},
                ],
                "highlight": "设置窗口内容较多，记得用鼠标滚轮下滑查看更多选项！",
                "widget": self.btn_settings,
            },
            {
                "title": "快捷抽取模式",
                "text": "顶部的「⚡ 快捷抽取」橙色按钮可以打开极简抽取窗口！\n\n适合只需要快速点名、不需要课文抽取的场景。",
                "cards": [
                    {"title": "快捷抽取特点", "content": "✓ 极简界面，一键抽取\n✓ 不抽取课文，纯点名\n✓ 独立设置，可置顶\n✓ 临时记录，关闭自动删除\n✓ 一键返回主界面"},
                    {"title": "⚠ 重要提示", "content": "快捷抽取的记录为临时文件（日期+时间.txt），关闭窗口后自动删除，不会保存到主程序记录中。如需保留请手动复制。"},
                ],
                "highlight": "点击顶部「⚡ 快捷抽取」橙色按钮体验",
                "widget": self.quick_draw_btn,
            },
            {
                "title": "引导完成",
                "text": "你已经完成了核心操作练习！\n\n更多功能等你探索：",
                "cards": [
                    {"title": "顶部功能栏", "content": "📊 统计 — 查看抽取数据，可导出到桌面\n🏆 排行榜 — 查看积分排名\n🔄 刷新名单 — 重载学生数据"},
                    {"title": "快捷抽取", "content": "⚡ 右下角按钮 — 极简点名窗口，临时记录\n⚙ 独立设置 — 置顶/动画/不重复等"},
                    {"title": "设置 → 关于", "content": "🌐 访问官网 / 📖 重新教学 / 🔧 重新运行向导 / 🎨 定制班级专属版"},
                ],
                "highlight": "祝你使用愉快，课堂点名高效顺畅！",
                "widget": None,
            },
        ]
        SpotlightGuide(self, self.theme, steps)

    def _setup_ttk_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Treeview", font=("微软雅黑", 10), rowheight=28,
                       background=self.theme["card_bg"], foreground=self.theme["text_primary"],
                       fieldbackground=self.theme["card_bg"], borderwidth=0)
        style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"),
                       background=self.theme["border_light"], foreground=self.theme["text_primary"])
        style.map("Treeview", background=[("selected", self.theme["primary_light"])])

    def _load_all_data(self):
        if self.splash:
            self.splash.set_status("加载学生名单...")
        self.students, _ = self.data_mgr.load_students()
        if self.splash:
            self.splash.set_status("加载课文库...")
        self._load_texts()
        self.draw_engine.set_student_list(self.students)

    def _load_texts(self):
        self.texts, _ = self.data_mgr.load_texts()

    def _init_stats(self):
        self.data_mgr.load_stats()
        self.data_mgr._init_stats_for_new_students(self.students)
        self.data_mgr.save_stats()

    def _build_ui(self):
        self._build_top_bar()
        content = tk.Frame(self, bg=self.theme["bg"])
        content.pack(fill="both", expand=True)
        self._build_sidebar(content)
        self._build_center(content)
        if self.config_mgr.get("ui", "show_status_bar"):
            self._build_status_bar()
            self._update_status_bar()

    def _build_top_bar(self):
        top_bar = tk.Frame(self, bg=self.theme["card_bg"], height=76)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        left = tk.Frame(top_bar, bg=self.theme["card_bg"])
        left.pack(side="left", padx=24, pady=10)
        icon_frame = tk.Frame(left, bg=self.theme["primary"], width=44, height=44)
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text="📚", bg=self.theme["primary"], fg="white",
                font=("微软雅黑", 20)).pack(expand=True)
        title_frame = tk.Frame(left, bg=self.theme["card_bg"])
        title_frame.pack(side="left")
        tk.Label(title_frame, text="A13 课堂点名系统", font=("微软雅黑", 17, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w")
        tk.Label(title_frame, text="V6.2  ·  第六代A13智能抽取引擎", font=("微软雅黑", 9),
                bg=self.theme["card_bg"], fg=self.theme["text_hint"]).pack(anchor="w", pady=(2, 0))
        right = tk.Frame(top_bar, bg=self.theme["card_bg"])
        right.pack(side="right", padx=16, pady=10)

        def _make_btn_col(parent, text, subtitle, style, width, cmd, icon=None):
            col = tk.Frame(parent, bg=self.theme["card_bg"])
            col.pack(side="left", padx=3)
            btn = RoundedButton(col, text=text, style=style, width=width, height=36,
                              command=cmd, icon=icon, font=("微软雅黑", 10, "bold"))
            btn.pack(pady=(4, 1))
            tk.Label(col, text=subtitle, bg=self.theme["card_bg"],
                    fg=self.theme["text_hint"], font=("微软雅黑", 8)).pack()
            return btn

        self.btn_settings = _make_btn_col(right, "设置", "系统配置", "ghost", 80, self._open_settings, icon="⚙")
        self.btn_stats = _make_btn_col(right, "统计", "数据统计", "ghost", 80, self._open_stats, icon="📊")
        self.btn_ranking = _make_btn_col(right, "排行榜", "积分排行", "ghost", 80, self._open_ranking, icon="🏆")
        self.btn_refresh = _make_btn_col(right, "刷新名单", "重载数据", "primary", 90, self._refresh_students, icon="🔄")

        qd_col = tk.Frame(top_bar, bg=self.theme["card_bg"])
        qd_col.pack(side="right", padx=(8, 4), pady=8)
        self.quick_draw_btn = tk.Button(qd_col, text="⚡ 快捷抽取", bg="#f59e0b", fg="white",
                                         activebackground="#d97706", activeforeground="white",
                                         bd=0, font=("微软雅黑", 12, "bold"), cursor="hand2",
                                         padx=20, pady=10, relief="flat", command=self._open_quick_draw)
        self.quick_draw_btn.pack()
        tk.Label(qd_col, text="极简点名模式", bg=self.theme["card_bg"],
                fg="#f59e0b", font=("微软雅黑", 8, "bold")).pack(pady=(2, 0))

        win_ctrl = tk.Frame(top_bar, bg=self.theme["card_bg"])
        win_ctrl.pack(side="right", padx=(20, 20), pady=14)
        self._win_min_btn = tk.Button(win_ctrl, text="最小化", bg=self.theme["card_bg"],
                                       fg=self.theme["text_secondary"], activebackground="#e2e8f0",
                                       activeforeground=self.theme["text_primary"], bd=0,
                                       font=("微软雅黑", 9), cursor="hand2", padx=10, pady=4,
                                       command=self._minimize_window)
        self._win_min_btn.pack(side="left", padx=2)
        self._win_max_btn = tk.Button(win_ctrl, text="最大化", bg=self.theme["card_bg"],
                                       fg=self.theme["text_secondary"], activebackground="#e2e8f0",
                                       activeforeground=self.theme["text_primary"], bd=0,
                                       font=("微软雅黑", 9), cursor="hand2", padx=10, pady=4,
                                       command=self._toggle_maximize)
        self._win_max_btn.pack(side="left", padx=2)
        self._win_close_btn = tk.Button(win_ctrl, text="关闭", bg=self.theme["card_bg"],
                                         fg=self.theme["text_secondary"], activebackground="#ef4444",
                                         activeforeground="white", bd=0,
                                         font=("微软雅黑", 9, "bold"), cursor="hand2", padx=10, pady=4,
                                         command=self._on_close)
        self._win_close_btn.pack(side="left", padx=2)

        for widget in (top_bar, left, title_frame, icon_frame):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<Double-Button-1>", lambda e: self._toggle_maximize())

        shadow = tk.Frame(self, bg=self.theme["border"], height=1)
        shadow.pack(fill="x")

    def _build_sidebar(self, parent):
        sidebar_width = self.config_mgr.get("ui", "sidebar_width") or 300
        sidebar = tk.Frame(parent, bg=self.theme["sidebar_bg"], width=sidebar_width)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        card = Card(sidebar, self.theme, padding=16)
        card.pack(fill="x", padx=12, pady=12)
        tk.Label(card.inner, text="课文选择", font=("微软雅黑", 13, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w")
        mode_frame = tk.Frame(card.inner, bg=self.theme["card_bg"])
        mode_frame.pack(fill="x", pady=(12, 8))
        self.text_mode_var = tk.StringVar(value="random")
        tk.Radiobutton(mode_frame, text="随机抽取", variable=self.text_mode_var, value="random",
                      command=self._on_text_mode_change, bg=self.theme["card_bg"],
                      fg=self.theme["text_primary"], selectcolor=self.theme["card_bg"],
                      activebackground=self.theme["card_bg"]).pack(side="left")
        tk.Radiobutton(mode_frame, text="指定课文", variable=self.text_mode_var, value="指定",
                      command=self._on_text_mode_change, bg=self.theme["card_bg"],
                      fg=self.theme["text_primary"], selectcolor=self.theme["card_bg"],
                      activebackground=self.theme["card_bg"]).pack(side="left", padx=15)
        self.text_tree = ttk.Treeview(card.inner, show="tree", height=10)
        self.text_tree.pack(fill="x", pady=4)
        self.text_tree.bind("<<TreeviewSelect>>", self._on_text_select)
        self._populate_text_tree()
        card2 = Card(sidebar, self.theme, padding=16)
        card2.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(card2.inner, text="本轮管理", font=("微软雅黑", 13, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w")
        btn_row = tk.Frame(card2.inner, bg=self.theme["card_bg"])
        btn_row.pack(fill="x", pady=(12, 0))
        self.btn_history = RoundedButton(btn_row, text="📋 本轮记录", style="primary", width=110, height=38,
                     font=("微软雅黑", 10, "bold"), command=self._open_drawn_history)
        self.btn_history.pack(side="left", expand=True, fill="x", padx=2)
        self.btn_reset = RoundedButton(btn_row, text="🔄 重置本轮", style="warning", width=110, height=38,
                     font=("微软雅黑", 10, "bold"), command=self._reset_round)
        self.btn_reset.pack(side="left", expand=True, fill="x", padx=2)
        card3 = Card(sidebar, self.theme, padding=16)
        card3.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tk.Label(card3.inner, text="状态标记", font=("微软雅黑", 13, "bold"),
                bg=self.theme["card_bg"], fg=self.theme["text_primary"]).pack(anchor="w")
        tk.Label(card3.inner, text="抽取完成后标记当前学生状态",
                bg=self.theme["card_bg"], fg=self.theme["text_hint"],
                font=("微软雅黑", 10)).pack(anchor="w", pady=(4, 12))
        btn_grid = tk.Frame(card3.inner, bg=self.theme["card_bg"])
        btn_grid.pack(fill="x")
        self.btn_mastered = RoundedButton(btn_grid, text="✅ 已背过  (1)", style="success", height=40,
                     font=("微软雅黑", 10, "bold"), command=lambda: self._mark_current_status("已背过"))
        self.btn_mastered.pack(fill="x", pady=4)
        self.btn_familiar = RoundedButton(btn_grid, text="⚠️ 未背熟  (2)", style="warning", height=40,
                     font=("微软雅黑", 10, "bold"), command=lambda: self._mark_current_status("未背熟"))
        self.btn_familiar.pack(fill="x", pady=4)
        self.btn_unlearned = RoundedButton(btn_grid, text="❌ 未背过  (3)", style="danger", height=40,
                     font=("微软雅黑", 10, "bold"), command=lambda: self._mark_current_status("未背过"))
        self.btn_unlearned.pack(fill="x", pady=4)

    def _build_center(self, parent):
        center = tk.Frame(parent, bg=self.theme["bg"])
        center.pack(side="left", fill="both", expand=True, padx=20, pady=15)
        canvas_card = Card(center, self.theme, padding=0, height=280)
        canvas_card.pack(fill="x")
        canvas_card.pack_propagate(False)
        self.draw_canvas = DrawCanvas(canvas_card, self.theme)
        name_size = self.config_mgr.get("ui", "name_font_size") or 50
        self.draw_canvas.set_name_size(name_size)
        self.draw_canvas.pack(fill="both", expand=True)
        self.draw_canvas.bind("<Button-1>", lambda e: self._on_draw_click())
        text_card = Card(center, self.theme, padding=16, height=260)
        text_card.pack(fill="x", pady=(15, 0))
        text_card.pack_propagate(False)
        text_size = self.config_mgr.get("ui", "text_font_size") or 14
        self.text_display = tk.Text(text_card.inner, bg=self.theme["card_bg"],
                                    fg=self.theme["text_primary"],
                                    font=("微软雅黑", text_size), wrap="word",
                                    relief="flat", padx=4, pady=4,
                                    spacing1=4, spacing2=2)
        self.text_display.pack(fill="both", expand=True)
        self.text_display.insert("1.0", "抽取学生后将显示对应课文段落")
        self.text_display.config(state="disabled")

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self, bg=self.theme["status_bar_bg"], height=32)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        tk.Frame(self.status_bar, bg=self.theme["border"], height=1).pack(fill="x")
        left = tk.Frame(self.status_bar, bg=self.theme["status_bar_bg"])
        left.pack(side="left", padx=18, pady=4)
        self.student_status_label = tk.Label(left, text="👥 名单：加载中",
                                            bg=self.theme["status_bar_bg"],
                                            fg=self.theme["text_secondary"],
                                            font=("微软雅黑", 9))
        self.student_status_label.pack(side="left", padx=(0, 16))
        tk.Label(left, text="│", bg=self.theme["status_bar_bg"],
                fg=self.theme["border"], font=("微软雅黑", 9)).pack(side="left", padx=(0, 16))
        self.text_status_label = tk.Label(left, text="📖 课文：加载中",
                                         bg=self.theme["status_bar_bg"],
                                         fg=self.theme["text_secondary"],
                                         font=("微软雅黑", 9))
        self.text_status_label.pack(side="left", padx=(0, 16))
        tk.Label(left, text="│", bg=self.theme["status_bar_bg"],
                fg=self.theme["border"], font=("微软雅黑", 9)).pack(side="left", padx=(0, 16))
        self.round_progress_label = tk.Label(left, text="📋 本轮进度：0/0",
                                            bg=self.theme["status_bar_bg"],
                                            fg=self.theme["text_primary"],
                                            font=("微软雅黑", 9, "bold"))
        self.round_progress_label.pack(side="left")
        self.weight_tip_label = tk.Label(self.status_bar, text="",
                                        bg=self.theme["status_bar_bg"],
                                        fg=self.theme["warning"],
                                        font=("微软雅黑", 9, "bold"))
        self.weight_tip_label.pack(side="left", padx=30, pady=4)
        right = tk.Frame(self.status_bar, bg=self.theme["status_bar_bg"])
        right.pack(side="right", padx=18, pady=4)
        tk.Label(right, text="🔒 数据保护中",
                bg=self.theme["status_bar_bg"], fg=self.theme["success"],
                font=("微软雅黑", 9)).pack(side="right", padx=(12, 0))
        tk.Label(right, text="│", bg=self.theme["status_bar_bg"],
                fg=self.theme["border"], font=("微软雅黑", 9)).pack(side="right", padx=12)
        tk.Label(right, text="A13 Engine v6.2",
                bg=self.theme["status_bar_bg"], fg=self.theme["text_secondary"],
                font=("微软雅黑", 9)).pack(side="right", padx=(12, 0))
        tk.Label(right, text="│", bg=self.theme["status_bar_bg"],
                fg=self.theme["border"], font=("微软雅黑", 9)).pack(side="right", padx=12)
        self.draw_state_label = tk.Label(right, text="● 就绪",
                                        bg=self.theme["status_bar_bg"],
                                        fg=self.theme["success"],
                                        font=("微软雅黑", 9, "bold"))
        self.draw_state_label.pack(side="right")

    def _update_status_bar(self):
        if not hasattr(self, "status_bar") or not self.status_bar.winfo_exists():
            return
        if self.students:
            self.student_status_label.config(text=f"👥 名单：已就绪 ({len(self.students)}人)",
                                            fg=self.theme["success"])
        else:
            self.student_status_label.config(text="👥 名单：未加载", fg=self.theme["warning"])
        if self.texts:
            self.text_status_label.config(text=f"📖 课文：已就绪 ({len(self.texts)}篇)",
                                         fg=self.theme["success"])
        else:
            self.text_status_label.config(text="📖 课文：未加载", fg=self.theme["warning"])
        drawn_count = len(self.draw_engine.drawn_students)
        total = len(self.students)
        self.round_progress_label.config(text=f"📋 本轮进度：{drawn_count}/{total}")
        if self.draw_engine.is_drawing:
            self.draw_state_label.config(text="● 抽取中", fg=self.theme["primary"])
        else:
            self.draw_state_label.config(text="● 就绪", fg=self.theme["success"])

    def _update_weight_tip(self):
        if not hasattr(self, "weight_tip_label") or not self.weight_tip_label.winfo_exists():
            return
        special_students = []
        base_weight = 1
        for name in self.students:
            w = self.data_mgr.get_student_weight(name)
            if w != base_weight:
                special_students.append(name)
        if not special_students:
            dynamic = self.config_mgr.get("draw", "dynamic_focus")
            if dynamic:
                self._weight_tip_text = "动态重点抽取已开启，按背诵状态智能加权"
            else:
                self._weight_tip_text = "所有同学权重一致"
        else:
            self._weight_tip_text = "重点关注：" + "、".join(special_students)
        self.weight_tip_label.config(text=self._weight_tip_text)

    def _start_weight_scroll(self):
        if not hasattr(self, "weight_tip_label") or not self.weight_tip_label.winfo_exists():
            self.after(2000, self._start_weight_scroll)
            return
        text = self._weight_tip_text
        if len(text) > 20:
            self._weight_tip_index = (self._weight_tip_index + 1) % (len(text) + 10)
            display = text[self._weight_tip_index:self._weight_tip_index + 20]
            if self._weight_tip_index + 20 > len(text):
                display += " " * (self._weight_tip_index + 20 - len(text))
            self.weight_tip_label.config(text=display)
        else:
            self.weight_tip_label.config(text=text)
        self.after(300, self._start_weight_scroll)

    def _populate_text_tree(self):
        for item in self.text_tree.get_children():
            self.text_tree.delete(item)
        for i, text in enumerate(self.texts):
            text_id = self.text_tree.insert("", "end", text=text["title"], values=(i,))
            for j, para in enumerate(text["paragraphs"]):
                self.text_tree.insert(text_id, "end", text=f"第{j+1}段", values=(i, j))

    def _on_text_mode_change(self):
        self.text_mode = self.text_mode_var.get()

    def _on_text_select(self, event):
        selected = self.text_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.text_tree.item(item, "values")
        if len(values) >= 1:
            self.selected_text_index = int(values[0])
            self.selected_paragraph_index = int(values[1]) if len(values) >= 2 else None

    def _refresh_students(self):
        self.students, err = self.data_mgr.load_students()
        self.draw_engine.set_student_list(self.students)
        self.draw_engine.reset_round()
        self.draw_canvas.reset()
        self.data_mgr._init_stats_for_new_students(self.students)
        self._update_weight_tip()
        self._update_status_bar()
        if err:
            CustomMessageBox(self, self.theme, "提示", err, "warning")

    def _open_settings(self):
        self._unbind_shortcuts()
        SettingsWindow(self, self.config_mgr, self.theme)
        self._bind_shortcuts()

    def _open_stats(self):
        StatsWindow(self, self.data_mgr, self.theme)

    def _open_ranking(self):
        RankingWindow(self, self.data_mgr, self.theme)

    def _open_quick_draw(self):
        self.withdraw()
        def _on_return():
            self.deiconify()
            self.lift()
            self.focus_force()
        QuickDrawWindow(self, self.config_mgr, self.data_mgr, self.theme, on_return=_on_return)

    def _open_website(self):
        import webbrowser
        try:
            webbrowser.open(WEBSITE_URL)
        except Exception as e:
            CustomMessageBox(self, self.theme, "打开失败", f"无法打开官网：{str(e)}", "error")

    def _rerun_tutorial(self):
        """重新运行交互式界面教学引导"""
        self._show_floating_guide()

    def _rerun_wizard(self):
        """重新运行首次配置向导：重置ini标记并重启程序"""
        result = CustomMessageBox(self, self.theme, "重新运行向导",
                                 "确定要重新运行首次配置向导吗？\n\n程序将重启并打开向导，向导完成后可重新进入软件。",
                                 "confirm")
        if not result:
            return
        set_wizard_unfinished()
        CustomMessageBox(self, self.theme, "操作完成", "向导标记已重置，程序将自动重启", "info")
        restart_application()

    def _open_drawn_history(self):
        DrawnHistoryWindow(self, self.draw_engine, self.theme)

    def _bind_shortcuts(self):
        if not self.config_mgr.get("shortcut", "enabled"):
            return
        def safe(handler):
            def wrapper(event=None):
                if self._is_input_focused():
                    return
                handler()
            return wrapper
        self.bind_all("<space>", safe(self._on_draw_click))
        self.bind_all("<Escape>", safe(self._reset_round))
        self.bind_all("n", safe(self._toggle_no_repeat))
        self.bind_all("w", safe(self._toggle_dynamic_weight))
        self.bind_all("r", safe(self._open_drawn_history))
        self.bind_all("1", safe(lambda: self._mark_current_status("已背过")))
        self.bind_all("2", safe(lambda: self._mark_current_status("未背熟")))
        self.bind_all("3", safe(lambda: self._mark_current_status("未背过")))
        self.bind_all("z", safe(self._undo_last_mark))
        self.bind_all("<Tab>", safe(self._skip_current))
        self.bind_all("t", safe(self._toggle_draw_mode))
        self.bind_all("<Left>", safe(self._prev_text))
        self.bind_all("<Right>", safe(self._next_text))
        self.bind_all("m", safe(self._toggle_theme))
        self.bind_all(",", safe(self._open_settings))
        self.bind_all("p", safe(self._toggle_particle))
        self.bind_all("<F11>", safe(self._toggle_fullscreen))
        self.bind_all("l", safe(self._open_ranking))
        self.bind_all("<Control-s>", safe(self._save_data))
        self.bind_all("?", safe(self._show_shortcut_help))
        self.bind_all("/", safe(self._show_shortcut_help))

    def _is_input_focused(self):
        try:
            w = self.focus_get()
            if w is None:
                return False
            class_name = w.winfo_class()
            return class_name in ("Entry", "Text", "TEntry", "TCombobox", "Spinbox")
        except Exception:
            return False

    def _unbind_shortcuts(self):
        keys = ["<space>", "<Escape>", "n", "w", "r", "1", "2", "3", "z",
                "<Tab>", "t", "<Left>", "<Right>", "m", ",", "p", "<F11>",
                "l", "<Control-s>", "?", "/"]
        for key in keys:
            try:
                self.unbind_all(key)
            except Exception:
                pass

    def _reload_settings(self):
        theme_name = self.config_mgr.get("ui", "theme")
        new_theme = DARK_THEME if theme_name == "dark" else LIGHT_THEME
        if new_theme != self.theme:
            self.theme = new_theme
            CustomMessageBox(self, self.theme, "提示", "主题已切换，完整效果请重启程序", "info")
        if self.config_mgr.get("ui", "show_status_bar"):
            if not hasattr(self, "status_bar"):
                self._build_status_bar()
            else:
                self.status_bar.pack(fill="x")
            self._update_status_bar()
        else:
            if hasattr(self, "status_bar"):
                self.status_bar.pack_forget()
        name_size = self.config_mgr.get("ui", "name_font_size") or 50
        self.draw_canvas.set_name_size(name_size)
        self.draw_canvas.particles.count = self.config_mgr.get("ui", "particle_count") or 30
        self._unbind_shortcuts()
        self._bind_shortcuts()
        self._update_weight_tip()

    def _on_draw_click(self):
        if not self.students:
            CustomMessageBox(self, self.theme, "提示", "没有可用的学生名单，请先添加学生", "warning")
            return
        if self._countdown_active:
            return
        if self.draw_engine.current_name and not self._current_marked and not self.draw_engine.is_drawing:
            self._show_skip_confirm()
            return
        available = self.draw_engine.get_available_students()
        if not available and self.config_mgr.get("draw", "auto_reset_round"):
            self._reset_round()
            available = self.draw_engine.get_available_students()
            if not available:
                return
        if self.draw_engine.is_drawing:
            if self.config_mgr.get("draw", "mode") == "manual":
                self._finish_draw_process()
            return
        if self.config_mgr.get("ui", "draw_countdown"):
            self._start_countdown_then_draw()
        else:
            self._start_draw_process()

    def _show_skip_confirm(self):
        name = self.draw_engine.current_name
        dlg = tk.Toplevel(self)
        dlg.overrideredirect(True)
        dlg.attributes("-topmost", True)
        dlg.config(bg="#f59e0b")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 420, 220
        x = (sw - w) // 2
        y = sh // 4
        dlg.geometry(f"{w}x{h}+{x}+{y}")
        outer = tk.Frame(dlg, bg="white")
        outer.pack(fill="both", expand=True, padx=2, pady=2)
        header = tk.Frame(outer, bg="#f59e0b", height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="⚠ 未标记提醒", bg="#f59e0b", fg="white",
                font=("微软雅黑", 13, "bold")).pack(side="left", padx=16)
        body = tk.Frame(outer, bg="white")
        body.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(body, text=f"学生「{name}」尚未标记背诵状态", bg="white",
                fg="#1e293b", font=("微软雅黑", 12, "bold"), wraplength=360,
                justify="center").pack(pady=(8, 4))
        tk.Label(body, text="请选择操作：", bg="white", fg="#64748b",
                font=("微软雅黑", 10)).pack(pady=(0, 12))
        btn_row = tk.Frame(body, bg="white")
        btn_row.pack(fill="x")
        def _do_mark():
            dlg.destroy()
        def _do_skip():
            self._skip_current_student()
            dlg.destroy()
            self.after(100, self._start_draw_process)
        tk.Button(btn_row, text="✏ 去标记", bg="#2563eb", fg="white",
                  activebackground="#1d4ed8", activeforeground="white",
                  bd=0, font=("微软雅黑", 11, "bold"), cursor="hand2",
                  padx=24, pady=10, command=_do_mark).pack(side="left", expand=True, fill="x", padx=(0, 6))
        tk.Button(btn_row, text="⏭ 略过此学生", bg="#ef4444", fg="white",
                  activebackground="#dc2626", activeforeground="white",
                  bd=0, font=("微软雅黑", 11, "bold"), cursor="hand2",
                  padx=24, pady=10, command=_do_skip).pack(side="right", expand=True, fill="x", padx=(6, 0))
        dlg.after(50, lambda: apply_round_corner(dlg, 12))
        dlg.after(200, lambda: apply_round_corner(dlg, 12))

    def _skip_current_student(self):
        name = self.draw_engine.current_name
        if not name:
            return
        text_title = self.current_text["title"] if self.current_text else "-"
        para_info = self.current_paragraph_info if hasattr(self, "current_paragraph_info") else "-"
        self.data_mgr.save_record(name, text_title, para_info, "略过", "课堂抽查")
        if self.draw_engine.drawn_history:
            self.draw_engine.drawn_history[-1]["status"] = "略过"
        self._current_marked = True
        self._show_toast(f"⏭ {name} 已略过", "未背熟")

    def _start_countdown_then_draw(self):
        self._countdown_active = True
        self._countdown_num = self.config_mgr.get("ui", "countdown_number") or 3
        self._countdown_step()

    def _countdown_step(self):
        if self._countdown_num > 0:
            self.draw_canvas.update_name(str(self._countdown_num))
            self._countdown_num -= 1
            self.after(1000, self._countdown_step)
        else:
            self.draw_canvas.update_name("开始")
            self.after(300, self._start_draw_process)

    def _start_draw_process(self):
        self._countdown_active = False
        mode = self.config_mgr.get("draw", "mode")
        success, name, interval = self.draw_engine.start_draw(self.students, mode)
        if not success:
            return
        if self.config_mgr.get("ui", "particle_enabled"):
            self.draw_canvas.start_particles()
        self._update_status_bar()
        self._roll_loop(interval)

    def _roll_loop(self, interval):
        running, name, next_interval = self.draw_engine.update()
        if running:
            self.draw_canvas.update_name(name)
            self.after(int(next_interval * 1000), lambda: self._roll_loop(next_interval))
        else:
            self._finish_draw_process()

    def _finish_draw_process(self):
        if self.config_mgr.get("draw", "mode") == "manual" and self.draw_engine.is_drawing:
            _, name, _ = self.draw_engine.stop_manual()
        else:
            name = self.draw_engine.current_name
        self.draw_canvas.stop_particles()
        self.draw_canvas.update_name(name)
        self.data_mgr.increment_draw_count(name)
        self._current_marked = False
        self._select_text_for_result()
        self._update_status_bar()
        if self.config_mgr.get("ui", "result_popup"):
            title = f"{self.current_text['title']} · {self.current_paragraph_info}" if self.current_text else ""
            ResultPopup(self, name, title, self.current_paragraph, self.theme)
        if self.config_mgr.get("draw", "auto_reset_round"):
            available = self.draw_engine.get_available_students()
            if not available:
                self.after(1500, self._reset_round)

    def _select_text_for_result(self):
        if not self.texts:
            self.current_text = None
            self.current_paragraph = "暂无课文数据"
            self.current_paragraph_info = "-"
            self._update_text_display()
            return
        extract_mode = self.config_mgr.get("text", "extract_mode") or "段落抽取"
        if self.text_mode == "random":
            text_idx = random.randint(0, len(self.texts)-1)
            text = self.texts[text_idx]
        else:
            text_idx = min(self.selected_text_index, len(self.texts)-1)
            text = self.texts[text_idx]
        self.current_text = text
        if extract_mode == "整篇抽取":
            self.current_paragraph = "\n\n".join(text["paragraphs"])
            self.current_paragraph_info = "全文"
        elif extract_mode == "分段抽取":
            progress = self.data_mgr.get_text_progress(text["title"])
            para_idx = progress % len(text["paragraphs"]) if text["paragraphs"] else 0
            self.current_paragraph = text["paragraphs"][para_idx] if text["paragraphs"] else ""
            self.current_paragraph_info = f"第{para_idx+1}段"
            self.data_mgr.set_text_progress(text["title"], para_idx + 1)
        else:
            if self.text_mode == "指定" and self.selected_paragraph_index is not None:
                para_idx = min(self.selected_paragraph_index, len(text["paragraphs"])-1)
            elif self.config_mgr.get("text", "paragraph_random"):
                para_idx = random.randint(0, len(text["paragraphs"])-1) if text["paragraphs"] else 0
            else:
                progress = self.data_mgr.get_text_progress(text["title"])
                para_idx = progress % len(text["paragraphs"]) if text["paragraphs"] else 0
                self.data_mgr.set_text_progress(text["title"], para_idx + 1)
            self.current_paragraph = text["paragraphs"][para_idx] if text["paragraphs"] else ""
            self.current_paragraph_info = f"第{para_idx+1}段"
        self._update_text_display()

    def _update_text_display(self):
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", tk.END)
        align = self.config_mgr.get("text", "text_align") or "left"
        self.text_display.tag_config("title", font=("微软雅黑", 12, "bold"),
                                    foreground=self.theme["primary"])
        self.text_display.tag_config("content", justify=align)
        if self.current_text and self.config_mgr.get("text", "show_title"):
            self.text_display.insert("1.0", f"【{self.current_text['title']}】 {self.current_paragraph_info}\n\n", "title")
            self.text_display.insert("end", self.current_paragraph, "content")
        else:
            self.text_display.insert("1.0", self.current_paragraph or "抽取学生后将显示对应课文段落", "content")
        self.text_display.config(state="disabled")

    def _mark_current_status(self, status):
        name = self.draw_engine.current_name
        if not name or not self.draw_engine.drawn_students:
            return
        old_status = self.data_mgr.get_student_status(name)
        text_title = self.current_text["title"] if self.current_text else "-"
        para_info = self.current_paragraph_info if hasattr(self, "current_paragraph_info") else "-"
        self.data_mgr.set_student_status(name, status)
        self.data_mgr.save_record(name, text_title, para_info, status, "课堂抽查")
        if self.draw_engine.drawn_history:
            self.draw_engine.drawn_history[-1]["status"] = status
        self._mark_history.append({"name": name, "old": old_status, "new": status})
        if len(self._mark_history) > 50:
            self._mark_history.pop(0)
        self._current_marked = True
        self._update_weight_tip()
        self._show_toast(f"✓ {name} 已标记为「{status}」", status)

    def _show_toast(self, message, status="已背过"):
        toast = tk.Toplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        if status == "已背过":
            color = "#10b981"
            icon = "✓"
        elif status == "未背熟":
            color = "#f59e0b"
            icon = "⚠"
        else:
            color = "#ef4444"
            icon = "✕"
        toast.config(bg=color)
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        tw, th = 440, 80
        tx = (sw - tw) // 2
        ty = sh // 6
        toast.geometry(f"{tw}x{th}+{tx}+{ty}")
        inner = tk.Frame(toast, bg="white")
        inner.pack(fill="both", expand=True, padx=3, pady=3)
        icon_frame = tk.Frame(inner, bg=color, width=56)
        icon_frame.pack(side="left", fill="y")
        icon_frame.pack_propagate(False)
        tk.Label(icon_frame, text=icon, bg=color, fg="white",
                font=("微软雅黑", 28, "bold")).pack(expand=True)
        tk.Label(inner, text=message, bg="white", fg="#1e293b",
                font=("微软雅黑", 12, "bold"), wraplength=300,
                justify="left").pack(side="left", padx=16, expand=True)
        toast.after(2500, toast.destroy)
        toast.after(50, lambda: apply_round_corner(toast, 14))
        toast.after(200, lambda: apply_round_corner(toast, 14))

    def _reset_round(self):
        self.draw_engine.reset_round()
        self.draw_canvas.reset()
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", tk.END)
        self.text_display.insert("1.0", "抽取学生后将显示对应课文段落")
        self.text_display.config(state="disabled")
        self._current_marked = False
        self._update_status_bar()

    def _hide_status_buttons(self):
        pass

    def _minimize_window(self):
        try:
            self.update_idletasks()
            self.overrideredirect(False)
            self.iconify()
        except Exception:
            pass

    def _restore_overrideredirect(self):
        try:
            self.overrideredirect(True)
            self._apply_window_round()
        except Exception:
            pass

    def _toggle_maximize(self):
        if self._is_maximized:
            if self._normal_geometry:
                self.geometry(self._normal_geometry)
            self._is_maximized = False
            self._win_max_btn.config(text="最大化")
        else:
            self._normal_geometry = self.geometry()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            self.geometry(f"{sw}x{sh - 40}+0+0")
            self._is_maximized = True
            self._win_max_btn.config(text="还原")
        self.after(100, self._apply_window_round)

    def _start_drag(self, event):
        if self._is_maximized:
            return
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag(self, event):
        if self._is_maximized:
            return
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _apply_window_round(self):
        try:
            import ctypes
            self.update_idletasks()
            w = self.winfo_width()
            h = self.winfo_height()
            if w <= 10 or h <= 10:
                return
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if not hwnd:
                hwnd = self.winfo_id()
            radius = 12 if not self._is_maximized else 0
            if radius > 0:
                hrgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, w + 1, h + 1, radius * 2, radius * 2)
                ctypes.windll.user32.SetWindowRgn(hwnd, hrgn, True)
            else:
                ctypes.windll.user32.SetWindowRgn(hwnd, 0, True)
        except Exception:
            pass

    def _toggle_no_repeat(self):
        try:
            cur = self.config_mgr.get("draw", "no_repeat")
            new_val = not cur
            self.config_mgr.set(new_val, "draw", "no_repeat")
            self.config_mgr.save_config()
            self.draw_engine.no_repeat = new_val
            status = "已开启" if new_val else "已关闭"
            self._show_toast(f"不重复模式：{status}", "已背过" if new_val else "未背过")
            self._update_status_bar()
        except Exception:
            pass

    def _toggle_dynamic_weight(self):
        try:
            cur = self.config_mgr.get("draw", "dynamic_weight")
            new_val = not cur
            self.config_mgr.set(new_val, "draw", "dynamic_weight")
            self.config_mgr.save_config()
            status = "已开启" if new_val else "已关闭"
            self._show_toast(f"动态权重：{status}", "已背过" if new_val else "未背过")
        except Exception:
            pass

    def _undo_last_mark(self):
        try:
            if not self._mark_history:
                self._show_toast("没有可撤销的标记", "未背熟")
                return
            last = self._mark_history.pop()
            name = last["name"]
            old = last["old"]
            if old:
                self.data_mgr.set_student_status(name, old)
            else:
                self.data_mgr.set_student_status(name, "未背过")
            self._update_weight_tip()
            self._show_toast(f"↩ 已撤销 {name} 的标记", "未背熟")
        except Exception:
            pass

    def _skip_current(self):
        try:
            name = self.draw_engine.current_name
            if not name:
                return
            self._hide_status_buttons()
            self.draw_canvas.reset()
            self.text_display.config(state="normal")
            self.text_display.delete("1.0", tk.END)
            self.text_display.insert("1.0", "抽取学生后将显示对应课文段落")
            self.text_display.config(state="disabled")
            self._show_toast(f"⏭ 已跳过 {name}", "未背熟")
        except Exception:
            pass

    def _toggle_draw_mode(self):
        try:
            cur = self.config_mgr.get("draw", "mode")
            new_mode = "manual" if cur == "auto" else "auto"
            self.config_mgr.set(new_mode, "draw", "mode")
            self.config_mgr.save_config()
            label = "手动模式（空格停止）" if new_mode == "manual" else "自动模式"
            self._show_toast(f"抽取模式：{label}", "已背过")
        except Exception:
            pass

    def _prev_text(self):
        try:
            if not self.texts:
                return
            self.selected_text_index = (self.selected_text_index - 1) % len(self.texts)
            self._select_text_by_index(self.selected_text_index)
        except Exception:
            pass

    def _next_text(self):
        try:
            if not self.texts:
                return
            self.selected_text_index = (self.selected_text_index + 1) % len(self.texts)
            self._select_text_by_index(self.selected_text_index)
        except Exception:
            pass

    def _select_text_by_index(self, idx):
        try:
            if 0 <= idx < len(self.texts):
                text = self.texts[idx]
                self.current_text = text
                self._update_text_display()
                if hasattr(self, "text_tree"):
                    for item in self.text_tree.get_children():
                        if self.text_tree.item(item, "text") == text.get("title", ""):
                            self.text_tree.selection_set(item)
                            self.text_tree.see(item)
                            break
        except Exception:
            pass

    def _toggle_theme(self):
        try:
            cur = self.config_mgr.get("ui", "theme")
            new_theme = "dark" if cur == "light" else "light"
            self.config_mgr.set(new_theme, "ui", "theme")
            self.config_mgr.save_config()
            label = "深色模式" if new_theme == "dark" else "浅色模式"
            self._show_toast(f"主题已切换为{label}，重启后生效", "已背过")
        except Exception:
            pass

    def _toggle_particle(self):
        try:
            cur = self.config_mgr.get("ui", "particle_enabled")
            new_val = not cur
            self.config_mgr.set(new_val, "ui", "particle_enabled")
            self.config_mgr.save_config()
            if not new_val and hasattr(self, "draw_canvas"):
                self.draw_canvas.stop_particles()
            status = "已开启" if new_val else "已关闭"
            self._show_toast(f"粒子效果：{status}", "已背过" if new_val else "未背过")
        except Exception:
            pass

    def _toggle_fullscreen(self):
        try:
            if self._is_fullscreen:
                self.overrideredirect(False)
                if self._normal_geometry:
                    self.geometry(self._normal_geometry)
                self.overrideredirect(True)
                self._is_fullscreen = False
                self._show_toast("已退出全屏", "未背熟")
            else:
                self._normal_geometry = self.geometry()
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                self.overrideredirect(False)
                self.geometry(f"{sw}x{sh}+0+0")
                self.overrideredirect(True)
                self._is_fullscreen = True
                self._show_toast("已进入全屏（F11退出）", "已背过")
            self.after(50, self._apply_window_round)
        except Exception:
            pass

    def _save_data(self):
        try:
            self.config_mgr.save_config()
            if hasattr(self.data_mgr, "save_stats"):
                self.data_mgr.save_stats()
            self._show_toast("✓ 数据已保存", "已背过")
        except Exception as e:
            self._show_toast(f"保存失败：{str(e)[:15]}", "未背过")

    def _show_shortcut_help(self):
        if self._shortcut_help_open:
            return
        self._shortcut_help_open = True
        ShortcutHelpWindow(self, self.theme, on_close=self._on_shortcut_help_close)

    def _on_shortcut_help_close(self):
        self._shortcut_help_open = False

    def _on_close(self):
        try:
            self.destroy()
        except Exception:
            pass
        sys.exit()


def open_external_file(file_path):
    try:
        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])
    except Exception as e:
        CustomMessageBox(None, LIGHT_THEME, "打开失败", f"无法打开文件：{str(e)}", "error")


def restart_application():
    try:
        python = sys.executable
        subprocess.Popen([python] + sys.argv)
        sys.exit()
    except Exception as e:
        CustomMessageBox(None, LIGHT_THEME, "重启失败", f"程序重启失败：{str(e)}", "error")


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    students_path = os.path.join(BASE_DIR, "students.txt")
    texts_path = os.path.join(BASE_DIR, "texts.txt")

    wizard_done = is_wizard_finished()

    # 增强格式校验
    stu_valid, stu_error, stu_count = validate_students_file(students_path)
    txt_valid, txt_error, txt_count, para_count = validate_texts_file(texts_path)
    data_valid = stu_valid and txt_valid

    # 收集错误信息
    error_messages = []
    if not stu_valid:
        error_messages.append(f"学生名单：{stu_error}")
    if not txt_valid:
        error_messages.append(f"课文库：{txt_error}")

    if not data_valid:
        set_wizard_unfinished()
        wizard_done = False

    if not wizard_done:
        reason = "；".join(error_messages) if error_messages else ""
        launch_wizard_and_exit(reason)

    show_first_tip = "--show-tip" in sys.argv
    app = MainApp(show_first_tip)
    app.mainloop()
