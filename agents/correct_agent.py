"""
代码修正 Agent
根据 review 结果修正代码
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import read_file, write_file


@tool
def read_code_for_correction(file_path: str) -> str:
    """读取需要修正的代码文件"""
    return read_file(file_path)


@tool
def write_corrected_code(file_path: str, code: str) -> str:
    """写入修正后的代码"""
    return write_file(file_path, code)


class CorrectAgent(BaseAgent):
    """代码修正 Agent"""
    
    def __init__(self):
        tools = [
            read_code_for_correction,
            write_corrected_code
        ]
        
        system_prompt = """You are a code correction expert.
Your task is to fix issues identified by review agents.

You will receive:
1. The original code
2. Review results from Security, Build, and BDL review agents
3. Specific issues and recommendations

You should:
1. Address all critical and high-severity issues first
2. Fix build errors and compilation issues
3. Correct security vulnerabilities
4. Fix BDL usage and best practice violations
5. Maintain the original functionality
6. Ensure code quality and readability

For each fix:
- Explain what you changed
- Ensure the fix doesn't break existing functionality
- Follow the recommendations from review agents

Output the corrected code with clear explanations of changes made."""
        
        super().__init__(
            name="CorrectAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.2
        )
