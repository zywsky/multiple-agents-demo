"""
AEM 工具函数
用于识别和分析 AEM 组件文件类型
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# AEM 文件类型优先级（按重要性排序）
AEM_FILE_PRIORITIES = {
    'htl': 1,           # HTL 模板 - 最重要，包含UI结构和逻辑
    'html': 1,          # HTML 模板（可能是 HTL）
    'dialog': 2,        # Dialog XML - 定义了编辑属性和配置
    'xml': 2,           # XML 配置文件（包括 dialog, cq:dialog）
    'js': 3,            # JavaScript - 客户端交互逻辑
    'javascript': 3,    # JavaScript 文件
    'java': 4,          # Java Sling Model（后续提供）
    'css': 5,           # CSS 样式（后续提供）
    'less': 5,          # LESS 样式
    'scss': 5,          # SCSS 样式
    'json': 6,          # JSON 配置
    'properties': 7,    # Properties 文件
    'txt': 8,           # 文本文件
    'md': 8,            # Markdown 文档
}

# AEM 文件类型模式
FILE_PATTERNS = {
    'htl': ['*.html', '*.htl'],
    'dialog': ['.content.xml', '_cq_dialog.xml', '_cq_dialog/*.xml'],
    'java': ['*.java'],
    'js': ['*.js', 'clientlibs.js'],
    'css': ['*.css'],
    'config': ['.content.xml', '*_cq_*.xml'],
}


def identify_aem_file_type(file_path: str) -> Tuple[str, int]:
    """
    识别 AEM 文件类型和优先级
    
    Returns:
        (file_type, priority): 文件类型和优先级（数字越小越重要）
    """
    file_name = os.path.basename(file_path).lower()
    file_ext = os.path.splitext(file_name)[1].lower().lstrip('.')
    dir_path = os.path.dirname(file_path)
    dir_name = os.path.basename(dir_path).lower()
    
    # 检查 dialog 文件
    if '_cq_dialog' in dir_path.lower() or 'dialog' in dir_name:
        return ('dialog', AEM_FILE_PRIORITIES.get('dialog', 2))
    
    # 检查 .content.xml
    if file_name.endswith('.content.xml') or 'content.xml' in file_path.lower():
        return ('config', AEM_FILE_PRIORITIES.get('xml', 6))
    
    # 检查文件扩展名
    if file_ext in AEM_FILE_PRIORITIES:
        priority = AEM_FILE_PRIORITIES.get(file_ext, 10)
        return (file_ext, priority)
    
    # 默认
    return ('unknown', 99)


def prioritize_aem_files(files: List[str]) -> List[str]:
    """
    根据文件重要性对 AEM 组件文件进行排序
    
    Args:
        files: 文件路径列表
    
    Returns:
        排序后的文件列表（重要的在前）
    """
    def get_priority(file_path: str) -> int:
        _, priority = identify_aem_file_type(file_path)
        return priority
    
    return sorted(files, key=get_priority)


def categorize_aem_files(files: List[str]) -> Dict[str, List[str]]:
    """
    将 AEM 文件按类型分类
    
    Returns:
        按类型分组的文件字典
    """
    categorized = {
        'htl': [],
        'dialog': [],
        'js': [],
        'java': [],
        'css': [],
        'config': [],
        'other': []
    }
    
    for file_path in files:
        file_type, _ = identify_aem_file_type(file_path)
        if file_type in categorized:
            categorized[file_type].append(file_path)
        else:
            categorized['other'].append(file_path)
    
    return categorized


def extract_htl_properties(htl_content: str) -> Dict[str, any]:
    """
    从 HTL 模板中提取关键属性（增强版：支持更多 HTL 特性）
    
    Returns:
        提取的属性字典
    """
    import re
    
    properties = {
        'uses_models': [],
        'model_properties_used': [],  # 从 HTL 使用中提取的模型属性
        'uses_sly': False,
        'data_sly_attributes': [],  # 所有 data-sly-* 属性
        'sly_elements': [],  # sly 元素使用
        'data_sly_call': [],  # data-sly-call 使用
        'data_sly_element': [],  # data-sly-element 使用
        'data_sly_attribute': [],  # data-sly-attribute 使用
        'data_sly_repeat': [],  # data-sly-repeat 使用
        'data_sly_test': [],  # data-sly-test 使用
        'data_sly_resource': [],  # data-sly-resource 使用
        'event_handlers': [],
        'ui_elements': [],
        'i18n_usage': []  # i18n 使用
    }
    
    content_lower = htl_content.lower()
    
    # 检查 data-sly-* 使用
    if 'data-sly' in content_lower:
        properties['uses_sly'] = True
    
    # 提取所有 data-sly-* 属性
    data_sly_pattern = r'data-sly-(\w+)'
    all_data_sly = re.findall(data_sly_pattern, content_lower)
    properties['data_sly_attributes'] = list(set(all_data_sly))
    
    # 提取 data-sly-use 和模型名称
    use_pattern = r'data-sly-use(?:\.\w+)?\s*=\s*["\']([^"\']+)["\']'
    uses = re.findall(use_pattern, htl_content, re.IGNORECASE)
    properties['uses_models'] = list(set(uses))
    
    # 提取模型属性使用（如 ${button.text}, ${model.property}）
    model_prop_pattern = r'\$\{([\w.]+)\}'
    model_props = re.findall(model_prop_pattern, htl_content)
    # 过滤掉简单的变量，提取可能的模型属性
    model_properties = [prop for prop in model_props if '.' in prop]
    properties['model_properties_used'] = list(set(model_properties))
    
    # 提取 sly 元素
    sly_pattern = r'<sly[^>]*>'
    sly_elements = re.findall(sly_pattern, htl_content, re.IGNORECASE)
    if sly_elements:
        properties['sly_elements'] = [elem[:100] for elem in sly_elements]  # 限制长度
    
    # 提取 data-sly-call
    call_pattern = r'data-sly-call\s*=\s*["\']([^"\']+)["\']'
    calls = re.findall(call_pattern, htl_content, re.IGNORECASE)
    properties['data_sly_call'] = list(set(calls))
    
    # 提取 data-sly-element
    element_pattern = r'data-sly-element\s*=\s*["\']([^"\']+)["\']'
    elements = re.findall(element_pattern, htl_content, re.IGNORECASE)
    properties['data_sly_element'] = list(set(elements))
    
    # 提取 data-sly-attribute
    attr_pattern = r'data-sly-attribute(?:\.\w+)?\s*=\s*["\']([^"\']+)["\']'
    attrs = re.findall(attr_pattern, htl_content, re.IGNORECASE)
    properties['data_sly_attribute'] = list(set(attrs))
    
    # 提取 data-sly-repeat
    repeat_pattern = r'data-sly-repeat\s*=\s*["\']([^"\']+)["\']'
    repeats = re.findall(repeat_pattern, htl_content, re.IGNORECASE)
    properties['data_sly_repeat'] = list(set(repeats))
    
    # 提取 data-sly-test
    test_pattern = r'data-sly-test\s*=\s*["\']([^"\']+)["\']'
    tests = re.findall(test_pattern, htl_content, re.IGNORECASE)
    properties['data_sly_test'] = list(set(tests))
    
    # 提取 data-sly-resource
    resource_pattern = r'data-sly-resource\s*=\s*["\']([^"\']+)["\']'
    resources = re.findall(resource_pattern, htl_content, re.IGNORECASE)
    properties['data_sly_resource'] = list(set(resources))
    
    # 提取 i18n 使用（@i18n 或 data-sly-i18n）
    i18n_patterns = [
        r'@i18n',
        r'data-sly-i18n\s*=\s*["\']([^"\']+)["\']',
        r'i18n\s*\.\s*\w+'
    ]
    i18n_usage = []
    for pattern in i18n_patterns:
        matches = re.findall(pattern, htl_content, re.IGNORECASE)
        if matches:
            i18n_usage.extend(matches if isinstance(matches[0], str) else ['found'])
    properties['i18n_usage'] = list(set(i18n_usage)) if i18n_usage else []
    
    # 提取事件处理器
    event_pattern = r'on\w+\s*=\s*["\']([^"\']+)["\']'
    events = re.findall(event_pattern, content_lower)
    properties['event_handlers'] = list(set(events))
    
    # 识别 UI 元素
    ui_elements = []
    if '<button' in content_lower:
        ui_elements.append('button')
    if '<input' in content_lower or '<textarea' in content_lower:
        ui_elements.append('form')
    if '<dialog' in content_lower:
        ui_elements.append('dialog')
    if 'class=' in content_lower and 'grid' in content_lower:
        ui_elements.append('grid')
    if '<img' in content_lower or '<image' in content_lower:
        ui_elements.append('image')
    if '<ul' in content_lower or '<ol' in content_lower:
        ui_elements.append('list')
    
    properties['ui_elements'] = list(set(ui_elements))
    
    return properties


def extract_dialog_properties(dialog_xml: str) -> Dict[str, any]:
    """
    从 Dialog XML 中提取属性定义
    
    Returns:
        属性定义字典
    """
    properties = {
        'fields': [],
        'field_types': {},
        'required_fields': [],
        'default_values': {},
        'tabs': []
    }
    
    content_lower = dialog_xml.lower()
    
    # 提取字段（简化处理，实际应该用 XML 解析器）
    import re
    
    # 查找字段定义
    field_pattern = r'<(\w+)\s+[^>]*name\s*=\s*["\']([^"\']+)["\']'
    fields = re.findall(field_pattern, content_lower)
    properties['fields'] = [name for _, name in fields]
    properties['field_types'] = {name: tag for tag, name in fields}
    
    # 查找必填字段
    required_pattern = r'required\s*=\s*["\']true["\']'
    # 简化处理
    
    return properties


def build_component_summary(file_analyses: List[Dict]) -> Dict[str, any]:
    """
    构建组件综合摘要
    
    Returns:
        组件摘要字典
    """
    summary = {
        'ui_structure': '',
        'props_definition': {},
        'interactions': [],
        'styling_approach': '',
        'dependencies': [],
        'key_features': []
    }
    
    for analysis in file_analyses:
        file_type = analysis.get('file_type', 'unknown')
        
        if file_type in ['htl', 'html']:
            summary['ui_structure'] = analysis.get('analysis', '')
        elif file_type == 'dialog':
            summary['props_definition'] = analysis.get('configuration', {})
        elif file_type == 'js':
            summary['interactions'].append(analysis.get('analysis', ''))
    
    # 合并依赖
    all_dependencies = []
    for analysis in file_analyses:
        deps = analysis.get('dependencies', [])
        if isinstance(deps, list):
            all_dependencies.extend(deps)
    summary['dependencies'] = list(set(all_dependencies))
    
    # 合并关键特性
    all_features = []
    for analysis in file_analyses:
        features = analysis.get('key_features', [])
        if isinstance(features, list):
            all_features.extend(features)
    summary['key_features'] = list(set(all_features))
    
    return summary
