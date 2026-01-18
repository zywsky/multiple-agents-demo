"""
BDL 组件匹配和验证工具
用于计算 AEM 功能和 BDL 组件的相关性
"""
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from tools import read_file

logger = logging.getLogger(__name__)

# AEM 到 BDL 的映射规则（基于常见模式）
AEM_BDL_MAPPING_RULES = {
    # UI 元素映射
    'button': ['Button', 'IconButton', 'Fab'],
    'text': ['Typography', 'Text'],
    'textfield': ['TextField', 'Input'],
    'textarea': ['TextField', 'Textarea'],
    'select': ['Select', 'Autocomplete', 'Dropdown'],
    'checkbox': ['Checkbox', 'FormControlLabel'],
    'radio': ['Radio', 'RadioGroup'],
    'image': ['CardMedia', 'Avatar', 'Image'],
    'list': ['List', 'ListItem'],
    'card': ['Card', 'CardContent', 'CardMedia'],
    'dialog': ['Dialog', 'Modal', 'Drawer'],
    'tabs': ['Tabs', 'Tab'],
    'accordion': ['Accordion', 'AccordionSummary', 'AccordionDetails'],
    'grid': ['Grid', 'Grid2', 'Box'],
    'container': ['Container', 'Box'],
    'navigation': ['AppBar', 'Drawer', 'Menu'],
    'table': ['Table', 'TableRow', 'TableCell'],
    
    # 功能映射
    'form': ['FormControl', 'FormGroup', 'TextField', 'Button'],
    'layout': ['Grid', 'Container', 'Box', 'Stack'],
    'media': ['CardMedia', 'Image', 'Avatar'],
}


def calculate_relevance_score(
    aem_feature: str,
    bdl_component_content: str,
    aem_context: Dict = None
) -> float:
    """
    计算 AEM 功能与 BDL 组件的相关性得分（0-1）
    
    Args:
        aem_feature: AEM 功能描述
        bdl_component_content: BDL 组件源代码
        aem_context: AEM 上下文信息
    
    Returns:
        相关性得分 (0-1)
    """
    score = 0.0
    feature_lower = aem_feature.lower()
    content_lower = bdl_component_content.lower()
    
    # 1. 关键词匹配（40%）
    feature_keywords = set(feature_lower.split())
    content_keywords = set(content_lower.split())
    
    # 移除常见停用词
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'can', 'must', 'to', 'from', 'in', 'on', 'at', 'by', 'for', 'with', 'of', 'and', 'or', 'but', 'not', 'as', 'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'}
    feature_keywords = feature_keywords - stop_words
    content_keywords = content_keywords - stop_words
    
    common_keywords = feature_keywords & content_keywords
    if feature_keywords:
        keyword_score = len(common_keywords) / len(feature_keywords)
        score += keyword_score * 0.4
    
    # 2. 功能匹配（30%）
    feature_normalized = feature_lower.replace('_', ' ').replace('-', ' ')
    for aem_pattern, bdl_names in AEM_BDL_MAPPING_RULES.items():
        if aem_pattern in feature_normalized:
            # 检查 BDL 组件是否匹配推荐列表
            for bdl_name in bdl_names:
                if bdl_name.lower() in content_lower:
                    score += 0.3
                    break
    
    # 3. API 匹配（20%）
    # 检查组件导出的 props 和接口
    if 'props' in content_lower or 'interface' in content_lower:
        # 如果有 context，检查 prop 匹配
        if aem_context and 'fields' in aem_context:
            # 简化处理：如果内容中包含相关的 API 关键词
            score += 0.2
    
    # 4. 组件类型匹配（10%）
    if 'functional component' in content_lower or 'function' in content_lower:
        score += 0.1
    
    # 限制在 0-1 范围内
    return min(score, 1.0)


def validate_component_match(
    aem_summary: Dict,
    bdl_component_path: str,
    min_relevance: float = 0.5
) -> Tuple[bool, float, str]:
    """
    验证 BDL 组件是否真的适合 AEM 组件
    
    Args:
        aem_summary: AEM 组件摘要
        bdl_component_path: BDL 组件路径
        min_relevance: 最小相关性阈值
    
    Returns:
        (is_valid, relevance_score, reason)
    """
    try:
        # 读取 BDL 组件内容
        bdl_content = read_file(bdl_component_path)
        if not bdl_content:
            return False, 0.0, "Cannot read BDL component file"
        
        # 计算相关性
        aem_features = ' '.join(aem_summary.get('key_features', []))
        if not aem_features:
            aem_features = aem_summary.get('ui_structure', '')[:500]  # 使用 UI 结构
        
        relevance = calculate_relevance_score(
            aem_features,
            bdl_content,
            aem_summary
        )
        
        # 验证
        is_valid = relevance >= min_relevance
        
        if is_valid:
            reason = f"Component matches (relevance: {relevance:.2f})"
        else:
            reason = f"Component relevance too low (relevance: {relevance:.2f} < {min_relevance})"
        
        return is_valid, relevance, reason
        
    except Exception as e:
        logger.error(f"Error validating component match: {str(e)}")
        return False, 0.0, f"Validation error: {str(e)}"


def find_best_matching_components(
    aem_summary: Dict,
    candidate_components: List[str],
    bdl_library_path: str,
    max_components: int = 5,
    min_relevance: float = 0.3
) -> List[Tuple[str, float, str]]:
    """
    从候选组件中找到最匹配的组件
    
    Args:
        aem_summary: AEM 组件摘要
        candidate_components: 候选组件路径列表
        bdl_library_path: BDL 库路径
        max_components: 最多返回的组件数
        min_relevance: 最小相关性阈值
    
    Returns:
        排序后的组件列表 [(component_path, relevance_score, reason), ...]
    """
    scored_components = []
    
    for comp_path in candidate_components:
        try:
            is_valid, relevance, reason = validate_component_match(
                aem_summary,
                comp_path,
                min_relevance=0.0  # 先不设阈值，全部评分
            )
            if relevance >= min_relevance:
                scored_components.append((comp_path, relevance, reason))
        except Exception as e:
            logger.warning(f"Error scoring component {comp_path}: {str(e)}")
            continue
    
    # 按相关性得分排序
    scored_components.sort(key=lambda x: x[1], reverse=True)
    
    # 返回前 N 个
    return scored_components[:max_components]
