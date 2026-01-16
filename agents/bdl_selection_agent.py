"""
BDL 组件选择 Agent
根据 AEM 组件分析结果选择对应的 BDL 组件
支持结构化输出
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import list_files, read_file
from utils.schemas import BDLComponentSelection


@tool
def search_bdl_components(bdl_library_path: str, component_name: str = None) -> str:
    """在 BDL 组件库中搜索组件"""
    if component_name:
        # 搜索特定组件
        all_files = list_files(bdl_library_path, recursive=True)
        matching = [f for f in all_files if component_name.lower() in f.lower()]
        return "\n".join(matching) if matching else "No matching components found"
    else:
        # 列出所有组件
        all_files = list_files(bdl_library_path, recursive=True)
        return "\n".join(all_files[:50])  # 限制返回数量


@tool
def read_bdl_component(bdl_component_path: str) -> str:
    """读取 BDL 组件源代码"""
    return read_file(bdl_component_path)


class BDLSelectionAgent(BaseAgent):
    """BDL 组件选择 Agent"""
    
    def __init__(self):
        tools = [
            search_bdl_components,
            read_bdl_component,
            list_files,
            read_file
        ]
        
        system_prompt = """You are a BDL (company's internal component library) component selection expert.
Your task is to analyze AEM component functionality and select appropriate BDL components to replicate the same behavior.

You have access to:
1. AEM component analysis results (functionality, features, UI elements)
2. BDL component library (local files)

For each AEM component feature, you should:
1. Identify the UI pattern (button, form, dialog, grid, card, etc.)
2. Map it to the most appropriate BDL component
3. Consider component composition (multiple BDL components may be needed)
4. Return the file paths of selected BDL components

Common mappings:
- AEM dialog/form → BDL Dialog, TextField, Button
- AEM grid/layout → BDL Grid, Box, Container
- AEM button → BDL Button
- AEM text → BDL Typography
- AEM image → BDL Card with CardMedia or Image
- AEM navigation → BDL AppBar, Drawer, Tabs
- AEM list → BDL List, ListItem
- AEM accordion → BDL Accordion
- AEM tabs → BDL Tabs

Provide:
1. Selected BDL component file paths
2. Reasoning for each selection
3. Any additional BDL components needed for composition"""
        
        super().__init__(
            name="BDLSelectionAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.3,
            output_schema=BDLComponentSelection  # 使用结构化输出
        )
