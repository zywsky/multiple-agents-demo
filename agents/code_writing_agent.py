"""
代码编写 Agent
根据 AEM 源代码和选定的 MUI 组件生成 React 代码
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import read_file, write_file, create_directory


@tool
def read_source_code(file_path: str) -> str:
    """读取源代码文件"""
    return read_file(file_path)


@tool
def write_react_component(file_path: str, code: str) -> str:
    """写入 React 组件代码到文件"""
    return write_file(file_path, code)


@tool
def create_component_directory(directory_path: str) -> str:
    """创建组件目录"""
    return create_directory(directory_path)


class CodeWritingAgent(BaseAgent):
    """代码编写 Agent"""
    
    def __init__(self):
        tools = [
            read_source_code,
            write_react_component,
            create_component_directory
        ]
        
        system_prompt = """You are an expert React and MUI developer.
Your task is to convert AEM HTL components to React components using MUI.

Given:
1. AEM component source code (HTL templates, dialogs, scripts)
2. Selected MUI components and their source code
3. Component analysis results

You should:
1. Create a React functional component that replicates the AEM component functionality
2. Use the selected MUI components appropriately
3. Follow React best practices (hooks, props, state management)
4. Follow MUI best practices (theme, styling, component composition)
5. Maintain the same UI/UX behavior as the original AEM component
6. Handle props, state, and events appropriately
7. Include proper TypeScript types if applicable
8. Add necessary imports

Code requirements:
- Use functional components with hooks
- Proper prop types/interfaces
- Clean, readable code
- Follow MUI component API correctly
- Handle edge cases
- Include comments for complex logic

Output the complete React component code."""
        
        super().__init__(
            name="CodeWritingAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.2
        )
