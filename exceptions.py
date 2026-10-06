# -*- coding: utf-8 -*-
"""
A13课堂点名系统 - 异常层级设计模块
定义项目统一的异常类层级，便于错误处理和排查
"""

import traceback
from datetime import datetime
from typing import Optional, Dict, Any


# ==================== 基础异常 ====================
class A13BaseError(Exception):
    """A13系统基础异常类"""

    def __init__(self, message: str = "", error_code: int = -1, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        super().__init__(message)

    def __str__(self):
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    def get_full_traceback(self) -> str:
        return traceback.format_exc()


# ==================== 配置相关异常 ====================
class ConfigError(A13BaseError):
    """配置相关异常基类"""
    pass


class ConfigNotFoundError(ConfigError):
    """配置文件不存在"""
    def __init__(self, config_path: str = "", message: str = ""):
        super().__init__(
            message=message or f"配置文件不存在: {config_path}",
            error_code=-200,
            details={"config_path": config_path}
        )


class ConfigParseError(ConfigError):
    """配置解析错误"""
    def __init__(self, config_path: str = "", parse_error: str = "", message: str = ""):
        super().__init__(
            message=message or f"配置文件解析失败: {config_path}\n错误: {parse_error}",
            error_code=-201,
            details={"config_path": config_path, "parse_error": parse_error}
        )


class ConfigSchemaError(ConfigError):
    """配置Schema验证错误"""
    def __init__(self, schema_errors: list = None, message: str = ""):
        super().__init__(
            message=message or f"配置Schema验证失败: {len(schema_errors or [])} 个错误",
            error_code=-202,
            details={"schema_errors": schema_errors or []}
        )


class ConfigValueError(ConfigError):
    """配置值错误"""
    def __init__(self, key: str = "", value: Any = None, expected: str = "", message: str = ""):
        super().__init__(
            message=message or f"配置值错误: {key} = {value}, 期望: {expected}",
            error_code=-203,
            details={"key": key, "value": value, "expected": expected}
        )


# ==================== 文件相关异常 ====================
class FileError(A13BaseError):
    """文件相关异常基类"""
    pass


class FileNotFoundError(FileError):
    """文件不存在"""
    def __init__(self, file_path: str = "", message: str = ""):
        super().__init__(
            message=message or f"文件不存在: {file_path}",
            error_code=-100,
            details={"file_path": file_path}
        )


class FileReadError(FileError):
    """文件读取错误"""
    def __init__(self, file_path: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"文件读取失败: {file_path}\n错误: {error}",
            error_code=-101,
            details={"file_path": file_path, "error": error}
        )


class FileWriteError(FileError):
    """文件写入错误"""
    def __init__(self, file_path: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"文件写入失败: {file_path}\n错误: {error}",
            error_code=-102,
            details={"file_path": file_path, "error": error}
        )


class FileCorruptedError(FileError):
    """文件损坏"""
    def __init__(self, file_path: str = "", message: str = ""):
        super().__init__(
            message=message or f"文件已损坏: {file_path}",
            error_code=-103,
            details={"file_path": file_path}
        )


class FileLockedError(FileError):
    """文件被锁定"""
    def __init__(self, file_path: str = "", message: str = ""):
        super().__init__(
            message=message or f"文件被锁定，无法访问: {file_path}",
            error_code=-104,
            details={"file_path": file_path}
        )


class FileEncodingError(FileError):
    """文件编码错误"""
    def __init__(self, file_path: str = "", encoding: str = "", message: str = ""):
        super().__init__(
            message=message or f"文件编码错误: {file_path}, 编码: {encoding}",
            error_code=-105,
            details={"file_path": file_path, "encoding": encoding}
        )


# ==================== 插件相关异常 ====================
class PluginError(A13BaseError):
    """插件相关异常基类"""
    pass


class PluginNotFoundError(PluginError):
    """插件不存在"""
    def __init__(self, plugin_name: str = "", message: str = ""):
        super().__init__(
            message=message or f"插件不存在: {plugin_name}",
            error_code=-300,
            details={"plugin_name": plugin_name}
        )


class PluginLoadError(PluginError):
    """插件加载错误"""
    def __init__(self, plugin_name: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"插件加载失败: {plugin_name}\n错误: {error}",
            error_code=-301,
            details={"plugin_name": plugin_name, "error": error}
        )


class PluginExecuteError(PluginError):
    """插件执行错误"""
    def __init__(self, plugin_name: str = "", function_name: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"插件执行失败: {plugin_name}.{function_name}\n错误: {error}",
            error_code=-302,
            details={"plugin_name": plugin_name, "function_name": function_name, "error": error}
        )


class PluginDependencyMissingError(PluginError):
    """插件依赖缺失"""
    def __init__(self, plugin_name: str = "", missing_deps: list = None, message: str = ""):
        super().__init__(
            message=message or f"插件依赖缺失: {plugin_name}\n缺失: {', '.join(missing_deps or [])}",
            error_code=-303,
            details={"plugin_name": plugin_name, "missing_deps": missing_deps or []}
        )


class PluginVersionIncompatibleError(PluginError):
    """插件版本不兼容"""
    def __init__(self, plugin_name: str = "", required_version: str = "", current_version: str = "", message: str = ""):
        super().__init__(
            message=message or f"插件版本不兼容: {plugin_name}\n要求: {required_version}, 当前: {current_version}",
            error_code=-304,
            details={"plugin_name": plugin_name, "required_version": required_version, "current_version": current_version}
        )


class PluginPermissionDeniedError(PluginError):
    """插件权限被拒绝"""
    def __init__(self, plugin_name: str = "", permission: str = "", message: str = ""):
        super().__init__(
            message=message or f"插件权限被拒绝: {plugin_name}\n权限: {permission}",
            error_code=-305,
            details={"plugin_name": plugin_name, "permission": permission}
        )


class PluginCrashedError(PluginError):
    """插件崩溃"""
    def __init__(self, plugin_name: str = "", crash_info: str = "", message: str = ""):
        super().__init__(
            message=message or f"插件崩溃: {plugin_name}\n崩溃信息: {crash_info}",
            error_code=-306,
            details={"plugin_name": plugin_name, "crash_info": crash_info}
        )


class PluginFormatError(PluginError):
    """插件格式错误"""
    def __init__(self, file_path: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"插件格式错误: {file_path}\n错误: {error}",
            error_code=-307,
            details={"file_path": file_path, "error": error}
        )


# ==================== 网络相关异常 ====================
class NetworkError(A13BaseError):
    """网络相关异常基类"""
    pass


class NetworkTimeoutError(NetworkError):
    """网络超时"""
    def __init__(self, url: str = "", timeout: float = 0, message: str = ""):
        super().__init__(
            message=message or f"网络请求超时: {url} (超时: {timeout}s)",
            error_code=-400,
            details={"url": url, "timeout": timeout}
        )


class NetworkConnectionError(NetworkError):
    """网络连接错误"""
    def __init__(self, url: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"网络连接失败: {url}\n错误: {error}",
            error_code=-401,
            details={"url": url, "error": error}
        )


class NetworkHttpError(NetworkError):
    """HTTP错误"""
    def __init__(self, url: str = "", status_code: int = 0, message: str = ""):
        super().__init__(
            message=message or f"HTTP请求错误: {url} (状态码: {status_code})",
            error_code=-402,
            details={"url": url, "status_code": status_code}
        )


class NetworkSslError(NetworkError):
    """SSL错误"""
    def __init__(self, url: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"SSL错误: {url}\n错误: {error}",
            error_code=-403,
            details={"url": url, "error": error}
        )


# ==================== 数据相关异常 ====================
class DataError(A13BaseError):
    """数据相关异常基类"""
    pass


class DataEmptyError(DataError):
    """数据为空"""
    def __init__(self, data_name: str = "", message: str = ""):
        super().__init__(
            message=message or f"数据为空: {data_name}",
            error_code=-500,
            details={"data_name": data_name}
        )


class DataInvalidError(DataError):
    """数据无效"""
    def __init__(self, data_name: str = "", invalid_value: Any = None, message: str = ""):
        super().__init__(
            message=message or f"数据无效: {data_name} = {invalid_value}",
            error_code=-501,
            details={"data_name": data_name, "invalid_value": invalid_value}
        )


class DataDuplicateError(DataError):
    """数据重复"""
    def __init__(self, data_name: str = "", duplicate_value: Any = None, message: str = ""):
        super().__init__(
            message=message or f"数据重复: {data_name} = {duplicate_value}",
            error_code=-502,
            details={"data_name": data_name, "duplicate_value": duplicate_value}
        )


class DataNotFoundError(DataError):
    """数据不存在"""
    def __init__(self, data_name: str = "", search_key: Any = None, message: str = ""):
        super().__init__(
            message=message or f"数据不存在: {data_name} (查找: {search_key})",
            error_code=-503,
            details={"data_name": data_name, "search_key": search_key}
        )


# ==================== 抽取相关异常 ====================
class DrawError(A13BaseError):
    """抽取相关异常基类"""
    pass


class DrawNoStudentsError(DrawError):
    """没有学生可抽取"""
    def __init__(self, message: str = ""):
        super().__init__(
            message=message or "没有学生可抽取，请先添加学生名单",
            error_code=-600
        )


class DrawAllDrawnError(DrawError):
    """所有学生已抽取完毕"""
    def __init__(self, message: str = ""):
        super().__init__(
            message=message or "所有学生已抽取完毕，请重置本轮",
            error_code=-601
        )


class DrawAlreadyRunningError(DrawError):
    """抽取正在进行中"""
    def __init__(self, message: str = ""):
        super().__init__(
            message=message or "抽取正在进行中，请稍候",
            error_code=-602
        )


class DrawNotRunningError(DrawError):
    """抽取未在进行中"""
    def __init__(self, message: str = ""):
        super().__init__(
            message=message or "当前没有正在进行的抽取",
            error_code=-603
        )


# ==================== UI相关异常 ====================
class UIError(A13BaseError):
    """UI相关异常基类"""
    pass


class WidgetNotFoundError(UIError):
    """控件不存在"""
    def __init__(self, widget_name: str = "", message: str = ""):
        super().__init__(
            message=message or f"控件不存在: {widget_name}",
            error_code=-700,
            details={"widget_name": widget_name}
        )


class LayoutError(UIError):
    """布局错误"""
    def __init__(self, layout_name: str = "", error: str = "", message: str = ""):
        super().__init__(
            message=message or f"布局错误: {layout_name}\n错误: {error}",
            error_code=-701,
            details={"layout_name": layout_name, "error": error}
        )


# ==================== 权限相关异常 ====================
class PermissionError(A13BaseError):
    """权限相关异常基类"""
    pass


class PermissionDeniedError(PermissionError):
    """权限被拒绝"""
    def __init__(self, permission: str = "", message: str = ""):
        super().__init__(
            message=message or f"权限被拒绝: {permission}",
            error_code=-4,
            details={"permission": permission}
        )


class OperationNotAllowedError(PermissionError):
    """操作不被允许"""
    def __init__(self, operation: str = "", reason: str = "", message: str = ""):
        super().__init__(
            message=message or f"操作不被允许: {operation}\n原因: {reason}",
            error_code=-5,
            details={"operation": operation, "reason": reason}
        )


# ==================== 异常工具函数 ====================
def get_error_category(error_code: int) -> str:
    """根据错误码获取错误类别"""
    if error_code == 0:
        return "成功"
    elif -100 > error_code >= -200:
        return "配置错误"
    elif -100 > error_code >= -100:
        return "文件错误"
    elif -300 > error_code >= -400:
        return "插件错误"
    elif -400 > error_code >= -500:
        return "网络错误"
    elif -500 > error_code >= -600:
        return "数据错误"
    elif -600 > error_code >= -700:
        return "抽取错误"
    elif -700 > error_code >= -800:
        return "UI错误"
    else:
        return "未知错误"


def format_error_message(error: Exception) -> str:
    """格式化错误消息，用户友好"""
    if isinstance(error, A13BaseError):
        return error.message
    elif isinstance(error, FileNotFoundError):
        return f"文件不存在: {error.filename}"
    elif isinstance(error, PermissionError):
        return "权限不足，无法执行此操作"
    elif isinstance(error, TimeoutError):
        return "操作超时，请重试"
    elif isinstance(error, MemoryError):
        return "内存不足，请关闭其他程序后重试"
    else:
        return f"发生错误: {str(error)}"


def get_user_friendly_suggestion(error: Exception) -> str:
    """获取用户友好的错误解决建议"""
    if isinstance(error, ConfigNotFoundError):
        return "配置文件将在下次保存时自动创建"
    elif isinstance(error, ConfigParseError):
        return "配置文件格式错误，建议删除配置文件后重启程序，将自动恢复默认配置"
    elif isinstance(error, FileNotFoundError):
        return "请检查文件路径是否正确，或重新创建该文件"
    elif isinstance(error, FileCorruptedError):
        return "文件已损坏，建议从备份恢复，或重新生成该文件"
    elif isinstance(error, PluginLoadError):
        return "插件加载失败，请检查插件文件是否完整，或尝试重新安装插件"
    elif isinstance(error, PluginDependencyMissingError):
        return "插件缺少依赖库，请安装所需的Python库后重试"
    elif isinstance(error, PluginVersionIncompatibleError):
        return "插件版本与当前程序不兼容，请更新程序或插件"
    elif isinstance(error, NetworkTimeoutError):
        return "网络连接超时，请检查网络连接后重试"
    elif isinstance(error, DrawNoStudentsError):
        return "请先在学生名单文件中添加学生信息"
    elif isinstance(error, DrawAllDrawnError):
        return "点击'重置本轮'按钮可以重新开始抽取"
    elif isinstance(error, PermissionDeniedError):
        return "请以管理员身份运行程序，或检查文件权限"
    else:
        return "如问题持续存在，请查看日志文件或联系技术支持"


# ==================== 异常上下文管理器 ====================
class ExceptionHandler:
    """异常处理器，用于统一捕获和处理异常"""

    def __init__(self, raise_errors: bool = False, log_errors: bool = True):
        self.raise_errors = raise_errors
        self.log_errors = log_errors
        self.last_error = None

    def handle(self, error: Exception, context: str = "") -> bool:
        """处理异常，返回是否成功处理"""
        self.last_error = error

        if self.log_errors:
            try:
                import logging
                logging.error(f"[{context}] {type(error).__name__}: {str(error)}")
                logging.error(traceback.format_exc())
            except Exception:
                pass

        if self.raise_errors:
            raise error

        return True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            return self.handle(exc_val, "context")
        return False


# ==================== 安全执行装饰器 ====================
def safe_execute(default_return=None, log_error: bool = True, show_error: bool = False):
    """安全执行装饰器，捕获异常并返回默认值"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    try:
                        import logging
                        logging.error(f"函数 {func.__name__} 执行失败: {str(e)}")
                        logging.error(traceback.format_exc())
                    except Exception:
                        pass
                if show_error:
                    try:
                        from PyQt5.QtWidgets import QMessageBox
                        QMessageBox.critical(None, "错误", format_error_message(e))
                    except Exception:
                        pass
                return default_return
        return wrapper
    return decorator
