"""
文件上下文构建工具
为每个 AEM 文件提供清晰的说明和上下文信息，帮助 LLM 更好地理解文件作用
"""
from typing import Dict, List, Any
from utils.aem_utils import identify_aem_file_type


def get_file_description(file_type: str, file_path: str) -> str:
    """
    为文件生成清晰的描述说明
    
    Args:
        file_type: 文件类型
        file_path: 文件路径
    
    Returns:
        文件描述文本
    """
    descriptions = {
        'htl': """HTL (HTML Template Language) Template File
Purpose: This file defines the UI structure and presentation logic of the AEM component.
What it contains:
- HTML structure with HTL-specific attributes (data-sly-*)
- Data binding expressions
- Conditional rendering logic
- Iteration patterns (data-sly-repeat)
- Component composition (data-sly-resource)
- Event handlers and interactions

Conversion importance: CRITICAL - This is the primary source for React JSX structure.
React equivalent: The JSX structure in your React component should mirror this HTL structure.""",

        'html': """HTML/HTL Template File
Purpose: Same as HTL template - defines component UI structure.
Note: May use HTL features or plain HTML with AEM includes.""",

        'dialog': """AEM Dialog Configuration File (_cq_dialog.xml)
Purpose: Defines the authoring dialog shown in AEM authoring mode.
What it contains:
- Property field definitions (textfields, textareas, selects, checkboxes, etc.)
- Field types, labels, and descriptions
- Required vs optional fields
- Default values
- Field groups and tabs
- Validation rules

Conversion importance: CRITICAL - This directly maps to React component Props interface.
React equivalent: Each field in the dialog becomes a prop in your React component.
Mapping: 
  - textfield → string prop
  - textarea → string prop
  - select → enum/string prop
  - checkbox → boolean prop
  - numberfield → number prop
  - pathfield → string prop (path)""",

        'js': """JavaScript Client-Side Logic File
Purpose: Handles client-side interactions, DOM manipulations, and user events.
What it contains:
- Event handlers (click, change, submit, etc.)
- DOM queries and manipulations
- Form validations
- API calls or data fetching
- Component lifecycle logic
- Third-party library integrations

Conversion importance: IMPORTANT - This maps to React hooks and event handlers.
React equivalent:
  - DOM queries → useRef or useState
  - Event handlers → React event handlers (onClick, onChange, etc.)
  - DOM manipulations → React state updates
  - Data fetching → useEffect + fetch/axios
  - Component lifecycle → useEffect hooks""",

        'config': """AEM Component Configuration File (.content.xml or cq:*)
Purpose: Defines component metadata, allowed parents, allowed children, and policies.
What it contains:
- Component resource type
- Allowed parent components
- Allowed child components
- Component groups
- Policy configurations

Conversion importance: LOW-MEDIUM - Used for understanding component relationships and constraints.
React equivalent: Documentation or prop types about component composition rules.""",

        'java': """Java Sling Model Class
Purpose: Defines the data model and business logic (server-side).
What it contains:
- Properties exposed to HTL templates
- Business logic methods
- Data fetching and processing
- Service injections
- Validation logic

Conversion importance: HIGH - Understanding data structure is important, but will be provided later.
React equivalent: The data structure (props/state shape) your React component expects.
Note: The HTL template's data-sly-use attribute tells you which model properties are used.""",

        'css': """CSS Stylesheet File
Purpose: Defines component styling and visual appearance.
What it contains:
- CSS classes and selectors
- Layout styles (flexbox, grid, positioning)
- Responsive breakpoints
- Theme variables
- Component-specific styles

Conversion importance: LOW (for initial conversion) - Styling will be handled separately.
React equivalent: CSS-in-JS, styled-components, or CSS modules (depending on BDL conventions).
Note: Focus on structure first, styling can be added after.""",
    }
    
    return descriptions.get(file_type, f"Unknown file type: {file_type}")


def build_file_context(file_analysis: Dict[str, Any]) -> str:
    """
    为文件分析结果构建上下文信息
    
    Args:
        file_analysis: 文件分析结果字典
    
    Returns:
        格式化的上下文信息
    """
    file_path = file_analysis.get('file_path', 'unknown')
    file_type = file_analysis.get('file_type', 'unknown')
    purpose = file_analysis.get('purpose', 'N/A')
    
    description = get_file_description(file_type, file_path)
    
    context = f"""
=== FILE CONTEXT ===
File: {file_path}
Type: {file_type}
Description:
{description}

Purpose: {purpose}

Key Information:
"""
    
    # 添加关键特性
    key_features = file_analysis.get('key_features', [])
    if key_features:
        context += f"- Key Features: {', '.join(key_features)}\n"
    
    # 添加依赖
    dependencies = file_analysis.get('dependencies', [])
    if dependencies:
        context += f"- Dependencies: {', '.join(dependencies)}\n"
    
    # 添加配置信息（如果是 dialog）
    if file_type == 'dialog':
        config = file_analysis.get('configuration', {})
        if config:
            context += f"- Configuration Details: {config}\n"
    
    # 添加转换说明
    context += "\n=== CONVERSION NOTES ===\n"
    
    if file_type == 'htl':
        context += "- Maintain exact HTML structure in JSX\n"
        context += "- Convert data-sly-* attributes to React patterns\n"
        context += "- Map Sling Model properties to React props/state\n"
    elif file_type == 'dialog':
        context += "- Each dialog field → React prop\n"
        context += "- Required fields → required props\n"
        context += "- Default values → default prop values\n"
    elif file_type == 'js':
        context += "- Event handlers → React event handlers\n"
        context += "- DOM operations → React state/refs\n"
        context += "- Data fetching → useEffect hooks\n"
    
    return context


def build_comprehensive_context(file_analyses: List[Dict[str, Any]]) -> str:
    """
    为所有文件构建综合上下文
    
    Args:
        file_analyses: 文件分析结果列表
    
    Returns:
        综合上下文信息
    """
    contexts = []
    
    for analysis in file_analyses:
        context = build_file_context(analysis)
        contexts.append(context)
    
    return "\n\n".join(contexts)


def enhance_code_generation_prompt(
    file_analyses: List[Dict[str, Any]],
    base_prompt: str
) -> str:
    """
    增强代码生成 prompt，添加文件上下文说明
    
    Args:
        file_analyses: 文件分析结果列表
        base_prompt: 基础 prompt
    
    Returns:
        增强后的 prompt
    """
    # 为每个文件添加上下文
    file_contexts = []
    
    for analysis in file_analyses:
        file_type = analysis.get('file_type', 'unknown')
        file_path = analysis.get('file_path', 'unknown')
        description = get_file_description(file_type, file_path)
        
        file_contexts.append(f"""
File: {file_path} ({file_type})
{description}
Purpose: {analysis.get('purpose', 'N/A')}
""")
    
    contexts_section = "\n".join(file_contexts)
    
    enhanced_prompt = f"""{base_prompt}

=== FILE CONTEXTS AND THEIR ROLES ===
Each file in the AEM component serves a specific purpose. Understanding these roles is crucial for accurate conversion:

{contexts_section}

=== KEY CONVERSION PRINCIPLES ===
1. HTL Template → React JSX Structure (1:1 mapping of HTML elements)
2. Dialog Fields → React Props Interface (direct mapping)
3. JavaScript Logic → React Hooks & Event Handlers
4. Data-sly-use → React Props/State
5. Data-sly-repeat → Array.map()
6. Data-sly-test → Conditional rendering

Remember: The HTL template shows you WHAT to render, the Dialog shows you WHAT data is available, and the JS shows you HOW users interact with it.
"""
    
    return enhanced_prompt
