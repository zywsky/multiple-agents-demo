"""
输出解析工具
用于从 Agent 输出中提取结构化信息
"""
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


def extract_code_from_response(response: str) -> str:
    """
    从 LLM 响应中提取代码块
    
    Args:
        response: LLM 的原始响应
    
    Returns:
        提取的代码字符串
    """
    # 尝试提取代码块（markdown 格式）
    code_block_pattern = r'```(?:jsx|tsx|javascript|typescript|js|ts)?\n(.*?)```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # 尝试提取 JSON 代码块
    json_block_pattern = r'```json\n(.*?)```'
    json_matches = re.findall(json_block_pattern, response, re.DOTALL)
    if json_matches:
        return json_matches[0].strip()
    
    # 如果没有代码块，返回整个响应（可能是纯代码）
    return response.strip()


def extract_file_paths(text: str) -> List[str]:
    """
    从文本中提取文件路径
    
    Args:
        text: 包含路径的文本
    
    Returns:
        提取的文件路径列表
    """
    paths = []
    
    # 匹配绝对路径和相对路径
    path_patterns = [
        r'[A-Za-z]:[\\/][^\s\n]+',  # Windows 绝对路径
        r'/[^\s\n]+',  # Unix 绝对路径
        r'\.\.?/[^\s\n]+',  # 相对路径
    ]
    
    for pattern in path_patterns:
        matches = re.findall(pattern, text)
        paths.extend(matches)
    
    # 去重并验证
    unique_paths = []
    for path in set(paths):
        # 清理路径（移除引号、尾随标点等）
        clean_path = path.strip('"\'.,;')
        if clean_path and (Path(clean_path).exists() or '/' in clean_path or '\\' in clean_path):
            unique_paths.append(clean_path)
    
    return unique_paths


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    从文本中提取 JSON 对象
    
    Args:
        text: 包含 JSON 的文本
    
    Returns:
        解析后的 JSON 字典，如果失败返回 None
    """
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试提取 JSON 块
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    return None


def parse_component_paths(text: str, library_path: str) -> List[str]:
    """
    解析组件路径（相对于库路径）
    
    Args:
        text: Agent 返回的文本
        library_path: BDL 库根路径
    
    Returns:
        完整的组件路径列表
    """
    from pathlib import Path
    
    paths = extract_file_paths(text)
    full_paths = []
    
    for path in paths:
        # 如果是绝对路径，直接使用
        if Path(path).is_absolute():
            full_paths.append(path)
        # 如果是相对路径，相对于库路径
        elif not path.startswith('/') and not path.startswith('\\'):
            full_path = str(Path(library_path) / path)
            full_paths.append(full_path)
        else:
            full_paths.append(path)
    
    return full_paths
