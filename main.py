"""
主入口文件
运行 AEM 到 React 转换工作流（使用 BDL 组件库）
支持跨平台路径（Windows、Linux、macOS）
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from workflow import create_workflow_graph, WorkflowState
from utils.path_utils import normalize_path, validate_path, format_path_for_display

load_dotenv()


def load_config() -> dict:
    """从 .env 文件加载配置"""
    config = {}
    
    # 检查必需的配置项
    required_configs = {
        # "OPENAI_API_KEY": "OpenAI API key",
        "AEM_REPO_PATH": "AEM repository path",
        "BDL_LIBRARY_PATH": "BDL library path"
    }
    
    missing_configs = []
    for key, description in required_configs.items():
        value = os.getenv(key)
        if not value or value.startswith("/path/to"):
            missing_configs.append(f"{key} ({description})")
        else:
            config[key] = value
    
    if missing_configs:
        print("Error: Missing or invalid configuration in .env file:")
        for config_name in missing_configs:
            print(f"  - {config_name}")
        print("\nPlease update your .env file with valid paths.")
        print("See .env.example for reference.")
        sys.exit(1)
    
    return config


def build_component_path(aem_repo_path: str, resource_type: str) -> str:
    """
    根据 resourceType 构建完整的组件路径
    
    Args:
        aem_repo_path: AEM repository 根路径
        resource_type: 相对于 AEM repo 的 resourceType（如 "example/components/button" 或 "example.components.button"）
    
    Returns:
        完整的组件路径
    """
    # 规范化路径
    repo_path = normalize_path(aem_repo_path)
    
    # 清理 resourceType（移除前导/尾随斜杠，处理路径分隔符）
    resource_type = resource_type.strip().strip("/").strip("\\")
    
    # 将 resourceType 中的点替换为路径分隔符（AEM resourceType 使用点分隔）
    # 但保留已有的路径分隔符
    if "/" in resource_type or "\\" in resource_type:
        # 已经是路径格式，只规范化分隔符
        resource_type = resource_type.replace("\\", os.sep).replace("/", os.sep)
    else:
        # 是点分隔格式，转换为路径
        resource_type = resource_type.replace(".", os.sep)
    
    # 构建完整路径
    component_path = Path(repo_path) / resource_type
    
    return str(component_path.resolve())


def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    aem_repo_path = normalize_path(config["AEM_REPO_PATH"])
    bdl_library_path = normalize_path(config["BDL_LIBRARY_PATH"])
    
    # 验证配置路径
    is_valid, error_msg = validate_path(aem_repo_path, must_exist=True, must_be_dir=True)
    if not is_valid:
        print(f"Error: Invalid AEM_REPO_PATH: {error_msg}")
        print(f"  Path: {format_path_for_display(aem_repo_path)}")
        sys.exit(1)
    
    is_valid, error_msg = validate_path(bdl_library_path, must_exist=True, must_be_dir=True)
    if not is_valid:
        print(f"Error: Invalid BDL_LIBRARY_PATH: {error_msg}")
        print(f"  Path: {format_path_for_display(bdl_library_path)}")
        sys.exit(1)
    
    # 获取用户输入
    print("=== AEM to React Component Converter (BDL) ===\n")
    print(f"AEM Repository: {format_path_for_display(aem_repo_path)}")
    print(f"BDL Library: {format_path_for_display(bdl_library_path)}\n")
    
    # 获取 resourceType
    resource_type = input("Enter AEM component resourceType (e.g., example/components/button): ").strip()
    if not resource_type:
        print("Error: ResourceType is required")
        sys.exit(1)
    
    # 构建组件路径
    component_path = build_component_path(aem_repo_path, resource_type)
    
    # 验证组件路径
    is_valid, error_msg = validate_path(component_path, must_exist=True, must_be_dir=True)
    if not is_valid:
        print(f"Error: Component not found: {error_msg}")
        print(f"  ResourceType: {resource_type}")
        print(f"  Full path: {format_path_for_display(component_path)}")
        print(f"\nTip: ResourceType should be relative to AEM repository root")
        sys.exit(1)
    
    print(f"✓ Component path: {format_path_for_display(component_path)}")
    
    # 获取并规范化输出路径
    output_path_input = input("Enter output path (default: ./output): ").strip() or "./output"
    output_path = normalize_path(output_path_input)
    print(f"✓ Output path: {format_path_for_display(output_path)}")
    
    max_iterations = input("Enter max review iterations (default: 5): ").strip()
    max_iterations = int(max_iterations) if max_iterations.isdigit() else 5
    
    # 创建初始状态
    initial_state: WorkflowState = {
        "resource_type": resource_type,
        "aem_repo_path": aem_repo_path,
        "component_path": component_path,
        "bdl_library_path": bdl_library_path,
        "output_path": output_path,
        "files": [],
        "dependency_tree": {},
        "dependency_analyses": {},
        "file_analyses": [],
        "selected_bdl_components": [],
        "aem_component_summary": {},  # AEM 组件综合摘要
        "generated_code": "",
        "code_file_path": "",
        "css_file_path": "",
        "review_results": {},
        "review_passed": False,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "messages": []
    }
    
    # 创建工作流
    print("\nCreating workflow...")
    app = create_workflow_graph()
    
    # 运行工作流
    print("Starting workflow execution...\n")
    
    config = {"configurable": {"thread_id": "1"}}
    
    try:
        final_state = None
        for state in app.stream(initial_state, config):
            # 打印当前步骤
            for node_name, node_state in state.items():
                print(f"\n[Step: {node_name}]")
                if node_name == "collect_files" and "files" in node_state:
                    print(f"Found {len(node_state['files'])} files")
                elif node_name == "analyze_aem" and "file_analyses" in node_state:
                    print(f"Analyzed {len(node_state['file_analyses'])} files")
                elif node_name == "select_bdl" and "selected_bdl_components" in node_state:
                    print(f"Selected {len(node_state['selected_bdl_components'])} BDL components")
                elif node_name == "write_code" and "generated_code" in node_state:
                    print(f"Code generated: {node_state.get('code_file_path', 'N/A')}")
                elif node_name == "review_code" and "review_results" in node_state:
                    print("Review completed")
                    # 处理结构化 review 结果
                    security_data = node_state['review_results'].get('security', {})
                    build_data = node_state['review_results'].get('build', {})
                    bdl_data = node_state['review_results'].get('bdl', {})
                    
                    security_passed = security_data.get('passed', False) if isinstance(security_data, dict) else False
                    build_passed = build_data.get('passed', False) if isinstance(build_data, dict) else False
                    bdl_passed = bdl_data.get('passed', False) if isinstance(bdl_data, dict) else False
                    
                    print(f"  Security: {'PASSED' if security_passed else 'ISSUES FOUND'}")
                    if not security_passed and isinstance(security_data, dict):
                        issues = security_data.get('issues', [])
                        if issues:
                            print(f"    - {len(issues)} issue(s) found")
                    
                    print(f"  Build: {'PASSED' if build_passed else 'ISSUES FOUND'}")
                    if not build_passed and isinstance(build_data, dict):
                        issues = build_data.get('issues', [])
                        if issues:
                            print(f"    - {len(issues)} issue(s) found")
                    
                    print(f"  BDL: {'PASSED' if bdl_passed else 'ISSUES FOUND'}")
                    if not bdl_passed and isinstance(bdl_data, dict):
                        issues = bdl_data.get('issues', [])
                        if issues:
                            print(f"    - {len(issues)} issue(s) found")
                elif node_name == "correct_code":
                    print(f"Code corrected (iteration {node_state.get('iteration_count', 0)})")
            
            # 保存最终状态
            final_state = state
        
        print("\n=== Workflow Completed ===")
        
        if final_state:
            final_node_state = list(final_state.values())[0] if final_state else {}
            if final_node_state.get("review_passed"):
                print("✓ All reviews passed!")
            else:
                print("⚠ Some reviews had issues, but workflow completed.")
            
            if final_node_state.get("code_file_path"):
                print(f"\nGenerated component: {final_node_state['code_file_path']}")
    
    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
        sys.exit(130)
    except ValueError as e:
        print(f"\nValidation Error: {str(e)}")
        print("\nPlease check:")
        print("  1. ResourceType is correct")
        print("  2. Component exists in AEM repository")
        print("  3. Paths in .env are correct")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during workflow execution: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\nFor help, check:")
        print("  - CONFIGURATION.md for configuration issues")
        print("  - CODE_REVIEW.md for troubleshooting")
        sys.exit(1)


if __name__ == "__main__":
    main()
