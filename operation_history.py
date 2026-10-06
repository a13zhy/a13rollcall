# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 操作历史管理器
支持多级撤销/重做，记录所有用户操作
"""

from collections import deque
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime


class Operation:
    """单个操作记录"""

    def __init__(self, operation_type: str, description: str,
                 undo_func: Callable, redo_func: Callable,
                 data: Optional[Dict[str, Any]] = None):
        self.operation_type = operation_type
        self.description = description
        self.undo_func = undo_func
        self.redo_func = redo_func
        self.data = data or {}
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def undo(self) -> bool:
        """执行撤销"""
        try:
            if self.undo_func:
                self.undo_func()
            return True
        except Exception as e:
            print(f"撤销操作失败: {e}")
            return False

    def redo(self) -> bool:
        """执行重做"""
        try:
            if self.redo_func:
                self.redo_func()
            return True
        except Exception as e:
            print(f"重做操作失败: {e}")
            return False


class OperationHistoryManager:
    """
    操作历史管理器
    支持多级撤销/重做，可配置历史记录最大数量
    """

    def __init__(self, max_history: int = 50):
        self._undo_stack: deque = deque(maxlen=max_history)
        self._redo_stack: deque = deque(maxlen=max_history)
        self._max_history = max_history
        self._history_callbacks: List[Callable] = []

    def add_operation(self, operation: Operation) -> None:
        """
        添加一个新操作
        添加新操作后会清空重做栈
        """
        self._undo_stack.append(operation)
        self._redo_stack.clear()
        self._notify_callbacks()

    def add_simple_operation(self, operation_type: str, description: str,
                              undo_func: Callable, redo_func: Callable,
                              data: Optional[Dict[str, Any]] = None) -> None:
        """简化的添加操作方法"""
        operation = Operation(operation_type, description, undo_func, redo_func, data)
        self.add_operation(operation)

    def undo(self) -> Optional[Operation]:
        """执行撤销"""
        if not self._undo_stack:
            return None

        operation = self._undo_stack.pop()
        if operation.undo():
            self._redo_stack.append(operation)
            self._notify_callbacks()
            return operation
        else:
            self._undo_stack.append(operation)
            return None

    def redo(self) -> Optional[Operation]:
        """执行重做"""
        if not self._redo_stack:
            return None

        operation = self._redo_stack.pop()
        if operation.redo():
            self._undo_stack.append(operation)
            self._notify_callbacks()
            return operation
        else:
            self._redo_stack.append(operation)
            return None

    def can_undo(self) -> bool:
        """是否可以撤销"""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """是否可以重做"""
        return len(self._redo_stack) > 0

    def get_undo_count(self) -> int:
        """获取可撤销操作数量"""
        return len(self._undo_stack)

    def get_redo_count(self) -> int:
        """获取可重做操作数量"""
        return len(self._redo_stack)

    def get_last_operation(self) -> Optional[Operation]:
        """获取最后一个操作"""
        if self._undo_stack:
            return self._undo_stack[-1]
        return None

    def get_undo_history(self) -> List[Operation]:
        """获取撤销历史列表（最新的在前）"""
        return list(reversed(self._undo_stack))

    def get_redo_history(self) -> List[Operation]:
        """获取重做历史列表"""
        return list(reversed(self._redo_stack))

    def clear(self) -> None:
        """清空所有历史"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._notify_callbacks()

    def register_callback(self, callback: Callable) -> None:
        """注册历史变更回调"""
        self._history_callbacks.append(callback)

    def unregister_callback(self, callback: Callable) -> None:
        """注销历史变更回调"""
        if callback in self._history_callbacks:
            self._history_callbacks.remove(callback)

    def _notify_callbacks(self) -> None:
        """通知所有回调"""
        for callback in self._history_callbacks:
            try:
                callback(self)
            except Exception as e:
                print(f"历史回调执行失败: {e}")


class MarkOperation(Operation):
    """标记操作专用类"""

    def __init__(self, student_name: str, status: str,
                 undo_func: Callable, redo_func: Callable):
        super().__init__(
            operation_type="mark",
            description=f"标记 {student_name} 为「{status}」",
            undo_func=undo_func,
            redo_func=redo_func,
            data={"student": student_name, "status": status}
        )
        self.student_name = student_name
        self.status = status


class DrawOperation(Operation):
    """抽取操作专用类"""

    def __init__(self, student_name: str, text_title: str = "",
                 undo_func: Callable = None, redo_func: Callable = None):
        super().__init__(
            operation_type="draw",
            description=f"抽取学生：{student_name}",
            undo_func=undo_func,
            redo_func=redo_func,
            data={"student": student_name, "text_title": text_title}
        )
        self.student_name = student_name
        self.text_title = text_title


class ResetOperation(Operation):
    """重置操作专用类"""

    def __init__(self, drawn_count: int,
                 undo_func: Callable, redo_func: Callable):
        super().__init__(
            operation_type="reset",
            description=f"重置本轮（已抽取 {drawn_count} 人）",
            undo_func=undo_func,
            redo_func=redo_func,
            data={"drawn_count": drawn_count}
        )
        self.drawn_count = drawn_count


def create_history_manager(max_history: int = 50) -> OperationHistoryManager:
    """创建操作历史管理器的工厂函数"""
    return OperationHistoryManager(max_history=max_history)
