# -*- coding: utf-8 -*-
import os
import sys
import subprocess


def is_windows():
    return sys.platform == "win32"


def is_macos():
    return sys.platform == "darwin"


def is_linux():
    return sys.platform.startswith("linux")


def open_file(path):
    if is_windows():
        os.startfile(path)
    elif is_macos():
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def open_folder(path):
    open_file(path)


def open_with_editor(path):
    if is_windows():
        subprocess.Popen(["notepad.exe", path])
    elif is_macos():
        subprocess.Popen(["open", "-a", "TextEdit", path])
    else:
        subprocess.Popen(["xdg-open", path])


def app_bundle_path():
    if is_macos() and getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(exe_dir))
    return None


def restart_app():
    if is_windows():
        os.execv(sys.executable, [sys.executable] + sys.argv)
    elif is_macos():
        bundle = app_bundle_path()
        if bundle and os.path.isdir(bundle):
            subprocess.Popen(["open", "-n", bundle])
        else:
            subprocess.Popen([sys.executable] + sys.argv)
        os._exit(0)
    else:
        os.execv(sys.executable, [sys.executable] + sys.argv)


def launch_wizard(base_dir):
    if is_macos():
        for name in ("向导启动器.app", "A13配置向导.app"):
            cand = os.path.join(base_dir, name)
            if os.path.isdir(cand):
                return subprocess.Popen(["open", "-n", cand])
        for name in ("向导启动器", "A13配置向导"):
            cand = os.path.join(base_dir, name)
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return subprocess.Popen([cand], cwd=base_dir)
        py_path = os.path.join(base_dir, "wizard_launcher.py")
        if os.path.exists(py_path):
            return subprocess.Popen([sys.executable, py_path], cwd=base_dir)
        return None
    for name in ("向导启动器.exe", "A13配置向导.exe"):
        cand = os.path.join(base_dir, name)
        if os.path.exists(cand):
            return subprocess.Popen([cand], cwd=base_dir)
    py_path = os.path.join(base_dir, "wizard_launcher.py")
    if os.path.exists(py_path):
        return subprocess.Popen([sys.executable, py_path], cwd=base_dir)
    return None


def launch_main(base_dir, args=None):
    args = args or []
    if is_macos():
        for name in ("A13课堂点名程序.app", "A13课堂点名系统.app", "A13Rollcall.app"):
            cand = os.path.join(base_dir, name)
            if os.path.isdir(cand):
                return subprocess.Popen(["open", "-n", cand, "--args"] + args)
        for name in ("A13课堂点名程序", "A13课堂点名系统", "A13Rollcall"):
            cand = os.path.join(base_dir, name)
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return subprocess.Popen([cand] + args, cwd=base_dir)
        py_path = os.path.join(base_dir, "main_qt.py")
        if os.path.exists(py_path):
            return subprocess.Popen([sys.executable, py_path] + args, cwd=base_dir)
        return None
    for name in ("A13课堂点名程序.exe", "A13课堂点名系统.exe", "A13Rollcall.exe"):
        cand = os.path.join(base_dir, name)
        if os.path.exists(cand):
            return subprocess.Popen([cand] + args, cwd=base_dir)
    py_path = os.path.join(base_dir, "main_qt.py")
    if os.path.exists(py_path):
        return subprocess.Popen([sys.executable, py_path] + args, cwd=base_dir)
    return None


def register_url_protocol(base_dir, show_ok=None, show_fail=None):
    if is_windows():
        try:
            import winreg
            key_path = r"Software\Classes\a13rollcall"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:A13 Roll Call Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            command_key = winreg.CreateKey(key, r"shell\open\command")
            exe_path = os.path.join(base_dir, "main_qt.exe")
            if not os.path.exists(exe_path):
                exe_path = sys.executable + " " + os.path.join(base_dir, "main_qt.py")
            winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, '"%s" "%%1"' % exe_path)
            winreg.CloseKey(key)
            winreg.CloseKey(command_key)
            if show_ok:
                show_ok()
            return True
        except Exception as e:
            if show_fail:
                show_fail(str(e))
            return False
    if is_macos():
        if show_ok:
            show_ok()
        return True
    if show_fail:
        show_fail("当前系统暂不支持自动注册 URL 协议")
    return False
