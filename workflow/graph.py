"""
LangGraph 工作流定义
"""
from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import operator
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from agents import (
    FileCollectionAgent,
    AEMAnalysisAgent,
    BDLSelectionAgent,
    CodeWritingAgent,
    SecurityReviewAgent,
    BuildReviewAgent,
    BDLReviewAgent,
    CorrectAgent
)


class WorkflowState(TypedDict):
    """工作流状态"""
    resource_type: str  # AEM component resourceType (relative path)
    aem_repo_path: str  # AEM repository root path
    component_path: str  # Full path to component (aem_repo_path + resource_type)
    bdl_library_path: str  # BDL library root path
    output_path: str
    files: List[str]
    file_analyses: List[Dict[str, Any]]
    selected_bdl_components: List[str]
    generated_code: str
    code_file_path: str
    review_results: Dict[str, Any]
    review_passed: bool
    iteration_count: int
    max_iterations: int
    messages: Annotated[List, add_messages]


def create_workflow_graph():
    """创建工作流图"""
    
    # 延迟初始化 agents（在节点函数中初始化，避免在创建图时就失败）
    agents = {}
    
    def _get_agent(agent_class, agent_name):
        """获取或创建 agent（单例模式）"""
        if agent_name not in agents:
            try:
                agents[agent_name] = agent_class()
            except ValueError as e:
                logger.error(f"Failed to initialize {agent_name}: {str(e)}")
                raise
        return agents[agent_name]
    
    # 定义节点函数
    def collect_files(state: WorkflowState) -> WorkflowState:
        """步骤1: 收集文件"""
        component_path = state["component_path"]
        logger.info(f"Collecting files from: {component_path}")
        
        try:
            # 使用工具直接列出文件（更可靠）
            from tools import list_files
            files = list_files(component_path, recursive=True)
            
            if not files:
                logger.warning(f"No files found in component path: {component_path}")
                # 尝试使用 agent 作为备用
                file_collection_agent = _get_agent(FileCollectionAgent, "file_collection")
                prompt = f"List all files in the AEM component directory: {component_path}"
                result = file_collection_agent.run(prompt)
                files = [f.strip() for f in result.split("\n") if f.strip() and not f.startswith("Error")]
            
            logger.info(f"Found {len(files)} files")
            
            if len(files) == 0:
                raise ValueError(f"No files found in component directory: {component_path}")
            
            return {
                **state,
                "files": files
            }
        except Exception as e:
            logger.error(f"Error collecting files: {str(e)}")
            raise  # 重新抛出异常，让工作流知道失败
    
    def analyze_aem_files(state: WorkflowState) -> WorkflowState:
        """步骤2: 分析 AEM 文件（逐个处理）"""
        files = state["files"]
        file_analyses = []
        
        logger.info(f"Analyzing {len(files)} files...")
        
        # 逐个文件分析，避免 token 超限
        aem_analysis_agent = _get_agent(AEMAnalysisAgent, "aem_analysis")
        for i, file_path in enumerate(files, 1):
            try:
                logger.info(f"Analyzing file {i}/{len(files)}: {file_path}")
                analysis = aem_analysis_agent.analyze_file(file_path)
                file_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {str(e)}")
                file_analyses.append({
                    "file_path": file_path,
                    "analysis": f"Error: {str(e)}"
                })
        
        logger.info(f"Completed analysis of {len(file_analyses)} files")
        
        return {
            **state,
            "file_analyses": file_analyses
        }
    
    def select_bdl_components(state: WorkflowState) -> WorkflowState:
        """步骤3: 选择 BDL 组件"""
        bdl_library_path = state["bdl_library_path"]
        file_analyses = state["file_analyses"]
        
        if not file_analyses:
            logger.error("No file analyses available for BDL component selection")
            return {
                **state,
                "selected_bdl_components": []
            }
        
        # 构建分析摘要
        analysis_summary = "\n\n".join([
            f"File: {fa.get('file_path', 'unknown')}\nAnalysis: {fa.get('analysis', 'No analysis')}"
            for fa in file_analyses
        ])
        
        prompt = f"""Based on the following AEM component analysis, select appropriate BDL components:

{analysis_summary}

BDL library path: {bdl_library_path}

Select BDL components and return their file paths."""
        
        try:
            bdl_selection_agent = _get_agent(BDLSelectionAgent, "bdl_selection")
            result = bdl_selection_agent.run(prompt)
            
            # 提取组件路径（更智能的解析）
            selected_components = []
            for line in result.split("\n"):
                line = line.strip()
                if not line or line.startswith("Error"):
                    continue
                # 检查是否包含路径特征或组件名称
                if ("bdl" in line.lower() or "component" in line.lower() or 
                    "/" in line or "\\" in line or line.endswith((".tsx", ".ts", ".jsx", ".js"))):
                    selected_components.append(line)
            
            logger.info(f"Selected {len(selected_components)} BDL components")
            
            return {
                **state,
                "selected_bdl_components": selected_components
            }
        except Exception as e:
            logger.error(f"Error selecting BDL components: {str(e)}")
            return {
                **state,
                "selected_bdl_components": []
            }
    
    def write_code(state: WorkflowState) -> WorkflowState:
        """步骤4: 编写代码"""
        file_analyses = state["file_analyses"]
        selected_bdl_components = state.get("selected_bdl_components", [])
        output_path = state.get("output_path", "./output")
        resource_type = state.get("resource_type", "unknown")
        
        if not file_analyses:
            logger.error("No file analyses available for code generation")
            raise ValueError("Cannot generate code without file analyses")
        
        # 构建提示
        analysis_summary = "\n\n".join([
            f"File: {fa.get('file_path', 'unknown')}\nAnalysis: {fa.get('analysis', 'No analysis')}"
            for fa in file_analyses
        ])
        
        bdl_components_info = "\n".join(selected_bdl_components) if selected_bdl_components else "No BDL components selected"
        
        # 从 resourceType 提取组件名称
        component_name = resource_type.split("/")[-1] if "/" in resource_type else resource_type.split(".")[-1]
        component_name = component_name.title().replace("_", "")  # 转换为 PascalCase
        
        prompt = f"""Generate a React component using BDL based on:

AEM Component ResourceType: {resource_type}
AEM Component Analysis:
{analysis_summary}

Selected BDL Components:
{bdl_components_info}

Output path: {output_path}
Component name: {component_name}

Generate the complete React component code following BDL conventions."""
        
        try:
            code_writing_agent = _get_agent(CodeWritingAgent, "code_writing")
            result = code_writing_agent.run(prompt)
            
            # 提取生成的代码
            generated_code = result
            
            # 生成文件路径（跨平台）
            from pathlib import Path
            output_path_obj = Path(output_path)
            output_path_obj.mkdir(parents=True, exist_ok=True)
            code_file_path = str(output_path_obj / f"{component_name}.jsx")
            
            logger.info(f"Code generated, saving to: {code_file_path}")
            
            return {
                **state,
                "generated_code": generated_code,
                "code_file_path": code_file_path
            }
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise
    
    def review_code(state: WorkflowState) -> WorkflowState:
        """步骤5: 审查代码（使用 subagents）"""
        code_file_path = state["code_file_path"]
        generated_code = state["generated_code"]
        output_path = state.get("output_path", "./output")
        iteration = state.get("iteration_count", 0)
        
        logger.info(f"Reviewing code (iteration {iteration})...")
        
        # 先写入代码文件（如果还没有）
        if generated_code:
            try:
                from tools import write_file
                write_file(code_file_path, generated_code)
                logger.info(f"Code written to: {code_file_path}")
            except Exception as e:
                logger.error(f"Error writing code file: {str(e)}")
        
        # 运行三个 review subagents
        security_review_agent = _get_agent(SecurityReviewAgent, "security_review")
        build_review_agent = _get_agent(BuildReviewAgent, "build_review")
        bdl_review_agent = _get_agent(BDLReviewAgent, "bdl_review")
        
        try:
            logger.info("Running security review...")
            security_prompt = f"Review this React code for security issues:\n\n{generated_code}"
            security_result = security_review_agent.run(security_prompt)
        except Exception as e:
            logger.error(f"Error in security review: {str(e)}")
            security_result = f"Error: {str(e)}"
        
        try:
            logger.info("Running build review...")
            build_prompt = f"Review this React code for build errors:\n\nCode file: {code_file_path}\nWorking directory: {output_path}"
            build_result = build_review_agent.run(build_prompt)
        except Exception as e:
            logger.error(f"Error in build review: {str(e)}")
            build_result = f"Error: {str(e)}"
        
        try:
            logger.info("Running BDL review...")
            bdl_prompt = f"Review this React code for BDL best practices:\n\n{generated_code}"
            bdl_result = bdl_review_agent.run(bdl_prompt)
        except Exception as e:
            logger.error(f"Error in BDL review: {str(e)}")
            bdl_result = f"Error: {str(e)}"
        
        # 汇总 review 结果
        review_results = {
            "security": security_result,
            "build": build_result,
            "bdl": bdl_result
        }
        
        # 判断是否通过（更智能的逻辑）
        security_passed = any(keyword in security_result.lower() 
                            for keyword in ["no issues", "passed", "no vulnerabilities", "secure", "safe"])
        build_passed = any(keyword in build_result.lower() 
                          for keyword in ["success", "no errors", "build successful", "compiles", "valid"])
        bdl_passed = any(keyword in bdl_result.lower() 
                        for keyword in ["compliant", "correct", "follows", "valid", "proper"])
        
        # 如果任何 review 有严重错误，则不通过
        has_critical_errors = any(
            "error" in result.lower() and "no errors" not in result.lower()
            for result in [security_result, build_result, bdl_result]
        )
        
        review_passed = security_passed and build_passed and bdl_passed and not has_critical_errors
        
        logger.info(f"Review completed. Passed: {review_passed}")
        
        return {
            **state,
            "review_results": review_results,
            "review_passed": review_passed
        }
    
    def correct_code(state: WorkflowState) -> WorkflowState:
        """步骤6: 修正代码"""
        code_file_path = state["code_file_path"]
        generated_code = state["generated_code"]
        review_results = state["review_results"]
        
        prompt = f"""Correct the following code based on review results:

Original Code:
{generated_code}

Review Results:
Security: {review_results.get('security', '')}
Build: {review_results.get('build', '')}
BDL: {review_results.get('bdl', '')}

Fix all issues and provide the corrected code."""
        
        correct_agent = _get_agent(CorrectAgent, "correct")
        result = correct_agent.run(prompt)
        
        # 更新生成的代码
        corrected_code = result
        
        return {
            **state,
            "generated_code": corrected_code,
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    
    def should_continue(state: WorkflowState) -> str:
        """决定是否继续修正循环"""
        review_passed = state.get("review_passed", False)
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 5)
        
        if review_passed:
            return "end"
        elif iteration_count >= max_iterations:
            return "end"  # 达到最大迭代次数，结束
        else:
            return "correct"
    
    # 创建图
    workflow = StateGraph(WorkflowState)
    
    # 添加节点
    workflow.add_node("collect_files", collect_files)
    workflow.add_node("analyze_aem", analyze_aem_files)
    workflow.add_node("select_bdl", select_bdl_components)
    workflow.add_node("write_code", write_code)
    workflow.add_node("review_code", review_code)
    workflow.add_node("correct_code", correct_code)
    
    # 添加边
    workflow.set_entry_point("collect_files")
    workflow.add_edge("collect_files", "analyze_aem")
    workflow.add_edge("analyze_aem", "select_bdl")
    workflow.add_edge("select_bdl", "write_code")
    workflow.add_edge("write_code", "review_code")
    
    # 条件边：review 后决定是结束还是修正
    workflow.add_conditional_edges(
        "review_code",
        should_continue,
        {
            "end": END,
            "correct": "correct_code"
        }
    )
    
    # 修正后再次审查
    workflow.add_edge("correct_code", "review_code")
    
    # 编译图
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app
