"""
Java Sling Model 分析器
解析 Java 文件，提取 Sling Model 的数据结构、字段、方法、注解等信息
"""
import re
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def parse_java_file(java_file_path: str) -> Dict[str, Any]:
    """
    解析 Java Sling Model 文件，提取关键信息
    
    Args:
        java_file_path: Java 文件路径
    
    Returns:
        解析结果字典，包含：
        - class_name: 类名
        - package: 包名
        - resource_type: Sling Model 的 resourceType
        - fields: 字段列表（包含类型、注解、是否必填等）
        - methods: 方法列表（包含 @PostConstruct 方法）
        - annotations: 类级别注解
        - implements: 实现的接口
        - data_structure: 数据结构摘要（用于生成 TypeScript 接口）
        - validation_rules: 验证规则
        - transformation_logic: 数据转换逻辑（@PostConstruct 方法）
    """
    try:
        with open(java_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read Java file {java_file_path}: {e}")
        return {}
    
    result = {
        'class_name': '',
        'package': '',
        'resource_type': '',
        'fields': [],
        'methods': [],
        'annotations': {},
        'implements': [],
        'data_structure': {},
        'validation_rules': [],
        'transformation_logic': [],
        'getter_methods': {}
    }
    
    # 提取包名
    package_match = re.search(r'package\s+([\w.]+);', content)
    if package_match:
        result['package'] = package_match.group(1)
    
    # 提取类名
    class_match = re.search(r'public\s+class\s+(\w+)', content)
    if class_match:
        result['class_name'] = class_match.group(1)
    
    # 提取实现的接口
    implements_match = re.search(r'implements\s+([^{]+)', content)
    if implements_match:
        interfaces = [i.strip() for i in implements_match.group(1).split(',')]
        result['implements'] = interfaces
    
    # 提取 @Model 注解信息
    model_annotation = _extract_model_annotation(content)
    if model_annotation:
        result['annotations']['Model'] = model_annotation
        result['resource_type'] = model_annotation.get('resourceType', '')
    
    # 提取 @Exporter 注解
    exporter_annotation = _extract_exporter_annotation(content)
    if exporter_annotation:
        result['annotations']['Exporter'] = exporter_annotation
    
    # 提取字段
    result['fields'] = _extract_fields(content)
    
    # 提取方法
    result['methods'] = _extract_methods(content)
    
    # 提取 @PostConstruct 方法（数据转换逻辑）
    result['transformation_logic'] = _extract_postconstruct_methods(content)
    
    # 提取验证规则
    result['validation_rules'] = _extract_validation_rules(content, result['fields'])
    
    # 构建数据结构摘要（用于生成 TypeScript 接口）
    result['data_structure'] = _build_data_structure(result['fields'], result['methods'])
    
    # 提取 getter 方法（用于推断字段类型）
    result['getter_methods'] = _extract_getter_methods(content)
    
    # 提取服务依赖
    result['service_dependencies'] = _extract_service_dependencies(result['fields'], result['methods'])
    
    return result


def _extract_model_annotation(content: str) -> Optional[Dict[str, Any]]:
    """提取 @Model 注解信息"""
    # 匹配 @Model 注解（可能跨多行）
    model_pattern = r'@Model\s*\(\s*([^)]+)\s*\)'
    match = re.search(model_pattern, content, re.DOTALL)
    if not match:
        return None
    
    annotation_content = match.group(1)
    result = {}
    
    # 提取 adaptables
    adaptables_match = re.search(r'adaptables\s*=\s*([^,)]+)', annotation_content)
    if adaptables_match:
        result['adaptables'] = adaptables_match.group(1).strip()
    
    # 提取 adapters
    adapters_match = re.search(r'adapters\s*=\s*\{([^}]+)\}', annotation_content)
    if adapters_match:
        result['adapters'] = [a.strip() for a in adapters_match.group(1).split(',')]
    
    # 提取 resourceType
    resource_type_match = re.search(r'resourceType\s*=\s*["\']([^"\']+)["\']', annotation_content)
    if resource_type_match:
        result['resourceType'] = resource_type_match.group(1)
    
    # 提取 defaultInjectionStrategy
    strategy_match = re.search(r'defaultInjectionStrategy\s*=\s*(\w+)', annotation_content)
    if strategy_match:
        result['defaultInjectionStrategy'] = strategy_match.group(1)
    
    return result


def _extract_exporter_annotation(content: str) -> Optional[Dict[str, Any]]:
    """提取 @Exporter 注解信息"""
    exporter_pattern = r'@Exporter\s*\(\s*([^)]+)\s*\)'
    match = re.search(exporter_pattern, content, re.DOTALL)
    if not match:
        return None
    
    annotation_content = match.group(1)
    result = {}
    
    # 提取 name
    name_match = re.search(r'name\s*=\s*([^,)]+)', annotation_content)
    if name_match:
        result['name'] = name_match.group(1).strip()
    
    # 提取 extensions
    extensions_match = re.search(r'extensions\s*=\s*([^,)]+)', annotation_content)
    if extensions_match:
        result['extensions'] = extensions_match.group(1).strip()
    
    return result


def _extract_fields(content: str) -> List[Dict[str, Any]]:
    """提取类字段（包括类型、注解、访问修饰符）"""
    fields = []
    
    # 匹配字段定义（包括注解、修饰符、类型、名称）
    # 例如: @ValueMapValue private String text;
    field_pattern = r'((?:@[\w.]+(?:\s*\([^)]*\))?\s+)*)\s*(private|protected|public)?\s*(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?(?:\[\])?)\s+(\w+)\s*[;=]'
    
    matches = re.finditer(field_pattern, content)
    for match in matches:
        annotations_str = match.group(1).strip()
        access_modifier = match.group(2) or 'private'
        field_type = match.group(3)
        field_name = match.group(4)
        
        # 跳过方法参数中的匹配
        if '{' in content[max(0, match.start()-50):match.start()]:
            continue
        
        field_info = {
            'name': field_name,
            'type': field_type,
            'access_modifier': access_modifier,
            'annotations': [],
            'is_required': False,
            'default_value': None,
            'injection_type': None
        }
        
        # 解析注解
        annotation_matches = re.finditer(r'@(\w+)(?:\(([^)]*)\))?', annotations_str)
        for ann_match in annotation_matches:
            ann_name = ann_match.group(1)
            ann_params = ann_match.group(2) if ann_match.group(2) else ''
            
            field_info['annotations'].append({
                'name': ann_name,
                'parameters': ann_params
            })
            
            # 检查是否是注入注解
            if ann_name in ['ValueMapValue', 'Inject', 'OSGiService', 'RequestAttribute', 'SlingObject']:
                field_info['injection_type'] = ann_name
                
                # 如果是服务注入，标记为服务依赖
                if ann_name in ['OSGiService', 'Inject']:
                    field_info['is_service'] = True
            
            # 检查是否必填
            if ann_name in ['Required', 'NotNull', 'NotEmpty']:
                field_info['is_required'] = True
            
            # 提取默认值（如果有）
            if 'default' in ann_params.lower() or 'value' in ann_params.lower():
                default_match = re.search(r'(?:default|value)\s*=\s*["\']?([^"\',)]+)["\']?', ann_params)
                if default_match:
                    field_info['default_value'] = default_match.group(1)
        
        fields.append(field_info)
    
    return fields


def _extract_methods(content: str) -> List[Dict[str, Any]]:
    """提取方法（包括 @PostConstruct 方法）"""
    methods = []
    
    # 匹配方法定义（包括注解、返回类型、方法名、参数）
    method_pattern = r'((?:@[\w.]+(?:\s*\([^)]*\))?\s+)*)\s*(public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(\w+(?:<[^>]+>)?(?:\[\])?)\s+(\w+)\s*\(([^)]*)\)\s*\{'
    
    matches = re.finditer(method_pattern, content, re.DOTALL)
    for match in matches:
        annotations_str = match.group(1).strip()
        access_modifier = match.group(2) or 'public'
        return_type = match.group(3)
        method_name = match.group(4)
        params = match.group(5)
        
        method_info = {
            'name': method_name,
            'return_type': return_type,
            'access_modifier': access_modifier,
            'parameters': params,
            'annotations': [],
            'is_postconstruct': False,
            'is_getter': method_name.startswith('get') and len(method_name) > 3
        }
        
        # 解析注解
        annotation_matches = re.finditer(r'@(\w+)(?:\(([^)]*)\))?', annotations_str)
        for ann_match in annotation_matches:
            ann_name = ann_match.group(1)
            ann_params = ann_match.group(2) if ann_match.group(2) else ''
            
            method_info['annotations'].append({
                'name': ann_name,
                'parameters': ann_params
            })
            
            if ann_name == 'PostConstruct':
                method_info['is_postconstruct'] = True
        
        # 提取方法体（简化版，只提取前几行）
        method_body_match = re.search(
            rf'{re.escape(method_name)}\s*\([^)]*\)\s*\{{([^}}]+)',
            content,
            re.DOTALL
        )
        if method_body_match:
            body = method_body_match.group(1)
            # 只保留前 20 行
            body_lines = body.split('\n')[:20]
            method_info['body_preview'] = '\n'.join(body_lines)
        
        methods.append(method_info)
    
    return methods


def _extract_postconstruct_methods(content: str) -> List[Dict[str, Any]]:
    """提取 @PostConstruct 方法（数据转换逻辑）"""
    postconstruct_methods = []
    
    # 匹配 @PostConstruct 方法
    pattern = r'@PostConstruct\s+(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(\w+)\s+(\w+)\s*\([^)]*\)\s*\{([^}]+)\}'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    for match in matches:
        return_type = match.group(1)
        method_name = match.group(2)
        method_body = match.group(3)
        
        postconstruct_methods.append({
            'method_name': method_name,
            'return_type': return_type,
            'body': method_body.strip(),
            'description': f'Data transformation logic in {method_name}'
        })
    
    return postconstruct_methods


def _extract_validation_rules(content: str, fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取验证规则"""
    validation_rules = []
    
    for field in fields:
        field_name = field['name']
        
        # 检查字段注解中的验证规则
        for annotation in field.get('annotations', []):
            ann_name = annotation['name']
            
            if ann_name in ['Required', 'NotNull', 'NotEmpty', 'NotBlank']:
                validation_rules.append({
                    'field': field_name,
                    'rule': ann_name,
                    'message': f'{field_name} is required'
                })
            
            # 检查其他验证注解（如 @Size, @Min, @Max）
            if ann_name in ['Size', 'Min', 'Max', 'Pattern']:
                validation_rules.append({
                    'field': field_name,
                    'rule': ann_name,
                    'parameters': annotation.get('parameters', '')
                })
    
    return validation_rules


def _extract_getter_methods(content: str) -> Dict[str, str]:
    """提取 getter 方法，用于推断字段类型"""
    getters = {}
    
    # 匹配 getter 方法：public Type getFieldName() { return fieldName; }
    getter_pattern = r'public\s+(\w+(?:<[^>]+>)?(?:\[\])?)\s+get(\w+)\s*\([^)]*\)\s*\{[^}]*return\s+(\w+);'
    
    matches = re.finditer(getter_pattern, content, re.DOTALL)
    for match in matches:
        return_type = match.group(1)
        method_name = match.group(2)
        field_name = match.group(3)
        
        # 将 getFieldName 转换为 fieldName
        field_name_lower = method_name[0].lower() + method_name[1:] if method_name else ''
        
        getters[field_name_lower] = {
            'return_type': return_type,
            'method_name': f'get{method_name}',
            'field_name': field_name
        }
    
    return getters


def _build_data_structure(fields: List[Dict[str, Any]], methods: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构建数据结构摘要（用于生成 TypeScript 接口）"""
    structure = {
        'properties': {},
        'required_fields': [],
        'optional_fields': [],
        'type_mapping': {}
    }
    
    for field in fields:
        field_name = field['name']
        field_type = field['type']
        is_required = field['is_required']
        
        # Java 类型到 TypeScript 类型映射
        ts_type = _map_java_to_typescript_type(field_type)
        
        structure['properties'][field_name] = {
            'java_type': field_type,
            'typescript_type': ts_type,
            'is_required': is_required,
            'default_value': field.get('default_value'),
            'annotations': [ann['name'] for ann in field.get('annotations', [])]
        }
        
        if is_required:
            structure['required_fields'].append(field_name)
        else:
            structure['optional_fields'].append(field_name)
    
    return structure


def _extract_service_dependencies(fields: List[Dict[str, Any]], methods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取服务依赖（@OSGiService, @Inject 等）"""
    service_deps = []
    
    for field in fields:
        if field.get('is_service'):
            service_deps.append({
                'field_name': field['name'],
                'field_type': field['type'],
                'injection_type': field.get('injection_type', ''),
                'description': f"Service dependency: {field['type']} injected via {field.get('injection_type', 'Inject')}"
            })
    
    return service_deps


def _map_java_to_typescript_type(java_type: str) -> str:
    """将 Java 类型映射到 TypeScript 类型"""
    # 移除泛型和数组标记（简化处理）
    base_type = re.sub(r'<[^>]+>', '', java_type)
    base_type = re.sub(r'\[\]', '', base_type)
    base_type = base_type.strip()
    
    type_mapping = {
        'String': 'string',
        'Integer': 'number',
        'int': 'number',
        'Long': 'number',
        'long': 'number',
        'Double': 'number',
        'double': 'number',
        'Float': 'number',
        'float': 'number',
        'Boolean': 'boolean',
        'boolean': 'boolean',
        'Date': 'Date | string',
        'Calendar': 'Date | string',
        'List': 'Array',
        'ArrayList': 'Array',
        'Map': 'Record<string, any>',
        'HashMap': 'Record<string, any>',
        'Resource': 'any',  # AEM Resource
        'SlingHttpServletRequest': 'any',  # AEM Request
    }
    
    # 检查是否是 List<T> 类型
    if 'List' in java_type or 'ArrayList' in java_type:
        generic_match = re.search(r'<([^>]+)>', java_type)
        if generic_match:
            inner_type = generic_match.group(1)
            inner_ts_type = _map_java_to_typescript_type(inner_type)
            return f'{inner_ts_type}[]'
        return 'any[]'
    
    return type_mapping.get(base_type, 'any')


def build_java_analysis_summary(java_analyses: List[Dict[str, Any]]) -> str:
    """
    构建 Java 分析摘要（用于传递给代码生成 Agent）
    
    Args:
        java_analyses: Java 文件分析结果列表
    
    Returns:
        格式化的摘要字符串
    """
    if not java_analyses:
        return ""
    
    summary_parts = []
    summary_parts.append("=== JAVA SLING MODELS (DATA STRUCTURE) - CRITICAL ===\n")
    
    for analysis in java_analyses:
        class_name = analysis.get('class_name', 'Unknown')
        resource_type = analysis.get('resource_type', '')
        data_structure = analysis.get('data_structure', {})
        fields = analysis.get('fields', [])
        transformation_logic = analysis.get('transformation_logic', [])
        
        summary_parts.append(f"\n--- Class: {class_name} ---")
        if resource_type:
            summary_parts.append(f"ResourceType: {resource_type}")
        
        # 数据结构
        if data_structure.get('properties'):
            summary_parts.append("\nProperties (TypeScript Interface):")
            for prop_name, prop_info in data_structure['properties'].items():
                ts_type = prop_info['typescript_type']
                is_required = prop_info['is_required']
                required_marker = "" if is_required else "?"
                default_val = prop_info.get('default_value')
                default_str = f" (default: {default_val})" if default_val else ""
                summary_parts.append(f"  {prop_name}{required_marker}: {ts_type}{default_str}")
        
        # 必填字段
        required_fields = data_structure.get('required_fields', [])
        if required_fields:
            summary_parts.append(f"\nRequired Fields: {', '.join(required_fields)}")
        
        # 数据转换逻辑
        if transformation_logic:
            summary_parts.append("\nData Transformation Logic (@PostConstruct methods):")
            for logic in transformation_logic:
                method_name = logic.get('method_name', '')
                body_preview = logic.get('body', '')[:200]  # 限制长度
                summary_parts.append(f"  - {method_name}: {body_preview}...")
                summary_parts.append("    → Convert this to React useEffect or useMemo")
        
        # 验证规则
        validation_rules = analysis.get('validation_rules', [])
        if validation_rules:
            summary_parts.append("\nValidation Rules:")
            for rule in validation_rules:
                field = rule.get('field', '')
                rule_type = rule.get('rule', '')
                summary_parts.append(f"  - {field}: {rule_type}")
    
    summary_parts.append("\n=== CONVERSION NOTES ===\n")
    summary_parts.append("1. Use the TypeScript interface above to define React component Props")
    summary_parts.append("2. Convert @PostConstruct methods to React useEffect or useMemo hooks")
    summary_parts.append("3. Apply validation rules using form validation library (e.g., react-hook-form, yup)")
    summary_parts.append("4. Map Java types to TypeScript types as shown above")
    
    return "\n".join(summary_parts)
