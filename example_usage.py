"""
示例使用脚本
演示如何使用工作流转换 AEM 组件（使用 BDL）
"""
import os
from workflow import create_workflow_graph, WorkflowState
from config import config

def example_usage():
    """示例用法"""
    
    # 使用配置管理模块获取路径
    aem_repo_path = config.get_aem_repo_path()
    bdl_library_path = config.get_bdl_library_path()
    output_path = config.get_output_path()
    
    # 示例 resourceType
    resource_type = "example/components/button"
    
    # 构建组件路径
    from pathlib import Path
    component_path = str(Path(aem_repo_path) / resource_type.replace(".", os.sep))
    
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
        "max_iterations": config.MAX_ITERATIONS,
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
