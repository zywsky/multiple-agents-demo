"""
AEM i18n 国际化分析器
收集和分析 i18n 字典文件，提取翻译键值对
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import logging

logger = logging.getLogger(__name__)


def find_i18n_dictionary_files(component_path: str, aem_repo_path: str) -> List[str]:
    """
    查找组件相关的 i18n 字典文件
    
    Args:
        component_path: 组件路径
        aem_repo_path: AEM repository 根路径
    
    Returns:
        i18n 字典文件路径列表
    """
    i18n_files = []
    
    # AEM i18n 字典文件通常位于：
    # 1. 组件目录下的 i18n/ 目录
    # 2. 组件目录下的 *.properties 文件
    # 3. 全局 i18n 目录（如 /libs/cq/i18n/）
    
    component_dir = Path(component_path)
    
    # 1. 查找组件目录下的 i18n 目录
    i18n_dir = component_dir / 'i18n'
    if i18n_dir.exists() and i18n_dir.is_dir():
        for prop_file in i18n_dir.glob('*.properties'):
            i18n_files.append(str(prop_file))
    
    # 2. 查找组件目录下的 .properties 文件
    for prop_file in component_dir.glob('*.properties'):
        i18n_files.append(str(prop_file))
    
    # 3. 查找组件目录下的 i18n 子目录中的文件
    for subdir in component_dir.rglob('i18n'):
        if subdir.is_dir():
            for prop_file in subdir.glob('*.properties'):
                i18n_files.append(str(prop_file))
    
    # 4. 查找全局 i18n 目录（可选，通常不需要）
    # global_i18n_dirs = [
    #     Path(aem_repo_path) / 'libs' / 'cq' / 'i18n',
    #     Path(aem_repo_path) / 'apps' / 'cq' / 'i18n',
    # ]
    # for i18n_dir in global_i18n_dirs:
    #     if i18n_dir.exists():
    #         for prop_file in i18n_dir.glob('*.properties'):
    #             i18n_files.append(str(prop_file))
    
    return sorted(list(set(i18n_files)))


def parse_properties_file(properties_file_path: str) -> Dict[str, str]:
    """
    解析 .properties 文件，提取键值对
    
    Args:
        properties_file_path: .properties 文件路径
    
    Returns:
        翻译键值对字典
    """
    translations = {}
    
    try:
        with open(properties_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read properties file {properties_file_path}: {e}")
        return translations
    
    # 解析 .properties 文件
    # 格式: key=value
    # 支持多行值（使用 \ 续行）
    # 支持注释（# 或 ! 开头）
    
    lines = content.split('\n')
    current_key = None
    current_value = []
    
    for line in lines:
        # 移除行尾空白
        line = line.rstrip()
        
        # 跳过空行
        if not line.strip():
            continue
        
        # 跳过注释
        if line.strip().startswith('#') or line.strip().startswith('!'):
            continue
        
        # 检查是否是续行（以 \ 结尾）
        if line.endswith('\\'):
            # 续行
            line = line[:-1].rstrip()
            if current_key:
                current_value.append(line)
            continue
        
        # 检查是否是键值对
        if '=' in line:
            # 保存之前的键值对
            if current_key and current_value:
                translations[current_key] = ' '.join(current_value)
            
            # 解析新的键值对
            parts = line.split('=', 1)
            if len(parts) == 2:
                current_key = parts[0].strip()
                current_value = [parts[1].strip()]
            else:
                current_key = None
                current_value = []
        elif current_key:
            # 可能是值的一部分（多行值）
            current_value.append(line)
    
    # 保存最后一个键值对
    if current_key and current_value:
        translations[current_key] = ' '.join(current_value)
    
    return translations


def extract_i18n_keys_from_htl(htl_content: str) -> Set[str]:
    """
    从 HTL 内容中提取所有 i18n 翻译键
    
    Args:
        htl_content: HTL 模板内容
    
    Returns:
        翻译键集合
    """
    i18n_keys = set()
    
    # 匹配 i18n 使用的各种格式
    # 1. ${'key' @ i18n}
    # 2. ${properties.key @ i18n}
    # 3. data-sly-i18n="key"
    
    patterns = [
        # ${'key' @ i18n}
        r"\$\{['\"]([^'\"]+)['\"]\s*@\s*i18n\}",
        # ${properties.key @ i18n}
        r"\$\{([\w.]+)\s*@\s*i18n\}",
        # data-sly-i18n="key"
        r'data-sly-i18n\s*=\s*["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, htl_content, re.IGNORECASE)
        for match in matches:
            key = match.group(1).strip()
            if key:
                i18n_keys.add(key)
    
    return i18n_keys


def build_i18n_summary(i18n_keys: Set[str], 
                       dictionary_files: List[str],
                       translations: Dict[str, Dict[str, str]]) -> str:
    """
    构建 i18n 摘要（用于传递给代码生成 Agent）
    
    Args:
        i18n_keys: HTL 中使用的翻译键集合
        dictionary_files: i18n 字典文件路径列表
        translations: 每个字典文件的翻译内容
    
    Returns:
        格式化的摘要字符串
    """
    if not i18n_keys and not dictionary_files:
        return ""
    
    summary_parts = []
    summary_parts.append("=== i18n INTERNATIONALIZATION - IMPORTANT ===\n")
    
    if i18n_keys:
        summary_parts.append(f"Translation Keys Used in HTL ({len(i18n_keys)} keys):")
        for key in sorted(i18n_keys):
            summary_parts.append(f"  - {key}")
        summary_parts.append("")
    
    if dictionary_files:
        summary_parts.append(f"i18n Dictionary Files Found ({len(dictionary_files)} files):")
        for dict_file in dictionary_files:
            summary_parts.append(f"  - {dict_file}")
            
            # 显示该文件的翻译内容
            file_translations = translations.get(dict_file, {})
            if file_translations:
                summary_parts.append(f"    Translations ({len(file_translations)} keys):")
                for key, value in list(file_translations.items())[:10]:  # 前10个
                    summary_parts.append(f"      {key} = {value}")
                if len(file_translations) > 10:
                    summary_parts.append(f"      ... and {len(file_translations) - 10} more")
        summary_parts.append("")
    else:
        summary_parts.append("⚠️ No i18n dictionary files found in component directory")
        summary_parts.append("   Translation keys may be in global i18n files or need manual mapping")
        summary_parts.append("")
    
    summary_parts.append("=== CONVERSION NOTES ===\n")
    summary_parts.append("1. Convert AEM i18n to React i18n library (e.g., react-i18next)")
    summary_parts.append("2. Map translation keys to React i18n keys")
    summary_parts.append("3. Use useTranslation hook or similar in React component")
    summary_parts.append("4. Example: ${'Button Text' @ i18n} → t('Button Text') or t('button.text')")
    summary_parts.append("5. If dictionary files are found, use them to create React i18n translation files")
    
    return "\n".join(summary_parts)
