"""
AEM 分析 Agent
负责分析 AEM 组件源代码
支持结构化输出，优先分析重要文件（HTL, Dialog, JS）
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import read_file, list_files
from utils.schemas import FileAnalysisResult
from utils.aem_utils import (
    prioritize_aem_files,
    categorize_aem_files,
    identify_aem_file_type,
    extract_htl_properties,
    extract_dialog_properties
)


@tool
def analyze_htl_file(file_path: str) -> str:
    """分析 HTL 模板文件"""
    content = read_file(file_path)
    # 这里可以添加更详细的 HTL 解析逻辑
    return f"HTL file content:\n{content}"


@tool
def analyze_dialog_file(file_path: str) -> str:
    """分析 dialog 配置文件"""
    content = read_file(file_path)
    return f"Dialog file content:\n{content}"


@tool
def analyze_script_file(file_path: str) -> str:
    """分析脚本文件"""
    content = read_file(file_path)
    return f"Script file content:\n{content}"


class AEMAnalysisAgent(BaseAgent):
    """AEM 分析 Agent - 逐个文件分析"""

    def __init__(self):
        from tools import (
            list_files,
            search_files_by_pattern,
            search_text_in_files,
            get_component_files_by_type,
            extract_css_classes_from_file,
            extract_htl_dependencies,
            find_files_in_similar_paths,
            find_css_for_component_in_similar_paths
        )

        tools = [
            analyze_htl_file,
            analyze_dialog_file,
            analyze_script_file,
            read_file,
            list_files,
            search_files_by_pattern,
            search_text_in_files,
            get_component_files_by_type,
            extract_css_classes_from_file,
            extract_htl_dependencies,
            find_files_in_similar_paths,
            find_css_for_component_in_similar_paths
        ]

        system_prompt = """You are an AEM (Adobe Experience Manager) expert analyst.
Your task is to analyze AEM component source code files with focus on conversion to React.

IMPORTANT ANALYSIS PRIORITIES:
1. HTL Templates (*.html) - MOST CRITICAL
   - Extract UI structure (HTML elements, structure hierarchy)
   - Identify data-sly-* usage (data-sly-use, data-sly-repeat, data-sly-resource)
   - Extract Sling Model references
   - Identify UI patterns (buttons, forms, lists, cards, dialogs, etc.)
   - Extract event handlers (onclick, onchange, etc.)
   - Note conditional rendering logic

2. Dialog XML (_cq_dialog.xml) - CRITICAL
   - Extract all property definitions (fields, types, labels)
   - Identify required vs optional fields
   - Extract default values
   - Note field types (textfield, textarea, select, checkbox, etc.)
   - Extract tabs and field groups (for organizing props in React)

3. JavaScript Files (*.js) - IMPORTANT
   - Extract client-side interactions
   - Identify event handlers and callbacks
   - Note DOM manipulations
   - Extract any data fetching logic
   - Identify component lifecycle hooks usage

4. Java Sling Models (*.java) - CRITICAL
   - Extract class name and package
   - Extract @Model annotation (resourceType, adaptables, adapters)
   - Extract all fields with their types and annotations (@ValueMapValue, @Required, @NotNull, etc.)
   - Extract @PostConstruct methods (data transformation logic)
   - Extract getter methods (to understand field access)
   - Extract validation rules (@Required, @NotNull, @Size, @Min, @Max, etc.)
   - Note: This information is critical for generating accurate TypeScript interfaces
   - Note: @PostConstruct methods need to be converted to React useEffect or useMemo hooks

5. CSS Files (*.css) - Will be provided later
   - Note: Styling approach will be handled separately

For each file, provide:
- File type (htl, dialog, js, java, css, etc.)
- Purpose/functionality (what this file does)
- Dependencies (components, services, resources referenced)
- Key features and behaviors (UI elements, interactions)
- Configuration details (props, settings, options)
- Conversion notes (how this should be converted to React)

Output format should be structured and clear for downstream agents."""

        super().__init__(
            name="AEMAnalysisAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.2,
            output_schema=FileAnalysisResult  # 使用结构化输出
        )

    def analyze_file(self, file_path: str) -> dict:
        """分析单个文件并返回结构化结果"""
        file_content = read_file(file_path)
        file_type, priority = identify_aem_file_type(file_path)

        # 根据文件类型构建针对性的提示
        type_specific_prompt = ""

        if file_type in ['htl', 'html']:
            # 提取 HTL 特定信息
            htl_props = extract_htl_properties(file_content)
            type_specific_prompt = f"""
This is an HTL template file - THE MOST IMPORTANT for React conversion.

Focus on:
1. UI Structure: Extract all HTML elements and their hierarchy
2. Data Binding: Identify all data-sly-* attributes and their purposes
3. Sling Models: Note all data-sly-use references (these become React props/data)
4. UI Patterns: Identify buttons, forms, inputs, lists, cards, dialogs, etc.
5. Conditional Logic: Note any data-sly-test or conditional rendering
6. Iterations: Identify data-sly-repeat patterns (become .map() in React)
7. Event Handlers: Extract all onclick, onchange, etc. (become React event handlers)

Extracted HTL properties:
- Uses Sling Models: {htl_props.get('uses_models', [])}
- Model properties used: {htl_props.get('model_properties_used', [])[:10]}  # 前10个
- HTL-specific features:
  * data-sly-call: {htl_props.get('data_sly_call', [])} (AEM-specific, remove in React)
  * data-sly-element: {htl_props.get('data_sly_element', [])} (dynamic element type)
  * data-sly-attribute: {htl_props.get('data_sly_attribute', [])} (dynamic attributes)
  * data-sly-repeat: {htl_props.get('data_sly_repeat', [])} (iteration)
  * data-sly-test: {htl_props.get('data_sly_test', [])} (conditional rendering)
  * data-sly-resource: {htl_props.get('data_sly_resource', [])} (component inclusion)
  * sly elements: {len(htl_props.get('sly_elements', []))} found (logic binding, not rendered)
  * i18n usage: {htl_props.get('i18n_usage', [])} (internationalization)
- UI Elements detected: {htl_props.get('ui_elements', [])}
- Event handlers: {htl_props.get('event_handlers', [])}

CONVERSION NOTES:
- data-sly-call: AEM-specific (placeholder, styles/scripts loading) - Remove in React or convert to imports
- data-sly-element: Convert to React conditional rendering or dynamic component
- data-sly-attribute: Convert to React conditional attribute spreading
- sly elements: Remove (logic binding, use directly in React)
- i18n: Convert to React i18n library (e.g., react-i18next)

This HTL structure should be converted to JSX structure in React, handling all HTL-specific features appropriately.
"""
        elif file_type == 'dialog':
            # 提取 Dialog 特定信息
            dialog_props = extract_dialog_properties(file_content)
            type_specific_prompt = f"""
This is a Dialog XML file - CRITICAL for React props definition.

Focus on:
1. Property Definitions: All fields defined here become React component props
2. Field Types: textfield → string, textarea → string, select → enum/string, checkbox → boolean, etc.
3. Required Fields: These become required React props
4. Default Values: Use these as React default prop values
5. Field Labels: Use for React prop documentation
6. Tabs/Groups: Can be used to organize props or create sub-components

Extracted Dialog properties:
- Fields: {dialog_props.get('fields', [])}
- Field types: {dialog_props.get('field_types', {})}

This dialog configuration maps directly to React component props interface.
"""
        elif file_type == 'js':
            type_specific_prompt = """
This is a JavaScript file - IMPORTANT for React interactions.

Focus on:
1. Event Handlers: Convert these to React event handlers (onClick, onChange, etc.)
2. DOM Manipulations: These should use React state and refs instead
3. Data Fetching: May need to use React hooks (useState, useEffect)
4. Component Logic: Convert to React component methods or hooks
5. Dependencies: Note any libraries used (may need React equivalents)

This JavaScript logic should be converted to React hooks and event handlers.
"""
        elif file_type == 'java':
            # 使用 Java 分析器解析 Java 文件
            try:
                from utils.java_analyzer import parse_java_file
                java_parsed = parse_java_file(file_path)

                if java_parsed:
                    class_name = java_parsed.get('class_name', 'Unknown')
                    resource_type = java_parsed.get('resource_type', '')
                    fields = java_parsed.get('fields', [])
                    data_structure = java_parsed.get('data_structure', {})
                    transformation_logic = java_parsed.get('transformation_logic', [])
                    validation_rules = java_parsed.get('validation_rules', [])

                    fields_summary = []
                    for field in fields[:10]:  # 前10个字段
                        field_name = field.get('name', '')
                        field_type = field.get('type', '')
                        is_required = field.get('is_required', False)
                        annotations = [ann.get('name', '') for ann in field.get('annotations', [])]
                        required_marker = " (required)" if is_required else ""
                        fields_summary.append(
                            f"  - {field_name}: {field_type}{required_marker} [{', '.join(annotations)}]")

                    type_specific_prompt = f"""
This is a Java Sling Model file - CRITICAL for React TypeScript types and data structure.

Focus on:
1. Class Structure: {class_name} (ResourceType: {resource_type})
2. Fields: Extract all fields with their types and annotations
3. TypeScript Mapping: Map Java types to TypeScript types (String → string, Integer → number, etc.)
4. Required Fields: Fields with @Required, @NotNull → required TypeScript props
5. Data Transformation: @PostConstruct methods → React useEffect or useMemo hooks
6. Validation Rules: Extract validation annotations for form validation

Extracted Java Sling Model information:
- Class: {class_name}
- ResourceType: {resource_type}
- Fields ({len(fields)} total):
{chr(10).join(fields_summary)}
- Data Structure (TypeScript):
  Properties: {len(data_structure.get('properties', {}))}
  Required: {', '.join(data_structure.get('required_fields', [])[:5])}
  Optional: {', '.join(data_structure.get('optional_fields', [])[:5])}
- Transformation Logic (@PostConstruct methods): {len(transformation_logic)} methods
- Validation Rules: {len(validation_rules)} rules

CONVERSION NOTES:
- This Java Sling Model defines the data structure for the React component
- Generate TypeScript interface based on the fields and types above
- Convert @PostConstruct methods to React useEffect or useMemo hooks
- Apply validation rules using form validation library (react-hook-form, yup)
- Required fields from Java annotations must be required in TypeScript interface
"""
                else:
                    type_specific_prompt = """
This is a Java Sling Model file - CRITICAL for React TypeScript types.

Focus on:
1. Extract class name and package
2. Extract @Model annotation (resourceType)
3. Extract all fields with types and annotations
4. Extract @PostConstruct methods (data transformation logic)
5. Extract validation rules

This information is critical for generating accurate TypeScript interfaces.
"""
            except Exception as e:
                logger.warning(f"Failed to parse Java file {file_path}: {e}")
                type_specific_prompt = """
This is a Java Sling Model file - CRITICAL for React TypeScript types.

Focus on extracting:
1. Class structure and @Model annotation
2. All fields with their types
3. @PostConstruct methods
4. Validation annotations

This information is critical for generating accurate TypeScript interfaces.
"""

        prompt = f"""Analyze this AEM component file for React conversion:

File path: {file_path}
File type: {file_type} (priority: {priority})
File content:
{file_content}
{type_specific_prompt}

Provide a structured analysis following the required format, with emphasis on React conversion requirements."""

        try:
            result = self.run(prompt, return_structured=True)

            # 如果返回的是结构化对象，转换为字典
            if isinstance(result, FileAnalysisResult):
                return result.model_dump()
            # 如果解析失败，返回原始结果
            elif isinstance(result, str):
                return {
                    "file_path": file_path,
                    "file_type": "unknown",
                    "purpose": "Analysis failed",
                    "dependencies": [],
                    "key_features": [],
                    "configuration": {},
                    "analysis": result
                }
            else:
                return {
                    "file_path": file_path,
                    "analysis": str(result)
                }
        except Exception as e:
            # 如果完全失败，返回错误信息
            return {
                "file_path": file_path,
                "file_type": "unknown",
                "purpose": f"Error: {str(e)}",
                "dependencies": [],
                "key_features": [],
                "configuration": {},
                "analysis": f"Error analyzing file: {str(e)}"
            }
