import os
from datetime import datetime
import copy


class DataManager:
    def __init__(self, config_manager):
        self.config_mgr = config_manager
        self.stats = {}
        self.text_progress = {}

    def _parse_student_line(self, line):
        line = line.strip()
        if not line:
            return None
        parts = line.split(maxsplit=1)
        if len(parts) == 2 and parts[0].isdigit():
            name = parts[1].strip()
        else:
            name = line
        if name.isdigit() or not name:
            return None
        return name

    def load_students(self):
        file_path = self.config_mgr.get("files", "students")
        students = []
        error = ""
        if not os.path.exists(file_path):
            error = f"学生名单文件 {file_path} 不存在，可在设置中创建"
            return students, error
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    name = self._parse_student_line(line)
                    if name:
                        students.append(name)
            if not students:
                error = "学生名单为空，请检查文件内容"
        except Exception as e:
            error = f"读取学生名单失败：{str(e)}"
        return students, error

    def load_texts(self):
        file_path = self.config_mgr.get("files", "texts")
        texts = []
        error = ""
        if not os.path.exists(file_path):
            error = f"课文库文件 {file_path} 不存在，可在设置中创建"
            return texts, error
        try:
            current_title = None
            current_paragraphs = []
            current_para = ""
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line.startswith("【") and line.endswith("】"):
                        if current_title is not None:
                            if current_para.strip():
                                current_paragraphs.append(current_para.strip())
                            texts.append({
                                "title": current_title,
                                "paragraphs": current_paragraphs
                            })
                        current_title = line[1:-1]
                        current_paragraphs = []
                        current_para = ""
                    elif line.strip() == "":
                        if current_para.strip():
                            current_paragraphs.append(current_para.strip())
                            current_para = ""
                    else:
                        if current_para:
                            current_para += "\n" + line
                        else:
                            current_para = line
                if current_title is not None:
                    if current_para.strip():
                        current_paragraphs.append(current_para.strip())
                    texts.append({
                        "title": current_title,
                        "paragraphs": current_paragraphs
                    })
        except Exception as e:
            error = f"读取课文库失败：{str(e)}"
        return texts, error

    def save_record(self, student_name, text_title, paragraph_info, status, remark="课堂抽查"):
        file_path = self.config_mgr.get("files", "records")
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{time_str} {student_name} {text_title} {paragraph_info} {status} {remark}\n"
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass

    def get_student_status(self, name):
        return self.config_mgr.get("student_status", name) or "未背过"

    def set_student_status(self, name, status):
        self.config_mgr.set(status, "student_status", name)
        self.config_mgr.trigger_hooks("status_change", name, status)
        self.config_mgr.save_config()
        self.update_status_stats(name, status)

    def get_student_weight(self, name):
        w = self.config_mgr.get("student_weights", name)
        return w if w is not None else 1

    def set_student_weight(self, name, weight, skip_save=False):
        self.config_mgr.set(weight, "student_weights", name)
        if not skip_save:
            self.config_mgr.save_config()

    def reset_all_weights(self, students):
        for name in students:
            self.set_student_weight(name, 1, skip_save=True)
        self.config_mgr.save_config()

    def load_stats(self):
        file_path = self.config_mgr.get("files", "stats")
        self.stats = {}
        if not os.path.exists(file_path):
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) < 6:
                        continue
                    try:
                        name = parts[0]
                        draw_count = int(parts[1])
                        mastered = int(parts[2])
                        familiar = int(parts[3])
                        unlearned = int(parts[4])
                        score = int(parts[5])
                        self.stats[name] = {
                            "draw_count": draw_count,
                            "mastered": mastered,
                            "familiar": familiar,
                            "unlearned": unlearned,
                            "score": score
                        }
                    except (ValueError, IndexError):
                        continue
        except Exception:
            self.stats = {}

    def save_stats(self):
        file_path = self.config_mgr.get("files", "stats")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for name, data in self.stats.items():
                    line = f"{name} {data['draw_count']} {data['mastered']} {data['familiar']} {data['unlearned']} {data['score']}\n"
                    f.write(line)
        except Exception:
            pass

    def _init_stats_for_new_students(self, students):
        for name in students:
            if name not in self.stats:
                self.stats[name] = {
                    "draw_count": 0,
                    "mastered": 0,
                    "familiar": 0,
                    "unlearned": 0,
                    "score": 100
                }

    def increment_draw_count(self, name):
        if name not in self.stats:
            self._init_stats_for_new_students([name])
        self.stats[name]["draw_count"] += 1
        self.save_stats()

    def update_status_stats(self, name, status):
        if name not in self.stats:
            self._init_stats_for_new_students([name])
        data = self.stats[name]
        if status == "已背过":
            data["mastered"] += 1
            data["score"] += 10
        elif status == "未背熟":
            data["familiar"] += 1
            data["score"] -= 5
        elif status == "未背过":
            data["unlearned"] += 1
            data["score"] -= 15
        self.save_stats()


    def revert_status_stats(self, name, status):
        if name not in self.stats:
            return
        data = self.stats[name]
        if status == "已背过":
            data["mastered"] = max(0, data["mastered"] - 1)
            data["score"] -= 10
        elif status == "未背熟":
            data["familiar"] = max(0, data["familiar"] - 1)
            data["score"] += 5
        elif status == "未背过":
            data["unlearned"] = max(0, data["unlearned"] - 1)
            data["score"] += 15
        self.save_stats()

    def get_all_stats(self):
        return copy.deepcopy(self.stats)

    def get_ranking(self):
        ranking = [(name, data["score"]) for name, data in self.stats.items()]
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking

    def get_text_progress(self, text_title):
        return self.config_mgr.get("text_progress", text_title) or 0

    def set_text_progress(self, text_title, index):
        self.config_mgr.set(index, "text_progress", text_title)
        self.config_mgr.save_config()
    def _get_rounds_file(self):
        return os.path.join(os.path.dirname(self.config_mgr.get("files", "stats") or "stats.txt"), "rounds_history.json")

    def save_round(self, round_data):
        import json
        file_path = self._get_rounds_file()
        rounds = self._load_rounds()
        rounds.append(round_data)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(rounds, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存轮次记录失败: {e}")

    def _load_rounds(self):
        import json
        file_path = self._get_rounds_file()
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_all_rounds(self):
        rounds = self._load_rounds()
        result = []
        for r in rounds:
            result.append({
                "round_id": r.get("round_id", 0),
                "start_time": r.get("start_time", ""),
                "end_time": r.get("end_time", ""),
                "total": r.get("summary", {}).get("total", 0),
                "mastered": r.get("summary", {}).get("mastered", 0),
                "familiar": r.get("summary", {}).get("familiar", 0),
                "unlearned": r.get("summary", {}).get("unlearned", 0),
            })
        return result

    def get_round_detail(self, round_id):
        rounds = self._load_rounds()
        for r in rounds:
            if r.get("round_id") == round_id:
                return r
        return None

    def delete_round(self, round_id):
        file_path = self._get_rounds_file()
        rounds = self._load_rounds()
        rounds = [r for r in rounds if r.get("round_id") != round_id]
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(rounds, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def get_text_stats(self):
        rounds = self._load_rounds()
        text_stats = {}
        for r in rounds:
            for rec in r.get("records", []):
                text = rec.get("text", "未抽取课文")
                if text not in text_stats:
                    text_stats[text] = {"total": 0, "mastered": 0, "familiar": 0, "unlearned": 0, "students": []}
                text_stats[text]["total"] += 1
                status = rec.get("status", "")
                if status == "已背过":
                    text_stats[text]["mastered"] += 1
                elif status == "未背熟":
                    text_stats[text]["familiar"] += 1
                elif status == "未背过":
                    text_stats[text]["unlearned"] += 1
                text_stats[text]["students"].append(rec.get("student", ""))
        return text_stats

    def get_draw_records(self):
        rounds = self._load_rounds()
        all_records = []
        for r in rounds:
            for rec in r.get("records", []):
                rec_copy = rec.copy()
                rec_copy["round_id"] = r.get("round_id", 0)
                rec_copy["round_start"] = r.get("start_time", "")
                all_records.append(rec_copy)
        all_records.sort(key=lambda x: x.get("time", ""), reverse=True)
        return all_records

    def next_round_id(self):
        rounds = self._load_rounds()
        if not rounds:
            return 1
        return max(r.get("round_id", 0) for r in rounds) + 1
