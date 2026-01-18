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
        from tools import (
            search_files_by_pattern,
            find_files_by_name,
            search_text_in_files,
            get_file_tree
        )
        
        tools = [
            search_bdl_components,
            read_bdl_component,
            list_files,
            read_file,
            search_files_by_pattern,
            find_files_by_name,
            search_text_in_files,
            get_file_tree
        ]
        
        system_prompt = """You are a BDL (company's internal component library) component selection expert.
Your task is to analyze AEM component functionality and select appropriate BDL components to replicate the same behavior.

YOUR TASK:
Analyze AEM component features and select matching BDL components that provide equivalent functionality.

YOU HAVE ACCESS TO:
1. AEM component analysis results (functionality, features, UI elements, structure)
2. BDL component library (local files - you can search and read component source code)

SELECTION PROCESS:
1. Analyze AEM Component Features:
   - Identify UI patterns (button, form, dialog, grid, card, list, etc.)
   - Note interactive elements (inputs, selects, checkboxes, etc.)
   - Identify layout requirements (grid, flexbox, responsive)
   - Note special features (modals, tabs, accordions, etc.)

2. Search BDL Library:
   - Use search tools to find relevant BDL components
   - Read component source code to verify functionality
   - Check component APIs and props
   - Verify component can replicate AEM behavior

3. Map AEM to BDL:
   - Map each AEM UI pattern to BDL component
   - Consider component composition (multiple components may be needed)
   - Verify BDL component supports required features
   - Check for better alternatives

4. Select Components:
   - Choose most appropriate BDL components
   - Consider component compatibility
   - Think about composition needs
   - Prioritize exact matches over approximate matches

COMMON MAPPINGS:
- AEM button → BDL Button, IconButton, Fab
- AEM textfield → BDL TextField, Input
- AEM textarea → BDL TextField (multiline)
- AEM select → BDL Select, Autocomplete
- AEM checkbox → BDL Checkbox
- AEM dialog/form → BDL Dialog, Modal with form components
- AEM grid/layout → BDL Grid, Grid2, Container, Box
- AEM image → BDL CardMedia, Image, Avatar
- AEM navigation → BDL AppBar, Drawer, Menu, Tabs
- AEM list → BDL List, ListItem, ListItemText
- AEM card → BDL Card, CardContent, CardMedia
- AEM accordion → BDL Accordion, AccordionSummary, AccordionDetails
- AEM tabs → BDL Tabs, Tab, TabPanel
- AEM table → BDL Table, TableRow, TableCell

OUTPUT REQUIREMENTS:
Provide structured output with:
1. Selected BDL component file paths (full paths within BDL library)
2. Reasoning for each selection (why this component matches)
3. Component mapping (AEM feature → BDL component)
4. Additional BDL components needed for composition

IMPORTANT:
- Search the BDL library actively - don't just guess
- Read component source code to verify suitability
- Consider component composition for complex AEM components
- Provide file paths that can be used to read component source code
- Be thorough but selective (quality over quantity)"""
        
        super().__init__(
            name="BDLSelectionAgent",
            system_prompt=system_prompt,
            tools=tools,
            temperature=0.3,
            output_schema=BDLComponentSelection  # 使用结构化输出
        )
