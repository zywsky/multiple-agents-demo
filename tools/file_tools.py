"""
文件操作工具集合
提供文件读取、写入、列表、存在性检查、命令执行等功能
"""
import os
import subprocess
from typing import List, Optional
from pathlib import Path


def list_files(directory_path: str, recursive: bool = True) -> List[str]:
    """
    列出指定目录下的所有文件
    
    Args:
        directory_path: 目录路径
        recursive: 是否递归列出子目录中的文件
    
    Returns:
        文件路径列表
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return []
        
        files = []
        if recursive:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    files.append(str(file_path.absolute()))
        else:
            for file_path in path.iterdir():
                if file_path.is_file():
                    files.append(str(file_path.absolute()))
        
        return sorted(files)
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


def read_file(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件内容字符串
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """
    写入内容到文件（如果文件不存在则创建）
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
    
    Returns:
        操作结果消息
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def file_exists(file_path: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件是否存在
    """
    return os.path.exists(file_path) and os.path.isfile(file_path)


def directory_exists(directory_path: str) -> bool:
    """
    检查目录是否存在
    
    Args:
        directory_path: 目录路径
    
    Returns:
        目录是否存在
    """
    return os.path.exists(directory_path) and os.path.isdir(directory_path)


def create_directory(directory_path: str) -> str:
    """
    创建目录（如果不存在）
    
    Args:
        directory_path: 目录路径
    
    Returns:
        操作结果消息
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return f"Successfully created directory: {directory_path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


def run_command(command: str, working_directory: Optional[str] = None, timeout: int = 300) -> dict:
    """
    在指定目录下执行命令
    
    Args:
        command: 要执行的命令
        working_directory: 工作目录（如果为None则使用当前目录）
        timeout: 超时时间（秒）
    
    Returns:
        包含stdout, stderr, returncode的字典
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "returncode": -1,
            "success": False
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "returncode": -1,
            "success": False
        }


def get_file_info(file_path: str) -> dict:
    """
    获取文件信息（大小、修改时间等）
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件信息字典
    """
    try:
        stat = os.stat(file_path)
        return {
            "path": file_path,
            "size": stat.st_size,
            "modified_time": stat.st_mtime,
            "exists": True
        }
    except Exception as e:
        return {
            "path": file_path,
            "exists": False,
            "error": str(e)
        }
