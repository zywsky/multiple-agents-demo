"""
文件收集 Agent
负责收集 AEM 组件源文件
"""
from langchain_core.tools import tool
from typing import List
from agents.base_agent import BaseAgent
from tools import list_files, read_file, file_exists, get_file_info


@tool
def list_component_files(component_path: str) -> str:
    """列出组件目录下的所有文件（包括子目录）"""
    files = list_files(component_path, recursive=True)
    return "\n".join(files) if files else "No files found"


@tool
def get_file_content(file_path: str) -> str:
    """获取文件内容"""
    return read_file(file_path)


@tool
def check_file_exists(file_path: str) -> str:
    """检查文件是否存在"""
    exists = file_exists(file_path)
    return f"File exists: {exists}"


@tool
def get_file_details(file_path: str) -> str:
    """获取文件详细信息"""
    info = get_file_info(file_path)
    return str(info)


class FileCollectionAgent(BaseAgent):
    """文件收集 Agent"""
    
    def __init__(self):
        tools = [
            list_component_files,
            get_file_content,
            check_file_exists,
            get_file_details
        ]
        
        system_prompt = """You are a file collection agent specialized in AEM components.
Your task is to:
1. List all files in a given AEM component directory (including subdirectories)
2. Read file contents when needed
3. Check file existence
4. Provide file information

When given a component path, you should:
- First list all files in that directory recursively
- Organize the files by type (HTL templates, dialogs, scripts, etc.)
- Return a structured list of all files found

Be thorough and include all files, even configuration files."""
        
        super().__init__(
            name="FileCollectionAgent",
            system_prompt=system_prompt,
            tools=tools
        )
