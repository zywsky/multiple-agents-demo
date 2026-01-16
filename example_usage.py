"""
示例使用脚本
演示如何使用工作流转换 AEM 组件
"""
import os
from dotenv import load_dotenv
from workflow import create_workflow_graph, WorkflowState

load_dotenv()


def example_usage():
    """示例用法"""
    
    # 示例路径（请根据实际情况修改）
    component_path = "/path/to/aem/components/my-component"
    mui_library_path = "/path/to/mui/packages"
    output_path = "./output"
    
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
