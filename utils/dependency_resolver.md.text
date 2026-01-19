"""
AEM 组件依赖解析器
递归解析组件依赖关系，找到所有被引用的组件并分析它们
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def extract_component_dependencies(htl_content: str, current_resource_type: str) -> List[str]:
    """
    从 HTL 内容中提取组件依赖（data-sly-resource）
    
    Args:
        htl_content: HTL 模板内容
        current_resource_type: 当前组件的 resourceType
    
    Returns:
        被引用的组件 resourceType 列表
    """
    dependencies = []
    
    # 提取 data-sly-resource 的值
    # 格式可能是：
    # - data-sly-resource="${component.path}"
    # - data-sly-resource="core/wcm/components/button/v1/button"
    # - data-sly-resource="${resource @ resourceType='example/components/button'}"
    
    patterns = [
        # 直接路径引用
        r'data-sly-resource\s*=\s*["\']([^"\']+)["\']',
        # 使用 resourceType 参数
        r"resourceType\s*=\s*['\"]([^'\"]+)['\"]",
        # 变量引用（需要从表达式中提取）
        r'\$\{([\w.]+)\}',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, htl_content, re.IGNORECASE)
        for match in matches:
            # 清理匹配结果
            resource_ref = match.strip().strip("'\"")
            
            # 跳过明显不是 resourceType 的值
            if not resource_ref or resource_ref in ['resource', 'component', 'item']:
                continue
            
            # 如果是相对路径，可能需要转换为 resourceType
            # 如果是绝对路径（以 / 开头），直接使用
            if resource_ref.startswith('/'):
                # 移除前导斜杠并转换为 resourceType 格式
                resource_type = resource_ref.lstrip('/')
            elif '/' in resource_ref or '.' in resource_ref:
                # 已经是 resourceType 格式
                resource_type = resource_ref
            else:
                # 可能是变量名，跳过（无法确定实际值）
                continue
            
            # 添加到依赖列表（去重）
            if resource_type not in dependencies:
                dependencies.append(resource_type)
    
    return dependencies


def resolve_resource_type_to_path(resource_type: str, aem_repo_path: str) -> Optional[str]:
    """
    将 resourceType 解析为文件系统路径
    
    Args:
        resource_type: AEM resourceType（如 "example/components/button"）
        aem_repo_path: AEM repository 根路径
    
    Returns:
        组件路径，如果不存在则返回 None
    """
    # 规范化 resourceType
    resource_type = resource_type.strip().strip("/").strip("\\")
    
    # 将点分隔符转换为路径分隔符
    if "." in resource_type and "/" not in resource_type:
        resource_type = resource_type.replace(".", os.sep)
    else:
        resource_type = resource_type.replace("\\", os.sep).replace("/", os.sep)
    
    # 构建完整路径
    component_path = Path(aem_repo_path) / resource_type
    
    # 检查路径是否存在
    if component_path.exists() and component_path.is_dir():
        return str(component_path.resolve())
    
    return None


def collect_component_dependencies(
    component_path: str,
    aem_repo_path: str,
    resource_type: str,
    visited: Optional[Set[str]] = None,
    max_depth: int = 5
) -> Dict[str, Dict]:
    """
    递归收集组件的所有依赖
    
    Args:
        component_path: 当前组件的文件系统路径
        aem_repo_path: AEM repository 根路径
        resource_type: 当前组件的 resourceType
        visited: 已访问的组件集合（防止循环依赖）
        max_depth: 最大递归深度
    
    Returns:
        依赖组件字典：{resource_type: {path, files, analyses}}
    """
    if visited is None:
        visited = set()
    
    if max_depth <= 0:
        logger.warning(f"Max depth reached for {resource_type}")
        return {}
    
    if resource_type in visited:
        logger.debug(f"Circular dependency detected: {resource_type}")
        return {}
    
    visited.add(resource_type)
    dependencies = {}
    
    # 读取当前组件的 HTL 文件
    from tools import list_files, read_file
    
    component_files = list_files(component_path, recursive=False)
    htl_files = [f for f in component_files if f.endswith('.html') or f.endswith('.htl')]
    
    all_dependencies_resource_types = []
    
    # 从所有 HTL 文件中提取依赖
    for htl_file in htl_files:
        try:
            htl_content = read_file(htl_file)
            deps = extract_component_dependencies(htl_content, resource_type)
            all_dependencies_resource_types.extend(deps)
        except Exception as e:
            logger.warning(f"Failed to read HTL file {htl_file}: {e}")
    
    # 去重
    all_dependencies_resource_types = list(set(all_dependencies_resource_types))
    
    logger.info(f"Component {resource_type} has {len(all_dependencies_resource_types)} dependencies")
    
    # 递归处理每个依赖
    for dep_resource_type in all_dependencies_resource_types:
        # 解析依赖组件的路径
        dep_path = resolve_resource_type_to_path(dep_resource_type, aem_repo_path)
        
        if not dep_path:
            logger.warning(f"Dependency component not found: {dep_resource_type}")
            continue
        
        # 收集依赖组件的文件
        try:
            dep_files = list_files(dep_path, recursive=False)
            
            # 递归收集依赖的依赖
            sub_dependencies = collect_component_dependencies(
                dep_path,
                aem_repo_path,
                dep_resource_type,
                visited.copy(),  # 传递已访问集合的副本
                max_depth - 1
            )
            
            # 存储依赖信息
            dependencies[dep_resource_type] = {
                'resource_type': dep_resource_type,
                'path': dep_path,
                'files': dep_files,
                'dependencies': sub_dependencies  # 嵌套依赖
            }
            
            logger.info(f"Collected dependency: {dep_resource_type} ({len(dep_files)} files)")
        except Exception as e:
            logger.error(f"Failed to collect dependency {dep_resource_type}: {e}")
    
    return dependencies


def build_dependency_tree(
    root_resource_type: str,
    root_component_path: str,
    aem_repo_path: str
) -> Dict[str, Dict]:
    """
    构建完整的组件依赖树
    
    Args:
        root_resource_type: 根组件的 resourceType
        root_component_path: 根组件的文件系统路径
        aem_repo_path: AEM repository 根路径
    
    Returns:
        依赖树字典
    """
    logger.info(f"Building dependency tree for {root_resource_type}")
    
    tree = {
        'root': {
            'resource_type': root_resource_type,
            'path': root_component_path,
            'dependencies': collect_component_dependencies(
                root_component_path,
                aem_repo_path,
                root_resource_type
            )
        }
    }
    
    return tree


def flatten_dependencies(dependency_tree: Dict[str, Dict]) -> List[Dict]:
    """
    将依赖树扁平化为列表（包含所有依赖组件）
    
    Args:
        dependency_tree: 依赖树
    
    Returns:
        扁平化的依赖组件列表
    """
    flattened = []
    
    def _flatten(deps: Dict[str, Dict]):
        for dep_resource_type, dep_info in deps.items():
            flattened.append({
                'resource_type': dep_resource_type,
                'path': dep_info['path'],
                'files': dep_info.get('files', [])
            })
            # 递归处理嵌套依赖
            if 'dependencies' in dep_info:
                _flatten(dep_info['dependencies'])
    
    root = dependency_tree.get('root', {})
    if 'dependencies' in root:
        _flatten(root['dependencies'])
    
    return flattened


def get_all_dependency_files(dependency_tree: Dict[str, Dict]) -> List[str]:
    """
    获取所有依赖组件的文件列表
    
    Args:
        dependency_tree: 依赖树
    
    Returns:
        所有依赖组件的文件路径列表
    """
    all_files = []
    
    def _collect_files(deps: Dict[str, Dict]):
        for dep_info in deps.values():
            all_files.extend(dep_info.get('files', []))
            if 'dependencies' in dep_info:
                _collect_files(dep_info['dependencies'])
    
    root = dependency_tree.get('root', {})
    if 'dependencies' in root:
        _collect_files(root['dependencies'])
    
    return all_files
