import os
import sys
import subprocess
import configparser
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font

APP_EXE = "A13课堂点名系统.exe"
WIZARD_INI = "wizard_record.ini"
STUDENT_FILE = "students.txt"
TEXT_FILE = "texts.txt"
MAIN_PY = "main_qt.py"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INI_PATH = os.path.join(BASE_DIR, WIZARD_INI)
STUDENT_PATH = os.path.join(BASE_DIR, STUDENT_FILE)
TEXT_PATH = os.path.join(BASE_DIR, TEXT_FILE)


class WizardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("A13 课堂点名系统 - 配置向导")
        self.root.geometry("640x820")
        self.root.resizable(False, False)
        self.root.configure(bg="#f3f3f3")
        try:
            self.root.iconbitmap(os.path.join(BASE_DIR, "app.ico"))
        except Exception:
            pass

        self.current_step = 0
        self.class_name = tk.StringVar(value="A13")
        self.steps = [
            self._page_welcome,
            self._page_class,
            self._page_students,
            self._page_texts,
            self._page_finish,
        ]

        self._setup_style()
        self._build_ui()
        self._show_step()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Wiz.TFrame", background="#f3f3f3")
        style.configure("Title.TLabel", font=("微软雅黑", 20, "bold"), foreground="#0067c0", background="#f3f3f3")
        style.configure("Subtitle.TLabel", font=("微软雅黑", 11), foreground="#666666", background="#f3f3f3")
        style.configure("Content.TLabel", font=("微软雅黑", 11), foreground="#333333", background="#f3f3f3")
        style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Primary.TButton", font=("微软雅黑", 11, "bold"), padding=10)
        style.configure("Nav.TButton", font=("微软雅黑", 10), padding=8)

    def _build_ui(self):
        main = ttk.Frame(self.root, style="Wiz.TFrame")
        main.pack(fill="both", expand=True, padx=0, pady=0)

        header = tk.Frame(main, bg="#0067c0", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        header_title = tk.Label(header, text="A13 课堂点名系统", font=("微软雅黑", 16, "bold"), fg="white", bg="#0067c0")
        header_title.pack(side="left", padx=24, pady=14)
        self.step_label = tk.Label(header, text="", font=("微软雅黑", 11), fg="#cce8ff", bg="#0067c0")
        self.step_label.pack(side="right", padx=24, pady=18)

        self.content = tk.Frame(main, bg="#f3f3f3")
        self.content.pack(fill="both", expand=True, padx=32, pady=24)

        nav = tk.Frame(main, bg="#f3f3f3", height=60)
        nav.pack(fill="x", side="bottom")
        nav.pack_propagate(False)
        self.prev_btn = tk.Button(nav, text="上一步", font=("微软雅黑", 10), bg="#ffffff", fg="#333333", relief="solid", bd=1, padx=20, pady=6, command=self._prev)
        self.prev_btn.pack(side="left", padx=24, pady=12)
        self.next_btn = tk.Button(nav, text="下一步", font=("微软雅黑", 10, "bold"), bg="#0067c0", fg="white", relief="flat", padx=24, pady=6, command=self._next)
        self.next_btn.pack(side="right", padx=24, pady=12)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _show_step(self):
        self._clear_content()
        self.step_label.config(text=f"第 {self.current_step + 1} / {len(self.steps)} 步")
        self.steps[self.current_step]()
        self.prev_btn.config(state="normal" if self.current_step > 0 else "disabled")
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="完成")
        else:
            self.next_btn.config(text="下一步")

    def _page_welcome(self):
        title = tk.Label(self.content, text="欢迎使用！", font=("微软雅黑", 22, "bold"), fg="#0067c0", bg="#f3f3f3")
        title.pack(pady=(20, 8))
        subtitle = tk.Label(self.content, text="A13 智能抽取引擎 V6.8", font=("微软雅黑", 12), fg="#666666", bg="#f3f3f3")
        subtitle.pack(pady=(0, 24))

        card = tk.Frame(self.content, bg="white", relief="solid", bd=1)
        card.pack(fill="x", padx=20, pady=10)
        card_inner = tk.Frame(card, bg="white")
        card_inner.pack(fill="x", padx=20, pady=16)

        features = [
            ("🎲", "智能随机抽取", "支持自动/手动模式，不重复抽取"),
            ("📖", "课文联动", "抽取学生同时展示对应课文"),
            ("📊", "积分统计", "自动记录背诵状态，生成排行榜"),
            ("💬", "回声洞", "匿名留言功能，倾听每一个心声"),
        ]
        for icon, title, desc in features:
            row = tk.Frame(card_inner, bg="white")
            row.pack(fill="x", pady=6)
            icon_label = tk.Label(row, text=icon, font=("微软雅黑", 18), bg="white")
            icon_label.pack(side="left", padx=(0, 12))
            text_col = tk.Frame(row, bg="white")
            text_col.pack(side="left", fill="x", expand=True)
            t_label = tk.Label(text_col, text=title, font=("微软雅黑", 11, "bold"), fg="#333333", bg="white", anchor="w")
            t_label.pack(fill="x")
            d_label = tk.Label(text_col, text=desc, font=("微软雅黑", 10), fg="#888888", bg="white", anchor="w")
            d_label.pack(fill="x")

        tip = tk.Label(self.content, text="点击「下一步」开始配置你的班级点名系统", font=("微软雅黑", 10), fg="#999999", bg="#f3f3f3")
        tip.pack(pady=20)

    def _page_class(self):
        title = tk.Label(self.content, text="设置班级名称", font=("微软雅黑", 20, "bold"), fg="#0067c0", bg="#f3f3f3")
        title.pack(pady=(20, 8))
        subtitle = tk.Label(self.content, text="窗口标题将显示为「某某班点名程序」", font=("微软雅黑", 11), fg="#666666", bg="#f3f3f3")
        subtitle.pack(pady=(0, 24))

        card = tk.Frame(self.content, bg="white", relief="solid", bd=1)
        card.pack(fill="x", padx=40, pady=10)
        card_inner = tk.Frame(card, bg="white")
        card_inner.pack(fill="x", padx=24, pady=24)

        label = tk.Label(card_inner, text="班级名称：", font=("微软雅黑", 12), fg="#333333", bg="white")
        label.pack(anchor="w", pady=(0, 8))
        entry = tk.Entry(card_inner, textvariable=self.class_name, font=("微软雅黑", 14), relief="solid", bd=1)
        entry.pack(fill="x", ipady=6)
        entry.focus_set()

        preview = tk.Label(card_inner, text="", font=("微软雅黑", 11), fg="#0067c0", bg="white")
        preview.pack(anchor="w", pady=(12, 0))

        def update_preview(*args):
            name = self.class_name.get().strip() or "A13"
            preview.config(text=f"预览：{name}班点名程序")

        self.class_name.trace_add("write", update_preview)
        update_preview()

        tip = tk.Label(self.content, text="提示：可以在设置中随时修改班级名称", font=("微软雅黑", 10), fg="#999999", bg="#f3f3f3")
        tip.pack(pady=20)

    def _page_students(self):
        title = tk.Label(self.content, text="学生名单", font=("微软雅黑", 20, "bold"), fg="#0067c0", bg="#f3f3f3")
        title.pack(pady=(20, 8))
        subtitle = tk.Label(self.content, text="配置学生名单文件格式", font=("微软雅黑", 11), fg="#666666", bg="#f3f3f3")
        subtitle.pack(pady=(0, 20))

        card = tk.Frame(self.content, bg="white", relief="solid", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        card_inner = tk.Frame(card, bg="white")
        card_inner.pack(fill="both", expand=True, padx=20, pady=16)

        format_label = tk.Label(card_inner, text="文件格式：students.txt", font=("微软雅黑", 12, "bold"), fg="#333333", bg="white")
        format_label.pack(anchor="w", pady=(0, 8))

        example = tk.Text(card_inner, height=6, font=("Consolas", 11), relief="solid", bd=1, bg="#fafafa")
        example.pack(fill="x", pady=(0, 12))
        example.insert("1.0", "张三\n李四\n王五\n赵六\n...")
        example.config(state="disabled")

        tips = [
            "• 每行一个学生姓名",
            "• 支持带序号格式（如「1 张三」）",
            "• 文件编码请使用 UTF-8",
            "• 点击下方按钮可用记事本编辑",
        ]
        for tip in tips:
            t = tk.Label(card_inner, text=tip, font=("微软雅黑", 10), fg="#666666", bg="white", anchor="w")
            t.pack(fill="x", pady=2)

        btn_row = tk.Frame(card_inner, bg="white")
        btn_row.pack(fill="x", pady=(12, 0))
        edit_btn = tk.Button(btn_row, text="📝 编辑学生名单", font=("微软雅黑", 10), bg="#0067c0", fg="white", relief="flat", padx=16, pady=6, command=lambda: self._edit_file(STUDENT_PATH))
        edit_btn.pack(side="left")

    def _page_texts(self):
        title = tk.Label(self.content, text="课文库", font=("微软雅黑", 20, "bold"), fg="#0067c0", bg="#f3f3f3")
        title.pack(pady=(20, 8))
        subtitle = tk.Label(self.content, text="配置课文库文件格式", font=("微软雅黑", 11), fg="#666666", bg="#f3f3f3")
        subtitle.pack(pady=(0, 20))

        card = tk.Frame(self.content, bg="white", relief="solid", bd=1)
        card.pack(fill="both", expand=True, padx=20, pady=10)
        card_inner = tk.Frame(card, bg="white")
        card_inner.pack(fill="both", expand=True, padx=20, pady=16)

        format_label = tk.Label(card_inner, text="文件格式：texts.txt", font=("微软雅黑", 12, "bold"), fg="#333333", bg="white")
        format_label.pack(anchor="w", pady=(0, 8))

        example = tk.Text(card_inner, height=6, font=("Consolas", 11), relief="solid", bd=1, bg="#fafafa")
        example.pack(fill="x", pady=(0, 12))
        example.insert("1.0", "【第一课 春】\n春天来了，万物复苏...\n\n【第二课 夏】\n夏天到了，烈日炎炎...")
        example.config(state="disabled")

        tips = [
            "• 用【】包裹课文标题",
            "• 标题下方为课文内容，空行分隔段落",
            "• 支持多篇课文，抽取时自动联动",
            "• 点击下方按钮可用记事本编辑",
        ]
        for tip in tips:
            t = tk.Label(card_inner, text=tip, font=("微软雅黑", 10), fg="#666666", bg="white", anchor="w")
            t.pack(fill="x", pady=2)

        btn_row = tk.Frame(card_inner, bg="white")
        btn_row.pack(fill="x", pady=(12, 0))
        edit_btn = tk.Button(btn_row, text="📝 编辑课文库", font=("微软雅黑", 10), bg="#0067c0", fg="white", relief="flat", padx=16, pady=6, command=lambda: self._edit_file(TEXT_PATH))
        edit_btn.pack(side="left")

    def _page_finish(self):
        title = tk.Label(self.content, text="配置完成！", font=("微软雅黑", 22, "bold"), fg="#107c10", bg="#f3f3f3")
        title.pack(pady=(30, 8))

        class_name = self.class_name.get().strip() or "A13"
        subtitle = tk.Label(self.content, text=f"{class_name}班点名程序已准备就绪", font=("微软雅黑", 12), fg="#666666", bg="#f3f3f3")
        subtitle.pack(pady=(0, 24))

        card = tk.Frame(self.content, bg="white", relief="solid", bd=1)
        card.pack(fill="x", padx=40, pady=10)
        card_inner = tk.Frame(card, bg="white")
        card_inner.pack(fill="x", padx=24, pady=20)

        summary = [
            ("班级名称", class_name),
            ("学生名单", STUDENT_FILE),
            ("课文库", TEXT_FILE),
            ("引擎版本", "A13 V6.8"),
        ]
        for label, value in summary:
            row = tk.Frame(card_inner, bg="white")
            row.pack(fill="x", pady=4)
            l = tk.Label(row, text=label + "：", font=("微软雅黑", 11), fg="#888888", bg="white", width=10, anchor="e")
            l.pack(side="left")
            v = tk.Label(row, text=value, font=("微软雅黑", 11, "bold"), fg="#333333", bg="white")
            v.pack(side="left", padx=(8, 0))

        tip = tk.Label(self.content, text="点击「完成」启动点名程序，首次启动将显示操作引导", font=("微软雅黑", 10), fg="#999999", bg="#f3f3f3")
        tip.pack(pady=20)

    def _edit_file(self, filepath):
        if not os.path.exists(filepath):
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass
        try:
            subprocess.Popen(["notepad.exe", filepath])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开记事本：{e}")

    def _prev(self):
        if self.current_step > 0:
            self.current_step -= 1
            self._show_step()

    def _next(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self._show_step()
        else:
            self._finish()

    def _finish(self):
        class_name = self.class_name.get().strip() or "A13"

        try:
            cfg = configparser.ConfigParser()
            cfg["status"] = {"finished": "True"}
            cfg["app"] = {"class_name": class_name}
            with open(INI_PATH, "w", encoding="utf-8") as f:
                cfg.write(f)
        except Exception as e:
            messagebox.showerror("错误", f"写入配置失败：{e}")
            return

        try:
            config_path = os.path.join(BASE_DIR, "config.json")
            import json
            config = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except Exception:
                    pass
            if "app" not in config:
                config["app"] = {}
            config["app"]["class_name"] = class_name
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        self.root.destroy()

        exe_path = os.path.join(BASE_DIR, APP_EXE)
        py_path = os.path.join(BASE_DIR, MAIN_PY)
        try:
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path, "--show-tip"], cwd=BASE_DIR)
            elif os.path.exists(py_path):
                subprocess.Popen([sys.executable, py_path, "--show-tip"], cwd=BASE_DIR)
        except Exception as e:
            print(f"启动主程序失败: {e}")


def generate_sample_files():
    if not os.path.exists(STUDENT_PATH):
        try:
            with open(STUDENT_PATH, "w", encoding="utf-8") as f:
                f.write("张三\n李四\n王五\n赵六\n钱七\n孙八\n周九\n吴十\n")
        except Exception:
            pass
    if not os.path.exists(TEXT_PATH):
        try:
            with open(TEXT_PATH, "w", encoding="utf-8") as f:
                f.write("【第一课 春】\n春天来了，万物复苏。\n小草从土里探出头来，\n花儿也露出了笑脸。\n\n【第二课 夏】\n夏天到了，烈日炎炎。\n知了在树上不停地叫着，\n小朋友们在河边玩耍。\n\n【第三课 秋】\n秋天来了，树叶变黄。\n一片片叶子从树上落下，\n像一只只蝴蝶在飞舞。\n")
        except Exception:
            pass


def main():
    generate_sample_files()
    root = tk.Tk()
    app = WizardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
