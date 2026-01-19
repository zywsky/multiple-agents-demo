"""
测试跨平台路径处理
"""
import sys
import os
from utils.path_utils import normalize_path, validate_path, format_path_for_display

def test_path_normalization():
    """测试路径规范化"""
    print("=== 测试路径规范化 ===\n")
    
    test_cases = [
        # (输入, 描述)
        ("./test", "相对路径"),
        ("../test", "上级目录相对路径"),
        ("~/test", "用户目录"),
        ("test_data/aem_components/example-button", "相对路径（多级）"),
        ("C:\\Users\\test", "Windows 绝对路径（反斜杠）"),
        ("C:/Users/test", "Windows 绝对路径（正斜杠）"),
        ("/home/user/test", "Unix 绝对路径"),
    ]
    
    for path_input, description in test_cases:
        try:
            normalized = normalize_path(path_input)
            print(f"✓ {description}:")
            print(f"  输入: {path_input}")
            print(f"  输出: {normalized}")
            print()
        except Exception as e:
            print(f"✗ {description}: {path_input} - 错误: {str(e)}\n")


def test_path_validation():
    """测试路径验证"""
    print("=== 测试路径验证 ===\n")
    
    # 测试存在的路径
    test_path = normalize_path("test_data/aem_components/example-button")
    is_valid, error_msg = validate_path(test_path, must_exist=True, must_be_dir=True)
    
    print(f"测试路径: {test_path}")
    print(f"验证结果: {'✓ 有效' if is_valid else '✗ 无效'}")
    if error_msg:
        print(f"错误信息: {error_msg}")
    print()


def test_cross_platform():
    """测试跨平台特性"""
    print("=== 跨平台特性 ===\n")
    
    print(f"当前操作系统: {os.name}")
    print(f"路径分隔符: {os.sep}")
    print()
    
    # 测试不同格式的路径
    paths = [
        "test_data/aem_components/example-button",  # Unix 风格
        "test_data\\aem_components\\example-button",  # Windows 风格
    ]
    
    for path in paths:
        normalized = normalize_path(path)
        print(f"输入: {path}")
        print(f"规范化: {normalized}")
        print(f"显示格式: {format_path_for_display(normalized)}")
        print()


if __name__ == "__main__":
    print("跨平台路径处理测试\n")
    print("=" * 50)
    print()
    
    test_path_normalization()
    test_path_validation()
    test_cross_platform()
    
    print("=" * 50)
    print("\n测试完成！")
