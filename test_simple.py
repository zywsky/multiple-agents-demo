#!/usr/bin/env python3
"""
简化测试脚本 - 逐步测试工作流的每个阶段
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_step_by_step():
    """逐步测试工作流的每个阶段"""
    from workflow.graph import create_workflow_graph
    
    # 测试配置
    resource_type = "example/components/button"
    test_data_dir = project_root / "test_data"
    aem_repo_path = str(test_data_dir / "aem_components")
    bdl_library_path = str(test_data_dir / "mui_library")
    output_path = str(project_root / "output" / "test_button")
    
    # 构建组件路径
    component_path = os.path.join(aem_repo_path, "example-button")
    
    print("\n" + "="*60)
    print("AEM to React Component Converter - Step by Step Test")
    print("="*60 + "\n")
    
    print(f"ResourceType: {resource_type}")
    print(f"Component Path: {component_path}")
    print(f"Output Path: {output_path}\n")
    
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
        "review_results": {},
        "review_passed": False,
        "iteration_count": 0,
        "max_iterations": 3,  # 减少迭代次数以加快测试
        "messages": [],
        "dependency_tree": {},
        "dependency_analyses": {}
    }
    
    try:
        # 创建工作流图
        print("Creating workflow graph...")
        graph = create_workflow_graph()
        print("✓ Workflow graph created\n")
        
        # 配置
        config = {"configurable": {"thread_id": "test_button_simple"}}
        
        # 运行工作流（使用 stream 来监控进度）
        print("Starting workflow execution...\n")
        print("-" * 60)
        
        final_state = None
        step_count = 0
        
        # 使用 stream 来逐步执行
        for event in graph.stream(initial_state, config=config):
            step_count += 1
            node_name = list(event.keys())[0] if event else "unknown"
            print(f"Step {step_count}: {node_name}")
            
            # 更新状态
            if event:
                state_update = list(event.values())[0]
                if isinstance(state_update, dict):
                    initial_state.update(state_update)
                    final_state = initial_state.copy()
            
            # 显示关键信息
            if node_name == "collect_files":
                files_count = final_state.get("files", []) if final_state else []
                print(f"  → Collected {len(files_count)} files")
            elif node_name == "analyze_aem_files":
                analyses_count = len(final_state.get("file_analyses", [])) if final_state else 0
                print(f"  → Analyzed {analyses_count} files")
            elif node_name == "select_bdl_components":
                selected = final_state.get("selected_bdl_components", []) if final_state else []
                print(f"  → Selected {len(selected)} BDL components")
            elif node_name == "write_code":
                code_file = final_state.get("code_file_path", "") if final_state else ""
                if code_file:
                    print(f"  → Code written to: {code_file}")
            elif node_name == "review_code":
                passed = final_state.get("review_passed", False) if final_state else False
                iterations = final_state.get("iteration_count", 0) if final_state else 0
                print(f"  → Review passed: {passed} (iteration {iterations})")
        
        print("-" * 60 + "\n")
        
        # 检查最终结果
        if final_state:
            print("=" * 60)
            print("Final Results")
            print("=" * 60)
            
            review_passed = final_state.get("review_passed", False)
            code_file = final_state.get("code_file_path", "")
            iterations = final_state.get("iteration_count", 0)
            
            print(f"Review Passed: {'✅ YES' if review_passed else '❌ NO'}")
            print(f"Iterations: {iterations}")
            
            if code_file and os.path.exists(code_file):
                print(f"\nGenerated Code File: {code_file}")
                with open(code_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                    print(f"Code Length: {len(code)} characters")
                    print(f"\nFirst 800 characters:")
                    print("-" * 60)
                    print(code[:800])
                    print("-" * 60)
                
                # 检查代码质量
                issues = []
                if "import React" not in code and "import { " not in code:
                    issues.append("Missing React import")
                if "export" not in code:
                    issues.append("Missing export statement")
                if code.count("<") != code.count(">"):
                    issues.append("JSX tag mismatch")
                
                if issues:
                    print(f"\n⚠️ Code Issues Found:")
                    for issue in issues:
                        print(f"  - {issue}")
                else:
                    print("\n✅ Code looks good!")
            else:
                print("\n⚠️ No code file generated")
            
            return review_passed
        else:
            print("\n❌ Workflow did not complete")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_step_by_step()
    sys.exit(0 if success else 1)
