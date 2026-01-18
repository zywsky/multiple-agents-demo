"""
JavaScript 分析器
提取JS文件中的依赖关系、AEM API、初始化逻辑等信息
"""
import re
from typing import Dict, List, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


def extract_js_dependencies(js_content: str) -> List[Dict[str, str]]:
    """
    提取JS文件中的依赖关系
    
    Args:
        js_content: JavaScript 文件内容
    
    Returns:
        依赖列表，每个依赖包含：
        - type: 依赖类型（import, require, define, use）
        - module: 模块路径/名称
        - line: 行号（可选）
    """
    dependencies = []
    
    # ES6 import
    import_pattern = r"import\s+(?:.*\s+from\s+)?['\"]([^'\"]+)['\"]"
    for match in re.finditer(import_pattern, js_content):
        dependencies.append({
            'type': 'import',
            'module': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # CommonJS require
    require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
    for match in re.finditer(require_pattern, js_content):
        dependencies.append({
            'type': 'require',
            'module': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # AMD define
    define_pattern = r"define\(['\"]([^'\"]+)['\"]"
    for match in re.finditer(define_pattern, js_content):
        dependencies.append({
            'type': 'define',
            'module': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # AEM use (Granite/jQuery style)
    use_pattern = r"use\(\[['\"]([^'\"]+)['\"]"
    for match in re.finditer(use_pattern, js_content):
        dependencies.append({
            'type': 'use',
            'module': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    return dependencies


def extract_aem_apis(js_content: str) -> Dict[str, List[Dict[str, str]]]:
    """
    提取AEM特定的API调用
    
    Args:
        js_content: JavaScript 文件内容
    
    Returns:
        API调用字典，包含：
        - granite: Granite API调用
        - coral: Coral UI API调用
        - sling: Sling API调用
        - aem: 其他AEM API调用
    """
    apis = {
        'granite': [],
        'coral': [],
        'sling': [],
        'aem': []
    }
    
    # Granite API (Granite.author.*, Granite.*)
    granite_pattern = r'Granite\.(\w+)(?:\.(\w+))?'
    for match in re.finditer(granite_pattern, js_content):
        apis['granite'].append({
            'namespace': match.group(1),
            'method': match.group(2) if match.group(2) else None,
            'full': match.group(0),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # Coral UI API (Coral.*)
    coral_pattern = r'Coral\.(\w+)(?:\.(\w+))?'
    for match in re.finditer(coral_pattern, js_content):
        apis['coral'].append({
            'namespace': match.group(1),
            'method': match.group(2) if match.group(2) else None,
            'full': match.group(0),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # Sling API (通过JS访问)
    sling_pattern = r'(?:sling|Sling)\.(\w+)(?:\.(\w+))?'
    for match in re.finditer(sling_pattern, js_content, re.IGNORECASE):
        apis['sling'].append({
            'namespace': match.group(1),
            'method': match.group(2) if match.group(2) else None,
            'full': match.group(0),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # 其他AEM特定API
    aem_patterns = [
        r'cq\.(\w+)',  # CQ API
        r'CQ\.(\w+)',  # CQ API (大写)
        r'Granite\.author',  # Author API
    ]
    for pattern in aem_patterns:
        for match in re.finditer(pattern, js_content):
            apis['aem'].append({
                'api': match.group(0),
                'line': js_content[:match.start()].count('\n') + 1
            })
    
    return apis


def extract_initialization_logic(js_content: str) -> Dict[str, Any]:
    """
    提取JS初始化逻辑
    
    Args:
        js_content: JavaScript 文件内容
    
    Returns:
        初始化逻辑字典，包含：
        - dom_ready_handlers: DOM ready事件处理
        - init_functions: 初始化函数
        - event_listeners: 事件监听器
        - config: 配置和常量
    """
    logic = {
        'dom_ready_handlers': [],
        'init_functions': [],
        'event_listeners': [],
        'config': {}
    }
    
    # DOM ready处理
    dom_ready_patterns = [
        r"document\.addEventListener\(['\"]DOMContentLoaded['\"]",
        r'jQuery\(document\)\.ready\(',
        r'\$\(document\)\.ready\(',
        r'\$\(function\s*\(',
        r"if\s*\(document\.readyState\s*===\s*['\"]loading['\"]",
    ]
    for pattern in dom_ready_patterns:
        for match in re.finditer(pattern, js_content, re.IGNORECASE):
            # 提取后续的代码块（简化版）
            start = match.end()
            # 查找对应的函数体
            logic['dom_ready_handlers'].append({
                'type': 'DOMContentLoaded',
                'pattern': match.group(0),
                'line': js_content[:match.start()].count('\n') + 1
            })
    
    # 初始化函数（init*, initialize*, setup*）
    init_function_pattern = r'function\s+(init\w*|initialize\w*|setup\w*)\s*\('
    for match in re.finditer(init_function_pattern, js_content, re.IGNORECASE):
        logic['init_functions'].append({
            'name': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # 事件监听器
    event_listener_pattern = r"\.addEventListener\(['\"]([^'\"]+)['\"]"
    for match in re.finditer(event_listener_pattern, js_content):
        logic['event_listeners'].append({
            'event': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # 配置和常量（简化版：查找常见的配置模式）
    config_patterns = [
        r'const\s+(\w+Config)\s*=',
        r'var\s+(\w+Config)\s*=',
        r'const\s+(\w+_CONFIG)\s*=',
    ]
    for pattern in config_patterns:
        for match in re.finditer(pattern, js_content):
            logic['config'][match.group(1)] = {
                'line': js_content[:match.start()].count('\n') + 1
            }
    
    return logic


def extract_component_communication(js_content: str) -> List[Dict[str, Any]]:
    """
    提取JS中的组件间通信
    
    Args:
        js_content: JavaScript 文件内容
    
    Returns:
        通信模式列表，包含：
        - type: 通信类型（custom_event, event_bus, global_state）
        - details: 详细信息
    """
    communications = []
    
    # 自定义事件
    custom_event_pattern = r"new\s+CustomEvent\(['\"]([^'\"]+)['\"]"
    for match in re.finditer(custom_event_pattern, js_content):
        communications.append({
            'type': 'custom_event',
            'event_name': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    # 事件分发
    dispatch_pattern = r'\.dispatchEvent\('
    if re.search(dispatch_pattern, js_content):
        communications.append({
            'type': 'event_dispatch',
            'line': js_content.find('dispatchEvent')
        })
    
    # 全局状态（简化版：查找常见的全局变量模式）
    global_state_pattern = r'(?:window|global)\.(\w+State|\w+Store)'
    for match in re.finditer(global_state_pattern, js_content):
        communications.append({
            'type': 'global_state',
            'name': match.group(1),
            'line': js_content[:match.start()].count('\n') + 1
        })
    
    return communications


def analyze_javascript_file(js_file_path: str) -> Dict[str, Any]:
    """
    完整分析JavaScript文件
    
    Args:
        js_file_path: JavaScript 文件路径
    
    Returns:
        完整的分析结果，包含：
        - dependencies: 依赖关系
        - aem_apis: AEM特定API
        - initialization: 初始化逻辑
        - communication: 组件间通信
        - file_path: 文件路径
    """
    try:
        with open(js_file_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read JavaScript file {js_file_path}: {e}")
        return {}
    
    result = {
        'file_path': js_file_path,
        'dependencies': extract_js_dependencies(js_content),
        'aem_apis': extract_aem_apis(js_content),
        'initialization': extract_initialization_logic(js_content),
        'communication': extract_component_communication(js_content),
    }
    
    return result


def build_js_analysis_summary(js_analyses: List[Dict[str, Any]]) -> str:
    """
    构建JS分析摘要（用于传递给代码生成 Agent）
    
    Args:
        js_analyses: JS文件分析结果列表
    
    Returns:
        格式化的摘要字符串
    """
    if not js_analyses:
        return ""
    
    summary_parts = []
    summary_parts.append("=== JAVASCRIPT ANALYSIS (REACT CONVERSION) - CRITICAL ===\n")
    
    for analysis in js_analyses:
        file_path = analysis.get('file_path', 'Unknown')
        dependencies = analysis.get('dependencies', [])
        aem_apis = analysis.get('aem_apis', {})
        initialization = analysis.get('initialization', {})
        communication = analysis.get('communication', [])
        
        summary_parts.append(f"\n--- File: {file_path} ---")
        
        # 依赖关系
        if dependencies:
            summary_parts.append("\nDependencies:")
            for dep in dependencies:
                dep_type = dep.get('type', 'unknown')
                module = dep.get('module', '')
                summary_parts.append(f"  - {dep_type}: {module}")
            summary_parts.append("  → Convert to React imports or npm packages")
        
        # AEM特定API
        has_aem_apis = any(aem_apis.values())
        if has_aem_apis:
            summary_parts.append("\nAEM-Specific APIs (NEED REPLACEMENT):")
            for api_type, api_list in aem_apis.items():
                if api_list:
                    summary_parts.append(f"  - {api_type.upper()}:")
                    for api in api_list[:5]:  # 限制显示数量
                        api_name = api.get('full', api.get('api', ''))
                        summary_parts.append(f"    * {api_name}")
            summary_parts.append("  → Replace with BDL components or React equivalents")
        
        # 初始化逻辑
        init_logic = initialization
        if init_logic.get('dom_ready_handlers') or init_logic.get('init_functions'):
            summary_parts.append("\nInitialization Logic:")
            if init_logic.get('dom_ready_handlers'):
                summary_parts.append(f"  - DOM Ready Handlers: {len(init_logic['dom_ready_handlers'])}")
                summary_parts.append("    → Convert to React useEffect(() => {...}, [])")
            if init_logic.get('init_functions'):
                summary_parts.append(f"  - Init Functions: {', '.join([f['name'] for f in init_logic['init_functions']])}")
                summary_parts.append("    → Convert to React custom hooks or useEffect")
            if init_logic.get('event_listeners'):
                summary_parts.append(f"  - Event Listeners: {len(init_logic['event_listeners'])} events")
                summary_parts.append("    → Convert to React event handlers (onClick, onChange, etc.)")
        
        # 组件间通信
        if communication:
            summary_parts.append("\nComponent Communication:")
            for comm in communication:
                comm_type = comm.get('type', 'unknown')
                summary_parts.append(f"  - {comm_type}")
            summary_parts.append("  → Convert to React Context, props, or state management")
    
    summary_parts.append("\n=== CONVERSION NOTES ===\n")
    summary_parts.append("1. Convert DOM ready handlers to React useEffect hooks")
    summary_parts.append("2. Convert event listeners to React event handlers")
    summary_parts.append("3. Replace AEM-specific APIs with BDL components or React equivalents")
    summary_parts.append("4. Convert JS dependencies to React imports or npm packages")
    summary_parts.append("5. Convert component communication to React patterns (Context, props, state)")
    
    return "\n".join(summary_parts)
