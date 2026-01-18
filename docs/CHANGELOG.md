# 更新日志

## 重大更新 - BDL 替换 MUI

### 主要变更

1. **组件库替换**: 将所有 MUI (Material-UI) 相关代码替换为 BDL（公司内部组件库）

2. **配置方式改进**:
   - AEM repository 路径和 BDL library 路径现在从 `.env` 文件读取
   - 不再需要每次运行时输入路径

3. **输入方式改进**:
   - 输入改为 `resourceType`（相对于 AEM repo 的相对路径）
   - 支持点分隔格式（`example.components.button`）和路径格式（`example/components/button`）

### 详细变更

#### 文件变更

- ✅ `agents/mui_selection_agent.py` → `agents/bdl_selection_agent.py`
- ✅ `agents/review_agents.py`: `MUIReviewAgent` → `BDLReviewAgent`
- ✅ `agents/code_writing_agent.py`: 更新 prompt 使用 BDL
- ✅ `agents/correct_agent.py`: 更新 prompt 使用 BDL
- ✅ `workflow/graph.py`: 所有 MUI 引用替换为 BDL
- ✅ `main.py`: 完全重写，使用 .env 配置和 resourceType 输入
- ✅ `.env.example`: 添加 AEM_REPO_PATH 和 BDL_LIBRARY_PATH

#### 状态结构变更

**之前**:
```python
{
    "component_path": str,
    "mui_library_path": str,
    "selected_mui_components": List[str],
    ...
}
```

**现在**:
```python
{
    "resource_type": str,  # 新增
    "aem_repo_path": str,  # 新增
    "component_path": str,
    "bdl_library_path": str,  # 重命名
    "selected_bdl_components": List[str],  # 重命名
    ...
}
```

#### 工作流节点变更

- `select_mui` → `select_bdl`
- 所有相关的 prompt 和逻辑都已更新

### 使用方式变更

**之前**:
```bash
python main.py
# 输入: AEM component path
# 输入: MUI library path
```

**现在**:
```bash
# 1. 配置 .env 文件
cp .env.example .env
# 编辑 .env，填入 AEM_REPO_PATH 和 BDL_LIBRARY_PATH

# 2. 运行
python main.py
# 输入: resourceType (如 "example/components/button")
```

### 改进的错误处理

1. **配置验证**: 启动时验证所有必需配置
2. **路径验证**: 验证路径存在性和类型
3. **resourceType 验证**: 验证组件目录存在
4. **文件验证**: 验证文件存在性
5. **更清晰的错误信息**: 提供具体的修复建议

### 健壮性改进

1. **边界情况处理**: 空列表、空结果等
2. **错误恢复**: 部分失败不影响整体流程
3. **日志记录**: 详细的日志记录
4. **状态验证**: 每个节点验证必需状态

### 文档更新

- ✅ `CONFIGURATION.md`: 配置说明
- ✅ `CODE_REVIEW.md`: 代码审查和健壮性检查
- ✅ `CHANGELOG.md`: 本文件

### 向后兼容性

⚠️ **不兼容**: 这是一个重大更新，不向后兼容。需要：
1. 更新 `.env` 文件
2. 使用新的 resourceType 输入方式
3. 确保 BDL library 路径正确

### 迁移指南

1. **更新配置**:
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

2. **更新使用方式**:
   - 不再输入完整路径
   - 只输入 resourceType

3. **验证**:
   ```bash
   python main.py
   # 输入 resourceType 测试
   ```
