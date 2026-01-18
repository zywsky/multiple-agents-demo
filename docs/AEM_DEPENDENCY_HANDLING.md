# AEM 组件依赖处理说明

## 问题

在 AEM 中，组件可以通过 `data-sly-resource` 引用其他组件，形成组件组合。例如：

```html
<div data-sly-resource="${resource @ resourceType='core/wcm/components/button/v1/button'}"></div>
```

如果当前组件依赖其他组件，那么需要：
1. ✅ 找到被引用的组件（从 `data-sly-resource` 中提取 resourceType）
2. ✅ 递归分析这些依赖组件
3. ✅ 分析所有依赖组件的 HTL, Dialog, JS, Java, CSS 等文件

## 解决方案

### 1. 依赖解析器 (`utils/dependency_resolver.py`)

实现了完整的依赖解析功能：

#### 核心功能

1. **`extract_component_dependencies(htl_content, current_resource_type)`**
   - 从 HTL 内容中提取所有 `data-sly-resource` 引用
   - 支持多种格式：
     - 直接路径：`data-sly-resource="core/wcm/components/button/v1/button"`
     - 使用 resourceType 参数：`resourceType='example/components/button'`
     - 变量引用：`data-sly-resource="${component.path}"`

2. **`resolve_resource_type_to_path(resource_type, aem_repo_path)`**
   - 将 resourceType 解析为文件系统路径
   - 处理点分隔符和路径分隔符转换
   - 验证路径是否存在

3. **`collect_component_dependencies(component_path, aem_repo_path, resource_type, visited, max_depth)`**
   - 递归收集组件的所有依赖
   - 防止循环依赖（使用 `visited` 集合）
   - 限制最大递归深度（默认 5 层）
   - 返回依赖树结构

4. **`build_dependency_tree(root_resource_type, root_component_path, aem_repo_path)`**
   - 构建完整的组件依赖树
   - 包含所有嵌套依赖

5. **`flatten_dependencies(dependency_tree)`**
   - 将依赖树扁平化为列表
   - 便于遍历所有依赖组件

6. **`get_all_dependency_files(dependency_tree)`**
   - 获取所有依赖组件的文件列表
   - 用于统一分析

### 2. 工作流集成

#### 状态扩展

在 `WorkflowState` 中添加了：
- `dependency_tree: Dict[str, Any]` - 组件依赖树
- `dependency_analyses: Dict[str, List[Dict[str, Any]]]` - 依赖组件的分析结果

#### 文件收集阶段 (`collect_files`)

**之前**：
- 只收集当前组件的文件

**现在**：
- ✅ 收集当前组件的文件
- ✅ 构建依赖树（递归查找所有依赖组件）
- ✅ 收集所有依赖组件的文件
- ✅ 合并所有文件到 `files` 列表

#### 文件分析阶段 (`analyze_aem_files`)

**之前**：
- 只分析当前组件的文件

**现在**：
- ✅ 分析当前组件的文件（优先）
- ✅ 分析所有依赖组件的文件
- ✅ 递归分析嵌套依赖
- ✅ 为每个依赖组件的分析结果标记来源（`component_resource_type`）
- ✅ 限制每个依赖组件最多分析 10 个关键文件（避免过多）

#### 代码生成阶段 (`write_code`)

**之前**：
- 只使用当前组件的分析结果

**现在**：
- ✅ 使用当前组件的分析结果
- ✅ 使用所有依赖组件的分析结果
- ✅ 在 prompt 中明确区分当前组件和依赖组件
- ✅ 提示 LLM 如何处理依赖组件（转换为 React 组件导入）

### 3. 依赖树结构

```python
{
    'root': {
        'resource_type': 'example/components/button',
        'path': '/path/to/component',
        'dependencies': {
            'core/wcm/components/button/v1/button': {
                'resource_type': 'core/wcm/components/button/v1/button',
                'path': '/path/to/dependency',
                'files': [...],
                'dependencies': {
                    # 嵌套依赖
                }
            }
        }
    }
}
```

## 使用示例

### 示例 1: 简单依赖

**组件 A** (`example/components/card`) 依赖 **组件 B** (`core/wcm/components/button/v1/button`):

```html
<!-- card.html -->
<div class="card">
    <h2>${properties.title}</h2>
    <div data-sly-resource="${resource @ resourceType='core/wcm/components/button/v1/button'}"></div>
</div>
```

**处理流程**:
1. 分析 `card.html` → 发现依赖 `core/wcm/components/button/v1/button`
2. 查找依赖组件路径 → `/aem-repo/core/wcm/components/button/v1/button`
3. 收集依赖组件文件 → `button.html`, `_cq_dialog/.content.xml`, `button.js`, etc.
4. 分析依赖组件文件
5. 生成代码时，将依赖组件转换为 React 组件导入

### 示例 2: 嵌套依赖

**组件 A** → **组件 B** → **组件 C**

**处理流程**:
1. 分析组件 A → 发现依赖组件 B
2. 分析组件 B → 发现依赖组件 C
3. 递归分析组件 C
4. 构建完整的依赖树
5. 分析所有组件的文件

### 示例 3: 循环依赖

**组件 A** → **组件 B** → **组件 A**

**处理流程**:
1. 分析组件 A → 发现依赖组件 B
2. 分析组件 B → 发现依赖组件 A（已在 `visited` 中）
3. 跳过循环依赖，避免无限递归

## 限制和注意事项

### 1. 最大递归深度

默认最大深度为 5 层，防止过深的依赖链：
```python
max_depth: int = 5
```

### 2. 文件分析限制

每个依赖组件最多分析 10 个关键文件，避免过多：
```python
dep_files_to_analyze[:10]  # 限制每个依赖组件最多分析 10 个文件
```

### 3. 变量引用

如果 `data-sly-resource` 使用变量（如 `${component.path}`），可能无法在静态分析时确定实际值。这种情况下：
- 会尝试提取变量名
- 如果无法确定，会跳过该依赖
- 建议在 HTL 中使用明确的 resourceType

### 4. 性能考虑

- 大量依赖组件会增加分析时间
- 建议限制依赖深度和文件数量
- 可以考虑缓存依赖分析结果

## 代码生成时的处理

在代码生成 prompt 中，会明确说明：

1. **当前组件**：主要转换目标
2. **依赖组件**：需要转换为 React 组件导入
3. **转换规则**：
   - AEM `data-sly-resource` → React 组件导入和使用
   - 依赖组件的 Props 需要从当前组件的配置中传递
   - 依赖组件的功能需要完整保留

## 总结

✅ **已实现**：
- 递归依赖解析
- 依赖组件文件收集
- 依赖组件分析
- 循环依赖检测
- 深度限制

✅ **工作流集成**：
- 文件收集阶段自动处理依赖
- 文件分析阶段分析所有依赖
- 代码生成阶段使用依赖信息

✅ **结果**：
- 完整的组件依赖树
- 所有依赖组件的分析结果
- 更准确的 React 组件生成

现在流程可以正确处理组件依赖关系，确保生成的 React 组件包含所有必要的依赖组件！🎉
