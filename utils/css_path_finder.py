"""
CSS 路径查找器
用于在相似路径中查找 CSS 文件

AEM 中，CSS 文件可能位于：
1. 组件目录下：/apps/example/components/button/button.css
2. 组件 styles 子目录：/apps/example/components/button/styles/button.css
3. 同级 styles 目录：/apps/example/components/styles/button.css
4. 父级 styles 目录：/apps/example/styles/components/button.css
5. 共享 styles 目录：/apps/example/styles/button.css
"""
import os
from pathlib import Path
from typing import List, Optional, Set
import logging

logger = logging.getLogger(__name__)


def find_css_in_similar_paths(component_path: str, css_filename: str = None) -> List[str]:
    """
    在组件路径的相似位置查找 CSS 文件
    
    搜索策略（按优先级）：
    1. 组件目录下：component_path/*.css
    2. 组件 styles 子目录：component_path/styles/*.css
    3. 组件 clientlibs 子目录：component_path/clientlibs/*.css
    4. 同级 styles 目录：component_path/../styles/component_name/*.css
    5. 父级 styles 目录：component_path/../../styles/component_name/*.css
    6. 共享 styles 目录：component_path/../../styles/*.css
    
    Args:
        component_path: 组件路径
        css_filename: CSS 文件名（可选，如 "button.css"）
    
    Returns:
        CSS 文件路径列表
    """
    css_files = []
    component_dir = Path(component_path)
    component_name = component_dir.name
    
    if not component_dir.exists():
        return css_files
    
    # 策略 1: 组件目录下直接查找
    if css_filename:
        css_file = component_dir / css_filename
        if css_file.exists():
            css_files.append(str(css_file))
    else:
        for css_file in component_dir.glob('*.css'):
            css_files.append(str(css_file))
    
    # 策略 2: 组件 styles 子目录
    styles_dir = component_dir / 'styles'
    if styles_dir.exists() and styles_dir.is_dir():
        if css_filename:
            css_file = styles_dir / css_filename
            if css_file.exists():
                css_files.append(str(css_file))
        else:
            for css_file in styles_dir.glob('*.css'):
                css_files.append(str(css_file))
    
    # 策略 3: 组件 clientlibs 子目录
    clientlibs_dir = component_dir / 'clientlibs'
    if clientlibs_dir.exists() and clientlibs_dir.is_dir():
        if css_filename:
            css_file = clientlibs_dir / css_filename
            if css_file.exists():
                css_files.append(str(css_file))
        else:
            for css_file in clientlibs_dir.glob('*.css'):
                css_files.append(str(css_file))
    
    # 策略 4: 同级 styles 目录（components/styles/button/）
    parent_dir = component_dir.parent
    styles_dir = parent_dir / 'styles' / component_name
    if styles_dir.exists() and styles_dir.is_dir():
        if css_filename:
            css_file = styles_dir / css_filename
            if css_file.exists():
                css_files.append(str(css_file))
        else:
            for css_file in styles_dir.glob('*.css'):
                css_files.append(str(css_file))
    
    # 策略 5: 父级 styles 目录（components/styles/）
    styles_dir = parent_dir / 'styles'
    if styles_dir.exists() and styles_dir.is_dir():
        if css_filename:
            css_file = styles_dir / css_filename
            if css_file.exists():
                css_files.append(str(css_file))
        else:
            for css_file in styles_dir.glob('*.css'):
                css_files.append(str(css_file))
    
    # 策略 6: 更上级的 styles 目录（向上查找最多 3 层）
    current_dir = parent_dir
    for depth in range(3):
        styles_dir = current_dir / 'styles'
        if styles_dir.exists() and styles_dir.is_dir():
            # 尝试按组件名称查找
            component_styles_dir = styles_dir / component_name
            if component_styles_dir.exists():
                if css_filename:
                    css_file = component_styles_dir / css_filename
                    if css_file.exists():
                        css_files.append(str(css_file))
                else:
                    for css_file in component_styles_dir.glob('*.css'):
                        css_files.append(str(css_file))
            
            # 也查找 styles 目录下的所有 CSS
            if css_filename:
                css_file = styles_dir / css_filename
                if css_file.exists():
                    css_files.append(str(css_file))
        
        # 向上移动一层
        current_dir = current_dir.parent
        if not current_dir or current_dir == current_dir.parent:
            break
    
    # 去重
    return list(set(css_files))


def find_css_by_component_name(base_path: str, component_name: str, max_depth: int = 5) -> List[str]:
    """
    根据组件名称在相似路径中查找 CSS 文件
    
    搜索模式：
    - {base_path}/**/styles/{component_name}/*.css
    - {base_path}/**/styles/*{component_name}*.css
    - {base_path}/**/{component_name}/*.css
    - {base_path}/**/*{component_name}*.css
    
    Args:
        base_path: 基础搜索路径（通常是组件路径的父目录）
        component_name: 组件名称
        max_depth: 最大搜索深度
    
    Returns:
        CSS 文件路径列表
    """
    css_files = []
    base_dir = Path(base_path)
    
    if not base_dir.exists():
        return css_files
    
    # 模式 1: styles/{component_name}/*.css
    for css_file in base_dir.rglob(f'styles/{component_name}/*.css'):
        if css_file.is_file():
            css_files.append(str(css_file))
    
    # 模式 2: styles/*{component_name}*.css
    for css_file in base_dir.rglob(f'styles/*{component_name}*.css'):
        if css_file.is_file():
            css_files.append(str(css_file))
    
    # 模式 3: {component_name}/*.css（不在 styles 目录下）
    for css_file in base_dir.rglob(f'{component_name}/*.css'):
        if css_file.is_file() and 'styles' not in str(css_file):
            css_files.append(str(css_file))
    
    # 模式 4: *{component_name}*.css（文件名包含组件名）
    for css_file in base_dir.rglob(f'*{component_name}*.css'):
        if css_file.is_file():
            css_files.append(str(css_file))
    
    # 限制深度（如果指定）
    if max_depth > 0:
        filtered_files = []
        for css_file in css_files:
            path = Path(css_file)
            relative_path = path.relative_to(base_dir)
            depth = len(relative_path.parts)
            if depth <= max_depth:
                filtered_files.append(css_file)
        css_files = filtered_files
    
    return list(set(css_files))


def find_files_by_name_pattern(base_path: str, name_pattern: str, file_extension: str = None, max_depth: int = 5) -> List[str]:
    """
    根据名称模式在相似路径中查找文件
    
    这是一个通用的文件查找工具，可以根据文件名模式在相似路径中搜索。
    
    Args:
        base_path: 基础搜索路径
        name_pattern: 文件名模式（支持部分匹配，如 "button", "test_*"）
        file_extension: 文件扩展名（如 "css", "js"，不需要点）
        max_depth: 最大搜索深度
    
    Returns:
        匹配的文件路径列表
    """
    files = []
    base_dir = Path(base_path)
    
    if not base_dir.exists():
        return files
    
    # 构建搜索模式
    if file_extension:
        if not file_extension.startswith('.'):
            file_extension = f'.{file_extension}'
        pattern = f'*{name_pattern}*{file_extension}'
    else:
        pattern = f'*{name_pattern}*'
    
    # 搜索文件
    for file_path in base_dir.rglob(pattern):
        if file_path.is_file():
            # 检查深度
            if max_depth > 0:
                relative_path = file_path.relative_to(base_dir)
                depth = len(relative_path.parts)
                if depth > max_depth:
                    continue
            files.append(str(file_path))
    
    return sorted(list(set(files)))


def infer_css_path_from_component(component_path: str) -> List[str]:
    """
    从组件路径推断可能的 CSS 文件路径
    
    推断策略：
    1. 组件目录下的 CSS 文件
    2. 组件名称匹配的 CSS 文件（在 styles 目录中）
    3. 路径相似的 CSS 文件
    
    Args:
        component_path: 组件路径
    
    Returns:
        可能的 CSS 文件路径列表
    """
    css_files = []
    component_dir = Path(component_path)
    component_name = component_dir.name
    
    if not component_dir.exists():
        return css_files
    
    # 1. 组件目录下的 CSS
    for css_file in component_dir.glob('*.css'):
        css_files.append(str(css_file))
    
    # 2. 在父目录的 styles 中查找
    parent_dir = component_dir.parent
    # 向上查找最多 5 层
    current_dir = parent_dir
    for depth in range(5):
        # styles/{component_name}/*.css
        styles_dir = current_dir / 'styles' / component_name
        if styles_dir.exists():
            for css_file in styles_dir.glob('*.css'):
                css_files.append(str(css_file))
        
        # styles/*{component_name}*.css
        styles_dir = current_dir / 'styles'
        if styles_dir.exists():
            for css_file in styles_dir.glob(f'*{component_name}*.css'):
                css_files.append(str(css_file))
        
        # 向上移动
        if current_dir == current_dir.parent:
            break
        current_dir = current_dir.parent
    
    # 3. 在相同路径结构的其他位置查找
    # 例如：如果组件在 /apps/example/components/button
    # 可能在 /apps/example/styles/components/button 或 /apps/example/styles/button
    path_parts = component_dir.parts
    if len(path_parts) >= 3:
        # 尝试替换 "components" 为 "styles"
        new_parts = []
        for part in path_parts:
            if part == 'components':
                new_parts.append('styles')
            else:
                new_parts.append(part)
        
        # 构建新路径
        inferred_path = Path(*new_parts)
        if inferred_path.exists():
            for css_file in inferred_path.glob('*.css'):
                css_files.append(str(css_file))
        
        # 也尝试在 styles 目录下直接查找组件名
        if len(path_parts) >= 2:
            styles_base = Path(*path_parts[:-1]) / 'styles' / component_name
            if styles_base.exists():
                for css_file in styles_base.glob('*.css'):
                    css_files.append(str(css_file))
    
    return list(set(css_files))
