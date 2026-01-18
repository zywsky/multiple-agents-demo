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
    
    # 必需配置
    AEM_REPO_PATH: str = os.getenv("AEM_REPO_PATH", "")
    BDL_LIBRARY_PATH: str = os.getenv("BDL_LIBRARY_PATH", "")
    
    # 可选配置
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")
    COMPONENT_REGISTRY_FILE: str = os.getenv("COMPONENT_REGISTRY_FILE", ".component_registry.json")
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "5"))
    
    # API配置（可选）
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4")
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        验证必需配置是否已设置
        
        Returns:
            (is_valid, missing_configs): 是否有效，缺失的配置列表
        """
        missing = []
        
        if not cls.AEM_REPO_PATH or cls.AEM_REPO_PATH.startswith("/path/to"):
            missing.append("AEM_REPO_PATH")
        
        if not cls.BDL_LIBRARY_PATH or cls.BDL_LIBRARY_PATH.startswith("/path/to"):
            missing.append("BDL_LIBRARY_PATH")
        
        return len(missing) == 0, missing
    
    @classmethod
    def get_aem_repo_path(cls) -> Path:
        """获取AEM仓库路径（Path对象）"""
        return Path(cls.AEM_REPO_PATH).expanduser().resolve()
    
    @classmethod
    def get_bdl_library_path(cls) -> Path:
        """获取BDL库路径（Path对象）"""
        return Path(cls.BDL_LIBRARY_PATH).expanduser().resolve()
    
    @classmethod
    def get_output_dir(cls) -> Path:
        """获取输出目录（Path对象）"""
        return Path(cls.OUTPUT_DIR).expanduser().resolve()
    
    @classmethod
    def get_component_registry_path(cls, output_path: Optional[str] = None) -> Path:
        """
        获取组件注册表文件路径
        
        Args:
            output_path: 输出目录路径（可选，默认使用OUTPUT_DIR）
        
        Returns:
            组件注册表文件路径
        """
        if output_path:
            output_dir = Path(output_path)
        else:
            output_dir = cls.get_output_dir()
        
        return output_dir / cls.COMPONENT_REGISTRY_FILE
    
    @classmethod
    def print_config(cls):
        """打印当前配置（用于调试）"""
        print("=" * 60)
        print("Current Configuration")
        print("=" * 60)
        print(f"AEM_REPO_PATH: {cls.AEM_REPO_PATH}")
        print(f"BDL_LIBRARY_PATH: {cls.BDL_LIBRARY_PATH}")
        print(f"OUTPUT_DIR: {cls.OUTPUT_DIR}")
        print(f"COMPONENT_REGISTRY_FILE: {cls.COMPONENT_REGISTRY_FILE}")
        print(f"MAX_ITERATIONS: {cls.MAX_ITERATIONS}")
        print(f"LOG_LEVEL: {cls.LOG_LEVEL}")
        if cls.LOG_FILE:
            print(f"LOG_FILE: {cls.LOG_FILE}")
        print("=" * 60)


def load_config() -> Config:
    """
    加载并验证配置
    
    Returns:
        Config对象
    
    Raises:
        ValueError: 如果必需配置缺失
    """
    config = Config()
    is_valid, missing = config.validate()
    
    if not is_valid:
        error_msg = "Missing required configuration in .env file:\n"
        for config_name in missing:
            error_msg += f"  - {config_name}\n"
        error_msg += "\nPlease update your .env file with valid paths.\n"
        error_msg += "See .env.example for reference."
        raise ValueError(error_msg)
    
    return config
