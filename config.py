"""
配置管理模块
统一管理项目配置，支持环境变量和默认值
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


class Config:
    """项目配置类"""
    
    # 项目根目录
    PROJECT_ROOT = Path(__file__).parent.absolute()
    
    # AEM 相关路径
    AEM_REPO_PATH: str = os.getenv(
        "AEM_REPO_PATH",
        str(PROJECT_ROOT / "test_data" / "aem_components")
    )
    
    # BDL 组件库路径
    BDL_LIBRARY_PATH: str = os.getenv(
        "BDL_LIBRARY_PATH",
        str(PROJECT_ROOT / "test_data" / "mui_library")
    )
    
    # 输出路径
    OUTPUT_PATH: str = os.getenv(
        "OUTPUT_PATH",
        str(PROJECT_ROOT / "output")
    )
    
    # 组件注册表路径（相对于输出路径）
    COMPONENT_REGISTRY_PATH: str = os.getenv(
        "COMPONENT_REGISTRY_PATH",
        str(PROJECT_ROOT / "output")
    )
    
    # LLM API 配置
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "ep-20250118160000-xxxxx")
    
    # 工作流配置
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "8192"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)
    
    @classmethod
    def normalize_path(cls, path: str) -> str:
        """标准化路径，支持相对路径和绝对路径"""
        path_obj = Path(path)
        if not path_obj.is_absolute():
            # 相对路径相对于项目根目录
            path_obj = cls.PROJECT_ROOT / path_obj
        return str(path_obj.resolve())
    
    @classmethod
    def get_aem_repo_path(cls) -> str:
        """获取AEM仓库路径（标准化）"""
        return cls.normalize_path(cls.AEM_REPO_PATH)
    
    @classmethod
    def get_bdl_library_path(cls) -> str:
        """获取BDL组件库路径（标准化）"""
        return cls.normalize_path(cls.BDL_LIBRARY_PATH)
    
    @classmethod
    def get_output_path(cls) -> str:
        """获取输出路径（标准化）"""
        return cls.normalize_path(cls.OUTPUT_PATH)
    
    @classmethod
    def get_component_registry_path(cls) -> str:
        """获取组件注册表路径（标准化）"""
        return cls.normalize_path(cls.COMPONENT_REGISTRY_PATH)
    
    @classmethod
    def validate(cls) -> list[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 检查必需路径是否存在
        aem_path = Path(cls.get_aem_repo_path())
        if not aem_path.exists():
            errors.append(f"AEM仓库路径不存在: {aem_path}")
        
        bdl_path = Path(cls.get_bdl_library_path())
        if not bdl_path.exists():
            errors.append(f"BDL组件库路径不存在: {bdl_path}")
        
        # 检查LLM配置
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY 未设置")
        
        return errors
    
    @classmethod
    def print_config(cls):
        """打印当前配置（隐藏敏感信息）"""
        print("=" * 60)
        print("项目配置")
        print("=" * 60)
        print(f"项目根目录: {cls.PROJECT_ROOT}")
        print(f"AEM仓库路径: {cls.get_aem_repo_path()}")
        print(f"BDL组件库路径: {cls.get_bdl_library_path()}")
        print(f"输出路径: {cls.get_output_path()}")
        print(f"组件注册表路径: {cls.get_component_registry_path()}")
        print(f"LLM API Base: {cls.LLM_API_BASE[:50] + '...' if len(cls.LLM_API_BASE) > 50 else cls.LLM_API_BASE}")
        print(f"LLM Model: {cls.LLM_MODEL}")
        print(f"最大迭代次数: {cls.MAX_ITERATIONS}")
        print(f"日志级别: {cls.LOG_LEVEL}")
        print("=" * 60)


# 创建全局配置实例
config = Config()
