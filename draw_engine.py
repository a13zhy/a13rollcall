import random
import time
from datetime import datetime


class DrawEngine:
    def __init__(self, data_manager, config_manager):
        self.data = data_manager
        self.config = config_manager
        self.is_drawing = False
        self.current_name = ""
        self.drawn_students = set()
        self.drawn_history = []
        self._start_time = 0
        self._is_manual = False
        self._students = []
        self._available = []
        self._duration = 3
        self._base_interval = 0.05

    def reset_round(self):
        self.drawn_students.clear()
        self.drawn_history.clear()
        self.current_name = ""

    def set_student_list(self, students):
        self._students = students

    def get_available_students(self):
        no_repeat = self.config.get("draw", "no_repeat")
        if no_repeat:
            return [s for s in self._students if s not in self.drawn_students]
        return self._students.copy()

    def _calculate_weight(self, student_name):
        base_weight = self.data.get_student_weight(student_name)
        dynamic = self.config.get("draw", "dynamic_focus")
        if not dynamic:
            return base_weight
        status = self.data.get_student_status(student_name)
        if status == "已背过":
            rate = self.config.get("draw", "rate_mastered")
        elif status == "未背熟":
            rate = self.config.get("draw", "rate_familiar")
        else:
            rate = self.config.get("draw", "rate_unlearned")
        return base_weight * rate

    def _weighted_random(self, students):
        if not students:
            return None
        weights = [self._calculate_weight(s) for s in students]
        total = sum(weights)
        if total <= 0:
            return random.choice(students)
        r = random.uniform(0, total)
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return students[i]
        return students[-1]

    def start_draw(self, students, mode="auto"):
        if self.is_drawing:
            return False, "", 0
        self._students = students
        self._available = self.get_available_students()
        if not self._available:
            return False, None, 0
        self.is_drawing = True
        self._is_manual = (mode == "manual")
        self._start_time = time.time()
        self._duration = self.config.get("draw", "auto_duration")
        speed = self.config.get("ui", "scroll_speed")
        self._base_interval = 0.05 / speed
        self.current_name = random.choice(self._available)
        self.config.trigger_hooks("draw_start")
        return True, self.current_name, self._base_interval

    def update(self):
        if not self.is_drawing:
            return False, self.current_name, 0
        elapsed = time.time() - self._start_time
        if not self._is_manual and elapsed >= self._duration:
            return self._finish()
        if self._is_manual:
            interval = self._base_interval
        else:
            progress = elapsed / self._duration
            ease = self.config.get("ui", "ease_strength")
            if progress > 0.7:
                slow_factor = 1 + 3 * ease * ((progress - 0.7) / 0.3)
                interval = self._base_interval * slow_factor
            else:
                interval = self._base_interval
        self.current_name = random.choice(self._available)
        return True, self.current_name, interval

    def stop_manual(self):
        if not self.is_drawing or not self._is_manual:
            return False, self.current_name, 0
        return self._finish()

    def _finish(self):
        self.is_drawing = False
        result = self._weighted_random(self._available)
        if result:
            self.drawn_students.add(result)
            self.current_name = result
            time_str = datetime.now().strftime("%H:%M:%S")
            self.drawn_history.append({
                "name": result,
                "time": time_str,
                "status": "待标记"
            })
            limit = self.config.get("draw", "history_limit") or 50
            if len(self.drawn_history) > limit:
                self.drawn_history = self.drawn_history[-limit:]
        self.config.trigger_hooks("draw_finish", result)
        return False, result, 0