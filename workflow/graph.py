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
    files: List[str]  # 当前组件和所有依赖组件的文件
    dependency_tree: Dict[str, Any]  # 组件依赖树
    dependency_analyses: Dict[str, List[Dict[str, Any]]]  # 依赖组件的分析结果 {resource_type: [analyses]}
    file_analyses: List[Dict[str, Any]]  # 当前组件的文件分析
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
        步骤1: 收集文件（包括依赖组件）
        优化：递归收集所有依赖组件的文件
        """
        component_path = state["component_path"]
        resource_type = state["resource_type"]
        aem_repo_path = state["aem_repo_path"]
        
        logger.info(f"Collecting files from: {component_path}")
        
        try:
            # 直接使用工具函数收集当前组件文件
            from tools import list_files
            current_files = list_files(component_path, recursive=True)
            
            if not current_files:
                raise ValueError(
                    f"No files found in component directory: {component_path}. "
                    f"Please verify the resourceType is correct."
                )
            
            logger.info(f"Found {len(current_files)} files in current component")
            
            # 构建依赖树
            from utils.dependency_resolver import build_dependency_tree, get_all_dependency_files
            
            logger.info("Building component dependency tree...")
            dependency_tree = build_dependency_tree(
                resource_type,
                component_path,
                aem_repo_path
            )
            
            # 获取所有依赖组件的文件
            dependency_files = get_all_dependency_files(dependency_tree)
            logger.info(f"Found {len(dependency_files)} files in {len(dependency_tree.get('root', {}).get('dependencies', {}))} dependency components")
            
            # 合并所有文件（当前组件 + 依赖组件）
            all_files = current_files + dependency_files
            
            logger.info(f"Total files collected: {len(all_files)} (current: {len(current_files)}, dependencies: {len(dependency_files)})")
            
            return {
                **state,
                "files": all_files,
                "dependency_tree": dependency_tree
            }
        except Exception as e:
            logger.error(f"Error collecting files: {str(e)}")
            raise
            raise  # 重新抛出异常，让工作流知道失败
    
    def analyze_aem_files(state: WorkflowState) -> WorkflowState:
        """
        步骤2: 分析 AEM 文件（包括依赖组件）
        优化：优先分析重要文件（HTL, Dialog, JS），递归分析依赖组件
        """
        files = state.get("files", [])
        dependency_tree = state.get("dependency_tree", {})
        component_path = state["component_path"]
        aem_repo_path = state["aem_repo_path"]
        
        if not files:
            logger.error("No files to analyze")
            raise ValueError("Cannot analyze files: no files collected")
        
        # 分离当前组件文件和依赖组件文件
        current_component_files = [f for f in files if component_path in f]
        dependency_files = [f for f in files if f not in current_component_files]
        
        logger.info(
            f"Files to analyze: {len(current_component_files)} current component, "
            f"{len(dependency_files)} dependency components"
        )
        
        # 优先排序文件（HTL > Dialog > JS > ...）
        from utils.aem_utils import prioritize_aem_files, categorize_aem_files
        
        # 分析当前组件文件
        prioritized_files = prioritize_aem_files(current_component_files)
        categorized = categorize_aem_files(prioritized_files)
        
        logger.info(
            f"Analyzing current component: {len(current_component_files)} files. "
            f"HTL: {len(categorized['htl'])}, Dialog: {len(categorized['dialog'])}, "
            f"JS: {len(categorized['js'])}, Java: {len(categorized['java'])}"
        )
        
        # 分析关键文件：HTL, Dialog, JS, Java, Config
        # Java 文件现在也需要分析（用于提取 Sling Model 数据结构）
        files_to_analyze = (
            categorized['htl'] +
            categorized['dialog'] +
            categorized['js'] +
            categorized['java'] +  # 添加 Java 文件分析
            categorized['config']
        )
        
        if not files_to_analyze:
            logger.warning("No critical files to analyze (HTL, Dialog, JS)")
            files_to_analyze = prioritized_files[:5]  # 至少分析前 5 个
        
        file_analyses = []
        aem_analysis_agent = _get_agent(AEMAnalysisAgent, "aem_analysis")
        successful_analyses = 0
        
        logger.info(f"Will analyze {len(files_to_analyze)} critical files from current component")
        
        # 分析当前组件文件
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
                
                logger.info(f"Analyzing file {i}/{len(files_to_analyze)}: {file_path}")
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
        
        # 分析依赖组件文件
        dependency_analyses = {}
        root_deps = dependency_tree.get('root', {}).get('dependencies', {})
        
        if root_deps:
            logger.info(f"Analyzing {len(root_deps)} dependency components...")
            
            def analyze_dependency_component(dep_resource_type: str, dep_info: Dict[str, Any]):
                """递归分析依赖组件"""
                dep_files = dep_info.get('files', [])
                if not dep_files:
                    return []
                
                # 优先排序依赖组件的文件
                dep_prioritized = prioritize_aem_files(dep_files)
                dep_categorized = categorize_aem_files(dep_prioritized)
                
                # 只分析关键文件（包括 Java）
                dep_files_to_analyze = (
                    dep_categorized['htl'] +
                    dep_categorized['dialog'] +
                    dep_categorized['js'] +
                    dep_categorized['java'] +  # 添加 Java 文件分析
                    dep_categorized['config']
                )[:10]  # 限制每个依赖组件最多分析 10 个文件
                
                dep_analyses = []
                for dep_file in dep_files_to_analyze:
                    try:
                        from tools import file_exists
                        if not file_exists(dep_file):
                            continue
                        
                        logger.debug(f"Analyzing dependency file: {dep_file}")
                        analysis = aem_analysis_agent.analyze_file(dep_file)
                        
                        if isinstance(analysis, dict):
                            if "file_path" not in analysis:
                                analysis["file_path"] = dep_file
                            analysis["component_resource_type"] = dep_resource_type  # 标记来源
                            dep_analyses.append(analysis)
                    except Exception as e:
                        logger.warning(f"Error analyzing dependency file {dep_file}: {e}")
                
                return dep_analyses
            
            # 分析所有依赖组件
            for dep_resource_type, dep_info in root_deps.items():
                logger.info(f"Analyzing dependency component: {dep_resource_type}")
                dep_analyses = analyze_dependency_component(dep_resource_type, dep_info)
                dependency_analyses[dep_resource_type] = dep_analyses
                
                # 递归分析嵌套依赖
                nested_deps = dep_info.get('dependencies', {})
                for nested_resource_type, nested_info in nested_deps.items():
                    nested_analyses = analyze_dependency_component(nested_resource_type, nested_info)
                    dependency_analyses[nested_resource_type] = nested_analyses
        
        logger.info(
            f"Completed analysis: {successful_analyses}/{len(files_to_analyze)} current component files, "
            f"{sum(len(analyses) for analyses in dependency_analyses.values())} dependency component files"
        )
        
        if successful_analyses == 0:
            raise ValueError("All file analyses failed")
        
        return {
            **state,
            "file_analyses": file_analyses,
            "dependency_analyses": dependency_analyses
        }
    
    def select_bdl_components(state: WorkflowState) -> WorkflowState:
        """
        步骤3: 选择 BDL 组件（带验证和重新搜索）
        优化：验证选择的组件相关性，不适合时重新搜索
        """
        bdl_library_path = state["bdl_library_path"]
        file_analyses = state["file_analyses"]
        
        if not file_analyses:
            logger.error("No file analyses available for BDL component selection")
            return {
                **state,
                "selected_bdl_components": [],
                "aem_component_summary": {}  # 确保设置空摘要
            }
        
        # 构建组件摘要（用于匹配）
        from utils.aem_utils import build_component_summary
        aem_summary = build_component_summary(file_analyses)
        
        # 构建分析摘要（用于 Agent 提示）
        analysis_summary = "\n\n".join([
            f"File: {fa.get('file_path', 'unknown')} (Type: {fa.get('file_type', 'unknown')})\n"
            f"Purpose: {fa.get('purpose', 'N/A')}\n"
            f"Key Features: {', '.join(fa.get('key_features', []))}\n"
            f"Analysis: {fa.get('analysis', 'No analysis')}"
            for fa in file_analyses
        ])
        
        prompt = f"""Based on the following AEM component analysis, select appropriate BDL components:

AEM Component Summary:
- UI Structure: {aem_summary.get('ui_structure', '')[:500]}...
- Key Features: {', '.join(aem_summary.get('key_features', []))}
- Dependencies: {', '.join(aem_summary.get('dependencies', []))}

Detailed File Analysis:
{analysis_summary}

BDL library path: {bdl_library_path}

CRITICAL REQUIREMENTS:
1. Search the BDL library for components that match the AEM functionality
2. Read candidate component source code to verify they are suitable
3. Consider component composition (multiple BDL components may be needed)
4. Prioritize components that match the UI patterns and features identified

Select BDL components and return their file paths with reasoning."""
        
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
        包括所有依赖组件的信息
        """
        file_analyses = state["file_analyses"]
        dependency_analyses = state.get("dependency_analyses", {})
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
        java_analyses = [fa for fa in file_analyses if fa.get('file_type') == 'java']
        
        # 提取并查找 CSS 样式（当前组件 + 依赖组件）
        css_summary = {}
        component_path = state.get("component_path", "")
        aem_repo_path = state.get("aem_repo_path", "")
        dependency_analyses = state.get("dependency_analyses", {})
        dependency_tree = state.get("dependency_tree", {})
        
        if htl_analyses and component_path and aem_repo_path:
            # 1. 处理当前组件的 CSS
            first_htl = htl_analyses[0]
            htl_file_path = first_htl.get('file_path', '')
            if htl_file_path:
                try:
                    from tools import read_file
                    from utils.css_resolver import (
                        build_css_summary,
                        build_dependency_css_summary,
                        merge_css_summaries
                    )
                    htl_content = read_file(htl_file_path)
                    current_css_summary = build_css_summary(
                        component_path,
                        htl_content,
                        aem_repo_path
                    )
                    logger.info(
                        f"Current Component CSS: {len(current_css_summary.get('used_classes', []))} classes used, "
                        f"{len(current_css_summary.get('found_classes', []))} found, "
                        f"{len(current_css_summary.get('missing_classes', []))} missing"
                    )
                    
                    # 2. 处理依赖组件的 CSS
                    dependency_css_summaries = {}
                    if dependency_analyses and dependency_tree:
                        dependency_css_summaries = build_dependency_css_summary(
                            dependency_analyses,
                            dependency_tree,
                            aem_repo_path
                        )
                        logger.info(
                            f"Dependency Components CSS: {len(dependency_css_summaries)} components processed"
                        )
                    
                    # 3. 合并所有 CSS 摘要
                    if dependency_css_summaries:
                        css_summary = merge_css_summaries(current_css_summary, dependency_css_summaries)
                        logger.info(
                            f"Merged CSS Summary: {len(css_summary.get('used_classes', []))} total classes used, "
                            f"{len(css_summary.get('found_classes', []))} found, "
                            f"{len(css_summary.get('missing_classes', []))} missing"
                        )
                    else:
                        css_summary = current_css_summary
                    
                except Exception as e:
                    logger.warning(f"Failed to build CSS summary: {e}")
                    import traceback
                    traceback.print_exc()
        
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
        
        # 提取并分析 Java Sling Models（用于生成 TypeScript 类型和数据转换逻辑）
        java_summary = ""
        java_analyses_raw = []
        if java_analyses:
            try:
                from utils.java_analyzer import parse_java_file, build_java_analysis_summary
                
                # 解析所有 Java 文件
                for java_analysis in java_analyses:
                    java_file_path = java_analysis.get('file_path', '')
                    if java_file_path:
                        try:
                            java_parsed = parse_java_file(java_file_path)
                            if java_parsed:
                                java_analyses_raw.append(java_parsed)
                                logger.info(f"Parsed Java Sling Model: {java_parsed.get('class_name', 'Unknown')}")
                        except Exception as e:
                            logger.warning(f"Failed to parse Java file {java_file_path}: {e}")
                
                # 构建 Java 分析摘要
                if java_analyses_raw:
                    java_summary = build_java_analysis_summary(java_analyses_raw)
                    logger.info(f"Built Java analysis summary for {len(java_analyses_raw)} Sling Models")
            except Exception as e:
                logger.warning(f"Failed to build Java analysis summary: {e}")
                import traceback
                traceback.print_exc()
        
        # 处理依赖组件的 Java 文件
        dependency_java_analyses = []
        if dependency_analyses:
            try:
                from utils.java_analyzer import parse_java_file
                
                for dep_resource_type, dep_analyses in dependency_analyses.items():
                    for dep_analysis in dep_analyses:
                        if dep_analysis.get('file_type') == 'java':
                            java_file_path = dep_analysis.get('file_path', '')
                            if java_file_path:
                                try:
                                    java_parsed = parse_java_file(java_file_path)
                                    if java_parsed:
                                        dependency_java_analyses.append(java_parsed)
                                except Exception as e:
                                    logger.warning(f"Failed to parse dependency Java file {java_file_path}: {e}")
            except Exception as e:
                logger.warning(f"Failed to parse dependency Java files: {e}")
        
        # 合并依赖组件的 Java 分析
        if dependency_java_analyses:
            try:
                from utils.java_analyzer import build_java_analysis_summary
                dependency_java_summary = build_java_analysis_summary(dependency_java_analyses)
                if java_summary:
                    java_summary += "\n\n=== DEPENDENCY COMPONENTS' SLING MODELS ===\n" + dependency_java_summary
                else:
                    java_summary = "\n\n=== DEPENDENCY COMPONENTS' SLING MODELS ===\n" + dependency_java_summary
            except Exception as e:
                logger.warning(f"Failed to build dependency Java summary: {e}")
        
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
        
        # 构建文件上下文说明（帮助 LLM 理解每个文件的作用）
        from utils.file_context_builder import build_file_context
        
        file_contexts_section = "\n\n=== FILE ROLES AND CONTEXTS ===\n"
        file_contexts_section += "Each AEM file serves a specific purpose. Here's what each file provides:\n\n"
        
        # 当前组件的文件
        file_contexts_section += "--- CURRENT COMPONENT FILES ---\n"
        for analysis in file_analyses:
            file_type = analysis.get('file_type', 'unknown')
            if file_type in ['htl', 'html', 'dialog', 'js']:  # 只包含关键文件
                context = build_file_context(analysis)
                file_contexts_section += context + "\n"
        
        # 依赖组件的文件
        if dependency_analyses:
            file_contexts_section += "\n--- DEPENDENCY COMPONENT FILES ---\n"
            file_contexts_section += "The following files are from components that this component depends on:\n\n"
            for dep_resource_type, dep_analyses in dependency_analyses.items():
                file_contexts_section += f"\n### Dependency Component: {dep_resource_type}\n"
                for analysis in dep_analyses[:5]:  # 限制每个依赖组件最多 5 个文件
                    file_type = analysis.get('file_type', 'unknown')
                    if file_type in ['htl', 'html', 'dialog', 'js']:
                        context = build_file_context(analysis)
                        file_contexts_section += context + "\n"
        
        # 评估信息充分性
        has_htl = len(htl_analyses) > 0
        has_dialog = len(dialog_analyses) > 0
        has_js = len(js_analyses) > 0
        has_java = len(java_analyses) > 0 or len(java_analyses_raw) > 0
        
        completeness_note = ""
        if not has_htl:
            completeness_note = "\n⚠️ WARNING: Missing HTL template - cannot determine UI structure accurately.\n"
        elif not has_dialog:
            completeness_note = "\n⚠️ WARNING: Missing Dialog configuration - cannot determine Props interface accurately.\n"
        elif has_htl and has_dialog and has_js and has_java:
            completeness_note = "\n✓ COMPLETE INFORMATION: HTL + Dialog + JS + Java Sling Model provide complete information for accurate React conversion with proper TypeScript types.\n"
        elif has_htl and has_dialog and has_js:
            completeness_note = "\n✓ SUFFICIENT INFORMATION: HTL + Dialog + JS provide enough information for React conversion. Java Sling Model would improve type accuracy.\n"
        elif has_htl and has_dialog:
            completeness_note = "\n✓ BASIC INFORMATION: HTL + Dialog provide basic information for React conversion. JS and Java Sling Model would improve completeness.\n"
        
        prompt = f"""Generate a React component using BDL that perfectly replicates the AEM component:

AEM Component ResourceType: {resource_type}
Component Name: {component_name}
{completeness_note}
{file_contexts_section}
=== AEM COMPONENT SOURCE CODE ===

{htl_summary}
{dialog_summary}
{js_summary}
{java_summary}

=== SELECTED BDL COMPONENTS ===
{bdl_components_info}
"""
        
        # 添加 CSS 样式信息（包括依赖组件）
        if css_summary:
            css_section = f"""

=== CSS STYLES (from AEM) ===

The component and its dependencies use the following CSS classes:
- Total classes used: {len(css_summary.get('used_classes', []))}
- Found CSS definitions: {len(css_summary.get('found_classes', []))} classes
- Missing CSS definitions: {len(css_summary.get('missing_classes', []))} classes

CSS Rules Found (Current Component):
"""
            # 分离当前组件和依赖组件的 CSS 规则
            current_css_rules = {}
            dependency_css_rules = {}
            
            for class_name, rules_dict in css_summary.get('css_rules', {}).items():
                for file_path, rule in rules_dict.items():
                    if file_path.startswith('['):
                        # 依赖组件的规则（标记为 [resource_type] path）
                        if class_name not in dependency_css_rules:
                            dependency_css_rules[class_name] = []
                        dependency_css_rules[class_name].append((file_path, rule))
                    else:
                        # 当前组件的规则
                        if class_name not in current_css_rules:
                            current_css_rules[class_name] = []
                        current_css_rules[class_name].append((file_path, rule))
            
            # 显示当前组件的 CSS
            for class_name, rules_list in current_css_rules.items():
                css_section += f"\n.{class_name}:\n"
                for file_path, rule in rules_list:
                    rule_preview = rule[:300] + "..." if len(rule) > 300 else rule
                    css_section += f"  From: {file_path}\n  {rule_preview}\n"
            
            # 显示依赖组件的 CSS
            if dependency_css_rules:
                css_section += "\nCSS Rules from Dependency Components:\n"
                for class_name, rules_list in dependency_css_rules.items():
                    css_section += f"\n.{class_name}:\n"
                    for file_path, rule in rules_list:
                        rule_preview = rule[:300] + "..." if len(rule) > 300 else rule
                        css_section += f"  From: {file_path}\n  {rule_preview}\n"
            
            # 显示依赖组件的 CSS 摘要
            if css_summary.get('dependency_css'):
                css_section += "\n\nDependency Components CSS Summary:\n"
                for dep_resource_type, dep_css in css_summary.get('dependency_css', {}).items():
                    css_section += f"\n- {dep_resource_type}:\n"
                    css_section += f"  Used classes: {len(dep_css.get('used_classes', []))}\n"
                    css_section += f"  Found: {len(dep_css.get('found_classes', []))}\n"
                    css_section += f"  Missing: {len(dep_css.get('missing_classes', []))}\n"
            
            if css_summary.get('missing_classes'):
                css_section += f"\n⚠️ Missing CSS for classes: {', '.join(css_summary.get('missing_classes', []))}\n"
                css_section += "Note: These classes may be defined in global styles or need manual handling.\n"
            
            css_section += """
IMPORTANT: When converting to React:
1. Convert these CSS classes to BDL styling approach (sx prop, styled-components, or CSS modules)
2. Preserve the visual appearance and behavior (colors, spacing, transitions, etc.)
3. Handle responsive styles if present
4. Maintain hover, focus, and other pseudo-class states
5. For missing classes, you may need to infer styles or use BDL's default styling
6. Include styles from dependency components when they are used in the final React component
"""
            prompt += css_section
        else:
            prompt += "\n=== CSS STYLES ===\nNote: CSS styles will be handled separately. Focus on structure and functionality.\n"

        prompt += f"""
=== CRITICAL CONVERSION REQUIREMENTS ===

1. UI Structure (from HTL Template):
   - Convert HTL HTML structure to JSX, maintaining EXACT same structure and hierarchy
   - Preserve all HTML elements and their nesting
   - Keep all semantic HTML elements (header, nav, main, section, article, footer, etc.)
   - Map data-sly-resource to appropriate component composition

2. Props Interface (from Dialog Configuration):
   - Each Dialog field → React prop
   - Required fields → required props (use PropTypes.required or TypeScript required)
   - Field types mapping:
     * textfield → string
     * textarea → string  
     * select → enum/string
     * checkbox → boolean
     * numberfield → number
     * pathfield → string (path)
     * datepicker → Date or string (ISO format)
   - Default values from Dialog → default prop values
   - Field labels → JSDoc comments for props

3. Data Binding (from HTL data-sly-use and Java Sling Model):
   - data-sly-use.model → React props (data comes from parent or API)
   - model.property → props.property or state.property
   - If model is used for calculations → useMemo or derived state
   - **CRITICAL: Use the TypeScript interface from Java Sling Model analysis above**
   - Java Sling Model fields → TypeScript Props interface (with correct types)
   - @PostConstruct methods → React useEffect or useMemo hooks for data transformation
   - Required fields from Java annotations (@Required, @NotNull) → required TypeScript props
   - Default values from Java → default prop values in React

4. Conditional Rendering (from HTL data-sly-test):
   - data-sly-test="{{condition}}" → use single braces: condition && <Component />
   - data-sly-test="{{!condition}}" → use single braces: !condition && <Component />
   - Complex conditions → extract to variables for readability
   - In JSX, use single curly braces for expressions (not double braces like HTL)

5. Iterations (from HTL data-sly-repeat):
   - data-sly-repeat="{{items}}" → items.map((item, index) => (...))
   - Preserve item context and index
   - Map item properties correctly

6. Event Handlers (from HTL/JS):
   - onclick="function()" → onClick={{handleClick}}
   - onchange="function()" → onChange={{handleChange}}
   - Extract event handlers from JS file and convert to React handlers
   - Use useState for form inputs, useCallback for memoization if needed

7. BDL Component Usage:
   - Map AEM UI elements to BDL components based on selected components
   - Use BDL component APIs correctly (check component source code provided)
   - Maintain BDL component prop patterns
   - Follow BDL composition patterns

8. Component Composition (from data-sly-resource):
   - data-sly-resource="{{component}}" → <ComponentName />
   - Map AEM component paths to React component imports
   - Pass appropriate props to child components
   - IMPORTANT: All dependency components have been analyzed and their information is provided above
   - Convert each dependency component to a React component import
   - Ensure dependency components are properly integrated with correct props

9. Styling:
   - Note: CSS will be handled separately later
   - Use BDL's styling approach (sx prop, styled-components, or CSS modules)
   - Preserve responsive behavior if mentioned in HTL/JS

=== CONVERSION EXAMPLE (Reference) ===

AEM HTL:
  <button data-sly-test="{{model.showButton}}" 
          data-sly-attribute.onclick="{{model.onClick}}">
    {{model.text}}
  </button>

React Equivalent (note: JSX uses single braces for expressions):
  [Example: props.showButton && (<Button onClick=props.onClick>props.text</Button>)]

IMPORTANT: In JSX, use SINGLE curly braces for JavaScript expressions (not double braces like HTL).
HTL uses double braces for expressions, but React JSX uses single braces.

=== FINAL REQUIREMENTS ===

The React component MUST:
✓ Have EXACT same functionality as the AEM component
✓ Use the SAME props structure as defined in Dialog
✓ Maintain the SAME UI structure as the HTL template  
✓ Implement the SAME interactions as the JavaScript file
✓ Use BDL components appropriately (based on selected components)
✓ Follow React best practices (hooks, functional components, proper state management)
✓ Follow BDL best practices (component API, styling patterns, composition)
✓ Include proper TypeScript/PropTypes definitions
✓ Include JSDoc comments for props (from Dialog field labels)
✓ Handle edge cases (null checks, default values, etc.)
✓ Be production-ready code

Output path: {output_path}

Generate the complete React component code following ALL these requirements.

CRITICAL: Output ONLY the complete React component code. The code must:
- Be complete and compilable
- Include all necessary imports
- Include all prop definitions
- Be ready to save directly to a .jsx file
- Have no syntax errors
- Follow all conversion requirements above"""
        
        try:
            code_writing_agent = _get_agent(CodeWritingAgent, "code_writing")
            result = code_writing_agent.run(prompt, return_structured=True)
            
            # 处理结构化输出并验证代码质量
            from utils.code_validator import extract_and_validate_code, improve_code_extraction
            
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
                # 回退到改进的代码提取
                generated_code = improve_code_extraction(str(result))
                logger.warning("Received unstructured code output, using improved code extraction")
            
            # 验证生成的代码基本质量
            from utils.code_validator import validate_react_code
            is_valid, warnings, errors = validate_react_code(generated_code)
            
            if errors:
                logger.error(f"Generated code has basic errors: {errors}")
                # 即使有错误也继续，让 review 阶段发现并修正
            if warnings:
                logger.warning(f"Generated code warnings: {warnings}")
            
            if not is_valid:
                logger.warning("Generated code validation failed, but continuing to review stage for detailed feedback")
            
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
        """
        步骤5: 审查代码（使用 subagents）
        优化：提供迭代上下文，确保 review 知道这是第几次迭代
        """
        code_file_path = state["code_file_path"]
        generated_code = state["generated_code"]
        output_path = state.get("output_path", "./output")
        iteration = state.get("iteration_count", 0)
        previous_review_results = state.get("review_results", {})
        
        logger.info(f"Reviewing code (iteration {iteration})...")
        
        # 构建迭代上下文
        iteration_context = ""
        if iteration == 0:
            iteration_context = "\n=== INITIAL CODE REVIEW ===\nThis is the first review of the generated code."
        else:
            iteration_context = f"""
=== ITERATION {iteration} CODE REVIEW ===
This is review iteration {iteration} (after {iteration} correction(s)).
Previous review found issues that should now be fixed.

Previous Review Summary:
- Security: {previous_review_results.get('security', {}).get('passed', False) and 'PASSED' or 'FAILED'} 
  ({len(previous_review_results.get('security', {}).get('issues', []))} issues)
- Build: {previous_review_results.get('build', {}).get('passed', False) and 'PASSED' or 'FAILED'}
  ({len(previous_review_results.get('build', {}).get('issues', []))} issues)
- BDL: {previous_review_results.get('bdl', {}).get('passed', False) and 'PASSED' or 'FAILED'}
  ({len(previous_review_results.get('bdl', {}).get('issues', []))} issues)

Please review the corrected code to verify that previous issues have been resolved.
If issues persist or new issues are found, document them clearly.
"""
        
        # 先写入代码文件（确保文件存在）
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
            security_prompt = f"""{iteration_context}

Review this React code for security issues:

Code file: {code_file_path}
React Code:
{generated_code}

Please provide a thorough security review focusing on all security vulnerabilities."""
            security_result_obj = security_review_agent.run(security_prompt, return_structured=True)
        except Exception as e:
            logger.error(f"Error in security review: {str(e)}")
            security_result_obj = None
        
        try:
            logger.info("Running build review...")
            build_prompt = f"""{iteration_context}

Review this React code for build errors and code quality:

Code file: {code_file_path}
Working directory: {output_path}
React Code:
{generated_code}

Please check for compilation errors, syntax issues, missing dependencies, and code quality problems.
If a build command can be run, use it to verify compilation."""
            build_result_obj = build_review_agent.run(build_prompt, return_structured=True)
        except Exception as e:
            logger.error(f"Error in build review: {str(e)}")
            build_result_obj = None
        
        try:
            logger.info("Running BDL review...")
            bdl_prompt = f"""{iteration_context}

Review this React code for BDL best practices and compliance:

Code file: {code_file_path}
React Code:
{generated_code}

Please verify BDL component usage, styling approach, and compliance with BDL conventions."""
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
        """
        步骤6: 修正代码
        优化：提供完整的 review 结果上下文，包括所有问题和建议，以及迭代历史
        """
        code_file_path = state["code_file_path"]
        generated_code = state["generated_code"]
        review_results = state["review_results"]
        iteration = state.get("iteration_count", 0)
        
        # 构建详细的 review 结果摘要
        security_data = review_results.get('security', {})
        build_data = review_results.get('build', {})
        bdl_data = review_results.get('bdl', {})
        
        security_issues = security_data.get('issues', [])
        security_recommendations = security_data.get('recommendations', [])
        security_severity = security_data.get('severity', 'unknown')
        
        build_issues = build_data.get('issues', [])
        build_recommendations = build_data.get('recommendations', [])
        build_errors = build_data.get('errors', [])
        build_warnings = build_data.get('warnings', [])
        build_status = build_data.get('build_status', 'unknown')
        
        bdl_issues = bdl_data.get('issues', [])
        bdl_recommendations = bdl_data.get('recommendations', [])
        bdl_compliance_issues = bdl_data.get('compliance_issues', [])
        bdl_api_issues = bdl_data.get('api_usage_issues', [])
        
        # 构建完整的 review 结果提示
        review_summary = f"""
=== CODE CORRECTION REQUEST ===
Iteration: {iteration + 1}
Code File: {code_file_path}

=== CURRENT CODE TO CORRECT ===
{generated_code}

=== REVIEW RESULTS - ALL ISSUES TO FIX ===

1. SECURITY REVIEW:
   Status: {'PASSED' if security_data.get('passed', False) else 'FAILED'}
   Severity: {security_severity}
   
   Issues Found ({len(security_issues)}):
"""
        for i, issue in enumerate(security_issues, 1):
            review_summary += f"   {i}. {issue}\n"
        
        review_summary += f"""
   Recommendations ({len(security_recommendations)}):
"""
        for i, rec in enumerate(security_recommendations, 1):
            review_summary += f"   {i}. {rec}\n"
        
        review_summary += f"""
   Full Details: {security_data.get('details', 'N/A')}

2. BUILD REVIEW:
   Status: {'PASSED' if build_data.get('passed', False) else 'FAILED'}
   Build Status: {build_status}
   
   Errors Found ({len(build_errors)}):
"""
        for i, error in enumerate(build_errors, 1):
            review_summary += f"   {i}. {error}\n"
        
        review_summary += f"""
   Warnings ({len(build_warnings)}):
"""
        for i, warning in enumerate(build_warnings, 1):
            review_summary += f"   {i}. {warning}\n"
        
        review_summary += f"""
   Other Issues ({len(build_issues)}):
"""
        for i, issue in enumerate(build_issues, 1):
            review_summary += f"   {i}. {issue}\n"
        
        review_summary += f"""
   Recommendations ({len(build_recommendations)}):
"""
        for i, rec in enumerate(build_recommendations, 1):
            review_summary += f"   {i}. {rec}\n"
        
        review_summary += f"""
   Full Details: {build_data.get('details', 'N/A')}

3. BDL REVIEW:
   Status: {'PASSED' if bdl_data.get('passed', False) else 'FAILED'}
   
   Compliance Issues ({len(bdl_compliance_issues)}):
"""
        for i, issue in enumerate(bdl_compliance_issues, 1):
            review_summary += f"   {i}. {issue}\n"
        
        review_summary += f"""
   API Usage Issues ({len(bdl_api_issues)}):
"""
        for i, issue in enumerate(bdl_api_issues, 1):
            review_summary += f"   {i}. {issue}\n"
        
        review_summary += f"""
   Other Issues ({len(bdl_issues)}):
"""
        for i, issue in enumerate(bdl_issues, 1):
            review_summary += f"   {i}. {issue}\n"
        
        review_summary += f"""
   Recommendations ({len(bdl_recommendations)}):
"""
        for i, rec in enumerate(bdl_recommendations, 1):
            review_summary += f"   {i}. {rec}\n"
        
        review_summary += f"""
   Full Details: {bdl_data.get('details', 'N/A')}

=== CORRECTION REQUIREMENTS ===

CRITICAL PRIORITY (Must Fix):
- Build errors (must compile successfully)
- Critical security vulnerabilities
- High severity security issues

HIGH PRIORITY (Should Fix):
- Security vulnerabilities (all severities)
- Build warnings
- BDL compliance issues

MEDIUM PRIORITY (Nice to Fix):
- Code quality improvements
- BDL best practice improvements
- Performance optimizations

IMPORTANT NOTES:
- Fix ALL issues mentioned above
- Prioritize critical and high-severity issues first
- Ensure the corrected code COMPILES without errors
- Maintain ALL original functionality
- Follow recommendations provided by each review agent
- If this is iteration {iteration + 1}, ensure previous fixes are not reverted

Provide the COMPLETE corrected code, not just changes.

CRITICAL OUTPUT REQUIREMENTS:
- Output ONLY the complete, corrected React component code
- The code must compile without errors
- Include all necessary imports
- Include all prop definitions
- Be ready to save directly to a .jsx file
- Address ALL issues listed above"""
        
        prompt = review_summary
        
        try:
            correct_agent = _get_agent(CorrectAgent, "correct")
            result = correct_agent.run(prompt)
            
            # 提取修正后的代码（使用改进的提取方法）
            from utils.code_validator import improve_code_extraction, validate_react_code
            
            corrected_code = improve_code_extraction(str(result))
            
            # 验证修正后的代码
            is_valid, warnings, errors = validate_react_code(corrected_code)
            
            if errors:
                logger.warning(f"Corrected code still has basic errors: {errors}")
            if warnings:
                logger.info(f"Corrected code warnings: {warnings}")
            
            # 即使有基本错误也继续，可能需要在后续迭代中修复
            
            logger.info(f"Code corrected (iteration {iteration + 1}). Code length: {len(corrected_code)} chars")
            
            # 立即写入修正后的代码，确保 review 能读取最新版本
            try:
                from tools import write_file
                write_file(code_file_path, corrected_code)
                logger.info(f"Corrected code written to: {code_file_path}")
            except Exception as e:
                logger.warning(f"Could not write corrected code to file: {str(e)}")
            
            return {
                **state,
                "generated_code": corrected_code,
                "iteration_count": iteration + 1,
                # 保留 review_results 以便下次 review 时比较
            }
        except Exception as e:
            logger.error(f"Error correcting code: {str(e)}")
            # 即使修正失败，也增加迭代计数，避免无限循环
            return {
                **state,
                "iteration_count": iteration + 1,
                # generated_code 保持不变，下次 review 会发现问题依旧
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
