"""
Review Agents - 包含 Security, Build, 和 BDL 三个子 agent
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import read_file, run_command, file_exists


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
        tools = [read_code_file, check_file_exists_tool]
        
        system_prompt = """You are a security expert reviewing React code.
Your task is to identify security vulnerabilities and issues.

Check for:
1. XSS (Cross-Site Scripting) vulnerabilities
2. Injection attacks (SQL, command, etc.)
3. Unsafe API usage
4. Sensitive data exposure
5. Insecure dependencies
6. Authentication/authorization issues
7. CSRF vulnerabilities
8. Unsafe use of dangerouslySetInnerHTML
9. Unsafe URL handling
10. Missing input validation

For each issue found:
- Describe the vulnerability
- Explain the risk
- Suggest fixes

Return a structured review with:
- Issues found (if any)
- Severity level (Critical, High, Medium, Low)
- Recommendations for fixes"""
        
        super().__init__(
            name="SecurityReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1
        )


class BuildReviewAgent(BaseAgent):
    """构建审查 Agent"""
    
    def __init__(self):
        tools = [read_code_file, run_build_command, check_file_exists_tool]
        
        system_prompt = """You are a build and code quality expert.
Your task is to check if the generated React code:
1. Compiles without errors
2. Has no syntax errors
3. Has no type errors (if TypeScript)
4. Has proper imports
5. Has no missing dependencies
6. Follows React best practices
7. Has no runtime errors

You can run build commands to verify compilation.
Analyze the code statically and check build output.

Return a structured review with:
- Build status (success/failure)
- Errors found (if any)
- Warnings (if any)
- Code quality issues
- Recommendations for fixes"""
        
        super().__init__(
            name="BuildReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1
        )


class BDLReviewAgent(BaseAgent):
    """BDL 规范审查 Agent"""
    
    def __init__(self):
        tools = [read_code_file, check_file_exists_tool]
        
        system_prompt = """You are a BDL (company's internal component library) expert.
Your task is to review React code to ensure it follows BDL best practices and conventions.

Check for:
1. Correct BDL component usage (props, API)
2. Proper theme integration
3. Correct styling approach (sx prop, styled components, makeStyles)
4. Component composition best practices
5. Accessibility (a11y) compliance
6. Responsive design implementation
7. BDL component imports are correct
8. Theme customization is appropriate
9. Component variants and sizes are used correctly
10. Icons are imported from correct packages
11. BDL-specific patterns and conventions are followed

Return a structured review with:
- BDL compliance issues (if any)
- Best practice violations
- Recommendations for improvements
- Specific code examples for fixes"""
        
        super().__init__(
            name="BDLReviewAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.1
        )
