import os
import json
import shutil
import zipfile
import tempfile
import urllib.request
from datetime import datetime

INDEX_NAME = "plugin_market.json"
REMOTE_INDEX = "https://raw.githubusercontent.com/a13zhy/a13rollcall/main/plugin_market.json"
APP_VERSION = "6.8.2"

REQUIRED_FIELDS = ("id", "name", "version")
DEFAULT_ICON = "puzzle"


def app_dir():
    return os.path.dirname(os.path.abspath(__file__))


def plugins_dir():
    return os.path.join(app_dir(), "plugins")


def state_file():
    return os.path.join(plugins_dir(), "plugin_states.json")


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_json(path, data):
    try:
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def version_tuple(text):
    parts = []
    for chunk in str(text or "0").replace("-", ".").split("."):
        digits = ""
        for ch in chunk:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def compare_version(a, b):
    ta, tb = version_tuple(a), version_tuple(b)
    if ta > tb:
        return 1
    if ta < tb:
        return -1
    return 0


def normalize_manifest(raw, fallback_id=""):
    data = dict(raw or {})
    pid = str(data.get("id") or data.get("name") or fallback_id or "plugin").strip()
    data["id"] = pid
    data["name"] = str(data.get("name") or pid)
    data["version"] = str(data.get("version") or "1.0.0")
    data["author"] = str(data.get("author") or "未知")
    data["description"] = str(data.get("description") or "")
    data["icon"] = str(data.get("icon") or "")
    data["repo"] = str(data.get("repo") or "")
    data["homepage"] = str(data.get("homepage") or "")
    data["entry"] = str(data.get("entry") or "main.py")
    data["min_app_version"] = str(data.get("min_app_version") or "6.0")
    data["max_app_version"] = str(data.get("max_app_version") or "99.0")
    tags = data.get("tags") or []
    data["tags"] = [str(t) for t in tags] if isinstance(tags, list) else []
    permissions = data.get("permissions") or []
    data["permissions"] = [str(p) for p in permissions] if isinstance(permissions, list) else []
    return data


def validate_manifest(data):
    problems = []
    for field in REQUIRED_FIELDS:
        if not data.get(field):
            problems.append("缺少字段 %s" % field)
    try:
        if compare_version(data.get("min_app_version", "6.0"), APP_VERSION) > 0:
            problems.append("要求软件版本高于当前 %s" % APP_VERSION)
    except Exception:
        pass
    try:
        if compare_version(APP_VERSION, data.get("max_app_version", "99.0")) > 0:
            problems.append("与当前软件版本 %s 不兼容" % APP_VERSION)
    except Exception:
        pass
    return (len(problems) == 0, problems)


def read_folder_plugin(folder):
    manifest_path = os.path.join(folder, "manifest.json")
    if not os.path.exists(manifest_path):
        return None
    raw = _read_json(manifest_path)
    if not isinstance(raw, dict):
        return None
    data = normalize_manifest(raw, os.path.basename(folder))
    entry_path = os.path.join(folder, data["entry"])
    if not os.path.exists(entry_path):
        for candidate in ("main.py", "plugin.py", "index.py"):
            if os.path.exists(os.path.join(folder, candidate)):
                data["entry"] = candidate
                entry_path = os.path.join(folder, candidate)
                break
    data["_folder"] = folder
    data["_manifest"] = manifest_path
    data["_entry_path"] = entry_path if os.path.exists(entry_path) else ""
    return data


def scan_folders(root=None):
    root = root or plugins_dir()
    found = []
    if not os.path.isdir(root):
        return found
    for name in sorted(os.listdir(root)):
        folder = os.path.join(root, name)
        if not os.path.isdir(folder):
            continue
        item = read_folder_plugin(folder)
        if item:
            found.append(item)
    return found


def load_states():
    data = _read_json(state_file())
    return data if isinstance(data, dict) else {}


def save_state(plugin_id, enabled):
    states = load_states()
    states[plugin_id] = {"enabled": bool(enabled), "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    _write_json(state_file(), states)


def load_local_index(root=None):
    root = root or app_dir()
    for path in (os.path.join(root, INDEX_NAME), os.path.join(plugins_dir(), INDEX_NAME)):
        data = _read_json(path)
        if isinstance(data, dict):
            items = data.get("plugins") or []
            return normalize_index(items), path
    return [], ""


def normalize_index(items):
    result = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        data = normalize_manifest(item, item.get("id", ""))
        data["download_url"] = str(item.get("download_url") or "")
        data["updated_at"] = str(item.get("updated_at") or "")
        data["size"] = str(item.get("size") or "")
        data["screenshots"] = item.get("screenshots") or []
        result.append(data)
    return result


def fetch_remote_index(url=REMOTE_INDEX, timeout=4):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "A13Rollcall"})
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        items = payload.get("plugins") if isinstance(payload, dict) else payload
        return normalize_index(items), ""
    except Exception as exc:
        return [], str(exc)


def installed_plugins(manager=None):
    result = []
    states = load_states()
    for item in scan_folders():
        entry = dict(item)
        entry["installed"] = True
        entry["enabled"] = states.get(item["id"], {}).get("enabled", True)
        entry["kind"] = "folder"
        result.append(entry)
    if manager is not None:
        try:
            for plugin in manager.get_all_plugins():
                meta = plugin.get("meta", {}) or {}
                pid = str(meta.get("id") or meta.get("name") or "")
                if not pid:
                    continue
                if any(x["id"] == pid for x in result):
                    continue
                entry = normalize_manifest(meta, pid)
                entry["installed"] = True
                entry["enabled"] = bool(plugin.get("enabled", True))
                entry["kind"] = "arcx"
                entry["filename"] = plugin.get("filename", "")
                entry["_plugin"] = plugin
                result.append(entry)
        except Exception:
            pass
    return result


def market_plugins(manager=None, remote=False, url=REMOTE_INDEX):
    index, source = load_local_index()
    error = ""
    if remote or not index:
        fetched, error = fetch_remote_index(url)
        if fetched:
            index = fetched
            source = url
    installed = {x["id"]: x for x in installed_plugins(manager)}
    cards = []
    for item in index:
        entry = dict(item)
        entry["installed"] = item["id"] in installed
        entry["enabled"] = installed.get(item["id"], {}).get("enabled", False)
        if entry["installed"]:
            entry["installed_version"] = installed[item["id"]]["version"]
            entry["update_available"] = compare_version(item["version"], entry["installed_version"]) > 0
        else:
            entry["installed_version"] = ""
            entry["update_available"] = False
        entry["kind"] = "market"
        cards.append(entry)
    return cards, source, error


def install_folder(source_folder, root=None):
    root = root or plugins_dir()
    item = read_folder_plugin(source_folder)
    if not item:
        return False, "没有找到 manifest.json"
    ok, problems = validate_manifest(item)
    if not ok:
        return False, "、".join(problems)
    if not item.get("_entry_path"):
        return False, "入口文件 %s 不存在" % item["entry"]
    target = os.path.join(root, item["id"])
    if os.path.isdir(target):
        backup = target + ".bak"
        try:
            if os.path.isdir(backup):
                shutil.rmtree(backup, ignore_errors=True)
            shutil.copytree(target, backup)
            shutil.rmtree(target)
        except Exception:
            pass
    try:
        shutil.copytree(source_folder, target)
    except Exception as exc:
        return False, "复制失败：%s" % exc
    save_state(item["id"], True)
    return True, "已安装 %s %s" % (item["name"], item["version"])


def install_archive(path, root=None):
    root = root or plugins_dir()
    if not os.path.exists(path):
        return False, "文件不存在"
    if path.lower().endswith(".arcx"):
        target = os.path.join(root, os.path.basename(path))
        try:
            shutil.copy2(path, target)
            return True, "已安装插件包 %s" % os.path.basename(path)
        except Exception as exc:
            return False, "复制失败：%s" % exc
    temp = tempfile.mkdtemp(prefix="a13plug_")
    try:
        with zipfile.ZipFile(path) as zf:
            zf.extractall(temp)
        candidate = temp
        if not os.path.exists(os.path.join(candidate, "manifest.json")):
            for name in os.listdir(temp):
                sub = os.path.join(temp, name)
                if os.path.isdir(sub) and os.path.exists(os.path.join(sub, "manifest.json")):
                    candidate = sub
                    break
        ok, msg = install_folder(candidate, root)
        return ok, msg
    except Exception as exc:
        return False, "解压失败：%s" % exc
    finally:
        shutil.rmtree(temp, ignore_errors=True)


def remove_plugin(plugin_id, manager=None):
    removed = False
    target = os.path.join(plugins_dir(), plugin_id)
    if os.path.isdir(target):
        try:
            shutil.rmtree(target)
            removed = True
        except Exception as exc:
            return False, "删除失败：%s" % exc
    if manager is not None:
        try:
            for plugin in manager.get_all_plugins():
                meta = plugin.get("meta", {}) or {}
                if str(meta.get("id") or meta.get("name")) == plugin_id:
                    path = plugin.get("file_path")
                    if path and os.path.exists(path):
                        os.remove(path)
                        removed = True
        except Exception:
            pass
    if removed:
        states = load_states()
        if plugin_id in states:
            states.pop(plugin_id, None)
            _write_json(state_file(), states)
        return True, "已卸载"
    return False, "没有找到插件"


def write_example_manifest(folder, plugin_id="com.a13.demo", name="示例插件"):
    data = {
        "id": plugin_id,
        "name": name,
        "version": "1.0.0",
        "author": "a13zhy",
        "description": "演示 ClassIsland 风格插件目录结构",
        "icon": "",
        "repo": "https://github.com/a13zhy/a13rollcall",
        "entry": "main.py",
        "min_app_version": "6.8",
        "max_app_version": "99.0",
        "permissions": [],
        "tags": ["示例"],
    }
    return _write_json(os.path.join(folder, "manifest.json"), data)
