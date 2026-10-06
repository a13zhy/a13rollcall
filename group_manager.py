# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 分组管理模块
支持创建、编辑、删除学生分组，按分组抽取，随机分组等功能
"""

import json
import os
import random
from typing import List, Dict, Optional, Tuple

try:
    from PyQt5.QtWidgets import QDialog
except ImportError:
    QDialog = object


class GroupManager:
    """
    分组管理器
    管理学生分组，支持持久化存储
    """

    def __init__(self, config_manager=None, base_dir=None):
        self.config_manager = config_manager
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.groups_file = os.path.join(self.base_dir, "groups.json")
        self.groups: Dict[str, List[str]] = {}
        self.current_group: Optional[str] = None
        self._load_groups()

    def _load_groups(self):
        """从文件加载分组"""
        try:
            if os.path.exists(self.groups_file):
                with open(self.groups_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.groups = data.get("groups", {})
                    self.current_group = data.get("current_group")
        except Exception as e:
            print(f"加载分组失败: {e}")
            self.groups = {}

    def _save_groups(self):
        """保存分组到文件"""
        try:
            data = {
                "groups": self.groups,
                "current_group": self.current_group
            }
            with open(self.groups_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存分组失败: {e}")

    def create_group(self, group_name: str, students: List[str] = None) -> bool:
        """
        创建新分组
        返回是否成功
        """
        if not group_name or not group_name.strip():
            return False
        group_name = group_name.strip()
        if group_name in self.groups:
            return False
        self.groups[group_name] = students or []
        self._save_groups()
        return True

    def delete_group(self, group_name: str) -> bool:
        """删除分组"""
        if group_name in self.groups:
            del self.groups[group_name]
            if self.current_group == group_name:
                self.current_group = None
            self._save_groups()
            return True
        return False

    def rename_group(self, old_name: str, new_name: str) -> bool:
        """重命名分组"""
        if old_name not in self.groups or not new_name.strip():
            return False
        new_name = new_name.strip()
        if new_name in self.groups:
            return False
        self.groups[new_name] = self.groups.pop(old_name)
        if self.current_group == old_name:
            self.current_group = new_name
        self._save_groups()
        return True

    def add_student_to_group(self, group_name: str, student: str) -> bool:
        """添加学生到分组"""
        if group_name not in self.groups:
            return False
        if student not in self.groups[group_name]:
            self.groups[group_name].append(student)
            self._save_groups()
        return True

    def remove_student_from_group(self, group_name: str, student: str) -> bool:
        """从分组移除学生"""
        if group_name not in self.groups:
            return False
        if student in self.groups[group_name]:
            self.groups[group_name].remove(student)
            self._save_groups()
        return True

    def get_group_students(self, group_name: str) -> List[str]:
        """获取分组中的学生列表"""
        return self.groups.get(group_name, [])

    def get_all_groups(self) -> List[str]:
        """获取所有分组名称"""
        return list(self.groups.keys())

    def set_current_group(self, group_name: Optional[str]):
        """设置当前选中的分组"""
        if group_name is None or group_name in self.groups:
            self.current_group = group_name
            self._save_groups()

    def get_current_group(self) -> Optional[str]:
        """获取当前选中的分组"""
        return self.current_group

    def get_current_students(self, all_students: List[str]) -> List[str]:
        """
        获取当前应该抽取的学生列表
        如果选中了分组，返回分组中的学生（且在总名单中）
        否则返回所有学生
        """
        if self.current_group and self.current_group in self.groups:
            group_students = self.groups[self.current_group]
            return [s for s in group_students if s in all_students]
        return all_students

    def random_grouping(self, students: List[str], group_count: int) -> Dict[str, List[str]]:
        """
        随机分组
        将学生随机分成指定数量的组
        """
        if group_count <= 0 or not students:
            return {}

        shuffled = students.copy()
        random.shuffle(shuffled)

        groups = {}
        base_size = len(shuffled) // group_count
        remainder = len(shuffled) % group_count

        idx = 0
        for i in range(group_count):
            size = base_size + (1 if i < remainder else 0)
            group_name = f"第{i+1}组"
            groups[group_name] = shuffled[idx:idx+size]
            idx += size

        return groups

    def save_random_groups(self, groups: Dict[str, List[str]]) -> bool:
        """保存随机生成的分组"""
        try:
            for name, students in groups.items():
                self.groups[name] = students
            self._save_groups()
            return True
        except Exception:
            return False

    def clear_all_groups(self):
        """清空所有分组"""
        self.groups = {}
        self.current_group = None
        self._save_groups()

    def get_group_count(self) -> int:
        """获取分组数量"""
        return len(self.groups)

    def get_student_groups(self, student: str) -> List[str]:
        """获取学生所在的所有分组"""
        return [name for name, students in self.groups.items() if student in students]

    def import_groups_from_file(self, file_path: str) -> bool:
        """从文件导入分组"""
        try:
            if not os.path.exists(file_path):
                return False
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "groups" in data:
                self.groups.update(data["groups"])
                self._save_groups()
                return True
        except Exception as e:
            print(f"导入分组失败: {e}")
        return False

    def export_groups_to_file(self, file_path: str) -> bool:
        """导出分组到文件"""
        try:
            data = {
                "groups": self.groups,
                "export_time": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出分组失败: {e}")
        return False


class GroupDialog(QDialog):
    """
    分组管理对话框
    可视化管理学生分组
    """

    def __init__(self, group_manager: GroupManager, all_students: List[str], parent=None):
        super().__init__(parent)
        self.group_manager = group_manager
        self.all_students = all_students
        self.setWindowTitle("分组管理")
        self.setMinimumSize(700, 500)
        self.resize(750, 550)
        self._setup_ui()
        self._refresh_group_list()

    def _setup_ui(self):
        from PyQt5.QtWidgets import (
            QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
            QPushButton, QLabel, QLineEdit, QInputDialog, QMessageBox,
            QFrame, QSpinBox
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_header = QHBoxLayout()
        title = QLabel("分组列表")
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0067c0;")
        left_header.addWidget(title)
        left_header.addStretch()
        left_layout.addLayout(left_header)

        self.group_list = QListWidget()
        self.group_list.itemClicked.connect(self._on_group_selected)
        left_layout.addWidget(self.group_list, 1)

        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(6)
        add_btn = QPushButton("➕ 新建分组")
        add_btn.clicked.connect(self._create_group)
        btn_layout.addWidget(add_btn)
        rename_btn = QPushButton("✏️ 重命名")
        rename_btn.clicked.connect(self._rename_group)
        btn_layout.addWidget(rename_btn)
        delete_btn = QPushButton("🗑️ 删除分组")
        delete_btn.clicked.connect(self._delete_group)
        btn_layout.addWidget(delete_btn)
        random_btn = QPushButton("🎲 随机分组")
        random_btn.clicked.connect(self._random_grouping)
        btn_layout.addWidget(random_btn)
        left_layout.addLayout(btn_layout)

        layout.addWidget(left, 1)

        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        right_header = QHBoxLayout()
        self.group_title = QLabel("选择一个分组查看学生")
        self.group_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0067c0;")
        right_header.addWidget(self.group_title)
        right_header.addStretch()
        right_layout.addLayout(right_header)

        self.student_list = QListWidget()
        right_layout.addWidget(self.student_list, 1)

        student_btn_layout = QHBoxLayout()
        add_student_btn = QPushButton("添加学生")
        add_student_btn.clicked.connect(self._add_student)
        student_btn_layout.addWidget(add_student_btn)
        remove_student_btn = QPushButton("移除学生")
        remove_student_btn.clicked.connect(self._remove_student)
        student_btn_layout.addWidget(remove_student_btn)
        right_layout.addLayout(student_btn_layout)

        layout.addWidget(right, 1)

        bottom_btn_layout = QHBoxLayout()
        bottom_btn_layout.addStretch()
        ok_btn = QPushButton("确定")
        ok_btn.setObjectName("primary")
        ok_btn.clicked.connect(self.accept)
        bottom_btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        bottom_btn_layout.addWidget(cancel_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(layout, 1)
        main_layout.addLayout(bottom_btn_layout)
        self.setLayout(main_layout)

    def _refresh_group_list(self):
        self.group_list.clear()
        all_item = QListWidgetItem("📋 全部学生")
        all_item.setData(0, "__all__")
        self.group_list.addItem(all_item)
        for name in self.group_manager.get_all_groups():
            count = len(self.group_manager.get_group_students(name))
            item = QListWidgetItem(f"📁 {name} ({count}人)")
            item.setData(0, name)
            self.group_list.addItem(item)

    def _on_group_selected(self, item):
        group_name = item.data(0)
        self.student_list.clear()
        if group_name == "__all__":
            self.group_title.setText("全部学生")
            for student in self.all_students:
                self.student_list.addItem(QListWidgetItem(student))
        else:
            self.group_title.setText(f"分组：{group_name}")
            students = self.group_manager.get_group_students(group_name)
            for student in students:
                self.student_list.addItem(QListWidgetItem(student))

    def _create_group(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        name, ok = QInputDialog.getText(self, "新建分组", "请输入分组名称：")
        if ok and name.strip():
            if self.group_manager.create_group(name.strip()):
                self._refresh_group_list()
            else:
                QMessageBox.warning(self, "创建失败", "分组名称已存在或无效！")

    def _rename_group(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        item = self.group_list.currentItem()
        if not item or item.data(0) == "__all__":
            QMessageBox.information(self, "提示", "请先选择一个分组！")
            return
        old_name = item.data(0)
        new_name, ok = QInputDialog.getText(self, "重命名分组", "请输入新名称：", text=old_name)
        if ok and new_name.strip():
            if self.group_manager.rename_group(old_name, new_name.strip()):
                self._refresh_group_list()
            else:
                QMessageBox.warning(self, "重命名失败", "新名称已存在或无效！")

    def _delete_group(self):
        from PyQt5.QtWidgets import QMessageBox
        item = self.group_list.currentItem()
        if not item or item.data(0) == "__all__":
            QMessageBox.information(self, "提示", "请先选择一个分组！")
            return
        group_name = item.data(0)
        reply = QMessageBox.question(self, "确认删除", f"确定要删除分组「{group_name}」吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.group_manager.delete_group(group_name)
            self._refresh_group_list()
            self.student_list.clear()
            self.group_title.setText("选择一个分组查看学生")

    def _random_grouping(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        if not self.all_students:
            QMessageBox.information(self, "提示", "没有学生可以分组！")
            return
        count, ok = QInputDialog.getInt(self, "随机分组", "请输入分组数量：", 2, 2, 20, 1)
        if ok:
            groups = self.group_manager.random_grouping(self.all_students, count)
            reply = QMessageBox.question(self, "确认保存",
                                          f"已随机分成 {len(groups)} 组，是否保存这些分组？\n（将覆盖同名分组）",
                                          QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.group_manager.save_random_groups(groups)
                self._refresh_group_list()

    def _add_student(self):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox
        item = self.group_list.currentItem()
        if not item or item.data(0) == "__all__":
            QMessageBox.information(self, "提示", "请先选择一个分组！")
            return
        group_name = item.data(0)
        available = [s for s in self.all_students if s not in self.group_manager.get_group_students(group_name)]
        if not available:
            QMessageBox.information(self, "提示", "所有学生都已在此分组中！")
            return
        student, ok = QInputDialog.getItem(self, "添加学生", "选择要添加的学生：", available, 0, False)
        if ok and student:
            self.group_manager.add_student_to_group(group_name, student)
            self._on_group_selected(item)
            self._refresh_group_list()

    def _remove_student(self):
        from PyQt5.QtWidgets import QMessageBox
        item = self.group_list.currentItem()
        if not item or item.data(0) == "__all__":
            return
        group_name = item.data(0)
        student_item = self.student_list.currentItem()
        if not student_item:
            QMessageBox.information(self, "提示", "请先选择要移除的学生！")
            return
        student = student_item.text()
        self.group_manager.remove_student_from_group(group_name, student)
        self._on_group_selected(item)
        self._refresh_group_list()


def create_group_manager(config_manager=None, base_dir=None) -> GroupManager:
    """创建分组管理器的工厂函数"""
    return GroupManager(config_manager, base_dir)
