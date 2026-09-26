import os
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class EchoHole:
    def __init__(self, config_mgr=None):
        self.config_mgr = config_mgr
        self.echoes = []
        self._load()

    def _get_file(self):
        try:
            path = self.config_mgr.get("files", "echoes")
            if path:
                if not os.path.isabs(path):
                    path = os.path.join(BASE_DIR, path)
                return path
        except Exception:
            pass
        return os.path.join(BASE_DIR, "echo_hole.txt")

    def _load(self):
        path = self._get_file()
        if not os.path.exists(path):
            self.echoes = []
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.echoes = self._parse(content)
        except Exception:
            self.echoes = []

    def _parse(self, content):
        echoes = []
        blocks = content.split("===ECHO===")
        for block in blocks[1:]:
            echo = {"id": 0, "text": "", "author": "匿名", "time": "", "echo_count": 0, "replies": []}
            lines = block.split("\n")
            in_reply = False
            current_reply = {}
            for line in lines:
                line = line.strip()
                if line == "===REPLY===":
                    in_reply = True
                    current_reply = {"text": "", "author": "匿名", "time": ""}
                    continue
                if line == "===END_REPLY===":
                    in_reply = False
                    if current_reply.get("text"):
                        echo["replies"].append(current_reply)
                    continue
                if in_reply:
                    if line.startswith("text:"):
                        current_reply["text"] = line[5:]
                    elif line.startswith("author:"):
                        current_reply["author"] = line[7:]
                    elif line.startswith("time:"):
                        current_reply["time"] = line[5:]
                else:
                    if line.startswith("id:"):
                        try:
                            echo["id"] = int(line[3:])
                        except Exception:
                            pass
                    elif line.startswith("text:"):
                        echo["text"] = line[5:]
                    elif line.startswith("author:"):
                        echo["author"] = line[7:]
                    elif line.startswith("time:"):
                        echo["time"] = line[5:]
                    elif line.startswith("echo_count:"):
                        try:
                            echo["echo_count"] = int(line[11:])
                        except Exception:
                            pass
            if echo.get("text"):
                echoes.append(echo)
        return echoes

    def _save(self):
        path = self._get_file()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except Exception:
            pass
        try:
            with open(path, "w", encoding="utf-8") as f:
                for echo in self.echoes:
                    f.write("===ECHO===\n")
                    f.write(f"id:{echo['id']}\n")
                    f.write(f"text:{echo['text']}\n")
                    f.write(f"author:{echo['author']}\n")
                    f.write(f"time:{echo['time']}\n")
                    f.write(f"echo_count:{echo['echo_count']}\n")
                    for reply in echo.get("replies", []):
                        f.write("===REPLY===\n")
                        f.write(f"text:{reply['text']}\n")
                        f.write(f"author:{reply['author']}\n")
                        f.write(f"time:{reply['time']}\n")
                        f.write("===END_REPLY===\n")
                    f.write("===END_ECHO===\n\n")
        except Exception:
            pass

    def add_echo(self, text, author="匿名"):
        if not text.strip():
            return None
        new_id = max([e["id"] for e in self.echoes], default=0) + 1
        echo = {
            "id": new_id,
            "text": text.strip(),
            "author": author,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "echo_count": 0,
            "replies": []
        }
        self.echoes.append(echo)
        self._save()
        return echo

    def echo_back(self, echo_id):
        for e in self.echoes:
            if e["id"] == echo_id:
                e["echo_count"] += 1
                self._save()
                return e["echo_count"]
        return 0

    def add_reply(self, echo_id, reply_text, author="匿名"):
        for e in self.echoes:
            if e["id"] == echo_id:
                reply = {
                    "text": reply_text.strip(),
                    "author": author,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                e["replies"].append(reply)
                self._save()
                return reply
        return None

    def get_random_echo(self):
        if not self.echoes:
            return None
        return random.choice(self.echoes)

    def get_all(self):
        return list(reversed(self.echoes))

    def get_hot(self, limit=10):
        sorted_echoes = sorted(self.echoes, key=lambda x: x.get("echo_count", 0), reverse=True)
        return sorted_echoes[:limit]

    def get_latest(self, limit=20):
        return list(reversed(self.echoes))[:limit]

    def delete_echo(self, echo_id):
        self.echoes = [e for e in self.echoes if e["id"] != echo_id]
        self._save()

    def clear_all(self):
        self.echoes = []
        self._save()

    def get_count(self):
        return len(self.echoes)

    def get_total_echoes(self):
        return sum(e.get("echo_count", 0) for e in self.echoes)
