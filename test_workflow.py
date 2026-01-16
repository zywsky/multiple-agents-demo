"""
测试工作流脚本
用于验证工作流是否能正常创建和运行（不需要实际的 API key 和路径）
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def test_workflow_creation():
    """测试工作流创建"""
    print("=== 测试工作流创建 ===")
    try:
        from workflow import create_workflow_graph
        app = create_workflow_graph()
        print("✓ Workflow 创建成功")
        return True
    except Exception as e:
        print(f"✗ Workflow 创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """测试所有导入"""
    print("\n=== 测试导入 ===")
    imports_to_test = [
        ("langchain_openai", "ChatOpenAI"),
        ("langchain_core.tools", "tool"),
        ("langchain.agents", "create_agent"),  # 更新为新 API
        ("langchain_core.messages", "HumanMessage"),
        ("langgraph.graph", "StateGraph"),
        ("langgraph.checkpoint.memory", "MemorySaver"),
        ("agents.base_agent", "BaseAgent"),
        ("agents.file_collection_agent", "FileCollectionAgent"),
        ("workflow", "create_workflow_graph"),
    ]
    
    failed = []
    for module, item in imports_to_test:
        try:
            mod = __import__(module, fromlist=[item])
            getattr(mod, item)
            print(f"✓ {module}.{item}")
        except Exception as e:
            print(f"✗ {module}.{item}: {str(e)}")
            failed.append((module, item, str(e)))
    
    if failed:
        print(f"\n失败 {len(failed)} 个导入")
        return False
    else:
        print("\n所有导入测试通过")
        return True


def test_tools():
    """测试工具函数"""
    print("\n=== 测试工具函数 ===")
    try:
        from tools import (
            list_files, read_file, write_file, file_exists,
            create_directory, run_command, get_file_info
        )
        print("✓ 所有工具函数导入成功")
        
        # 测试基本功能（不实际执行）
        test_dir = "/tmp"
        if os.path.exists(test_dir):
            files = list_files(test_dir, recursive=False)
            print(f"✓ list_files 测试: 找到 {len(files)} 个文件")
        
        return True
    except Exception as e:
        print(f"✗ 工具函数测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agent_initialization():
    """测试 Agent 初始化（需要 API key）"""
    print("\n=== 测试 Agent 初始化 ===")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠ 跳过 Agent 初始化测试（需要 OPENAI_API_KEY）")
        return True
    
    try:
        from agents import FileCollectionAgent
        agent = FileCollectionAgent()
        print("✓ FileCollectionAgent 初始化成功")
        return True
    except Exception as e:
        print(f"✗ Agent 初始化失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("开始测试...\n")
    
    results = []
    
    # 测试导入
    results.append(("导入测试", test_imports()))
    
    # 测试工具
    results.append(("工具函数测试", test_tools()))
    
    # 测试工作流创建
    results.append(("工作流创建测试", test_workflow_creation()))
    
    # 测试 Agent 初始化（可选，需要 API key）
    results.append(("Agent 初始化测试", test_agent_initialization()))
    
    # 汇总结果
    print("\n" + "="*50)
    print("测试结果汇总:")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
