"""
代码验证工具
用于验证生成的 React 组件代码的基本质量
"""
import re
from typing import Tuple, List, Dict, Any, Optional


def validate_react_code(code: str) -> Tuple[bool, List[str], List[str]]:
    """
    验证 React 代码的基本质量
    
    Args:
        code: React 代码字符串
    
    Returns:
        (is_valid, warnings, errors): 是否有效、警告列表、错误列表
    """
    errors = []
    warnings = []
    
    if not code or not code.strip():
        errors.append("Code is empty")
        return False, warnings, errors
    
    # 检查基本的 React 组件结构
    if not re.search(r'(?:function|const|export\s+(?:default\s+)?function)\s+\w+\s*[=\(]', code):
        warnings.append("May not be a valid React component (no function/const declaration found)")
    
    # 检查 JSX 语法
    if '<' in code and '>' in code:
        # 检查括号匹配
        open_tags = code.count('<')
        close_tags = code.count('>')
        if open_tags != close_tags:
            errors.append(f"Unmatched JSX tags: {open_tags} open vs {close_tags} close")
        
        # 检查基本的 JSX 结构
        if not re.search(r'<[A-Z]\w+', code) and not re.search(r'<[a-z]\w+', code):
            warnings.append("No JSX elements found - may not be valid React component")
    else:
        warnings.append("No JSX syntax found - may not be a React component")
    
    # 检查导入语句
    if 'import' not in code:
        warnings.append("No import statements found - React may not be imported")
    
    # 检查返回语句（函数组件应该返回 JSX）
    if 'return' in code:
        if not re.search(r'return\s*\(?\s*<', code):
            warnings.append("Component may not return JSX (check return statement)")
    
    # 检查常见的语法错误
    # 检查括号匹配
    open_parens = code.count('(')
    close_parens = code.count(')')
    if open_parens != close_parens:
        errors.append(f"Unmatched parentheses: {open_parens} open vs {close_parens} close")
    
    open_braces = code.count('{')
    close_braces = code.count('}')
    if open_braces != close_braces:
        errors.append(f"Unmatched braces: {open_braces} open vs {close_braces} close")
    
    open_brackets = code.count('[')
    close_brackets = code.count(']')
    if open_brackets != close_brackets:
        errors.append(f"Unmatched brackets: {open_brackets} open vs {close_brackets} close")
    
    # 检查常见问题
    if 'dangerouslySetInnerHTML' in code and '__html' not in code:
        warnings.append("dangerouslySetInnerHTML used but __html property may be missing")
    
    # 检查是否可能是代码块而不是纯代码
    if code.strip().startswith('```'):
        warnings.append("Code appears to be in markdown code block - may need extraction")
    
    is_valid = len(errors) == 0
    
    return is_valid, warnings, errors


def extract_and_validate_code(response: str) -> Tuple[str, bool, List[str], List[str]]:
    """
    从响应中提取代码并验证
    
    Args:
        response: Agent 响应字符串
    
    Returns:
        (code, is_valid, warnings, errors): 提取的代码、是否有效、警告、错误
    """
    from utils.parsers import extract_code_from_response
    
    # 提取代码
    code = extract_code_from_response(response)
    
    # 验证代码
    is_valid, warnings, errors = validate_react_code(code)
    
    return code, is_valid, warnings, errors


def improve_code_extraction(response: str) -> str:
    """
    改进代码提取，处理更多边界情况
    
    Args:
        response: Agent 响应字符串
    
    Returns:
        提取的代码字符串
    """
    from utils.parsers import extract_code_from_response
    
    # 首先尝试标准提取
    code = extract_code_from_response(response)
    
    # 如果提取失败或结果可疑，尝试其他方法
    if not code or len(code) < 50:  # 太短可能不是完整代码
        # 尝试查找 function/const 声明开始
        patterns = [
            r'(?:function|const|export\s+(?:default\s+)?function)\s+\w+.*?',
            r'(?:import\s+.*?from\s+.*?;\s*)*.*?(?:function|const|export)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                # 从匹配位置提取到末尾（或下一个```）
                start = match.start()
                remaining = response[start:]
                # 找到代码块的结束
                code_end = remaining.find('```')
                if code_end > 0:
                    code = remaining[:code_end].strip()
                else:
                    code = remaining.strip()
                break
    
    # 清理代码（移除可能的 markdown 格式）
    code = re.sub(r'^```(?:jsx|tsx|javascript|typescript|js|ts)?\s*\n', '', code)
    code = re.sub(r'\n```\s*$', '', code)
    
    return code.strip()
