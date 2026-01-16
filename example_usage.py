"""
示例使用脚本
演示如何使用工作流转换 AEM 组件（使用 BDL）
"""
import os
from dotenv import load_dotenv
from workflow import create_workflow_graph, WorkflowState
from utils.path_utils import normalize_path

load_dotenv()


def example_usage():
    """示例用法"""
    
    # 从 .env 读取配置
    aem_repo_path = normalize_path(os.getenv("AEM_REPO_PATH", "/path/to/aem/repo"))
    bdl_library_path = normalize_path(os.getenv("BDL_LIBRARY_PATH", "/path/to/bdl/library"))
    
    # 示例 resourceType
    resource_type = "example/components/button"
    
    # 构建组件路径
    from pathlib import Path
    component_path = str(Path(aem_repo_path) / resource_type.replace(".", os.sep))
    
    output_path = "./output"
    
    # 创建初始状态
    initial_state: WorkflowState = {
        "resource_type": resource_type,
        "aem_repo_path": aem_repo_path,
        "component_path": component_path,
        "bdl_library_path": bdl_library_path,
        "output_path": output_path,
        "files": [],
        "file_analyses": [],
        "selected_bdl_components": [],
        "generated_code": "",
        "code_file_path": "",
        "review_results": {},
        "review_passed": False,
        "iteration_count": 0,
        "max_iterations": 5,
        "messages": []
    }
    
    # 创建工作流
    app = create_workflow_graph()
    
    # 运行工作流
    config = {"configurable": {"thread_id": "example-1"}}
    
    print("Starting workflow...")
    for state in app.stream(initial_state, config):
        print(f"Current step: {list(state.keys())}")
    
    print("Workflow completed!")


if __name__ == "__main__":
    example_usage()
