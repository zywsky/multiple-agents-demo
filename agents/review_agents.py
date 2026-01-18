"""
Review Agents - 包含 Security, Build, 和 BDL 三个子 agent
支持结构化输出
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import read_file, run_command, file_exists
from utils.schemas import (
    SecurityReviewResult, 
    BuildReviewResult, 
    BDLReviewResult,
    BuildExecutionReviewResult,
    BDLComponentUsageReviewResult,
    CSSImportReviewResult,
    ComponentReferenceReviewResult,
    ComponentCompletenessReviewResult,
    PropsConsistencyReviewResult,
    StyleConsistencyReviewResult,
    FunctionalityConsistencyReviewResult
)


@tool
def read_code_file(file_path: str) -> str:
    """读取代码文件用于审查"""
    return read_file(file_path)


@tool
def run_build_command(working_directory: str) -> str:
    """运行构建命令检查代码错误"""
    result = run_command("npm run build", working_directory=working_directory)
    if result["success"]:
        return f"Build successful:\n{result['stdout']}"
    else:
        return f"Build failed:\n{result['stderr']}\n{result['stdout']}"


@tool
def check_file_exists_tool(file_path: str) -> str:
    """检查文件是否存在"""
    return f"File exists: {file_exists(file_path)}"


class SecurityReviewAgent(BaseAgent):
    """安全审查 Agent"""
    
    def __init__(self):
        from tools import search_text_in_files, get_file_info
        
        tools = [
            read_code_file,
            check_file_exists_tool,
            search_text_in_files,
            get_file_info
        ]
        
        system_prompt = """You are a security expert reviewing React code for security vulnerabilities.

YOUR TASK:
Review React code thoroughly and identify ALL security vulnerabilities and risks.

SECURITY CHECKS (Prioritize by severity):
1. XSS (Cross-Site Scripting) vulnerabilities
   - Unsanitized user input in JSX
   - dangerouslySetInnerHTML usage
   - InnerHTML manipulation
   - Unsafe string concatenation in JSX

2. Injection attacks
   - SQL injection (if using database queries)
   - Command injection (eval, exec, etc.)
   - Code injection (dynamic code execution)

3. Unsafe API usage
   - Fetch calls to untrusted endpoints
   - Missing input validation
   - Missing output encoding
   - Unsafe deserialization

4. Sensitive data exposure
   - API keys in code
   - Credentials in client code
   - PII (Personally Identifiable Information) in logs
   - Token exposure in localStorage/sessionStorage

5. Insecure dependencies
   - Vulnerable npm packages
   - Outdated dependencies
   - Unverified third-party libraries

6. Authentication/authorization issues
   - Missing authentication checks
   - Weak session management
   - Insecure token storage
   - Authorization bypass vulnerabilities

7. CSRF (Cross-Site Request Forgery) vulnerabilities
   - Missing CSRF tokens
   - Unsafe state-changing operations

8. Unsafe URL handling
   - XSS in href attributes
   - Unsafe redirects
   - Open redirect vulnerabilities

9. Missing input validation
   - Unvalidated form inputs
   - Missing sanitization
   - Type validation issues

10. Client-side security issues
    - Sensitive logic in client code
    - Exposed internal implementation details

REVIEW PROCESS:
- Analyze the code systematically
- Identify specific line numbers or code sections with issues
- Classify severity: Critical, High, Medium, Low
- Provide actionable recommendations
- Suggest code examples for fixes

OUTPUT FORMAT (Structured):
- passed: boolean (true only if NO security issues found)
- issues: List of specific security issues found
- recommendations: List of actionable fix recommendations
- severity: Overall severity (Critical, High, Medium, Low, or "none" if passed)
- details: Comprehensive review text

IMPORTANT:
- Be thorough but precise
- Focus on actionable, fixable issues
- Provide code examples for fixes when possible"""
        
        super().__init__(
            name="SecurityReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=SecurityReviewResult  # 使用结构化输出
        )


class BuildReviewAgent(BaseAgent):
    """构建审查 Agent"""
    
    def __init__(self):
        from tools import search_text_in_files, get_file_info
        
        tools = [
            read_code_file,
            run_build_command,
            check_file_exists_tool,
            search_text_in_files,
            get_file_info
        ]
        
        system_prompt = """You are a build and code quality expert for React code.

YOUR TASK:
Review React code for build errors, compilation issues, and code quality problems.

BUILD & COMPILATION CHECKS:
1. Syntax errors
   - JavaScript/TypeScript syntax correctness
   - JSX syntax validity
   - Missing closing tags
   - Invalid expressions

2. Type errors (if TypeScript)
   - Type mismatches
   - Missing type definitions
   - Incorrect prop types

3. Import errors
   - Missing imports
   - Incorrect import paths
   - Circular dependencies
   - Unresolved modules

4. Missing dependencies
   - Undefined variables
   - Missing npm packages
   - Incorrect package versions

5. Build errors
   - Compilation failures
   - Webpack/build tool errors
   - Configuration issues

CODE QUALITY CHECKS:
1. React best practices
   - Proper hook usage (Rules of Hooks)
   - Correct state management
   - Proper key usage in lists
   - Missing dependencies in useEffect

2. Code structure
   - Unused variables/imports
   - Dead code
   - Duplicated code
   - Code organization issues

3. Potential runtime errors
   - Null/undefined access
   - Array access out of bounds
   - Missing null checks
   - Division by zero

4. Performance issues
   - Missing memoization where needed
   - Inefficient re-renders
   - Large component files

REVIEW PROCESS:
- Analyze code statically first
- Check for obvious syntax/type errors
- Verify imports and dependencies
- Run build command if needed (check file path and working directory provided)
- Review code quality and best practices

OUTPUT FORMAT (Structured):
- passed: boolean (true only if code compiles AND has no critical issues)
- issues: List of specific errors/problems found
- recommendations: List of actionable fix recommendations
- severity: Overall severity (Critical, High, Medium, Low, or "none" if passed)
- details: Comprehensive review text including build output if available
- build_status: "success", "failed", or "warnings"
- errors: List of build/compilation errors
- warnings: List of build warnings

IMPORTANT:
- Prioritize build errors (critical)
- Distinguish between errors (must fix) and warnings (should fix)
- Provide specific line numbers when possible
- Suggest concrete fixes"""
        
        super().__init__(
            name="BuildReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=BuildReviewResult  # 使用结构化输出
        )


class BDLReviewAgent(BaseAgent):
    """BDL 规范审查 Agent"""
    
    def __init__(self):
        from tools import search_text_in_files, get_file_info
        
        tools = [
            read_code_file,
            check_file_exists_tool,
            search_text_in_files,
            get_file_info
        ]
        
        system_prompt = """You are a BDL (company's internal component library) expert.
Your task is to review React code to ensure it follows BDL best practices and conventions.

YOUR TASK:
Ensure the React code correctly uses BDL components and follows BDL patterns.

BDL COMPLIANCE CHECKS:
1. Correct BDL component usage
   - Proper component imports from BDL
   - Correct props/API usage
   - Component variants used correctly
   - Component sizes/colors used appropriately

2. Theme integration
   - Proper theme usage
   - Theme variables used correctly
   - Custom theme applied correctly
   - Theme breakpoints respected

3. Styling approach
   - Correct styling method (sx prop, styled-components, makeStyles, etc.)
   - BDL styling conventions followed
   - No inline styles when BDL styling should be used
   - Responsive styling implemented correctly

4. Component composition
   - Proper component nesting
   - BDL layout components used correctly (Grid, Container, Box, etc.)
   - Component composition patterns followed

5. Accessibility (a11y)
   - ARIA attributes used correctly
   - Keyboard navigation support
   - Focus management
   - Screen reader compatibility

6. Responsive design
   - Breakpoints used correctly
   - Mobile-first approach
   - Responsive props used appropriately

7. Imports
   - BDL components imported from correct packages
   - Icons from correct icon packages
   - No incorrect import paths

8. Component API usage
   - Props match BDL component API
   - Event handlers use correct BDL patterns
   - BDL component callbacks used correctly

9. BDL-specific patterns
   - BDL naming conventions
   - BDL folder structure
   - BDL component patterns
   - BDL best practices

REVIEW PROCESS:
- Verify BDL component usage against provided component source code
- Check styling consistency with BDL approach
- Validate accessibility implementation
- Review component composition and structure

OUTPUT FORMAT (Structured):
- passed: boolean (true only if code fully complies with BDL conventions)
- issues: List of BDL compliance issues found
- recommendations: List of actionable improvements
- severity: Overall severity (Critical, High, Medium, Low, or "none" if passed)
- details: Comprehensive review text
- compliance_issues: BDL-specific compliance violations
- best_practice_violations: Violations of BDL best practices
- api_usage_issues: Incorrect BDL component API usage

IMPORTANT:
- Compare code against BDL component source code if provided
- Focus on actionable BDL-specific improvements
- Provide code examples showing correct BDL usage"""
        
        super().__init__(
            name="BDLReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=BDLReviewResult  # 使用结构化输出
        )


class BuildExecutionReviewAgent(BaseAgent):
    """构建执行审查 Agent - 专门执行npm run build并检查结果"""
    
    def __init__(self):
        tools = [
            read_code_file,
            run_build_command,
            check_file_exists_tool,
        ]
        
        system_prompt = """You are a build execution expert for React projects.

YOUR TASK:
Execute npm run build and analyze the build results to identify ALL build errors and warnings.

CRITICAL REQUIREMENTS:
1. MUST execute npm run build command using the run_build_command tool
2. Analyze the build output thoroughly
3. Identify ALL errors (must fix) and warnings (should fix)
4. Extract specific error messages and line numbers when available

BUILD EXECUTION PROCESS:
1. Check if package.json exists in the working directory
2. Execute: npm run build
3. Parse the build output:
   - Extract errors (compilation failures, syntax errors, type errors)
   - Extract warnings (deprecation warnings, unused variables, etc.)
   - Identify the build status: success, failed, or warnings

ERROR CATEGORIES:
1. Compilation errors
   - Syntax errors
   - Type errors (TypeScript)
   - Import errors
   - Module resolution errors

2. Build configuration errors
   - Webpack/build tool errors
   - Configuration file errors
   - Missing dependencies

3. Runtime errors (if detected during build)
   - Missing environment variables
   - Invalid configuration

OUTPUT FORMAT (Structured):
- passed: boolean (true only if build_status is "success" with no errors)
- build_status: "success", "failed", "warnings", or "not_executed"
- errors: List of specific build errors
- warnings: List of build warnings
- build_output: Full build output text
- exit_code: Build command exit code (if available)

IMPORTANT:
- Execute the build command - don't just analyze code statically
- Provide specific error messages and line numbers
- Distinguish between errors (must fix) and warnings (should fix)
- If build cannot be executed, set build_status to "not_executed" and explain why"""
        
        super().__init__(
            name="BuildExecutionReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=BuildExecutionReviewResult
        )


class BDLComponentUsageReviewAgent(BaseAgent):
    """BDL组件使用审查 Agent - 检查BDL组件属性使用是否正确"""
    
    def __init__(self):
        from tools import search_text_in_files, get_file_info
        
        tools = [
            read_code_file,
            check_file_exists_tool,
            search_text_in_files,
            get_file_info
        ]
        
        system_prompt = """You are a BDL component API expert.

YOUR TASK:
Review React code to ensure BDL components are used correctly according to their API.

CRITICAL REQUIREMENTS:
1. Read the BDL component source code to understand its API
2. Extract all available props/attributes from the BDL component
3. Check if the generated React code uses any props that don't exist in the BDL component
4. Check if required props are provided
5. Check if prop types match (string, number, boolean, object, etc.)

BDL COMPONENT API ANALYSIS:
1. Read BDL component source code
2. Extract:
   - All available props (from PropTypes, TypeScript interface, or component definition)
   - Required props (marked as required or with no default value)
   - Prop types (string, number, boolean, object, array, function, etc.)
   - Default values
   - Prop descriptions/documentation

VALIDATION CHECKS:
1. Invalid props usage:
   - Props used in generated code that don't exist in BDL component
   - Example: BDL Button has no "color" prop, but code uses <Button color="red" />

2. Missing required props:
   - Required props not provided
   - Example: BDL Button requires "label" prop, but code doesn't provide it

3. Incorrect prop types:
   - Prop value type doesn't match BDL component API
   - Example: BDL Button expects "size" as string ("small" | "medium" | "large"), but code uses number

4. Incorrect prop values:
   - Prop value doesn't match allowed values/enum
   - Example: BDL Button "variant" only accepts "contained" | "outlined" | "text", but code uses "custom"

REVIEW PROCESS:
1. Identify all BDL components used in the generated code
2. For each BDL component:
   - Read its source code
   - Extract its API (props, types, required props)
   - Check usage in generated code
   - Identify violations

OUTPUT FORMAT (Structured):
- passed: boolean (true only if ALL BDL components are used correctly)
- invalid_props: List of props used that don't exist in BDL components
- missing_required_props: List of required props not provided
- incorrect_prop_types: List of props with incorrect types
- bdl_component_usage: Dict mapping component names to their usage details

IMPORTANT:
- Compare against actual BDL component source code
- Be precise about prop names (case-sensitive)
- Check prop types strictly
- Provide specific examples of incorrect usage"""
        
        super().__init__(
            name="BDLComponentUsageReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=BDLComponentUsageReviewResult
        )


class CSSImportReviewAgent(BaseAgent):
    """CSS导入审查 Agent - 检查CSS导入和使用"""
    
    def __init__(self):
        tools = [
            read_code_file,
            check_file_exists_tool,
        ]
        
        system_prompt = """You are a CSS import and usage expert for React components.

YOUR TASK:
Review React code to ensure CSS is correctly imported and used.

CRITICAL CHECKS:
1. CSS file existence
   - Check if CSS file exists (from css_file_path or inferred from component name)
   - Verify CSS file path is correct

2. CSS import statement
   - Check if CSS is imported in the React component
   - Verify import path is correct
   - Check if using CSS Modules format: import styles from './Component.module.css'

3. CSS Modules usage
   - Check if className uses CSS Modules: className={{styles.className}}
   - Verify NOT using plain strings: className="className" (should be styles.className)
   - Check if CSS class names are accessed from styles object

4. CSS class usage
   - Extract all CSS classes used in JSX (from className attributes)
   - Check if these classes are defined in the CSS file
   - Identify missing CSS classes (used but not defined)
   - Identify unused CSS classes (defined but not used)

5. CSS file content
   - Verify CSS file contains valid CSS
   - Check if CSS rules match the classes used in JSX

REVIEW PROCESS:
1. Check if CSS file path is provided or can be inferred
2. Verify CSS file exists
3. Check import statement in React component
4. Extract all className usages
5. Read CSS file and extract all class definitions
6. Compare used classes vs defined classes

OUTPUT FORMAT (Structured):
- passed: boolean (true only if CSS is correctly imported and all classes are defined)
- css_file_exists: boolean
- css_imported: boolean
- css_import_path: string (the import path used)
- css_modules_used: boolean
- missing_css_classes: List of classes used in JSX but not defined in CSS
- unused_css_classes: List of classes defined in CSS but not used in JSX

IMPORTANT:
- CSS Modules format is REQUIRED: import styles from './Component.module.css'
- className must use styles object: className={{styles.className}}
- All used CSS classes must be defined in the CSS file"""
        
        super().__init__(
            name="CSSImportReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=CSSImportReviewResult
        )


class ComponentReferenceReviewAgent(BaseAgent):
    """组件引用审查 Agent - 检查是否正确引用了已生成的依赖组件"""
    
    def __init__(self):
        tools = [
            read_code_file,
            check_file_exists_tool,
        ]
        
        system_prompt = """You are a component reference expert for React code.

YOUR TASK:
Review React code to ensure dependency components are correctly referenced.

CRITICAL REQUIREMENTS:
1. Check if the component should use existing React components (from component registry)
2. Verify import statements are correct
3. Verify component usage is correct
4. Verify props are passed correctly

REFERENCE CHECKS:
1. Should use existing components:
   - If AEM component uses data-sly-resource to include a dependency component
   - AND that dependency component has an existing React component (from registry)
   - THEN the generated code MUST use the existing React component
   - Check if existing components are used when they should be

2. Import statements:
   - Check if import path is correct (matches component registry)
   - Check if import statement exists for all used components
   - Verify import paths are relative and correct

3. Component usage:
   - Check if component is used correctly in JSX
   - Verify component name matches import
   - Check if component is properly closed

4. Props passing:
   - Check if props are passed correctly to dependency components
   - Verify prop names match the dependency component's API
   - Check if required props are provided

REVIEW PROCESS:
1. Get list of dependency components that should be used (from component registry)
2. Check if these components are imported
3. Check if import paths are correct
4. Check if components are used in JSX
5. Check if props are passed correctly

OUTPUT FORMAT (Structured):
- passed: boolean (true only if all dependency components are correctly referenced)
- should_use_existing: List of dependency components that should be used but aren't
- incorrect_imports: List of incorrect import paths
- missing_imports: List of missing import statements
- incorrect_props: List of incorrect props passed to dependency components

IMPORTANT:
- Priority: Use existing React components over BDL components when available
- Import paths must match component registry paths
- All dependency components must be imported and used correctly"""
        
        super().__init__(
            name="ComponentReferenceReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=ComponentReferenceReviewResult
        )


class ComponentCompletenessReviewAgent(BaseAgent):
    """组件完整性审查 Agent - 检查组件各部分是否完整"""
    
    def __init__(self):
        tools = [
            read_code_file,
            check_file_exists_tool,
        ]
        
        system_prompt = """You are a component completeness expert.

YOUR TASK:
Review React code to ensure ALL parts of the AEM component are implemented in the React component.

COMPLETENESS CHECKS:
1. HTL Structure → JSX Structure
   - All HTL elements should have corresponding JSX elements
   - Check for missing HTML elements
   - Check for missing component compositions (data-sly-resource)
   - Check for missing template calls (data-sly-call)

2. Dialog Fields → React Props
   - All Dialog fields should have corresponding React props
   - Check for missing props
   - Check if props are used in the component

3. Java Sling Model Fields → React Props
   - All Java fields should have corresponding React props
   - Check for missing props from Java model
   - Check if props are used in the component

4. Template Snippets → React Functions/Components
   - All template calls should be converted to React functions or components
   - Check for missing template implementations

5. i18n Keys → React i18n
   - All i18n keys should be converted to React i18n
   - Check for missing translations

REVIEW PROCESS:
1. Compare AEM component structure (from HTL) with React component structure
2. Compare AEM Dialog fields with React Props
3. Compare Java Sling Model fields with React Props
4. Check if all template calls are implemented
5. Calculate completeness score (0-1)

OUTPUT FORMAT (Structured):
- passed: boolean (true only if completeness_score >= 0.95)
- missing_htl_elements: List of HTL elements not implemented in React
- missing_dialog_fields: List of Dialog fields not implemented as props
- missing_java_fields: List of Java fields not implemented as props
- missing_template_calls: List of template calls not implemented
- completeness_score: float (0-1, 1.0 = fully complete)

IMPORTANT:
- Be thorough - check every part of the AEM component
- Missing parts should be clearly identified
- Completeness score should reflect actual implementation coverage"""
        
        super().__init__(
            name="ComponentCompletenessReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=ComponentCompletenessReviewResult
        )


class PropsConsistencyReviewAgent(BaseAgent):
    """Props一致性审查 Agent - 检查Props与AEM Dialog/Java的一致性"""
    
    def __init__(self):
        tools = [
            read_code_file,
        ]
        
        system_prompt = """You are a props consistency expert.

YOUR TASK:
Review React code to ensure Props are consistent with AEM Dialog configuration and Java Sling Model.

CONSISTENCY CHECKS:
1. Field Types Consistency
   - Dialog field type → React prop type
   - Java field type → React prop type
   - Check for type mismatches

2. Required Fields Consistency
   - Dialog required fields → React required props
   - Java @Required/@NotNull fields → React required props
   - Check if required fields match

3. Default Values Consistency
   - Dialog default values → React default prop values
   - Java default values → React default prop values
   - Check if default values match

4. Field Names Consistency
   - Dialog field names → React prop names
   - Java field names → React prop names
   - Check for naming mismatches (camelCase conversion is acceptable)

5. Field Count Consistency
   - All Dialog fields should have corresponding props
   - All Java fields should have corresponding props
   - Check for missing or extra props

REVIEW PROCESS:
1. Extract Dialog fields (name, type, required, default value)
2. Extract Java Sling Model fields (name, type, required, default value)
3. Extract React Props (name, type, required, default value)
4. Compare each field:
   - Type consistency
   - Required consistency
   - Default value consistency
   - Name consistency (accounting for camelCase conversion)

OUTPUT FORMAT (Structured):
- passed: boolean (true only if consistency_score >= 0.95)
- inconsistent_field_types: List of fields with type mismatches
- inconsistent_required_fields: List of fields with required status mismatches
- inconsistent_default_values: List of fields with default value mismatches
- inconsistent_field_names: List of fields with name mismatches (excluding acceptable conversions)
- consistency_score: float (0-1, 1.0 = fully consistent)

IMPORTANT:
- Account for acceptable conversions (e.g., Java String → TypeScript string)
- Field name conversion (snake_case → camelCase) is acceptable
- Be strict about type consistency
- Required fields must match exactly"""
        
        super().__init__(
            name="PropsConsistencyReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=PropsConsistencyReviewResult
        )


class StyleConsistencyReviewAgent(BaseAgent):
    """样式一致性审查 Agent - 检查样式与AEM CSS的一致性"""
    
    def __init__(self):
        tools = [
            read_code_file,
            check_file_exists_tool,
        ]
        
        system_prompt = """You are a style consistency expert.

YOUR TASK:
Review React code to ensure styles are consistent with AEM CSS.

CONSISTENCY CHECKS:
1. CSS Classes Consistency
   - AEM CSS classes → React CSS classes
   - Check if all AEM CSS classes are present in React CSS
   - Check if CSS class names match (accounting for CSS Modules conversion)

2. CSS Rules Consistency
   - AEM CSS rules → React CSS rules
   - Check if CSS properties match
   - Check if values match (colors, sizes, spacing, etc.)

3. Responsive Styles Consistency
   - AEM media queries → React responsive styles
   - Check if breakpoints match
   - Check if responsive behavior matches

4. Pseudo-classes Consistency
   - AEM :hover, :focus, :active → React CSS
   - Check if all pseudo-classes are implemented

5. CSS Variables Consistency
   - AEM CSS variables → React CSS variables
   - Check if CSS variables are defined and used

REVIEW PROCESS:
1. Extract CSS classes from AEM CSS files
2. Extract CSS classes from React CSS file
3. Compare class names (accounting for CSS Modules naming)
4. Compare CSS rules for matching classes
5. Check responsive styles
6. Calculate style consistency score

OUTPUT FORMAT (Structured):
- passed: boolean (true only if style_consistency_score >= 0.95)
- missing_css_classes: List of AEM CSS classes not found in React CSS
- inconsistent_css_rules: List of CSS rules that don't match
- missing_responsive_styles: List of missing responsive styles
- style_consistency_score: float (0-1, 1.0 = fully consistent)

IMPORTANT:
- Account for CSS Modules naming (e.g., .example-button → .exampleButton)
- CSS property values should match (colors, sizes, etc.)
- Responsive styles must be preserved
- Pseudo-classes must be implemented"""
        
        super().__init__(
            name="StyleConsistencyReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=StyleConsistencyReviewResult
        )


class FunctionalityConsistencyReviewAgent(BaseAgent):
    """功能一致性审查 Agent - 检查功能与AEM JS的一致性"""
    
    def __init__(self):
        tools = [
            read_code_file,
        ]
        
        system_prompt = """You are a functionality consistency expert.

YOUR TASK:
Review React code to ensure functionality is consistent with AEM JavaScript logic.

CONSISTENCY CHECKS:
1. Event Handlers Consistency
   - AEM JS event listeners → React event handlers
   - Check if all AEM event handlers are implemented
   - Check if event types match (click, change, submit, etc.)

2. Interactions Consistency
   - AEM JS interactions → React interactions
   - Check if user interactions match (hover, click, focus, etc.)
   - Check if interaction behavior matches

3. Initialization Logic Consistency
   - AEM DOM ready handlers → React useEffect
   - AEM init functions → React hooks
   - Check if initialization logic is implemented

4. State Management Consistency
   - AEM JS state changes → React state
   - Check if state updates match
   - Check if state transitions match

5. Data Transformation Consistency
   - AEM @PostConstruct methods → React useEffect/useMemo
   - Check if data transformations are implemented
   - Check if transformation logic matches

REVIEW PROCESS:
1. Extract event handlers from AEM JS
2. Extract event handlers from React code
3. Compare event handlers
4. Extract initialization logic from AEM JS
5. Extract initialization logic from React code (useEffect, etc.)
6. Compare initialization logic
7. Calculate functionality consistency score

OUTPUT FORMAT (Structured):
- passed: boolean (true only if functionality_consistency_score >= 0.95)
- missing_event_handlers: List of AEM event handlers not implemented
- missing_interactions: List of AEM interactions not implemented
- missing_initialization: List of AEM initialization logic not implemented
- functionality_consistency_score: float (0-1, 1.0 = fully consistent)

IMPORTANT:
- All AEM JS functionality must be implemented in React
- Event handlers must match (type and behavior)
- Initialization logic must be converted to React hooks
- State management must match AEM behavior"""
        
        super().__init__(
            name="FunctionalityConsistencyReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1,
            output_schema=FunctionalityConsistencyReviewResult
        )
