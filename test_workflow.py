#!/usr/bin/env python3
"""
快速测试工作流脚本
用于测试 AEM 组件转换工作流
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from workflow.graph import create_workflow_graph
from langgraph.graph import StateGraph
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_component(resource_type: str, component_name: str):
    """测试单个组件转换"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing Component: {component_name}")
    logger.info(f"ResourceType: {resource_type}")
    logger.info(f"{'='*60}\n")
    
    # 获取测试数据路径
    test_data_dir = project_root / "test_data"
    aem_repo_path = str(test_data_dir / "aem_components")
    bdl_library_path = str(test_data_dir / "mui_library")
    output_path = str(project_root / "output" / component_name)
    
    # 验证路径
    if not os.path.exists(aem_repo_path):
        logger.error(f"AEM repo path not found: {aem_repo_path}")
        return False
    
    if not os.path.exists(bdl_library_path):
        logger.warning(f"BDL library path not found: {bdl_library_path}")
        logger.warning("Will continue without BDL library...")
    
    # 构建组件路径
    # resourceType 格式可能是 "example/components/button" 或 "example.components.button"
    # 但实际目录名是 "example-button" 和 "example-card"
    # 需要将 resourceType 转换为实际的目录名
    resource_type_parts = resource_type.replace(".", "/").split("/")
    # 取最后一部分作为组件名，并添加 example- 前缀（如果是 example 开头的）
    if len(resource_type_parts) >= 2 and resource_type_parts[0] == "example":
        component_dir_name = f"example-{resource_type_parts[-1]}"
    else:
        # 如果不是 example 开头，尝试直接使用最后一部分
        component_dir_name = resource_type_parts[-1]
    
    component_path = os.path.join(aem_repo_path, component_dir_name)
    if not os.path.exists(component_path):
        logger.error(f"Component path not found: {component_path}")
        logger.error(f"Expected resourceType format: example/components/button -> example-button")
        return False
    
    logger.info(f"AEM Repo Path: {aem_repo_path}")
    logger.info(f"Component Path: {component_path}")
    logger.info(f"BDL Library Path: {bdl_library_path}")
    logger.info(f"Output Path: {output_path}\n")
    
    # 创建输出目录
    os.makedirs(output_path, exist_ok=True)
    
    # 创建初始状态
    initial_state = {
        "resource_type": resource_type,
        "aem_repo_path": aem_repo_path,
        "component_path": component_path,
        "bdl_library_path": bdl_library_path,
        "output_path": output_path,
        "files": [],
        "file_analyses": [],
        "selected_bdl_components": [],
        "aem_component_summary": {},
        "generated_code": "",
        "code_file_path": "",
        "css_file_path": "",
        "review_results": {},
        "review_passed": False,
        "iteration_count": 0,
        "max_iterations": 5,
        "messages": [],
        "dependency_tree": {},
        "dependency_analyses": {}
    }
    
    try:
        # 创建工作流图
        graph = create_workflow_graph()
        
        # 运行工作流
        logger.info("Starting workflow...\n")
        # 添加 checkpointer 配置
        config = {"configurable": {"thread_id": f"test_{component_name.replace(' ', '_')}"}}
        final_state = graph.invoke(initial_state, config=config)
        
        # 检查结果
        if final_state.get("review_passed"):
            logger.info(f"\n{'='*60}")
            logger.info("✅ Workflow completed successfully!")
            logger.info(f"{'='*60}\n")
            
            code_file = final_state.get("code_file_path", "")
            if code_file and os.path.exists(code_file):
                logger.info(f"Generated React component: {code_file}")
                with open(code_file, 'r') as f:
                    code = f.read()
                    logger.info(f"Code length: {len(code)} characters")
                    logger.info(f"First 500 characters:\n{code[:500]}\n")
            
            return True
        else:
            logger.warning(f"\n{'='*60}")
            logger.warning("⚠️ Workflow completed but review did not pass")
            logger.warning(f"Iterations: {final_state.get('iteration_count', 0)}")
            logger.warning(f"{'='*60}\n")
            return False
            
    except Exception as e:
        logger.error(f"\n{'='*60}")
        logger.error(f"❌ Workflow failed: {e}")
        logger.error(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*60)
    print("AEM to React Component Converter - Test Suite")
    print("="*60 + "\n")
    
    # 测试组件列表
    test_components = [
        {
            "resource_type": "example/components/button",
            "name": "Button Component (Simple)"
        },
        {
            "resource_type": "example/components/card",
            "name": "Card Component (Complex with Dependencies)"
        }
    ]
    
    print("Available test components:")
    for i, comp in enumerate(test_components, 1):
        print(f"  {i}. {comp['name']} ({comp['resource_type']})")
    print()
    
    # 选择要测试的组件
    if len(sys.argv) > 1:
        try:
            choice = int(sys.argv[1])
            if 1 <= choice <= len(test_components):
                selected = test_components[choice - 1]
            else:
                print(f"Invalid choice. Using first component.")
                selected = test_components[0]
        except ValueError:
            print(f"Invalid argument. Using first component.")
            selected = test_components[0]
    else:
        # 默认测试所有组件
        print("Testing all components...\n")
        results = []
        for comp in test_components:
            result = test_component(comp["resource_type"], comp["name"])
            results.append((comp["name"], result))
        
        # 打印总结
        print("\n" + "="*60)
        print("Test Summary")
        print("="*60)
        for name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"  {name}: {status}")
        print("="*60 + "\n")
        return
    
    # 测试选定的组件
    test_component(selected["resource_type"], selected["name"])


if __name__ == "__main__":
    main()
