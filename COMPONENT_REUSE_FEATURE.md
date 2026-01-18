# 组件复用功能实现

## 需求说明

在AEM中，组件可能是基于其他已有组件构建的（通过拼接、继承等方式）。在生成React组件时，应该：

1. **优先检查**：依赖组件是否已经生成过React组件
2. **如果有**：在已生成的React组件基础上构建
3. **如果没有**：使用BDL组件库的组件来构建

这样可以：
- 保持组件之间的依赖关系
- 复用已生成的组件
- 更接近AEM的组件构建方式

## 实现方案

### 1. ComponentRegistry（组件注册表）

**文件**: `utils/component_registry.py`

**功能**:
- 跟踪已生成的React组件
- 支持组件查找和验证
- 持久化到JSON文件（`.component_registry.json`）

**核心方法**:
- `register_component()`: 注册已生成的组件
- `get_component()`: 获取组件信息
- `has_component()`: 检查组件是否存在（并验证文件）
- `get_dependency_components()`: 批量获取依赖组件

**数据结构**:
```json
{
  "example/components/button": {
    "react_component_name": "Button",
    "react_component_path": "./Button",
    "css_path": "./Button.module.css",
    "aem_resource_type": "example/components/button"
  }
}
```

### 2. write_code节点增强

**位置**: `workflow/graph.py` 的 `write_code` 函数

**增强内容**:

#### 2.1 检查已生成的依赖组件

```python
# 检查依赖组件是否已经生成过React组件
from utils.component_registry import get_component_registry
component_registry = get_component_registry(output_path)
existing_dependency_components = {}

if dependency_tree:
    root_deps = dependency_tree.get('root', {}).get('dependencies', {})
    dependency_resource_types = list(root_deps.keys())
    
    # 获取已生成的依赖组件
    existing_dependency_components = component_registry.get_dependency_components(
        dependency_resource_types
    )
```

#### 2.2 在Prompt中提供已生成组件信息

```python
=== EXISTING REACT COMPONENTS (FOR DEPENDENCIES) ===
{_build_existing_components_section(existing_dependency_components) if existing_dependency_components else "No existing React components found for dependencies. Use BDL components instead."}
```

#### 2.3 自动注册新生成的组件

```python
# 注册生成的组件到组件注册表
registry = get_component_registry(output_path)

# 计算相对路径（用于import）
import_path = rel_code_path.replace('\\', '/').replace('.jsx', '')
if not import_path.startswith('.'):
    import_path = './' + import_path

registry.register_component(
    aem_resource_type=resource_type,
    react_component_name=component_name,
    react_component_path=import_path,
    css_path=css_file_path
)
```

### 3. 辅助函数

**函数**: `_build_existing_components_section()`

**功能**: 构建已生成React组件的说明部分，包括：
- 组件名称和路径
- Import语句示例
- 使用说明
- 转换规则

## 工作流程

### 场景1: 首次生成组件（无依赖或依赖未生成）

1. 分析AEM组件
2. 检查依赖组件 → 未找到已生成的组件
3. 使用BDL组件库生成React组件
4. 注册组件到注册表

### 场景2: 生成依赖已有组件的组件

1. 分析AEM组件（如container）
2. 检查依赖组件（button、card）→ 找到已生成的组件
3. 在prompt中提供已生成组件信息：
   ```
   === EXISTING REACT COMPONENTS (FOR DEPENDENCIES) ===
   --- Dependency: example/components/button ---
   React Component Name: Button
   React Component Path: ./Button
   IMPORT: import Button from './Button'
   USAGE: Use <Button /> in your JSX
   ```
4. Agent优先使用已生成的组件
5. 注册新组件到注册表

## 测试数据

### example-container组件

**位置**: `test_data/aem_components/example-container/`

**文件**:
- `container.html`: 使用`data-sly-resource`引用button和card组件
- `ContainerModel.java`: Java Sling Model
- `container.css`: 组件样式
- `_cq_dialog/.content.xml`: Dialog配置

**依赖关系**:
- 依赖 `example/components/button`
- 依赖 `example/components/card`

**测试场景**:
1. 先生成button组件 → 注册到注册表
2. 再生成card组件 → 注册到注册表
3. 最后生成container组件 → 检测到button和card已生成 → 使用已生成的组件

## Prompt中的说明

当检测到已生成的依赖组件时，prompt会包含：

```
=== EXISTING REACT COMPONENTS (FOR DEPENDENCIES) ===

The following dependency components have already been generated as React components.
PRIORITY: Use these existing React components instead of BDL components when building the current component.

--- Dependency: example/components/button ---
React Component Name: Button
React Component Path: ./Button
IMPORT: import Button from './Button'
USAGE: Use <Button /> in your JSX

IMPORTANT CONVERSION RULES:
1. When the current component uses data-sly-resource to include a dependency component,
   and that dependency component has an existing React component, use the existing React component.
2. Import the existing React component using the import path shown above.
3. Pass appropriate props to the existing React component based on the AEM component's usage.
4. Only use BDL components for parts that are NOT covered by existing React components.
5. Maintain the same component composition structure as in AEM.
```

## 优势

1. **组件复用**: 避免重复生成相同的组件
2. **依赖关系**: 保持AEM组件之间的依赖关系
3. **一致性**: 确保依赖组件的一致性
4. **效率**: 提高代码生成效率
5. **可维护性**: 组件注册表便于管理和维护

## 注意事项

1. **文件验证**: `has_component()`会验证文件是否真的存在，如果文件被删除，会自动从注册表中移除
2. **路径处理**: 自动处理跨平台路径（Windows/Linux/Mac）
3. **相对路径**: 使用相对路径便于import
4. **注册表位置**: 注册表文件保存在`output_path`目录下

## 总结

✅ **已实现**:
- ComponentRegistry组件注册表
- 依赖组件检查
- Prompt中提供已生成组件信息
- 自动注册新生成的组件
- 测试数据（example-container）

✅ **工作流程**:
- 检查依赖组件是否已生成
- 优先使用已生成的组件
- 如果没有，使用BDL组件库
- 自动注册新生成的组件

现在系统支持组件复用，更接近AEM的组件构建方式！🎉
