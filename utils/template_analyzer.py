"""
AEM 模板片段分析器
分析 data-sly-call 引用，收集和分析模板片段文件
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


def extract_template_calls(htl_content: str) -> List[Dict[str, Any]]:
    """
    从 HTL 内容中提取所有 data-sly-call 引用
    
    Args:
        htl_content: HTL 模板内容
    
    Returns:
        模板调用列表，每个包含：
        - template_path: 模板路径（如 "template.placeholder", "template.styles"）
        - parameters: 参数字典（如 {"isEmpty": "!button.text", "path": "button.css"}）
        - call_expression: 完整的调用表达式
    """
    template_calls = []
    
    # 匹配 data-sly-call 的各种格式
    # 1. data-sly-call="${template.placeholder @ isEmpty=!button.text}"
    # 2. data-sly-call="${template.styles @ path='button.css'}"
    # 3. data-sly-call="${template.scripts @ path='button.js'}"
    # 4. data-sly-call="${template.placeholder @ isEmpty=!button.text, path='test'}"
    
    pattern = r'data-sly-call\s*=\s*["\']\$\{([^}]+)\}["\']'
    matches = re.finditer(pattern, htl_content, re.IGNORECASE)
    
    for match in matches:
        call_expression = match.group(1).strip()
        
        # 解析模板路径和参数
        # 格式: template.placeholder @ isEmpty=!button.text, path='test'
        parts = call_expression.split('@', 1)
        template_path = parts[0].strip()
        
        parameters = {}
        if len(parts) > 1:
            # 解析参数（支持 key=value, key='value', key="value"）
            params_str = parts[1].strip()
            # 匹配 key=value 对
            param_pattern = r'(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)'
            param_matches = re.finditer(param_pattern, params_str)
            for param_match in param_matches:
                key = param_match.group(1).strip()
                value = param_match.group(2).strip().strip("'\"")
                parameters[key] = value
        
        template_calls.append({
            'template_path': template_path,
            'parameters': parameters,
            'call_expression': call_expression,
            'full_match': match.group(0)
        })
    
    return template_calls


def resolve_template_path(template_path: str, aem_repo_path: str) -> Optional[str]:
    """
    将模板路径解析为文件系统路径
    
    Args:
        template_path: 模板路径（如 "template.placeholder", "core/wcm/components/commons/v1/templates"）
        aem_repo_path: AEM repository 根路径
    
    Returns:
        模板文件路径，如果不存在则返回 None
    """
    # 处理常见的模板路径格式
    # 1. template.placeholder -> 需要找到 templates.html 文件
    # 2. core/wcm/components/commons/v1/templates -> 直接路径
    
    # 如果是点分隔的路径，转换为路径分隔符
    if '.' in template_path and '/' not in template_path:
        # template.placeholder -> template/placeholder 或 templates.html
        if template_path.startswith('template.'):
            # 可能是 core/wcm/components/commons/v1/templates.html
            possible_paths = [
                f"core/wcm/components/commons/v1/templates.html",
                f"libs/core/wcm/components/commons/v1/templates.html",
                f"apps/core/wcm/components/commons/v1/templates.html",
            ]
        else:
            template_path = template_path.replace('.', '/')
            possible_paths = [template_path]
    else:
        # 已经是路径格式
        if not template_path.endswith('.html'):
            template_path = f"{template_path}.html"
        possible_paths = [template_path]
    
    # 尝试查找模板文件
    for path in possible_paths:
        # 移除前导斜杠
        path = path.lstrip('/')
        
        # 构建完整路径
        full_path = Path(aem_repo_path) / path
        
        # 检查文件是否存在
        if full_path.exists() and full_path.is_file():
            return str(full_path.resolve())
        
        # 也尝试在 libs 和 apps 目录下查找
        for base_dir in ['libs', 'apps']:
            alt_path = Path(aem_repo_path) / base_dir / path
            if alt_path.exists() and alt_path.is_file():
                return str(alt_path.resolve())
    
    return None


def find_template_files(template_calls: List[Dict[str, Any]], aem_repo_path: str) -> Dict[str, Optional[str]]:
    """
    查找所有模板调用对应的文件
    
    Args:
        template_calls: 模板调用列表
        aem_repo_path: AEM repository 根路径
    
    Returns:
        模板路径到文件路径的映射
    """
    template_files = {}
    
    for call in template_calls:
        template_path = call['template_path']
        
        # 如果已经解析过，跳过
        if template_path in template_files:
            continue
        
        # 解析模板文件路径
        file_path = resolve_template_path(template_path, aem_repo_path)
        template_files[template_path] = file_path
        
        if file_path:
            logger.debug(f"Found template file for {template_path}: {file_path}")
        else:
            logger.warning(f"Could not find template file for {template_path}")
    
    return template_files


def analyze_template_file(template_file_path: str) -> Dict[str, Any]:
    """
    分析模板片段文件
    
    Args:
        template_file_path: 模板文件路径
    
    Returns:
        模板分析结果，包含：
        - file_path: 文件路径
        - template_functions: 定义的模板函数列表
        - parameters: 函数参数
        - content: 文件内容预览
    """
    try:
        with open(template_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read template file {template_file_path}: {e}")
        return {
            'file_path': template_file_path,
            'error': str(e)
        }
    
    result = {
        'file_path': template_file_path,
        'template_functions': [],
        'content_preview': content[:1000]  # 前1000字符
    }
    
    # 提取模板函数定义
    # AEM 模板函数通常使用 data-sly-template 定义
    # 例如: <template data-sly-template.functionName="${@ param1, param2}">
    template_function_pattern = r'data-sly-template\.(\w+)\s*=\s*["\']([^"\']*)["\']'
    function_matches = re.finditer(template_function_pattern, content, re.IGNORECASE)
    
    for match in function_matches:
        function_name = match.group(1)
        params_str = match.group(2) if match.group(2) else ''
        
        # 解析参数
        params = []
        if params_str:
            # 格式: @ param1, param2, param3
            param_list = [p.strip() for p in params_str.replace('@', '').split(',') if p.strip()]
            params = param_list
        
        result['template_functions'].append({
            'name': function_name,
            'parameters': params
        })
    
    return result


def build_template_summary(template_calls: List[Dict[str, Any]], 
                         template_files: Dict[str, Optional[str]],
                         template_analyses: Dict[str, Dict[str, Any]]) -> str:
    """
    构建模板片段摘要（用于传递给代码生成 Agent）
    
    Args:
        template_calls: 模板调用列表
        template_files: 模板路径到文件路径的映射
        template_analyses: 模板文件分析结果
    
    Returns:
        格式化的摘要字符串
    """
    if not template_calls:
        return ""
    
    summary_parts = []
    summary_parts.append("=== TEMPLATE SNIPPETS (data-sly-call) - IMPORTANT ===\n")
    summary_parts.append("The component uses AEM template snippets. These need special handling in React:\n\n")
    
    for call in template_calls:
        template_path = call['template_path']
        parameters = call.get('parameters', {})
        file_path = template_files.get(template_path)
        
        summary_parts.append(f"--- Template Call: {template_path} ---")
        summary_parts.append(f"Parameters: {parameters}")
        
        if file_path:
            summary_parts.append(f"Template File: {file_path}")
            
            # 添加模板分析结果
            analysis = template_analyses.get(file_path, {})
            if analysis.get('template_functions'):
                summary_parts.append("Template Functions:")
                for func in analysis['template_functions']:
                    func_name = func.get('name', '')
                    func_params = func.get('parameters', [])
                    summary_parts.append(f"  - {func_name}({', '.join(func_params)})")
        else:
            summary_parts.append("Template File: Not found (may be in AEM core/libs)")
        
        summary_parts.append("")
    
    summary_parts.append("=== CONVERSION NOTES ===\n")
    summary_parts.append("1. template.placeholder: AEM-specific for edit mode - Remove in React")
    summary_parts.append("2. template.styles: AEM-specific style loading - Convert to React import or CSS-in-JS")
    summary_parts.append("3. template.scripts: AEM-specific script loading - Convert to React import")
    summary_parts.append("4. Other template calls: Convert to React functions or components based on functionality")
    summary_parts.append("5. If template file is found, analyze its structure and convert accordingly")
    
    return "\n".join(summary_parts)
