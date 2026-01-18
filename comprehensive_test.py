#!/usr/bin/env python3
"""
全面测试工作流脚本
测试所有场景，涵盖各种情况
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from workflow.graph import create_workflow_graph
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult:
    """测试结果类"""
    def __init__(self, component_name, resource_type):
        self.component_name = component_name
        self.resource_type = resource_type
        self.start_time = None
        self.end_time = None
        self.success = False
        self.errors = []
        self.warnings = []
        self.generated_files = []
        self.review_results = {}
        self.iterations = 0
        self.duration = 0
    
    def to_dict(self):
        return {
            "component_name": self.component_name,
            "resource_type": self.resource_type,
            "success": self.success,
            "duration_seconds": self.duration,
            "iterations": self.iterations,
            "generated_files": self.generated_files,
            "errors": self.errors,
            "warnings": self.warnings,
            "review_summary": {
                "passed": self.review_results.get("review_passed", False),
                "core_reviews": {
                    "security": self.review_results.get("security", {}).get("passed", False),
                    "build_execution": self.review_results.get("build_execution", {}).get("passed", False),
                    "bdl_component_usage": self.review_results.get("bdl_component_usage", {}).get("passed", False),
                    "css_import": self.review_results.get("css_import", {}).get("passed", False),
                    "component_reference": self.review_results.get("component_reference", {}).get("passed", False),
                },
                "consistency_reviews": {
                    "component_completeness": self.review_results.get("component_completeness", {}).get("passed", False),
                    "props_consistency": self.review_results.get("props_consistency", {}).get("passed", False),
                    "style_consistency": self.review_results.get("style_consistency", {}).get("passed", False),
                    "functionality_consistency": self.review_results.get("functionality_consistency", {}).get("passed", False),
                }
            }
        }


def test_component(resource_type: str, component_name: str, test_scenario: str = "") -> TestResult:
    """测试单个组件转换"""
    result = TestResult(component_name, resource_type)
    result.start_time = datetime.now()
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing Component: {component_name}")
    logger.info(f"ResourceType: {resource_type}")
    if test_scenario:
        logger.info(f"Test Scenario: {test_scenario}")
    logger.info(f"{'='*80}\n")
    
    try:
        # 获取测试数据路径
        test_data_dir = project_root / "test_data"
        aem_repo_path = str(test_data_dir / "aem_components")
        bdl_library_path = str(test_data_dir / "mui_library")
        output_path = str(project_root / "output" / component_name.replace(" ", "_"))
        
        # 验证路径
        if not os.path.exists(aem_repo_path):
            result.errors.append(f"AEM repo path not found: {aem_repo_path}")
            return result
        
        # 构建组件路径
        resource_type_parts = resource_type.replace(".", "/").split("/")
        if len(resource_type_parts) >= 2 and resource_type_parts[0] == "example":
            component_dir_name = f"example-{resource_type_parts[-1]}"
        else:
            component_dir_name = resource_type_parts[-1]
        
        component_path = os.path.join(aem_repo_path, component_dir_name)
        if not os.path.exists(component_path):
            result.errors.append(f"Component path not found: {component_path}")
            return result
        
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
            "max_iterations": 3,  # 限制迭代次数以加快测试
            "messages": [],
            "dependency_tree": {},
            "dependency_analyses": {}
        }
        
        # 创建工作流图
        graph = create_workflow_graph()
        
        # 运行工作流
        logger.info("Starting workflow...\n")
        config = {"configurable": {"thread_id": f"test_{component_name.replace(' ', '_')}"}}
        final_state = graph.invoke(initial_state, config=config)
        
        # 记录结果
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds()
        result.iterations = final_state.get("iteration_count", 0)
        result.review_results = final_state.get("review_results", {})
        result.success = final_state.get("review_passed", False)
        
        # 检查生成的文件
        code_file = final_state.get("code_file_path", "")
        css_file = final_state.get("css_file_path", "")
        
        if code_file and os.path.exists(code_file):
            result.generated_files.append(code_file)
            with open(code_file, 'r') as f:
                code = f.read()
                # 检查代码质量
                if len(code) < 100:
                    result.warnings.append(f"Generated code is very short ({len(code)} chars)")
                if '```' in code:
                    result.errors.append("Generated code contains markdown code block markers")
                if 'import React' not in code and 'import { useState' not in code:
                    result.warnings.append("Generated code may not import React correctly")
        
        if css_file and os.path.exists(css_file):
            result.generated_files.append(css_file)
        
        # 检查组件注册表
        registry_file = os.path.join(output_path, ".component_registry.json")
        if os.path.exists(registry_file):
            result.generated_files.append(registry_file)
            with open(registry_file, 'r') as f:
                registry = json.load(f)
                if resource_type in registry:
                    logger.info(f"✅ Component registered: {resource_type} -> {registry[resource_type].get('react_component_name', 'Unknown')}")
                else:
                    result.warnings.append(f"Component not found in registry: {resource_type}")
        
        # 检查review结果
        if result.review_results:
            core_reviews = ["security", "build_execution", "bdl_component_usage", "css_import", "component_reference"]
            for review_name in core_reviews:
                review_data = result.review_results.get(review_name, {})
                if not review_data.get("passed", False):
                    result.warnings.append(f"Core review failed: {review_name}")
        
        if result.success:
            logger.info(f"\n{'='*80}")
            logger.info("✅ Workflow completed successfully!")
            logger.info(f"Duration: {result.duration:.2f} seconds")
            logger.info(f"Iterations: {result.iterations}")
            logger.info(f"Generated files: {len(result.generated_files)}")
            logger.info(f"{'='*80}\n")
        else:
            logger.warning(f"\n{'='*80}")
            logger.warning("⚠️ Workflow completed but review did not pass")
            logger.warning(f"Duration: {result.duration:.2f} seconds")
            logger.warning(f"Iterations: {result.iterations}")
            logger.warning(f"{'='*80}\n")
        
        return result
        
    except Exception as e:
        result.end_time = datetime.now()
        result.duration = (result.end_time - result.start_time).total_seconds() if result.start_time else 0
        result.errors.append(str(e))
        logger.error(f"\n{'='*80}")
        logger.error(f"❌ Workflow failed: {e}")
        logger.error(f"{'='*80}\n")
        import traceback
        traceback.print_exc()
        return result


def main():
    """主函数 - 全面测试所有场景"""
    print("\n" + "="*80)
    print("AEM to React Component Converter - Comprehensive Test Suite")
    print("="*80 + "\n")
    
    # 定义测试场景
    test_scenarios = [
        {
            "resource_type": "example/components/button",
            "name": "Button Component (Simple)",
            "scenario": "基础组件测试 - 无依赖，简单结构",
            "expected_dependencies": 0
        },
        {
            "resource_type": "example/components/card",
            "name": "Card Component (Medium)",
            "scenario": "中等组件测试 - 依赖button，包含多个功能",
            "expected_dependencies": 1
        },
        {
            "resource_type": "example/components/container",
            "name": "Container Component (Large)",
            "scenario": "大组件测试 - 依赖card和button，多层依赖",
            "expected_dependencies": 2
        },
        {
            "resource_type": "example/components/page",
            "name": "Page Component (Extra Large)",
            "scenario": "超大组件测试 - 依赖container、card、button，复杂依赖关系",
            "expected_dependencies": 3
        }
    ]
    
    print("测试场景列表：\n")
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"  {i}. {scenario['name']}")
        print(f"     ResourceType: {scenario['resource_type']}")
        print(f"     场景: {scenario['scenario']}")
        print(f"     预期依赖: {scenario['expected_dependencies']} 个组件")
        print()
    
    print("="*80)
    print("开始全面测试...")
    print("="*80 + "\n")
    
    # 执行所有测试
    results = []
    for scenario in test_scenarios:
        result = test_component(
            scenario["resource_type"],
            scenario["name"],
            scenario["scenario"]
        )
        results.append((scenario, result))
    
    # 生成测试报告
    print("\n" + "="*80)
    print("测试总结报告")
    print("="*80 + "\n")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result.success)
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ✅")
    print(f"失败: {failed_tests} ❌")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%\n")
    
    print("详细结果：\n")
    for scenario, result in results:
        status = "✅ PASSED" if result.success else "❌ FAILED"
        print(f"{status} - {result.component_name}")
        print(f"  ResourceType: {result.resource_type}")
        print(f"  持续时间: {result.duration:.2f} 秒")
        print(f"  迭代次数: {result.iterations}")
        print(f"  生成文件: {len(result.generated_files)} 个")
        
        if result.errors:
            print(f"  错误: {len(result.errors)} 个")
            for error in result.errors[:3]:  # 只显示前3个错误
                print(f"    - {error}")
        
        if result.warnings:
            print(f"  警告: {len(result.warnings)} 个")
            for warning in result.warnings[:3]:  # 只显示前3个警告
                print(f"    - {warning}")
        
        # Review结果摘要
        if result.review_results:
            core_passed = sum(1 for name in ["security", "build_execution", "bdl_component_usage", "css_import", "component_reference"]
                            if result.review_results.get(name, {}).get("passed", False))
            print(f"  核心Review通过: {core_passed}/5")
        
        print()
    
    # 保存测试报告到JSON文件
    report_file = project_root / "output" / "test_report.json"
    report_data = {
        "test_time": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "pass_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
        "results": [result.to_dict() for _, result in results]
    }
    
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"测试报告已保存到: {report_file}")
    print("\n" + "="*80)
    
    # 组件复用测试
    print("\n组件复用功能验证：\n")
    registry_files = []
    for _, result in results:
        output_dir = project_root / "output" / result.component_name.replace(" ", "_")
        registry_file = output_dir / ".component_registry.json"
        if registry_file.exists():
            registry_files.append(registry_file)
            with open(registry_file, 'r') as f:
                registry = json.load(f)
                print(f"  {result.component_name}:")
                print(f"    注册组件数: {len(registry)}")
                for resource_type, info in registry.items():
                    print(f"      - {resource_type} -> {info.get('react_component_name', 'Unknown')}")
                print()
    
    if len(registry_files) > 1:
        print("✅ 组件复用功能验证：")
        print("  - 多个组件已生成并注册")
        print("  - 后续组件可以复用已生成的组件")
    else:
        print("⚠️ 组件复用功能验证：")
        print("  - 需要生成多个组件才能验证复用功能")
    
    print("\n" + "="*80)
    print("测试完成！")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
