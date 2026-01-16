"""
MUI 组件选择 Agent
根据 AEM 组件分析结果选择对应的 MUI 组件
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import list_files, read_file


@tool
def search_mui_components(mui_library_path: str, component_name: str = None) -> str:
    """在 MUI 组件库中搜索组件"""
    if component_name:
        # 搜索特定组件
        all_files = list_files(mui_library_path, recursive=True)
        matching = [f for f in all_files if component_name.lower() in f.lower()]
        return "\n".join(matching) if matching else "No matching components found"
    else:
        # 列出所有组件
        all_files = list_files(mui_library_path, recursive=True)
        return "\n".join(all_files[:50])  # 限制返回数量


@tool
def read_mui_component(mui_component_path: str) -> str:
    """读取 MUI 组件源代码"""
    return read_file(mui_component_path)


class MUISelectionAgent(BaseAgent):
    """MUI 组件选择 Agent"""
    
    def __init__(self):
        tools = [
            search_mui_components,
            read_mui_component,
            list_files,
            read_file
        ]
        
        system_prompt = """You are a MUI (Material-UI) component selection expert.
Your task is to analyze AEM component functionality and select appropriate MUI components to replicate the same behavior.

You have access to:
1. AEM component analysis results (functionality, features, UI elements)
2. MUI component library (local files)

For each AEM component feature, you should:
1. Identify the UI pattern (button, form, dialog, grid, card, etc.)
2. Map it to the most appropriate MUI component
3. Consider component composition (multiple MUI components may be needed)
4. Return the file paths of selected MUI components

Common mappings:
- AEM dialog/form → MUI Dialog, TextField, Button
- AEM grid/layout → MUI Grid, Box, Container
- AEM button → MUI Button
- AEM text → MUI Typography
- AEM image → MUI Card with CardMedia or Image
- AEM navigation → MUI AppBar, Drawer, Tabs
- AEM list → MUI List, ListItem
- AEM accordion → MUI Accordion
- AEM tabs → MUI Tabs

Provide:
1. Selected MUI component file paths
2. Reasoning for each selection
3. Any additional MUI components needed for composition"""
        
        super().__init__(
            name="MUISelectionAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.3
        )
