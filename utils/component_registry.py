"""
组件注册表
用于跟踪已生成的React组件，支持组件复用
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class ComponentRegistry:
    """组件注册表，跟踪已生成的React组件"""
    
    def __init__(self, registry_file: Optional[str] = None):
        """
        初始化组件注册表
        
        Args:
            registry_file: 注册表文件路径（JSON格式）
        """
        self.registry_file = registry_file or ".component_registry.json"
        self.registry: Dict[str, Dict[str, str]] = {}
        self.load_registry()
    
    def load_registry(self):
        """从文件加载注册表"""
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    self.registry = json.load(f)
                logger.info(f"Loaded component registry with {len(self.registry)} entries")
            except Exception as e:
                logger.warning(f"Failed to load component registry: {e}")
                self.registry = {}
        else:
            self.registry = {}
    
    def save_registry(self):
        """保存注册表到文件"""
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved component registry with {len(self.registry)} entries")
        except Exception as e:
            logger.warning(f"Failed to save component registry: {e}")
    
    def register_component(
        self,
        aem_resource_type: str,
        react_component_name: str,
        react_component_path: str,
        css_path: Optional[str] = None
    ):
        """
        注册已生成的React组件
        
        Args:
            aem_resource_type: AEM组件的resourceType
            react_component_name: React组件名称
            react_component_path: React组件文件路径
            css_path: CSS文件路径（可选）
        """
        self.registry[aem_resource_type] = {
            'react_component_name': react_component_name,
            'react_component_path': react_component_path,
            'css_path': css_path,
            'aem_resource_type': aem_resource_type
        }
        self.save_registry()
        logger.info(f"Registered component: {aem_resource_type} -> {react_component_name}")
    
    def get_component(self, aem_resource_type: str) -> Optional[Dict[str, str]]:
        """
        获取已生成的React组件信息
        
        Args:
            aem_resource_type: AEM组件的resourceType
        
        Returns:
            组件信息字典，如果不存在返回None
        """
        return self.registry.get(aem_resource_type)
    
    def has_component(self, aem_resource_type: str) -> bool:
        """
        检查是否已生成React组件
        
        Args:
            aem_resource_type: AEM组件的resourceType
        
        Returns:
            如果已生成返回True，否则返回False
        """
        component = self.get_component(aem_resource_type)
        if component:
            # 验证文件是否真的存在
            react_path = component.get('react_component_path', '')
            if react_path and os.path.exists(react_path):
                return True
            else:
                # 文件不存在，从注册表中移除
                logger.warning(f"Registered component file not found: {react_path}, removing from registry")
                self.registry.pop(aem_resource_type, None)
                self.save_registry()
                return False
        return False
    
    def get_dependency_components(
        self,
        dependency_resource_types: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        获取依赖组件的已生成React组件信息
        
        Args:
            dependency_resource_types: 依赖组件的resourceType列表
        
        Returns:
            字典：{resource_type: component_info}
        """
        existing_components = {}
        for resource_type in dependency_resource_types:
            component = self.get_component(resource_type)
            if component and self.has_component(resource_type):
                existing_components[resource_type] = component
        return existing_components
    
    def list_all_components(self) -> Dict[str, Dict[str, str]]:
        """列出所有已注册的组件"""
        return self.registry.copy()


def get_component_registry(output_path: str) -> ComponentRegistry:
    """
    获取组件注册表实例
    
    Args:
        output_path: 输出路径，注册表文件将保存在此路径下
    
    Returns:
        ComponentRegistry实例
    """
    registry_file = os.path.join(output_path, ".component_registry.json")
    return ComponentRegistry(registry_file)
