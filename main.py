"""
主入口文件
运行 AEM 到 React 转换工作流
"""
import os
import sys
from dotenv import load_dotenv
from workflow import create_workflow_graph, WorkflowState

load_dotenv()


def main():
    """主函数"""
    # 检查 API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please create a .env file with your OpenAI API key.")
        sys.exit(1)
    
    # 获取用户输入
    print("=== AEM to React Component Converter ===\n")
    
    component_path = input("Enter AEM component path: ").strip()
    if not component_path:
        print("Error: Component path is required")
        sys.exit(1)
    
    mui_library_path = input("Enter MUI library path: ").strip()
    if not mui_library_path:
        print("Error: MUI library path is required")
        sys.exit(1)
    
    output_path = input("Enter output path (default: ./output): ").strip() or "./output"
    
    max_iterations = input("Enter max review iterations (default: 5): ").strip()
    max_iterations = int(max_iterations) if max_iterations.isdigit() else 5
    
    # 创建初始状态
    initial_state: WorkflowState = {
        "component_path": component_path,
        "mui_library_path": mui_library_path,
        "output_path": output_path,
        "files": [],
        "file_analyses": [],
        "selected_mui_components": [],
        "generated_code": "",
        "code_file_path": "",
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
                elif node_name == "select_mui" and "selected_mui_components" in node_state:
                    print(f"Selected {len(node_state['selected_mui_components'])} MUI components")
                elif node_name == "write_code" and "generated_code" in node_state:
                    print(f"Code generated: {node_state.get('code_file_path', 'N/A')}")
                elif node_name == "review_code" and "review_results" in node_state:
                    print("Review completed")
                    print(f"  Security: {'PASSED' if 'no issues' in str(node_state['review_results'].get('security', '')).lower() else 'ISSUES FOUND'}")
                    print(f"  Build: {'PASSED' if 'success' in str(node_state['review_results'].get('build', '')).lower() else 'ISSUES FOUND'}")
                    print(f"  MUI: {'PASSED' if 'compliant' in str(node_state['review_results'].get('mui', '')).lower() else 'ISSUES FOUND'}")
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
    
    except Exception as e:
        print(f"\nError during workflow execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
