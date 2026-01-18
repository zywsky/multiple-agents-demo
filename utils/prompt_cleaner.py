"""
提示词数据清洗工具
清洗发送给大语言模型的数据，移除不必要的字符、格式化代码等
"""
import re
from typing import Any, Dict, List, Optional


class PromptCleaner:
    """提示词清洗器"""
    
    # 需要移除的控制字符
    CONTROL_CHARS = [
        '\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
        '\x08', '\x0b', '\x0c', '\x0e', '\x0f', '\x10', '\x11', '\x12',
        '\x13', '\x14', '\x15', '\x16', '\x17', '\x18', '\x19', '\x1a',
        '\x1b', '\x1c', '\x1d', '\x1e', '\x1f', '\x7f'
    ]
    
    # 需要标准化的空白字符
    WHITESPACE_CHARS = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u202a', '\u202b', '\u202c', '\u202d', '\u202e']
    
    @classmethod
    def clean_text(cls, text: str, max_length: Optional[int] = None) -> str:
        """
        清洗文本内容
        
        Args:
            text: 原始文本
            max_length: 最大长度限制（None表示不限制）
        
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        # 移除控制字符
        for char in cls.CONTROL_CHARS:
            text = text.replace(char, '')
        
        # 移除零宽字符
        for char in cls.WHITESPACE_CHARS:
            text = text.replace(char, '')
        
        # 标准化换行符（统一为 \n）
        text = re.sub(r'\r\n|\r', '\n', text)
        
        # 移除多余的连续空白行（最多保留2个连续换行）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 移除行尾空白
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)
        
        # 移除开头和结尾的空白
        text = text.strip()
        
        # 长度限制
        if max_length and len(text) > max_length:
            text = text[:max_length] + "\n\n... (内容已截断)"
        
        return text
    
    @classmethod
    def clean_code_block(cls, code: str, language: Optional[str] = None) -> str:
        """
        清洗代码块
        
        Args:
            code: 代码内容
            language: 代码语言（用于验证）
        
        Returns:
            清洗后的代码
        """
        if not code:
            return ""
        
        # 移除markdown代码块标记
        code = re.sub(r'^```[\w]*\n?', '', code, flags=re.MULTILINE)
        code = re.sub(r'\n?```\s*$', '', code, flags=re.MULTILINE)
        
        # 移除代码块标记（如果存在）
        code = code.strip()
        
        # 清洗文本
        code = cls.clean_text(code)
        
        return code
    
    @classmethod
    def clean_file_content(cls, content: str, file_type: Optional[str] = None) -> str:
        """
        清洗文件内容
        
        Args:
            content: 文件内容
            file_type: 文件类型（html, js, java, css, xml等）
        
        Returns:
            清洗后的内容
        """
        if not content:
            return ""
        
        # 根据文件类型进行特殊处理
        if file_type == 'html' or file_type == 'htl':
            # HTML/HTL文件：移除注释中的敏感信息
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        elif file_type == 'java':
            # Java文件：移除注释中的敏感信息
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        
        elif file_type == 'js' or file_type == 'jsx':
            # JavaScript文件：移除注释
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        
        # 通用清洗
        content = cls.clean_text(content)
        
        return content
    
    @classmethod
    def clean_prompt_data(cls, data: Dict[str, Any], max_file_length: int = 50000) -> Dict[str, Any]:
        """
        清洗提示词数据字典
        
        Args:
            data: 包含提示词数据的字典
            max_file_length: 单个文件内容的最大长度
        
        Returns:
            清洗后的数据字典
        """
        cleaned_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # 字符串值：根据key判断类型
                if 'code' in key.lower() or 'file' in key.lower():
                    # 代码或文件内容
                    cleaned_data[key] = cls.clean_file_content(value, max_length=max_file_length)
                elif 'prompt' in key.lower() or 'message' in key.lower():
                    # 提示词或消息
                    cleaned_data[key] = cls.clean_text(value)
                else:
                    # 其他字符串
                    cleaned_data[key] = cls.clean_text(value)
            
            elif isinstance(value, list):
                # 列表：递归清洗
                cleaned_data[key] = [
                    cls.clean_prompt_data(item, max_file_length) if isinstance(item, dict)
                    else cls.clean_text(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            
            elif isinstance(value, dict):
                # 字典：递归清洗
                cleaned_data[key] = cls.clean_prompt_data(value, max_file_length)
            
            else:
                # 其他类型：直接复制
                cleaned_data[key] = value
        
        return cleaned_data
    
    @classmethod
    def truncate_long_content(cls, content: str, max_length: int = 50000, 
                             preserve_structure: bool = True) -> str:
        """
        截断过长内容，尽量保持结构
        
        Args:
            content: 原始内容
            max_length: 最大长度
            preserve_structure: 是否保持结构（如代码块、XML标签等）
        
        Returns:
            截断后的内容
        """
        if len(content) <= max_length:
            return content
        
        if preserve_structure:
            # 尝试在合理的位置截断（如函数结束、标签闭合等）
            # 查找最后一个完整的结构单元
            truncate_pos = max_length
            
            # 查找最后一个完整的函数/类/标签
            if 'function' in content[:truncate_pos] or 'class' in content[:truncate_pos]:
                # 查找最后一个完整的函数或类
                pattern = r'(function\s+\w+[^}]*\{[^}]*\})|(class\s+\w+[^}]*\{[^}]*\})'
                matches = list(re.finditer(pattern, content[:truncate_pos], re.DOTALL))
                if matches:
                    truncate_pos = matches[-1].end()
            
            elif '<' in content[:truncate_pos] and '>' in content[:truncate_pos]:
                # XML/HTML：查找最后一个完整的标签
                pattern = r'<[^>]+>.*?</[^>]+>'
                matches = list(re.finditer(pattern, content[:truncate_pos], re.DOTALL))
                if matches:
                    truncate_pos = matches[-1].end()
            
            content = content[:truncate_pos]
        else:
            content = content[:max_length]
        
        return content + "\n\n... (内容已截断，超过最大长度限制)"
    
    @classmethod
    def remove_sensitive_info(cls, text: str) -> str:
        """
        移除敏感信息（如API密钥、密码等）
        
        Args:
            text: 原始文本
        
        Returns:
            移除敏感信息后的文本
        """
        # 移除API密钥模式
        text = re.sub(r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?', 
                     'api_key="***"', text, flags=re.IGNORECASE)
        
        # 移除密码模式
        text = re.sub(r'password["\']?\s*[:=]\s*["\']?[^"\']+["\']?', 
                     'password="***"', text, flags=re.IGNORECASE)
        
        # 移除token模式
        text = re.sub(r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]{20,}["\']?', 
                     'token="***"', text, flags=re.IGNORECASE)
        
        return text


# 创建全局清洗器实例
cleaner = PromptCleaner()
