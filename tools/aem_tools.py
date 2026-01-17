"""
AEM 特定工具
用于 AEM 组件相关的操作
"""
from langchain_core.tools import tool
from typing import List, Optional, Dict
from tools import read_file, list_files
from utils.aem_utils import (
    identify_aem_file_type,
    categorize_aem_files,
    extract_htl_properties,
    extract_dialog_properties
)
from utils.dependency_resolver import (
    extract_component_dependencies,
    resolve_resource_type_to_path
)
from utils.css_resolver import (
    extract_css_classes_from_htl,
    find_css_for_classes,
    build_css_summary
)


@tool
def identify_aem_file_type_tool(file_path: str) -> str:
    """
    识别 AEM 文件类型
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件类型和优先级信息
    """
    try:
        from utils.aem_utils import identify_aem_file_type
        file_type, priority = identify_aem_file_type(file_path)
        return f"File type: {file_type}, Priority: {priority}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def extract_htl_dependencies(file_path: str) -> List[str]:
    """
    从 HTL 文件中提取组件依赖（data-sly-resource）
    
    Args:
        file_path: HTL 文件路径
    
    Returns:
        依赖组件的 resourceType 列表
    """
    try:
        content = read_file(file_path)
        # 从文件路径推断 resourceType（简化处理）
        # 实际应该从 .content.xml 或路径推断
        resource_type = "unknown"
        dependencies = extract_component_dependencies(content, resource_type)
        return dependencies
    except Exception as e:
        return [f"Error: {str(e)}"]


@tool
def extract_css_classes_from_file(file_path: str) -> List[str]:
    """
    从 HTL 文件中提取使用的 CSS classes
    
    Args:
        file_path: HTL 文件路径
    
    Returns:
        CSS class 列表
    """
    try:
        content = read_file(file_path)
        classes = extract_css_classes_from_htl(content)
        return list(classes)
    except Exception as e:
        return [f"Error: {str(e)}"]


@tool
def find_css_rules_for_component(component_path: str, aem_repo_path: str, css_classes: List[str]) -> Dict[str, Dict[str, str]]:
    """
    查找组件使用的 CSS classes 对应的样式规则
    
    Args:
        component_path: 组件路径
        aem_repo_path: AEM repository 根路径
        css_classes: CSS class 列表
    
    Returns:
        {class_name: {file_path: css_rule}} 字典
    """
    try:
        css_classes_set = set(css_classes)
        results = find_css_for_classes(component_path, css_classes_set, aem_repo_path)
        return results
    except Exception as e:
        return {}


@tool
def parse_clientlib_config(config_path: str) -> Dict:
    """
    解析 ClientLibs 配置文件
    
    Args:
        config_path: .content.xml 文件路径
    
    Returns:
        ClientLibs 配置信息
    """
    try:
        from utils.css_resolver import parse_clientlib_config
        return parse_clientlib_config(config_path)
    except Exception as e:
        return {"error": str(e)}


@tool
def get_component_files_by_type(component_path: str, file_type: str) -> List[str]:
    """
    获取组件中指定类型的文件
    
    Args:
        component_path: 组件路径
        file_type: 文件类型（htl, dialog, js, css, java 等）
    
    Returns:
        文件路径列表
    """
    try:
        all_files = list_files(component_path, recursive=False)
        categorized = categorize_aem_files(all_files)
        return categorized.get(file_type, [])
    except Exception as e:
        return []


@tool
def resolve_resource_type(resource_type: str, aem_repo_path: str) -> Optional[str]:
    """
    将 resourceType 解析为文件系统路径
    
    Args:
        resource_type: AEM resourceType
        aem_repo_path: AEM repository 根路径
    
    Returns:
        组件路径，如果不存在则返回 None
    """
    return resolve_resource_type_to_path(resource_type, aem_repo_path)
