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
    
    # 检查 JSX 语法（改进的验证逻辑）
    if '<' in code and '>' in code:
        # 移除JSX注释，避免干扰
        code_without_comments = re.sub(r'\{/\*.*?\*/\}', '', code, flags=re.DOTALL)
        code_without_comments = re.sub(r'<!--.*?-->', '', code_without_comments, flags=re.DOTALL)
        
        # 提取所有标签（包括自闭合标签）
        # 匹配: <Tag>, </Tag>, <Tag/>, <Tag />
        all_tags = re.findall(r'</?(\w+)(?:\s[^>]*)?/?>', code_without_comments)
        
        # 提取开始标签（非自闭合）
        open_tags = re.findall(r'<(\w+)(?:\s[^>]*)?(?<!/)>', code_without_comments)
        # 提取结束标签
        close_tags = re.findall(r'</(\w+)>', code_without_comments)
        # 提取自闭合标签
        self_closing_tags = re.findall(r'<(\w+)(?:\s[^>]*)?/>', code_without_comments)
        
        # 统计标签（排除自闭合标签）
        tag_stack = {}
        for tag in open_tags:
            tag_stack[tag] = tag_stack.get(tag, 0) + 1
        for tag in close_tags:
            tag_stack[tag] = tag_stack.get(tag, 0) - 1
        
        # 检查不匹配的标签
        unmatched = []
        for tag, count in tag_stack.items():
            if count > 0:
                unmatched.append(f"Unclosed tag: <{tag}> (missing {count} closing tag(s))")
            elif count < 0:
                unmatched.append(f"Extra closing tag: </{tag}> ({abs(count)} extra)")
        
        if unmatched:
            errors.extend(unmatched)
        
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


def improve_code_extraction(response: str, fallback_code: str = None) -> str:
    """
    改进代码提取，处理更多边界情况
    
    Args:
        response: Agent 响应字符串
        fallback_code: 如果提取失败，使用的回退代码
    
    Returns:
        提取的代码字符串
    """
    from utils.parsers import extract_code_from_response
    import logging
    logger = logging.getLogger(__name__)
    
    # 首先尝试标准提取
    code = extract_code_from_response(response)
    
    # 如果提取失败或结果可疑，尝试其他方法
    if not code or len(code) < 50:  # 太短可能不是完整代码
        logger.debug(f"Initial extraction failed or too short ({len(code) if code else 0} chars), trying alternative methods")
        
        # 方法1: 查找import语句开始
        import_match = re.search(r'(import\s+.*?from\s+.*?;.*?)(?:export|const|function|interface)', response, re.DOTALL)
        if import_match:
            start = import_match.start()
            # 找到最后一个export default或function结束
            remaining = response[start:]
            # 查找export default或最后一个大括号
            end_patterns = [
                r'(export\s+default.*?)(?:\n\n|\n```|$)',
                r'(export\s+default.*?)(?=\n\n|\n```|$)',
            ]
            for pattern in end_patterns:
                end_match = re.search(pattern, remaining, re.DOTALL)
                if end_match:
                    code = remaining[:end_match.end()].strip()
                    break
            if not code or len(code) < 50:
                # 如果还是失败，尝试提取到文件末尾
                code = remaining.strip()
        
        # 方法2: 查找function/const声明开始
        if not code or len(code) < 50:
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
        
        # 方法3: 如果还是失败，尝试提取所有看起来像代码的内容
        if not code or len(code) < 50:
            # 查找包含import和export的内容
            code_section = re.search(
                r'(import\s+.*?from\s+.*?;.*?export\s+default.*?)(?:\n\n|\n```|$)',
                response,
                re.DOTALL
            )
            if code_section:
                code = code_section.group(1).strip()
        
        # 方法4: 如果所有方法都失败，使用回退代码
        if (not code or len(code) < 50) and fallback_code:
            logger.warning(
                f"Code extraction failed completely (extracted {len(code) if code else 0} chars), "
                f"using fallback code ({len(fallback_code)} chars)"
            )
            return fallback_code
        
        # 如果还是没有代码且没有回退，记录错误
        if not code or len(code) < 50:
            logger.error(
                f"Code extraction failed and no fallback available. "
                f"Response length: {len(response)}, Extracted: {len(code) if code else 0} chars"
            )
            # 返回至少部分响应，而不是空字符串
            if response:
                # 尝试返回响应中看起来最像代码的部分
                lines = response.split('\n')
                code_lines = [line for line in lines if any(keyword in line for keyword in ['import', 'export', 'function', 'const', 'interface', '<', '>'])]
                if code_lines:
                    code = '\n'.join(code_lines)
    
    # 清理代码（移除可能的 markdown 格式）
    code = re.sub(r'^```(?:jsx|tsx|javascript|typescript|js|ts)?\s*\n', '', code, flags=re.MULTILINE)
    code = re.sub(r'\n```\s*$', '', code, flags=re.MULTILINE)
    
    # 移除可能的JSON包装
    code = re.sub(r'^\{[^}]*"component_code"\s*:\s*"', '', code)
    code = re.sub(r'"\s*\}\s*$', '', code)
    code = re.sub(r'\\n', '\n', code)  # 转换\n转义序列
    
    result = code.strip()
    
    # 最终验证：如果结果还是太短，使用回退
    if (not result or len(result) < 50) and fallback_code:
        logger.warning(f"Final code too short ({len(result)} chars), using fallback")
        return fallback_code
    
    return result
