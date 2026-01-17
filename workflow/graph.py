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
    AEMAnalysisAgent,
    BDLSelectionAgent,
    CodeWritingAgent,
    SecurityReviewAgent,
    BuildReviewAgent,
    BDLReviewAgent,
    CorrectAgent
)
# FileCollectionAgent 已移除，直接使用工具函数


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
    aem_component_summary: Dict[str, Any]  # AEM 组件综合摘要（用于匹配和验证）
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
        """
        步骤1: 收集文件
        优化：直接使用工具函数，不需要 LLM Agent
        """
        component_path = state["component_path"]
        logger.info(f"Collecting files from: {component_path}")
        
        try:
            # 直接使用工具函数（不需要 LLM）
            from tools import list_files
            files = list_files(component_path, recursive=True)
            
            if not files:
                raise ValueError(
                    f"No files found in component directory: {component_path}. "
                    f"Please verify the resourceType is correct."
                )
            
            logger.info(f"Found {len(files)} files")
            
            return {
                **state,
                "files": files
            }
        except Exception as e:
            logger.error(f"Error collecting files: {str(e)}")
            raise  # 重新抛出异常，让工作流知道失败
    
    def analyze_aem_files(state: WorkflowState) -> WorkflowState:
        """
        步骤2: 分析 AEM 文件（逐个处理）
        优化：优先分析重要文件（HTL, Dialog, JS），忽略后续会提供的 Java 和 CSS
        """
        files = state.get("files", [])
        
        if not files:
            logger.error("No files to analyze")
            raise ValueError("Cannot analyze files: no files collected")
        
        # 优先排序文件（HTL > Dialog > JS > ...）
        from utils.aem_utils import prioritize_aem_files, categorize_aem_files
        prioritized_files = prioritize_aem_files(files)
        categorized = categorize_aem_files(prioritized_files)
        
        logger.info(
            f"Analyzing {len(files)} files (prioritized). "
            f"HTL: {len(categorized['htl'])}, Dialog: {len(categorized['dialog'])}, "
            f"JS: {len(categorized['js'])}"
        )
        
        # 过滤掉后续会提供的文件类型
        # 只分析当前可用的：HTL, Dialog, JS, Config
        files_to_analyze = (
            categorized['htl'] +
            categorized['dialog'] +
            categorized['js'] +
            categorized['config']
        )
        
        if not files_to_analyze:
            logger.warning("No critical files to analyze (HTL, Dialog, JS)")
            files_to_analyze = prioritized_files[:5]  # 至少分析前 5 个
        
        file_analyses = []
        aem_analysis_agent = _get_agent(AEMAnalysisAgent, "aem_analysis")
        successful_analyses = 0
        
        logger.info(f"Will analyze {len(files_to_analyze)} critical files")
        
        for i, file_path in enumerate(files_to_analyze, 1):
            try:
                # 验证文件路径
                from tools import file_exists
                if not file_exists(file_path):
                    logger.warning(f"File does not exist: {file_path}")
                    file_analyses.append({
                        "file_path": file_path,
                        "analysis": "Error: File not found"
                    })
                    continue
                
                logger.info(f"Analyzing file {i}/{len(files)}: {file_path}")
                analysis = aem_analysis_agent.analyze_file(file_path)
                
                # 验证分析结果（现在应该是结构化的）
                if isinstance(analysis, dict):
                    # 确保包含必需的字段
                    if "file_path" not in analysis:
                        analysis["file_path"] = file_path
                    if "analysis" not in analysis and "purpose" in analysis:
                        # 从结构化数据构建分析文本
                        analysis["analysis"] = (
                            f"Type: {analysis.get('file_type', 'unknown')}\n"
                            f"Purpose: {analysis.get('purpose', 'N/A')}\n"
                            f"Features: {', '.join(analysis.get('key_features', []))}"
                        )
                    file_analyses.append(analysis)
                    successful_analyses += 1
                else:
                    logger.warning(f"Unexpected analysis format for {file_path}: {type(analysis)}")
                    file_analyses.append({
                        "file_path": file_path,
                        "file_type": "unknown",
                        "purpose": "Analysis failed",
                        "analysis": str(analysis) if analysis else "No analysis available"
                    })
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {str(e)}")
                file_analyses.append({
                    "file_path": file_path,
                    "analysis": f"Error: {str(e)}"
                })
        
        logger.info(f"Completed analysis: {successful_analyses}/{len(files)} successful")
        
        if successful_analyses == 0:
            raise ValueError("All file analyses failed")
        
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
            result = bdl_selection_agent.run(prompt, return_structured=True)
            
            # 处理结构化输出
            if hasattr(result, 'selected_components'):
                # 是 BDLComponentSelection 对象
                selected_components = result.selected_components
                logger.info(
                    f"Selected {len(selected_components)} BDL components. "
                    f"Reasoning: {len(result.reasoning)} mappings provided."
                )
            elif isinstance(result, dict) and "selected_components" in result:
                # 是字典格式
                selected_components = result["selected_components"]
            else:
                # 回退到智能文本解析
                logger.warning("Failed to get structured output, using intelligent text parsing...")
                from utils.parsers import parse_component_paths
                selected_components = parse_component_paths(str(result), bdl_library_path)
                
                # 如果解析失败，使用简单方法
                if not selected_components:
                    for line in str(result).split("\n"):
                        line = line.strip()
                        if not line or line.startswith("Error"):
                            continue
                        if ("bdl" in line.lower() or "component" in line.lower() or 
                            "/" in line or "\\" in line or line.endswith((".tsx", ".ts", ".jsx", ".js"))):
                            selected_components.append(line)
            
            if not selected_components:
                logger.warning("No BDL components selected. This may cause code generation issues.")
            
            # 验证选择的组件并重新搜索不合适的
            from utils.component_matcher import validate_component_match, find_best_matching_components
            
            validated_components = []
            min_relevance = 0.4  # 最小相关性阈值
            
            logger.info(f"Validating {len(selected_components)} selected BDL components...")
            
            for comp_path in selected_components:
                is_valid, relevance, reason = validate_component_match(
                    aem_summary,
                    comp_path,
                    min_relevance=min_relevance
                )
                
                if is_valid:
                    validated_components.append(comp_path)
                    logger.info(f"✓ {comp_path}: {reason}")
                else:
                    logger.warning(f"✗ {comp_path}: {reason} - Searching for alternatives...")
                    
                    # 尝试在 BDL 库中搜索更好的匹配
                    # 简化处理：使用文件名作为搜索关键词
                    from pathlib import Path
                    comp_name = Path(comp_path).stem.lower()
                    
                    # 这里可以触发重新搜索（简化实现）
                    # 实际应该让 Agent 重新搜索相关组件
            
            # 如果验证后的组件太少，尝试从库中找更多候选
            if len(validated_components) < 2 and len(file_analyses) > 0:
                logger.info("Not enough validated components, searching for additional matches...")
                # 从分析中提取关键词用于搜索
                all_features = ' '.join(aem_summary.get('key_features', []))
                # 这里可以调用 Agent 的搜索工具来找更多候选
            
            # 使用验证后的组件（如果验证失败，使用原始选择）
            final_components = validated_components if validated_components else selected_components
            
            if len(final_components) != len(selected_components):
                logger.info(
                    f"Component validation: {len(selected_components)} -> {len(final_components)} "
                    f"validated components"
                )
            
            return {
                **state,
                "selected_bdl_components": final_components,
                "aem_component_summary": aem_summary  # 保存摘要供后续使用
            }
        except Exception as e:
            logger.error(f"Error selecting BDL components: {str(e)}")
            # 返回空列表但继续流程（允许后续步骤处理）
            return {
                **state,
                "selected_bdl_components": []
            }
    
    def write_code(state: WorkflowState) -> WorkflowState:
        """
        步骤4: 编写代码
        优化：提供关键的 AEM 信息（HTL 结构、Dialog 配置、JS 逻辑）给代码生成 Agent
        """
        file_analyses = state["file_analyses"]
        selected_bdl_components = state.get("selected_bdl_components", [])
        aem_summary = state.get("aem_component_summary", {})
        output_path = state.get("output_path", "./output")
        resource_type = state.get("resource_type", "unknown")
        
        if not file_analyses:
            logger.error("No file analyses available for code generation")
            raise ValueError("Cannot generate code without file analyses")
        
        # 分类文件分析结果
        htl_analyses = [fa for fa in file_analyses if fa.get('file_type') in ['htl', 'html']]
        dialog_analyses = [fa for fa in file_analyses if fa.get('file_type') == 'dialog']
        js_analyses = [fa for fa in file_analyses if fa.get('file_type') == 'js']
        
        # 构建关键信息摘要
        htl_summary = ""
        if htl_analyses:
            # HTL 是最重要的 - 包含 UI 结构
            htl_analyses_str = "\n\n".join([
                f"HTL Template: {fa.get('file_path', 'unknown')}\n"
                f"UI Structure Analysis: {fa.get('analysis', 'No analysis')}\n"
                f"Key Features: {', '.join(fa.get('key_features', []))}\n"
                f"Dependencies: {', '.join(fa.get('dependencies', []))}"
                for fa in htl_analyses
            ])
            htl_summary = f"\n\n=== HTL TEMPLATE (UI STRUCTURE) - MOST CRITICAL ===\n{htl_analyses_str}\n"
        
        dialog_summary = ""
        if dialog_analyses:
            # Dialog 定义了 React Props
            dialog_analyses_str = "\n\n".join([
                f"Dialog Configuration: {fa.get('file_path', 'unknown')}\n"
                f"Property Definitions: {fa.get('analysis', 'No analysis')}\n"
                f"Configuration: {fa.get('configuration', {})}"
                for fa in dialog_analyses
            ])
            dialog_summary = f"\n\n=== DIALOG CONFIGURATION (REACT PROPS) - CRITICAL ===\n{dialog_analyses_str}\n"
        
        js_summary = ""
        if js_analyses:
            # JS 定义了交互逻辑
            js_analyses_str = "\n\n".join([
                f"JavaScript Logic: {fa.get('file_path', 'unknown')}\n"
                f"Interactions: {fa.get('analysis', 'No analysis')}\n"
                f"Key Features: {', '.join(fa.get('key_features', []))}"
                for fa in js_analyses
            ])
            js_summary = f"\n\n=== JAVASCRIPT LOGIC (REACT INTERACTIONS) - IMPORTANT ===\n{js_analyses_str}\n"
        
        # 读取选定的 BDL 组件源代码
        bdl_components_code = {}
        for comp_path in selected_bdl_components[:5]:  # 限制数量
            try:
                from tools import read_file
                comp_code = read_file(comp_path)
                if comp_code:
                    bdl_components_code[comp_path] = comp_code[:2000]  # 限制长度
            except Exception as e:
                logger.warning(f"Could not read BDL component {comp_path}: {str(e)}")
        
        bdl_components_info = ""
        if bdl_components_code:
            bdl_components_info = "\n\n=== SELECTED BDL COMPONENTS (SOURCE CODE) ===\n"
            for comp_path, comp_code in bdl_components_code.items():
                bdl_components_info += f"\n{comp_path}:\n{comp_code[:1000]}...\n"
        elif selected_bdl_components:
            bdl_components_info = f"\nSelected BDL Component Paths:\n" + "\n".join(selected_bdl_components)
        
        # 从 resourceType 提取组件名称
        component_name = resource_type.split("/")[-1] if "/" in resource_type else resource_type.split(".")[-1]
        component_name = component_name.title().replace("_", "")  # 转换为 PascalCase
        
        prompt = f"""Generate a React component using BDL that perfectly replicates the AEM component:

AEM Component ResourceType: {resource_type}
Component Name: {component_name}
{htl_summary}
{dialog_summary}
{js_summary}
{bdl_components_info}

CRITICAL CONVERSION REQUIREMENTS:
1. UI Structure: Convert HTL HTML structure to JSX, maintaining exact same structure and hierarchy
2. Props Interface: Map Dialog field definitions to TypeScript/PropTypes interface
   - Required fields from Dialog → required props
   - Field types from Dialog → prop types (textfield → string, checkbox → boolean, etc.)
   - Default values from Dialog → default prop values
3. Data Binding: Convert data-sly-use Sling Models to React props/state
4. Conditional Rendering: Convert data-sly-test to React conditional rendering ({{condition && <Component />}})
5. Iterations: Convert data-sly-repeat to React .map()
6. Event Handlers: Convert HTL/JS event handlers to React event handlers (onClick, onChange, etc.)
7. BDL Components: Use selected BDL components to implement UI elements
8. Styling: Maintain the same visual appearance (CSS will be handled separately later)

The React component should:
- Have the exact same functionality as the AEM component
- Use the same props structure as defined in Dialog
- Maintain the same UI structure as the HTL template
- Implement the same interactions as the JavaScript file
- Use BDL components appropriately
- Follow React and BDL best practices

Output path: {output_path}

Generate the complete React component code following these requirements."""
        
        try:
            code_writing_agent = _get_agent(CodeWritingAgent, "code_writing")
            result = code_writing_agent.run(prompt, return_structured=True)
            
            # 处理结构化输出
            if hasattr(result, 'component_code'):
                # 是 CodeGenerationResult 对象
                generated_code = result.component_code
                logger.info(
                    f"Code generated for {result.component_name}. "
                    f"Imports: {len(result.imports)}, Dependencies: {len(result.dependencies)}"
                )
                # 如果有 notes，记录
                if result.notes:
                    logger.info(f"Generation notes: {result.notes}")
            elif isinstance(result, dict) and "component_code" in result:
                # 是字典格式
                generated_code = result["component_code"]
            else:
                # 回退到智能代码提取
                from utils.parsers import extract_code_from_response
                generated_code = extract_code_from_response(str(result))
                logger.warning("Received unstructured code output, extracted code block")
            
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
        
        # 运行三个 review subagents（使用结构化输出）
        security_result_obj = None
        build_result_obj = None
        bdl_result_obj = None
        
        try:
            logger.info("Running security review...")
            security_prompt = f"Review this React code for security issues:\n\n{generated_code}"
            security_result_obj = security_review_agent.run(security_prompt, return_structured=True)
        except Exception as e:
            logger.error(f"Error in security review: {str(e)}")
            security_result_obj = None
        
        try:
            logger.info("Running build review...")
            build_prompt = f"Review this React code for build errors:\n\nCode file: {code_file_path}\nWorking directory: {output_path}"
            build_result_obj = build_review_agent.run(build_prompt, return_structured=True)
        except Exception as e:
            logger.error(f"Error in build review: {str(e)}")
            build_result_obj = None
        
        try:
            logger.info("Running BDL review...")
            bdl_prompt = f"Review this React code for BDL best practices:\n\n{generated_code}"
            bdl_result_obj = bdl_review_agent.run(bdl_prompt, return_structured=True)
        except Exception as e:
            logger.error(f"Error in BDL review: {str(e)}")
            bdl_result_obj = None
        
        # 处理结构化结果
        def extract_review_data(review_obj, default_text="Review failed"):
            """从结构化 review 结果中提取数据"""
            if hasattr(review_obj, 'passed'):
                return {
                    "passed": review_obj.passed,
                    "issues": review_obj.issues if hasattr(review_obj, 'issues') else [],
                    "recommendations": review_obj.recommendations if hasattr(review_obj, 'recommendations') else [],
                    "severity": review_obj.severity if hasattr(review_obj, 'severity') else "unknown",
                    "details": review_obj.details if hasattr(review_obj, 'details') else str(review_obj)
                }
            elif isinstance(review_obj, dict):
                return review_obj
            else:
                return {
                    "passed": False,
                    "issues": [default_text],
                    "recommendations": [],
                    "severity": "high",
                    "details": str(review_obj) if review_obj else default_text
                }
        
        security_data = extract_review_data(security_result_obj, "Security review failed")
        build_data = extract_review_data(build_result_obj, "Build review failed")
        bdl_data = extract_review_data(bdl_result_obj, "BDL review failed")
        
        # 汇总 review 结果（保留原始对象和提取的数据）
        review_results = {
            "security": security_data,
            "build": build_data,
            "bdl": bdl_data,
            "_raw": {
                "security": security_result_obj,
                "build": build_result_obj,
                "bdl": bdl_result_obj
            }
        }
        
        # 判断是否通过（使用结构化数据）
        security_passed = security_data.get("passed", False) and security_data.get("severity") not in ["critical", "high"]
        build_passed = build_data.get("passed", False) and build_data.get("severity") not in ["critical", "high"]
        bdl_passed = bdl_data.get("passed", False) and bdl_data.get("severity") not in ["critical", "high"]
        
        review_passed = security_passed and build_passed and bdl_passed
        
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
Security: {review_results.get('security', {}).get('details', 'N/A')}
  Issues: {len(review_results.get('security', {}).get('issues', []))}
  Passed: {review_results.get('security', {}).get('passed', False)}
Build: {review_results.get('build', {}).get('details', 'N/A')}
  Issues: {len(review_results.get('build', {}).get('issues', []))}
  Passed: {review_results.get('build', {}).get('passed', False)}
BDL: {review_results.get('bdl', {}).get('details', 'N/A')}
  Issues: {len(review_results.get('bdl', {}).get('issues', []))}
  Passed: {review_results.get('bdl', {}).get('passed', False)}

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
            logger.info("All reviews passed. Ending workflow.")
            return "end"
        elif iteration_count >= max_iterations:
            logger.warning(f"Reached max iterations ({max_iterations}). Ending workflow.")
            return "end"  # 达到最大迭代次数，结束
        else:
            logger.info(f"Reviews not passed. Continuing to correction (iteration {iteration_count + 1}/{max_iterations}).")
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
