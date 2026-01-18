"""
跨平台路径处理工具
支持 Windows、Linux、macOS
"""
import os
from pathlib import Path
from typing import Optional, Tuple


def normalize_path(path: str) -> str:
    """
    规范化路径，支持跨平台
    
    Args:
        path: 用户输入的路径（可以是相对路径或绝对路径）
    
    Returns:
        规范化的绝对路径字符串（使用当前系统的路径分隔符）
    """
    if not path:
        return ""
    
    # 移除首尾空格和引号
    path = path.strip().strip('"').strip("'")
    
    # 展开用户目录（~）
    path = os.path.expanduser(path)
    
    # 展开环境变量（如 $HOME, %USERPROFILE%）
    path = os.path.expandvars(path)
    
    # 使用 pathlib 处理路径（自动处理跨平台）
    path_obj = Path(path)
    
    # 转换为绝对路径
    try:
        absolute_path = path_obj.resolve()
        # 返回字符串，使用当前系统的路径分隔符
        return str(absolute_path)
    except (OSError, RuntimeError):
        # 如果路径不存在，仍然返回规范化的路径
        return str(path_obj)


def validate_path(path: str, must_exist: bool = True, must_be_dir: bool = False) -> Tuple[bool, Optional[str]]:
    """
    验证路径是否存在且有效
    
    Args:
        path: 要验证的路径
        must_exist: 路径是否必须存在
        must_be_dir: 是否必须是目录
    
    Returns:
        (is_valid, error_message) 元组
    """
    if not path:
        return False, "Path is empty"
    
    normalized = normalize_path(path)
    path_obj = Path(normalized)
    
    if must_exist and not path_obj.exists():
        return False, f"Path does not exist: {normalized}"
    
    if must_be_dir:
        if not path_obj.exists():
            return False, f"Directory does not exist: {normalized}"
        if not path_obj.is_dir():
            return False, f"Path is not a directory: {normalized}"
    
    return True, None


def get_relative_path(path: str, base_path: Optional[str] = None) -> str:
    """
    获取相对路径（如果可能）
    
    Args:
        path: 目标路径
        base_path: 基准路径（默认为当前工作目录）
    
    Returns:
        相对路径字符串
    """
    if not path:
        return ""
    
    normalized = normalize_path(path)
    path_obj = Path(normalized)
    
    if base_path:
        base_obj = Path(normalize_path(base_path))
        try:
            return str(path_obj.relative_to(base_obj))
        except ValueError:
            # 如果无法计算相对路径，返回绝对路径
            return normalized
    else:
        # 相对于当前工作目录
        try:
            return str(path_obj.relative_to(Path.cwd()))
        except ValueError:
            return normalized


def format_path_for_display(path: str) -> str:
    """
    格式化路径用于显示（统一使用正斜杠或反斜杠）
    
    Args:
        path: 路径字符串
    
    Returns:
        格式化后的路径
    """
    # 在 Windows 上，可以统一使用正斜杠显示（Python 支持）
    # 或者保持系统原生格式
    normalized = normalize_path(path)
    return normalized.replace('\\', '/') if os.name == 'nt' else normalized


def join_paths(*paths: str) -> str:
    """
    跨平台路径拼接
    
    Args:
        *paths: 多个路径片段
    
    Returns:
        拼接后的路径字符串
    """
    if not paths:
        return ""
    
    # 使用 pathlib 进行拼接
    result = Path(paths[0])
    for path in paths[1:]:
        result = result / path
    
    return str(result)
