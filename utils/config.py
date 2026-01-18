"""
配置管理模块
从环境变量加载配置，提供统一的配置访问接口
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


class Config:
    """配置类，从环境变量读取配置"""
    
    # ============================================
    # Required Paths
    # ============================================
    
    @staticmethod
    def get_aem_repo_path() -> Optional[str]:
        """获取AEM仓库根路径"""
        path = os.getenv("AEM_REPO_PATH")
        if path and not path.startswith("/path/to"):
            return os.path.expanduser(path)
        return None
    
    @staticmethod
    def get_bdl_library_path() -> Optional[str]:
        """获取BDL库根路径"""
        path = os.getenv("BDL_LIBRARY_PATH")
        if path and not path.startswith("/path/to"):
            return os.path.expanduser(path)
        return None
    
    # ============================================
    # Optional Paths
    # ============================================
    
    @staticmethod
    def get_output_path() -> str:
        """获取输出路径，默认为./output"""
        path = os.getenv("OUTPUT_PATH", "./output")
        return os.path.expanduser(path)
    
    @staticmethod
    def get_component_registry_path() -> str:
        """获取组件注册表路径"""
        registry_path = os.getenv("COMPONENT_REGISTRY_PATH")
        if registry_path:
            return os.path.expanduser(registry_path)
        
        # 默认在output目录下
        output_path = Config.get_output_path()
        return str(Path(output_path) / ".component_registry.json")
    
    # ============================================
    # Test Data Paths
    # ============================================
    
    @staticmethod
    def get_test_aem_components_path() -> str:
        """获取测试AEM组件路径"""
        path = os.getenv("TEST_AEM_COMPONENTS_PATH", "./test_data/aem_components")
        return os.path.expanduser(path)
    
    @staticmethod
    def get_test_bdl_library_path() -> str:
        """获取测试BDL库路径"""
        path = os.getenv("TEST_BDL_LIBRARY_PATH", "./test_data/mui_library")
        return os.path.expanduser(path)
    
    # ============================================
    # API Configuration
    # ============================================
    
    @staticmethod
    def get_openai_api_key() -> Optional[str]:
        """获取OpenAI API Key"""
        return os.getenv("OPENAI_API_KEY")
    
    @staticmethod
    def get_api_endpoint() -> Optional[str]:
        """获取自定义API端点"""
        return os.getenv("API_ENDPOINT")
    
    @staticmethod
    def get_api_model() -> str:
        """获取API模型名称，默认为gpt-4"""
        return os.getenv("API_MODEL", "gpt-4")
    
    # ============================================
    # Workflow Configuration
    # ============================================
    
    @staticmethod
    def get_max_iterations() -> int:
        """获取最大迭代次数，默认为5"""
        try:
            return int(os.getenv("MAX_ITERATIONS", "5"))
        except ValueError:
            return 5
    
    @staticmethod
    def is_debug() -> bool:
        """是否启用调试模式"""
        return os.getenv("DEBUG", "false").lower() == "true"
    
    # ============================================
    # Validation
    # ============================================
    
    @staticmethod
    def validate_required_paths() -> tuple[bool, list[str]]:
        """
        验证必需的路径配置
        
        Returns:
            (is_valid, missing_paths): 是否有效，缺失的路径列表
        """
        missing = []
        
        aem_path = Config.get_aem_repo_path()
        if not aem_path:
            missing.append("AEM_REPO_PATH")
        elif not os.path.exists(aem_path):
            missing.append(f"AEM_REPO_PATH (path does not exist: {aem_path})")
        
        bdl_path = Config.get_bdl_library_path()
        if not bdl_path:
            missing.append("BDL_LIBRARY_PATH")
        elif not os.path.exists(bdl_path):
            missing.append(f"BDL_LIBRARY_PATH (path does not exist: {bdl_path})")
        
        return len(missing) == 0, missing
    
    @staticmethod
    def validate_test_paths() -> tuple[bool, list[str]]:
        """
        验证测试路径配置
        
        Returns:
            (is_valid, missing_paths): 是否有效，缺失的路径列表
        """
        missing = []
        
        test_aem_path = Config.get_test_aem_components_path()
        if not os.path.exists(test_aem_path):
            missing.append(f"TEST_AEM_COMPONENTS_PATH (path does not exist: {test_aem_path})")
        
        test_bdl_path = Config.get_test_bdl_library_path()
        if not os.path.exists(test_bdl_path):
            missing.append(f"TEST_BDL_LIBRARY_PATH (path does not exist: {test_bdl_path})")
        
        return len(missing) == 0, missing
    
    # ============================================
    # Helper Methods
    # ============================================
    
    @staticmethod
    def print_config_summary():
        """打印配置摘要"""
        print("=" * 60)
        print("Configuration Summary")
        print("=" * 60)
        
        print("\nRequired Paths:")
        aem_path = Config.get_aem_repo_path()
        print(f"  AEM_REPO_PATH: {aem_path or 'NOT SET'}")
        bdl_path = Config.get_bdl_library_path()
        print(f"  BDL_LIBRARY_PATH: {bdl_path or 'NOT SET'}")
        
        print("\nOptional Paths:")
        print(f"  OUTPUT_PATH: {Config.get_output_path()}")
        print(f"  COMPONENT_REGISTRY_PATH: {Config.get_component_registry_path()}")
        
        print("\nTest Data Paths:")
        print(f"  TEST_AEM_COMPONENTS_PATH: {Config.get_test_aem_components_path()}")
        print(f"  TEST_BDL_LIBRARY_PATH: {Config.get_test_bdl_library_path()}")
        
        print("\nWorkflow Configuration:")
        print(f"  MAX_ITERATIONS: {Config.get_max_iterations()}")
        print(f"  DEBUG: {Config.is_debug()}")
        
        print("\nAPI Configuration:")
        api_key = Config.get_openai_api_key()
        print(f"  OPENAI_API_KEY: {'SET' if api_key else 'NOT SET'}")
        print(f"  API_ENDPOINT: {Config.get_api_endpoint() or 'NOT SET'}")
        print(f"  API_MODEL: {Config.get_api_model()}")
        
        print("=" * 60)
        
        # 验证配置
        is_valid, missing = Config.validate_required_paths()
        if not is_valid:
            print("\n⚠️  Warning: Missing or invalid required paths:")
            for path in missing:
                print(f"  - {path}")
            print("\nPlease update your .env file with valid paths.")
        else:
            print("\n✅ All required paths are configured correctly.")


# 创建全局配置实例
config = Config()
