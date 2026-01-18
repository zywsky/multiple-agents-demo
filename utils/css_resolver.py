"""
AEM CSS 样式解析器
用于查找组件使用的 CSS class 对应的样式定义

AEM 样式管理机制：
1. 组件本地 CSS 文件（组件目录下）
2. ClientLibs (Client Libraries) - 通过 category 和 embed 组织
3. 全局样式库
"""
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import logging

logger = logging.getLogger(__name__)


def extract_css_classes_from_htl(htl_content: str) -> Set[str]:
    """
    从 HTL 内容中提取所有使用的 CSS class
    
    Args:
        htl_content: HTL 模板内容
    
    Returns:
        CSS class 集合
    """
    classes = set()
    
    # 匹配 class 属性（支持多种格式）
    patterns = [
        r'class\s*=\s*["\']([^"\']+)["\']',  # class="example-button"
        r'class\s*=\s*\{([^}]+)\}',  # class="${variable}"
        r'data-sly-attribute\.class\s*=\s*["\']([^"\']+)["\']',  # data-sly-attribute.class
        r'className\s*=\s*["\']([^"\']+)["\']',  # className (React style, sometimes used)
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, htl_content, re.IGNORECASE)
        for match in matches:
            # 处理多个 class（空格分隔）
            class_names = match.strip().split()
            for class_name in class_names:
                # 清理 class 名（移除可能的变量语法）
                class_name = class_name.strip().strip('${}').strip('"\'')
                if class_name and not class_name.startswith('$'):
                    classes.add(class_name)
    
    return classes


def extract_inline_styles_from_htl(htl_content: str) -> Dict[str, str]:
    """
    从 HTL 内容中提取内联样式
    
    Args:
        htl_content: HTL 模板内容
    
    Returns:
        {element_identifier: style_string} 字典
    """
    inline_styles = {}
    
    # 匹配 style 属性
    patterns = [
        r'style\s*=\s*["\']([^"\']+)["\']',  # style="color: red;"
        r'data-sly-attribute\.style\s*=\s*["\']([^"\']+)["\']',  # data-sly-attribute.style
        r'style\s*=\s*\{([^}]+)\}',  # style="${variable}"
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, htl_content, re.IGNORECASE)
        for match in matches:
            style_content = match.group(1).strip().strip('${}').strip('"\'')
            if style_content and not style_content.startswith('$'):
                # 尝试找到对应的元素标识（class或id）
                context_start = max(0, match.start() - 200)
                context = htl_content[context_start:match.start()]
                # 查找最近的class或id
                class_match = re.search(r'class\s*=\s*["\']([^"\']+)["\']', context)
                id_match = re.search(r'id\s*=\s*["\']([^"\']+)["\']', context)
                identifier = None
                if class_match:
                    identifier = class_match.group(1).split()[0]  # 取第一个class
                elif id_match:
                    identifier = id_match.group(1)
                else:
                    identifier = f"inline-style-{len(inline_styles)}"
                
                inline_styles[identifier] = style_content
    
    return inline_styles


def extract_css_from_javascript(js_content: str) -> Dict[str, str]:
    """
    从 JavaScript 文件中提取 CSS 相关代码
    
    提取内容：
    1. CSS-in-JS 样式（style.textContent, style.innerHTML）
    2. 动态添加的 CSS 类
    3. 样式操作（element.style.*）
    
    Args:
        js_content: JavaScript 文件内容
    
    Returns:
        {type: content} 字典，包含提取的CSS信息
    """
    css_info = {
        'css_in_js': [],
        'dynamic_classes': [],
        'style_operations': []
    }
    
    # 提取 CSS-in-JS
    css_in_js_patterns = [
        r'style\.textContent\s*=\s*["\']([^"\']+)["\']',
        r'style\.innerHTML\s*=\s*["\']([^"\']+)["\']',
        r'\.textContent\s*=\s*["\']([^"\']*\{[^}]*\}[^"\']*)["\']',  # CSS规则
    ]
    
    for pattern in css_in_js_patterns:
        matches = re.finditer(pattern, js_content, re.IGNORECASE | re.DOTALL)
        for match in matches:
            css_content = match.group(1)
            if css_content and ('{' in css_content or ':' in css_content):
                css_info['css_in_js'].append(css_content)
    
    # 提取动态添加的CSS类
    class_patterns = [
        r'classList\.add\(["\']([^"\']+)["\']\)',
        r'className\s*\+=\s*["\']\s*([^"\']+)["\']',
        r'\.class\s*=\s*["\']([^"\']+)["\']',
    ]
    
    for pattern in class_patterns:
        matches = re.findall(pattern, js_content, re.IGNORECASE)
        for match in matches:
            if match.strip():
                css_info['dynamic_classes'].append(match.strip())
    
    # 提取样式操作
    style_patterns = [
        r'\.style\.(\w+)\s*=\s*["\']?([^;"\']+)["\']?',
        r'setProperty\(["\']([^"\']+)["\']\s*,\s*["\']?([^"\']+)["\']?\)',
    ]
    
    for pattern in style_patterns:
        matches = re.finditer(pattern, js_content, re.IGNORECASE)
        for match in matches:
            css_info['style_operations'].append(match.group(0))
    
    return css_info


def find_component_css_files(component_path: str) -> List[str]:
    """
    在组件目录下和相似路径中查找 CSS 文件
    
    搜索策略：
    1. 组件目录下直接查找
    2. 组件 styles/clientlibs 子目录
    3. 相似路径中查找（styles 目录、父级目录等）
    
    Args:
        component_path: 组件路径
    
    Returns:
        CSS 文件路径列表
    """
    css_files = []
    component_dir = Path(component_path)
    
    if not component_dir.exists():
        return css_files
    
    # 策略 1: 组件目录下直接查找
    for pattern in ['*.css', '*.less', '*.scss']:
        css_files.extend(component_dir.glob(pattern))
        # 也在子目录中查找（但限制深度）
        for css_file in component_dir.rglob(pattern):
            # 限制在组件目录下的 2 层深度内
            relative = css_file.relative_to(component_dir)
            if len(relative.parts) <= 2:
                css_files.append(css_file)
    
    # 策略 2: 使用路径查找器在相似路径中查找
    try:
        from utils.css_path_finder import (
            find_css_in_similar_paths,
            find_css_by_component_name,
            infer_css_path_from_component,
            find_css_in_dedicated_styles_directory
        )
        
        # 在相似路径中查找
        similar_css = find_css_in_similar_paths(component_path)
        css_files.extend(similar_css)
        
        # 根据组件名称查找
        component_name = component_dir.name
        parent_path = str(component_dir.parent)
        name_based_css = find_css_by_component_name(parent_path, component_name, max_depth=5)
        css_files.extend(name_based_css)
        
        # 推断可能的 CSS 路径
        inferred_css = infer_css_path_from_component(component_path)
        css_files.extend(inferred_css)
        
        # 在专门的CSS/样式目录中查找（保持相同层级结构）
        # 尝试从组件路径推断AEM repo路径
        aem_repo_path = None
        # 向上查找，找到可能的repo根目录（包含components目录的父目录）
        current_dir = component_dir
        for _ in range(10):  # 最多向上10层
            if (current_dir / 'components').exists() or (current_dir / 'styles').exists() or (current_dir / 'css').exists():
                aem_repo_path = str(current_dir)
                break
            if current_dir == current_dir.parent:
                break
            current_dir = current_dir.parent
        
        dedicated_css = find_css_in_dedicated_styles_directory(component_path, aem_repo_path)
        css_files.extend(dedicated_css)
        if dedicated_css:
            logger.info(f"Found {len(dedicated_css)} CSS files in dedicated styles/css directories")
        
    except ImportError as e:
        logger.warning(f"Could not import css_path_finder: {e}")
    
    # 去重并转换为字符串
    return sorted(list(set(str(f) for f in css_files)))


def parse_clientlib_config(config_path: str) -> Dict[str, any]:
    """
    解析 ClientLibs 配置文件 (.content.xml)
    
    Args:
        config_path: .content.xml 文件路径
    
    Returns:
        ClientLibs 配置信息
    """
    config = {
        'categories': [],
        'embeds': [],
        'dependencies': [],
        'allowProxy': False,
        'css_paths': [],
        'js_paths': []
    }
    
    try:
        tree = ET.parse(config_path)
        root = tree.getroot()
        
        # AEM ClientLibs namespace
        ns = {
            'jcr': 'http://www.jcp.org/jcr/1.0',
            'cq': 'http://www.day.com/jcr/cq/1.0',
            'sling': 'http://sling.apache.org/jcr/sling/1.0'
        }
        
        # 提取 categories
        categories_attr = root.get('{http://www.jcp.org/jcr/1.0}categories') or root.get('categories')
        if categories_attr:
            # categories 可能是字符串（单个）或数组
            if isinstance(categories_attr, str):
                # 处理方括号格式：[category1,category2] 或 "category1,category2"
                categories_str = categories_attr.strip().strip('[]').strip('"\'')
                config['categories'] = [cat.strip() for cat in categories_str.split(',') if cat.strip()]
            else:
                # 如果是列表，清理每个元素
                config['categories'] = [str(cat).strip().strip('[]').strip('"\'') for cat in categories_attr if str(cat).strip()]
        
        # 提取 embeds（嵌入的其他 ClientLibs）
        embeds_attr = root.get('{http://www.day.com/jcr/cq/1.0}embed') or root.get('embed')
        if embeds_attr:
            if isinstance(embeds_attr, str):
                config['embeds'] = [e.strip() for e in embeds_attr.split(',')]
            else:
                config['embeds'] = embeds_attr
        
        # 提取 dependencies
        dependencies_attr = root.get('{http://www.day.com/jcr/cq/1.0}dependencies') or root.get('dependencies')
        if dependencies_attr:
            if isinstance(dependencies_attr, str):
                config['dependencies'] = [d.strip() for d in dependencies_attr.split(',')]
            else:
                config['dependencies'] = dependencies_attr
        
        # 查找 CSS 和 JS 文件（在 ClientLibs 目录中）
        clientlib_dir = Path(config_path).parent
        for css_file in clientlib_dir.glob('*.css'):
            config['css_paths'].append(str(css_file))
        for js_file in clientlib_dir.glob('*.js'):
            config['js_paths'].append(str(js_file))
        
        # 查找子目录中的文件
        for css_file in clientlib_dir.rglob('*.css'):
            if str(css_file) not in config['css_paths']:
                config['css_paths'].append(str(css_file))
    
    except ET.ParseError as e:
        logger.warning(f"Failed to parse ClientLibs config {config_path}: {e}")
    except Exception as e:
        logger.warning(f"Error reading ClientLibs config {config_path}: {e}")
    
    return config


def find_clientlib_by_category(category: str, aem_repo_path: str) -> List[str]:
    """
    根据 category 查找 ClientLibs 目录
    
    Args:
        category: ClientLibs category 名称
        aem_repo_path: AEM repository 根路径
    
    Returns:
        ClientLibs 目录路径列表
    """
    clientlib_dirs = []
    repo_path = Path(aem_repo_path)
    
    # AEM ClientLibs 通常在这些位置：
    # 1. /apps/<project>/clientlibs/<category>
    # 2. /etc/clientlibs/<category>
    # 3. /libs/<project>/clientlibs/<category>
    
    # 清理category（移除可能的方括号和空格）
    category = category.strip().strip('[]').strip('"\'')
    
    # AEM ClientLibs 可能在这些位置：
    # 1. /apps/<project>/clientlibs/<任意目录名>（通过.content.xml中的category匹配）
    # 2. /etc/clientlibs/<任意目录名>
    # 3. /libs/<project>/clientlibs/<任意目录名>
    # 4. 组件目录下的 clientlibs/<任意目录名>
    # 5. 任何位置的 clientlibs/<任意目录名>
    
    # 注意：category存储在.content.xml中，而不是目录名
    # 所以我们需要搜索所有clientlibs目录，然后检查其.content.xml中的category
    
    search_patterns = [
        '**/clientlibs/**/.content.xml',  # 查找所有clientlibs目录下的.content.xml
        '**/clientlibs/.content.xml',  # 直接是clientlibs目录的情况
    ]
    
    for pattern in search_patterns:
        for config_file in repo_path.glob(pattern):
            try:
                config = parse_clientlib_config(str(config_file))
                # 验证category是否匹配
                config_categories = config.get('categories', [])
                
                # 检查category是否在配置的categories中
                if category in config_categories:
                    clientlib_dir = config_file.parent
                    if str(clientlib_dir) not in clientlib_dirs:
                        clientlib_dirs.append(str(clientlib_dir))
                        logger.debug(f"Found ClientLibs: {clientlib_dir} (category: {category})")
            except Exception as e:
                logger.debug(f"Error parsing ClientLibs config {config_file}: {e}")
    
    return clientlib_dirs


def extract_css_rules_from_file(css_file_path: str, target_classes: Set[str]) -> Dict[str, str]:
    """
    从 CSS 文件中提取指定 class 的样式规则
    
    Args:
        css_file_path: CSS 文件路径
        target_classes: 要查找的 CSS class 集合
    
    Returns:
        {class_name: css_rule} 字典
    """
    rules = {}
    
    try:
        with open(css_file_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # 对于每个目标 class，查找对应的规则
        for class_name in target_classes:
            # 匹配 CSS class 选择器（支持多种格式）
            patterns = [
                rf'\.{re.escape(class_name)}\s*\{{([^}}]+)\}}',  # .class-name { ... }
                rf'\.{re.escape(class_name)}\s*,\s*',  # .class-name, (在组合选择器中)
                rf'\.{re.escape(class_name)}\s+',  # .class-name (在组合选择器中)
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, css_content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for match in matches:
                    # 尝试提取完整的规则块
                    start_pos = match.start()
                    # 向前查找选择器开始
                    selector_start = css_content.rfind('\n', 0, start_pos)
                    if selector_start == -1:
                        selector_start = 0
                    
                    # 向后查找规则块结束
                    brace_count = 0
                    rule_end = start_pos
                    for i in range(start_pos, len(css_content)):
                        if css_content[i] == '{':
                            brace_count += 1
                        elif css_content[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                rule_end = i + 1
                                break
                    
                    if rule_end > start_pos:
                        rule = css_content[selector_start:rule_end].strip()
                        if class_name not in rules or len(rule) > len(rules[class_name]):
                            rules[class_name] = rule
        
        # 如果没有找到精确匹配，尝试查找包含该 class 的规则
        if not rules:
            for class_name in target_classes:
                # 查找包含该 class 的规则
                pattern = rf'[^{{]*\.{re.escape(class_name)}[^{{]*\{{[^}}]+\}}'
                matches = re.finditer(pattern, css_content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                for match in matches:
                    rule = match.group(0).strip()
                    if class_name not in rules:
                        rules[class_name] = rule
    
    except Exception as e:
        logger.warning(f"Error reading CSS file {css_file_path}: {e}")
    
    return rules


def find_css_for_classes(
    component_path: str,
    css_classes: Set[str],
    aem_repo_path: str,
    htl_content: Optional[str] = None,
    js_content: Optional[str] = None
) -> Dict[str, Dict[str, str]]:
    """
    查找 CSS class 对应的样式定义
    
    查找策略（按优先级）：
    1. 组件目录下的 CSS 文件（包括CSS Modules）
    2. 组件目录下的 ClientLibs 配置
    3. HTL 中引用的样式文件（data-sly-call template.styles）
    4. 根据 ClientLibs category 查找
    5. 专门的CSS目录（styles/css，保持相同层级）
    6. CSS变量文件、主题CSS、响应式CSS
    7. CSS-in-JS（JavaScript中的CSS）
    8. 全局搜索
    
    Args:
        component_path: 组件路径
        css_classes: 要查找的 CSS class 集合
        aem_repo_path: AEM repository 根路径
        htl_content: HTL 内容（可选，用于提取样式引用）
        js_content: JavaScript 内容（可选，用于提取CSS-in-JS）
    
    Returns:
        {class_name: {file_path: css_rule}} 字典
    """
    results = {}  # {class_name: {file_path: css_rule}}
    
    if not css_classes:
        return results
    
    logger.info(f"Finding CSS for {len(css_classes)} classes: {css_classes}")
    
    # 策略 1: 在组件目录下查找 CSS 文件
    component_css_files = find_component_css_files(component_path)
    logger.info(f"Found {len(component_css_files)} CSS files in component directory")
    
    for css_file in component_css_files:
        rules = extract_css_rules_from_file(css_file, css_classes)
        for class_name, rule in rules.items():
            if class_name not in results:
                results[class_name] = {}
            results[class_name][css_file] = rule
    
    # 策略 2: 查找组件目录下的 ClientLibs 配置
    component_dir = Path(component_path)
    clientlib_configs = list(component_dir.glob('**/.content.xml'))
    
    for config_file in clientlib_configs:
        config = parse_clientlib_config(str(config_file))
        if config['css_paths']:
            logger.info(f"Found ClientLibs config with {len(config['css_paths'])} CSS files")
            for css_path in config['css_paths']:
                if os.path.exists(css_path):
                    rules = extract_css_rules_from_file(css_path, css_classes)
                    for class_name, rule in rules.items():
                        if class_name not in results:
                            results[class_name] = {}
                        results[class_name][css_path] = rule
        
        # 处理 embeds（嵌入的其他 ClientLibs）- 递归处理
        def process_embeds_recursive(embed_categories: List[str], visited_categories: Set[str] = None):
            """递归处理嵌入的 ClientLibs"""
            if visited_categories is None:
                visited_categories = set()
            
            for embed_category in embed_categories:
                # 防止循环依赖
                if embed_category in visited_categories:
                    logger.debug(f"Skipping already visited embed category: {embed_category}")
                    continue
                
                visited_categories.add(embed_category)
                embedded_clientlibs = find_clientlib_by_category(embed_category, aem_repo_path)
                
                for clientlib_dir in embedded_clientlibs:
                    # 查找CSS文件（包括子目录，特别是css/目录）
                    clientlib_path = Path(clientlib_dir)
                    # 查找根目录和css子目录
                    css_search_paths = [
                        clientlib_path.glob('*.css'),  # 根目录
                        clientlib_path.glob('css/*.css'),  # css子目录
                        clientlib_path.rglob('*.css'),  # 所有子目录
                    ]
                    
                    for css_search in css_search_paths:
                        for css_file in css_search:
                            if css_file.is_file():
                                rules = extract_css_rules_from_file(str(css_file), css_classes)
                                for class_name, rule in rules.items():
                                    if class_name not in results:
                                        results[class_name] = {}
                                    results[class_name][str(css_file)] = rule
                    
                    # 递归处理嵌入的ClientLibs
                    embed_config_file = Path(clientlib_dir) / '.content.xml'
                    if embed_config_file.exists():
                        embed_config = parse_clientlib_config(str(embed_config_file))
                        if embed_config['embeds']:
                            process_embeds_recursive(embed_config['embeds'], visited_categories)
                        # 也处理embeds的dependencies（因为embeds的ClientLibs可能也有dependencies）
                        if embed_config['dependencies']:
                            process_dependencies_recursive(embed_config['dependencies'], visited_categories)
        
        if config['embeds']:
            logger.info(f"Processing {len(config['embeds'])} embedded ClientLibs (recursive)")
            process_embeds_recursive(config['embeds'])
        
        # 处理 dependencies（依赖的其他 ClientLibs）- 递归处理
        def process_dependencies_recursive(dep_categories: List[str], visited_categories: Set[str] = None):
            """递归处理依赖的 ClientLibs"""
            if visited_categories is None:
                visited_categories = set()
            
            for dep_category in dep_categories:
                # 防止循环依赖
                if dep_category in visited_categories:
                    logger.debug(f"Skipping already visited dependency category: {dep_category}")
                    continue
                
                visited_categories.add(dep_category)
                dep_clientlibs = find_clientlib_by_category(dep_category, aem_repo_path)
                
                for clientlib_dir in dep_clientlibs:
                    # 查找CSS文件（包括子目录，特别是css/目录）
                    clientlib_path = Path(clientlib_dir)
                    # 查找根目录和css子目录
                    css_search_paths = [
                        clientlib_path.glob('*.css'),  # 根目录
                        clientlib_path.glob('css/*.css'),  # css子目录
                        clientlib_path.rglob('*.css'),  # 所有子目录
                    ]
                    
                    for css_search in css_search_paths:
                        for css_file in css_search:
                            if css_file.is_file():
                                rules = extract_css_rules_from_file(str(css_file), css_classes)
                                for class_name, rule in rules.items():
                                    if class_name not in results:
                                        results[class_name] = {}
                                    results[class_name][str(css_file)] = rule
                    
                    # 递归处理依赖的ClientLibs
                    dep_config_file = Path(clientlib_dir) / '.content.xml'
                    if dep_config_file.exists():
                        dep_config = parse_clientlib_config(str(dep_config_file))
                        if dep_config['dependencies']:
                            process_dependencies_recursive(dep_config['dependencies'], visited_categories)
                        # 也处理embeds（因为dependencies的ClientLibs可能也有embeds）
                        if dep_config['embeds']:
                            process_embeds_recursive(dep_config['embeds'], visited_categories)
        
        if config['dependencies']:
            logger.info(f"Processing {len(config['dependencies'])} dependency ClientLibs (recursive)")
            process_dependencies_recursive(config['dependencies'])
    
    # 策略 3: 从 HTL 中提取样式文件引用
    if htl_content:
        # 查找 data-sly-call template.styles (path 参数)
        styles_pattern = r"data-sly-call\s*=\s*['\"]\$\{template\.styles\s*@\s*path=['\"]([^'\"]+)['\"]"
        style_matches = re.findall(styles_pattern, htl_content, re.IGNORECASE)
        
        for style_path in style_matches:
            # 构建完整路径
            full_style_path = os.path.join(component_path, style_path)
            if os.path.exists(full_style_path):
                rules = extract_css_rules_from_file(full_style_path, css_classes)
                for class_name, rule in rules.items():
                    if class_name not in results:
                        results[class_name] = {}
                    results[class_name][full_style_path] = rule
        
        # 查找 data-sly-call template.styles (categories 参数)
        categories_pattern = r"data-sly-call\s*=\s*['\"]\$\{template\.styles\s*@\s*categories=['\"]([^'\"]+)['\"]"
        category_matches = re.findall(categories_pattern, htl_content, re.IGNORECASE)
        
        for category in category_matches:
            # 清理category（移除可能的引号）
            category = category.strip().strip('"\'')
            # 根据 category 查找 ClientLibs
            clientlib_dirs = find_clientlib_by_category(category, aem_repo_path)
            for clientlib_dir in clientlib_dirs:
                clientlib_path = Path(clientlib_dir)
                # 查找CSS文件（包括子目录，特别是css/目录）
                css_search_paths = [
                    clientlib_path.glob('*.css'),  # 根目录
                    clientlib_path.glob('css/*.css'),  # css子目录
                    clientlib_path.rglob('*.css'),  # 所有子目录
                ]
                
                for css_search in css_search_paths:
                    for css_file in css_search:
                        if css_file.is_file():
                            rules = extract_css_rules_from_file(str(css_file), css_classes)
                            for class_name, rule in rules.items():
                                if class_name not in results:
                                    results[class_name] = {}
                                results[class_name][str(css_file)] = rule
    
    # 策略 5: 查找CSS变量文件、主题文件、响应式文件
    component_dir = Path(component_path)
    parent_dir = component_dir.parent
    # 向上查找，找到styles/css目录
    current_dir = parent_dir
    for depth in range(5):
        for styles_dir_name in ['styles', 'css']:
            # CSS变量文件
            variables_file = current_dir / styles_dir_name / 'variables.css'
            if variables_file.exists():
                # CSS变量文件通常不包含具体的class规则，但我们需要记录它
                logger.debug(f"Found CSS variables file: {variables_file}")
            
            # 主题CSS文件
            themes_dir = current_dir / styles_dir_name / 'themes'
            if themes_dir.exists():
                for theme_file in themes_dir.glob('*.css'):
                    rules = extract_css_rules_from_file(str(theme_file), css_classes)
                    for class_name, rule in rules.items():
                        if class_name not in results:
                            results[class_name] = {}
                        results[class_name][str(theme_file)] = rule
            
            # 响应式CSS文件
            responsive_dir = current_dir / styles_dir_name / 'responsive'
            if responsive_dir.exists():
                for responsive_file in responsive_dir.glob('*.css'):
                    rules = extract_css_rules_from_file(str(responsive_file), css_classes)
                    for class_name, rule in rules.items():
                        if class_name not in results:
                            results[class_name] = {}
                        results[class_name][str(responsive_file)] = rule
        
        if current_dir == current_dir.parent:
            break
        current_dir = current_dir.parent
    
    # 策略 6: 从JavaScript中提取CSS（CSS-in-JS）
    if js_content:
        css_info = extract_css_from_javascript(js_content)
        if css_info['css_in_js']:
            logger.info(f"Found {len(css_info['css_in_js'])} CSS-in-JS blocks in JavaScript")
            for idx, css_block in enumerate(css_info['css_in_js']):
                # 尝试从CSS-in-JS中提取规则
                for class_name in css_classes:
                    pattern = rf'\.{re.escape(class_name)}\s*\{{([^}}]+)\}}'
                    matches = re.findall(pattern, css_block, re.IGNORECASE)
                    if matches:
                        if class_name not in results:
                            results[class_name] = {}
                        results[class_name][f'javascript-css-in-js-{idx}'] = matches[0]
        
        # 记录动态添加的CSS类
        if css_info['dynamic_classes']:
            logger.info(f"Found {len(css_info['dynamic_classes'])} dynamically added CSS classes")
            # 将这些动态类添加到css_classes中，以便后续查找
            for dynamic_class in css_info['dynamic_classes']:
                if dynamic_class not in css_classes:
                    css_classes.add(dynamic_class)
    
    # 策略 7: 在 AEM repository 中全局搜索（作为最后手段）
    # 只在前面策略都没找到时才使用（性能考虑）
    missing_classes = css_classes - set(results.keys())
    if missing_classes:
        logger.info(f"Searching globally for {len(missing_classes)} missing classes")
        # 限制搜索范围：只在常见的 ClientLibs 目录中搜索
        common_clientlib_paths = [
            Path(aem_repo_path) / 'apps' / '**' / 'clientlibs' / '**' / '*.css',
            Path(aem_repo_path) / 'etc' / 'clientlibs' / '**' / '*.css',
        ]
        
        for pattern in common_clientlib_paths:
            for css_file in Path(aem_repo_path).glob(str(pattern.relative_to(Path(aem_repo_path)))):
                rules = extract_css_rules_from_file(str(css_file), missing_classes)
                for class_name, rule in rules.items():
                    if class_name not in results:
                        results[class_name] = {}
                    results[class_name][str(css_file)] = rule
                    missing_classes.discard(class_name)
                
                if not missing_classes:
                    break
            
            if not missing_classes:
                break
    
    logger.info(f"Found CSS for {len(results)}/{len(css_classes)} classes")
    return results


def build_css_summary(
    component_path: str,
    htl_content: str,
    aem_repo_path: str
) -> Dict[str, any]:
    """
    构建组件的 CSS 摘要
    
    Args:
        component_path: 组件路径
        htl_content: HTL 内容
        aem_repo_path: AEM repository 根路径
    
    Returns:
        CSS 摘要字典
    """
    # 提取使用的 CSS classes
    css_classes = extract_css_classes_from_htl(htl_content)
    
    # 查找 CSS 定义
    css_rules = find_css_for_classes(component_path, css_classes, aem_repo_path, htl_content)
    
    # 构建摘要
    summary = {
        'used_classes': list(css_classes),
        'found_classes': list(css_rules.keys()),
        'missing_classes': list(css_classes - set(css_rules.keys())),
        'css_rules': css_rules,
        'component_css_files': find_component_css_files(component_path),
        'component_path': component_path  # 保存组件路径，用于区分
    }
    
    return summary


def build_dependency_css_summary(
    dependency_analyses: Dict[str, List[Dict[str, Any]]],
    dependency_tree: Dict[str, Any],
    aem_repo_path: str
) -> Dict[str, Dict[str, any]]:
    """
    构建所有依赖组件的 CSS 摘要
    
    Args:
        dependency_analyses: 依赖组件的分析结果 {resource_type: [analyses]}
        dependency_tree: 依赖树
        aem_repo_path: AEM repository 根路径
    
    Returns:
        {resource_type: css_summary} 字典
    """
    dependency_css_summaries = {}
    
    def process_dependency(dep_resource_type: str, dep_info: Dict[str, Any]):
        """处理单个依赖组件"""
        dep_path = dep_info.get('path', '')
        if not dep_path:
            return
        
        # 从依赖组件的分析结果中查找 HTL 文件
        dep_analyses = dependency_analyses.get(dep_resource_type, [])
        htl_analyses = [a for a in dep_analyses if a.get('file_type') in ['htl', 'html']]
        
        if htl_analyses:
            # 使用第一个 HTL 文件
            first_htl = htl_analyses[0]
            htl_file_path = first_htl.get('file_path', '')
            
            if htl_file_path:
                try:
                    from tools import read_file
                    htl_content = read_file(htl_file_path)
                    css_summary = build_css_summary(
                        dep_path,
                        htl_content,
                        aem_repo_path
                    )
                    dependency_css_summaries[dep_resource_type] = css_summary
                    logger.info(
                        f"Dependency {dep_resource_type}: "
                        f"{len(css_summary.get('used_classes', []))} classes used, "
                        f"{len(css_summary.get('found_classes', []))} found"
                    )
                except Exception as e:
                    logger.warning(f"Failed to build CSS summary for dependency {dep_resource_type}: {e}")
        
        # 递归处理嵌套依赖
        nested_deps = dep_info.get('dependencies', {})
        for nested_resource_type, nested_info in nested_deps.items():
            process_dependency(nested_resource_type, nested_info)
    
    # 处理所有依赖组件
    root_deps = dependency_tree.get('root', {}).get('dependencies', {})
    for dep_resource_type, dep_info in root_deps.items():
        process_dependency(dep_resource_type, dep_info)
    
    return dependency_css_summaries


def merge_css_summaries(
    current_css_summary: Dict[str, any],
    dependency_css_summaries: Dict[str, Dict[str, any]]
) -> Dict[str, any]:
    """
    合并当前组件和依赖组件的 CSS 摘要
    
    Args:
        current_css_summary: 当前组件的 CSS 摘要
        dependency_css_summaries: 依赖组件的 CSS 摘要
    
    Returns:
        合并后的 CSS 摘要
    """
    merged = {
        'used_classes': set(current_css_summary.get('used_classes', [])),
        'found_classes': set(current_css_summary.get('found_classes', [])),
        'missing_classes': set(current_css_summary.get('missing_classes', [])),
        'css_rules': current_css_summary.get('css_rules', {}).copy(),
        'component_css_files': current_css_summary.get('component_css_files', []).copy(),
        'dependency_css': {}  # 依赖组件的 CSS
    }
    
    # 合并依赖组件的 CSS
    for dep_resource_type, dep_css_summary in dependency_css_summaries.items():
        merged['used_classes'].update(dep_css_summary.get('used_classes', []))
        merged['found_classes'].update(dep_css_summary.get('found_classes', []))
        merged['missing_classes'].update(dep_css_summary.get('missing_classes', []))
        
        # 合并 CSS 规则（如果同一个 class 在多个组件中定义，保留所有）
        for class_name, rules_dict in dep_css_summary.get('css_rules', {}).items():
            if class_name not in merged['css_rules']:
                merged['css_rules'][class_name] = {}
            # 添加依赖组件的规则，标记来源
            for file_path, rule in rules_dict.items():
                merged['css_rules'][class_name][f"[{dep_resource_type}] {file_path}"] = rule
        
        # 保存依赖组件的完整摘要
        merged['dependency_css'][dep_resource_type] = dep_css_summary
    
    # 转换为列表
    merged['used_classes'] = list(merged['used_classes'])
    merged['found_classes'] = list(merged['found_classes'])
    merged['missing_classes'] = list(merged['missing_classes'])
    
    return merged
