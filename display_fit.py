import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QFontMetrics, QGuiApplication
from PyQt5.QtWidgets import QApplication

BASE_PT = 9.0
BASE_W = 1180
BASE_H = 760
MIN_W = 1080
MIN_H = 660

FAMILY_ALIAS = {
    "微软雅黑": "Microsoft YaHei",
    "微软雅黑 UI": "Microsoft YaHei UI",
    "宋体": "SimSun",
    "黑体": "SimHei",
    "楷体": "KaiTi",
    "新宋体": "NSimSun",
    "等线": "DengXian",
    "仿宋": "FangSong",
}


def normalize_family(name):
    text = (name or "").strip().strip('"').strip("'")
    if not text:
        return "Microsoft YaHei"
    if text in FAMILY_ALIAS:
        return FAMILY_ALIAS[text]
    for ch in text:
        if ord(ch) > 127:
            return "Microsoft YaHei"
    return text


def enable_high_dpi():
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    except Exception:
        pass
    try:
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    try:
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass


_CACHE = {"profile": None, "scale": None}


def reset_cache():
    _CACHE["profile"] = None
    _CACHE["scale"] = None


def screen_profile(force=False):
    if _CACHE["profile"] is not None and not force:
        return dict(_CACHE["profile"])
    app = QApplication.instance()
    if app is None:
        return {"w": 1920, "h": 1080, "dpr": 1.0, "font_pt": BASE_PT, "dpi": 96, "name": ""}
    screen = app.primaryScreen()
    if screen is None:
        return {"w": 1920, "h": 1080, "dpr": 1.0, "font_pt": BASE_PT, "dpi": 96, "name": ""}
    geo = screen.availableGeometry()
    try:
        font_pt = app.font().pointSizeF()
    except Exception:
        font_pt = BASE_PT
    if not font_pt or font_pt <= 0:
        font_pt = BASE_PT
    try:
        dpi = screen.logicalDotsPerInch()
    except Exception:
        dpi = 96.0
    profile = {
        "w": int(geo.width()),
        "h": int(geo.height()),
        "dpr": float(screen.devicePixelRatio() or 1.0),
        "font_pt": float(font_pt),
        "dpi": float(dpi or 96.0),
        "name": screen.name() or "",
    }
    _CACHE["profile"] = dict(profile)
    return profile


def auto_scale(profile=None):
    if profile is None and _CACHE["scale"] is not None:
        return _CACHE["scale"]
    p = profile or screen_profile()
    res_part = min(p["w"] / 1366.0, p["h"] / 768.0)
    res_part = max(0.86, min(1.15, res_part))
    font_part = (p["font_pt"] / BASE_PT) ** 0.5
    font_part = max(0.9, min(1.3, font_part))
    scale = round(res_part * font_part, 2)
    if profile is None:
        _CACHE["scale"] = scale
    return scale


def window_size(profile=None):
    p = profile or screen_profile()
    scale = auto_scale(p)
    w = int(round(BASE_W * scale))
    h = int(round(BASE_H * scale))
    w = min(w, int(p["w"] * 0.94))
    h = min(h, int(p["h"] * 0.94))
    w = max(MIN_W, w)
    h = max(MIN_H, h)
    return w, h


def minimum_size(profile=None):
    p = profile or screen_profile()
    scale = max(0.9, min(1.05, auto_scale(p)))
    w = min(int(round(MIN_W * scale)), int(p["w"] * 0.9))
    h = min(int(round(MIN_H * scale)), int(p["h"] * 0.9))
    return w, h


def layout_tokens(profile=None):
    p = profile or screen_profile()
    scale = auto_scale(p)
    narrow = p["w"] < 1500
    return {
        "scale": scale,
        "sidebar": 240 if narrow else 280,
        "right": 210 if narrow else 250,
        "page_pad": 16 if narrow else 22,
        "card_pad": 16 if narrow else 20,
        "gap": 12 if narrow else 16,
        "row": 34 if narrow else 38,
        "btn_h": 34 if narrow else 38,
        "title_pt": 16 if narrow else 18,
        "font_pt": int(round(BASE_PT * scale)),
    }


def apply(app, config_mgr=None, family=None):
    reset_cache()
    profile = screen_profile(True)
    tokens = layout_tokens(profile)
    if config_mgr is not None:
        try:
            auto = config_mgr.get("ui", "auto_scale")
            if auto is None:
                auto = True
            if bool(auto):
                config_mgr.set(tokens["scale"], "ui", "scale")
        except Exception:
            pass
    if family is None and config_mgr is not None:
        try:
            family = config_mgr.get("ui", "font_family") or "Microsoft YaHei"
        except Exception:
            family = "Microsoft YaHei"
    if not family:
        family = "Microsoft YaHei"
    family = normalize_family(family)
    pt = tokens["font_pt"]
    try:
        app.setFont(QFont(family, pt))
    except Exception:
        pass
    return {
        "profile": profile,
        "tokens": tokens,
        "size": window_size(profile),
        "minimum": minimum_size(profile),
    }
