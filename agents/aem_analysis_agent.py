"""
AEM 分析 Agent
负责分析 AEM 组件源代码
支持结构化输出
"""
from langchain_core.tools import tool
from agents.base_agent import BaseAgent
from tools import read_file, list_files
from utils.schemas import FileAnalysisResult


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
        tools = [
            analyze_htl_file,
            analyze_dialog_file,
            analyze_script_file,
            read_file
        ]
        
        system_prompt = """You are an AEM (Adobe Experience Manager) expert analyst.
Your task is to analyze AEM component source code files one by one.

For each file, you should:
1. Identify the file type (HTL template, dialog XML, Java/JavaScript, CSS, etc.)
2. Analyze the content and functionality
3. Identify dependencies (other components, services, resources)
4. Extract key features and behaviors
5. Note any special configurations or properties
6. Create a summary for each file

IMPORTANT: Process files ONE AT A TIME to avoid token limits.
For each file, provide:
- File type
- Purpose/functionality
- Dependencies and references
- Key features
- Configuration details

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
        
        prompt = f"""Analyze this AEM component file:

File path: {file_path}
File content:
{file_content}

Provide a structured analysis following the required format."""
        
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
