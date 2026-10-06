# -*- coding: utf-8 -*-
import os, json, shutil

BASE = os.path.dirname(os.path.abspath(__file__))

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

sample_texts = """【岳阳楼记】
庆历四年春，滕子京谪守巴陵郡。越明年，政通人和，百废具兴。乃重修岳阳楼，增其旧制，刻唐贤今人诗赋于其上。属予作文以记之。

【醉翁亭记】
环滁皆山也。其西南诸峰，林壑尤美，望之蔚然而深秀者，琅琊也。
"""

default_config = {
  "app": {"class_name": "A13", "app_name": "课堂点名程序", "engine_name": "A13", "version": "6.8"},
  "ui": {"theme": "light", "font_family": "微软雅黑", "font_size": 12, "name_font_size": 50,
         "text_font_size": 14, "animation_duration": 3.0, "dark_mode": False,
         "particle_enabled": True, "window_topmost": False, "startup_animation": True},
  "draw": {"mode": "auto", "no_repeat": True, "auto_duration": 4.0,
           "dynamic_weight": True, "rate_mastered": 1.0, "rate_familiar": 2.0, "rate_unlearned": 3.0,
           "history_limit": 50, "sound_enabled": False},
  "files": {"students": "students.txt", "texts": "texts.txt", "records": "records.txt", "stats": "stats.txt"},
  "shortcut": {"enabled": True},
  "student_status": {}, "student_weights": {}, "text_progress": {},
  "quick_draw": {"enabled": True, "always_on_top": True, "no_repeat": True},
  "tts": {"enabled": False, "rate": 150, "volume": 1.0, "speak_text": True},
  "startup": {"default_mode": ""}
}

def w(path, content, enc="utf-8"):
    with open(path, "w", encoding=enc) as f:
        f.write(content)

w(os.path.join(BASE, "students.txt"), sample_students)
w(os.path.join(BASE, "texts.txt"), sample_texts)
w(os.path.join(BASE, "config.json"), json.dumps(default_config, ensure_ascii=False, indent=2))
w(os.path.join(BASE, "wizard_record.ini"), "[status]\nfinished = False\n\n[app]\nclass_name = A13\n")

for f in ("records.txt", "stats.txt"):
    p = os.path.join(BASE, f)
    if os.path.exists(p):
        os.remove(p)

plug = os.path.join(BASE, "plugins")
if os.path.isdir(plug):
    shutil.rmtree(plug, ignore_errors=True)
os.makedirs(os.path.join(plug, "data"), exist_ok=True)
os.makedirs(os.path.join(plug, "logs"), exist_ok=True)

for d in ("crash_reports",):
    dp = os.path.join(BASE, d)
    if os.path.isdir(dp):
        shutil.rmtree(dp, ignore_errors=True)

print("RESET DONE")
