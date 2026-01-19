"""
搜索和查找工具
用于在文件系统中搜索文件、内容等
"""
import os
import re
from pathlib import Path
from typing import List, Optional, Dict
from langchain_core.tools import tool


@tool
def search_files_by_pattern(directory_path: str, pattern: str, recursive: bool = True) -> List[str]:
    """
    根据文件名模式搜索文件
    
    Args:
        directory_path: 搜索的目录路径
        pattern: 文件名模式（支持通配符，如 *.js, button.*, *test*）
        recursive: 是否递归搜索子目录
    
    Returns:
        匹配的文件路径列表
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return []
        
        files = []
        if recursive:
            for file_path in path.rglob(pattern):
                if file_path.is_file():
                    files.append(str(file_path.absolute()))
        else:
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    files.append(str(file_path.absolute()))
        
        return sorted(files)
    except Exception as e:
        return [f"Error searching files: {str(e)}"]


@tool
def search_files_by_extension(directory_path: str, extension: str, recursive: bool = True) -> List[str]:
    """
    根据文件扩展名搜索文件
    
    Args:
        directory_path: 搜索的目录路径
        extension: 文件扩展名（如 'js', 'css', 'html'，不需要点）
        recursive: 是否递归搜索子目录
    
    Returns:
        匹配的文件路径列表
    """
    if not extension.startswith('.'):
        extension = f'.{extension}'
    
    pattern = f'*{extension}'
    return search_files_by_pattern(directory_path, pattern, recursive)


@tool
def search_text_in_files(directory_path: str, search_text: str, file_pattern: str = "*", case_sensitive: bool = False) -> Dict[str, List[str]]:
    """
    在文件中搜索文本内容
    
    Args:
        directory_path: 搜索的目录路径
        search_text: 要搜索的文本
        file_pattern: 文件模式（如 "*.js", "*.html"）
        case_sensitive: 是否区分大小写
    
    Returns:
        {file_path: [匹配的行]} 字典
    """
    results = {}
    
    try:
        path = Path(directory_path)
        if not path.exists():
            return results
        
        # 查找匹配的文件
        for file_path in path.rglob(file_pattern):
            if not file_path.is_file():
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                matching_lines = []
                flags = 0 if case_sensitive else re.IGNORECASE
                
                for line_num, line in enumerate(lines, 1):
                    if re.search(search_text, line, flags):
                        matching_lines.append(f"Line {line_num}: {line.strip()}")
                
                if matching_lines:
                    results[str(file_path.absolute())] = matching_lines
            except Exception as e:
                # 跳过无法读取的文件
                continue
        
        return results
    except Exception as e:
        return {"error": [f"Error searching text: {str(e)}"]}


@tool
def find_files_by_name(directory_path: str, name_pattern: str, recursive: bool = True) -> List[str]:
    """
    根据文件名模式查找文件
    
    Args:
        directory_path: 搜索的目录路径
        name_pattern: 文件名模式（支持部分匹配，如 "button", "test_*"）
        recursive: 是否递归搜索子目录
    
    Returns:
        匹配的文件路径列表
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return []
        
        files = []
        if recursive:
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    file_name = file_path.name
                    # 支持通配符和部分匹配
                    if '*' in name_pattern:
                        pattern = name_pattern.replace('*', '.*')
                        if re.match(pattern, file_name, re.IGNORECASE):
                            files.append(str(file_path.absolute()))
                    elif name_pattern.lower() in file_name.lower():
                        files.append(str(file_path.absolute()))
        else:
            for file_path in path.iterdir():
                if file_path.is_file():
                    file_name = file_path.name
                    if '*' in name_pattern:
                        pattern = name_pattern.replace('*', '.*')
                        if re.match(pattern, file_name, re.IGNORECASE):
                            files.append(str(file_path.absolute()))
                    elif name_pattern.lower() in file_name.lower():
                        files.append(str(file_path.absolute()))
        
        return sorted(files)
    except Exception as e:
        return [f"Error finding files: {str(e)}"]


@tool
def find_component_by_resource_type(aem_repo_path: str, resource_type: str) -> Optional[str]:
    """
    根据 resourceType 查找组件路径
    
    Args:
        aem_repo_path: AEM repository 根路径
        resource_type: 组件 resourceType（如 "example/components/button"）
    
    Returns:
        组件路径，如果不存在则返回 None
    """
    try:
        from utils.dependency_resolver import resolve_resource_type_to_path
        return resolve_resource_type_to_path(resource_type, aem_repo_path)
    except Exception as e:
        return None


@tool
def find_clientlib_by_category(aem_repo_path: str, category: str) -> List[str]:
    """
    根据 ClientLibs category 查找 ClientLibs 目录
    
    Args:
        aem_repo_path: AEM repository 根路径
        category: ClientLibs category 名称
    
    Returns:
        ClientLibs 目录路径列表
    """
    try:
        from utils.css_resolver import find_clientlib_by_category as _find
        return _find(category, aem_repo_path)
    except Exception as e:
        return []


@tool
def find_css_for_class(aem_repo_path: str, component_path: str, css_class: str) -> Dict[str, str]:
    """
    查找指定 CSS class 的样式定义
    
    Args:
        aem_repo_path: AEM repository 根路径
        component_path: 组件路径
        css_class: CSS class 名称
    
    Returns:
        {file_path: css_rule} 字典
    """
    try:
        from utils.css_resolver import find_css_for_classes
        results = find_css_for_classes(component_path, {css_class}, aem_repo_path)
        if css_class in results:
            return results[css_class]
        return {}
    except Exception as e:
        return {}


@tool
def find_files_in_similar_paths(base_path: str, filename_pattern: str, file_extension: str = None, max_depth: int = 5) -> List[str]:
    """
    在相似路径中查找文件（根据文件名模式）
    
    这个工具特别适用于查找 CSS、JS 等文件，它们可能不在组件目录下，
    而是在路径相似的 styles、clientlibs 等目录中。
    
    Args:
        base_path: 基础搜索路径（通常是组件路径或其父目录）
        filename_pattern: 文件名模式（如 "button", "test_*"）
        file_extension: 文件扩展名（如 "css", "js"，不需要点）
        max_depth: 最大搜索深度
    
    Returns:
        匹配的文件路径列表
    """
    try:
        from utils.css_path_finder import find_files_by_name_pattern
        return find_files_by_name_pattern(base_path, filename_pattern, file_extension, max_depth)
    except ImportError:
        # 回退到简单搜索
        from pathlib import Path
        files = []
        base_dir = Path(base_path)
        if base_dir.exists():
            pattern = f'*{filename_pattern}*'
            if file_extension:
                pattern += f'.{file_extension}'
            for file_path in base_dir.rglob(pattern):
                if file_path.is_file():
                    files.append(str(file_path))
        return files


@tool
def find_css_for_component_in_similar_paths(component_path: str, css_filename: str = None) -> List[str]:
    """
    在组件路径的相似位置查找 CSS 文件
    
    搜索策略：
    1. 组件目录下
    2. 组件 styles/clientlibs 子目录
    3. 同级/父级 styles 目录
    4. 路径相似的 styles 目录
    
    Args:
        component_path: 组件路径
        css_filename: CSS 文件名（可选，如 "button.css"）
    
    Returns:
        CSS 文件路径列表
    """
    try:
        from utils.css_path_finder import find_css_in_similar_paths
        return find_css_in_similar_paths(component_path, css_filename)
    except ImportError:
        # 回退到简单搜索
        from pathlib import Path
        css_files = []
        component_dir = Path(component_path)
        if component_dir.exists():
            if css_filename:
                css_file = component_dir / css_filename
                if css_file.exists():
                    css_files.append(str(css_file))
            else:
                for css_file in component_dir.glob('*.css'):
                    css_files.append(str(css_file))
        return css_files


@tool
def get_file_tree(directory_path: str, max_depth: int = 3, include_files: bool = True) -> str:
    """
    获取目录树结构（文本格式）
    
    Args:
        directory_path: 目录路径
        max_depth: 最大深度
        include_files: 是否包含文件
    
    Returns:
        目录树字符串
    """
    try:
        path = Path(directory_path)
        if not path.exists():
            return f"Directory does not exist: {directory_path}"
        
        tree_lines = []
        
        def build_tree(p: Path, prefix: str = "", depth: int = 0):
            if depth > max_depth:
                return
            
            if p.is_dir():
                tree_lines.append(f"{prefix}{p.name}/")
                if depth < max_depth:
                    items = sorted(p.iterdir())
                    dirs = [item for item in items if item.is_dir()]
                    files = [item for item in items if item.is_file()] if include_files else []
                    
                    for i, item in enumerate(dirs + files):
                        is_last = (i == len(dirs + files) - 1)
                        next_prefix = "└── " if is_last else "├── "
                        build_tree(item, prefix + ("    " if is_last else "│   "), depth + 1)
            elif include_files:
                tree_lines.append(f"{prefix}{p.name}")
        
        build_tree(path)
        return "\n".join(tree_lines)
    except Exception as e:
        return f"Error building file tree: {str(e)}"
