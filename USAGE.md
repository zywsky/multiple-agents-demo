# 使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_api_key_here
```

### 3. 运行工作流

```bash
python main.py
```

## 工作流详细说明

### 步骤 1: 文件收集 (File Collection Agent)

**输入**: AEM 组件路径

**功能**: 
- 递归列出指定目录下的所有文件
- 包括子目录中的所有文件
- 返回完整的文件路径列表

**工具**:
- `list_component_files()`: 列出所有文件
- `get_file_content()`: 读取文件内容
- `check_file_exists()`: 检查文件是否存在
- `get_file_details()`: 获取文件详细信息

### 步骤 2: AEM 分析 (AEM Analysis Agent)

**输入**: 文件列表

**功能**:
- **逐个文件分析**，避免 token 超限
- 识别文件类型（HTL、Dialog、Script、CSS 等）
- 分析功能和依赖关系
- 提取关键特征和行为

**输出**: 每个文件的结构化分析摘要

**工具**:
- `analyze_htl_file()`: 分析 HTL 模板
- `analyze_dialog_file()`: 分析 Dialog 配置
- `analyze_script_file()`: 分析脚本文件
- `read_file()`: 读取文件内容

### 步骤 3: MUI 组件选择 (MUI Selection Agent)

**输入**: AEM 组件分析结果 + MUI 库路径

**功能**:
- 根据 AEM 组件功能选择匹配的 MUI 组件
- 考虑组件组合（可能需要多个 MUI 组件）
- 返回选定的 MUI 组件文件路径

**常见映射**:
- AEM Dialog/Form → MUI Dialog, TextField, Button
- AEM Grid/Layout → MUI Grid, Box, Container
- AEM Button → MUI Button
- AEM Text → MUI Typography
- AEM Image → MUI Card with CardMedia
- AEM Navigation → MUI AppBar, Drawer, Tabs
- AEM List → MUI List, ListItem
- AEM Accordion → MUI Accordion
- AEM Tabs → MUI Tabs

**工具**:
- `search_mui_components()`: 搜索 MUI 组件
- `read_mui_component()`: 读取 MUI 组件源代码

### 步骤 4: 代码生成 (Code Writing Agent)

**输入**: AEM 源代码 + 选定的 MUI 组件

**功能**:
- 生成等价的 React 组件
- 使用选定的 MUI 组件
- 遵循 React 和 MUI 最佳实践
- 保持相同的 UI/UX 行为

**输出**: 完整的 React 组件代码

**工具**:
- `read_source_code()`: 读取源代码
- `write_react_component()`: 写入 React 组件
- `create_component_directory()`: 创建组件目录

### 步骤 5: 代码审查 (Review Agents - Subagents)

使用三个独立的 subagents 进行多维度审查：

#### 5.1 Security Review Agent

**检查项**:
- XSS 漏洞
- 注入攻击风险
- 不安全的 API 使用
- 敏感数据暴露
- 不安全的依赖
- 认证/授权问题
- CSRF 漏洞
- `dangerouslySetInnerHTML` 的不安全使用
- URL 处理安全问题
- 输入验证缺失

**输出**: 安全问题列表和修复建议

#### 5.2 Build Review Agent

**检查项**:
- 编译错误
- 语法错误
- 类型错误（TypeScript）
- 导入问题
- 缺失的依赖
- React 最佳实践
- 运行时错误

**工具**: 可以运行 `npm run build` 验证编译

**输出**: 构建状态和错误列表

#### 5.3 MUI Review Agent

**检查项**:
- MUI 组件 API 使用正确性
- Theme 集成
- 样式方法（sx prop, styled components）
- 组件组合最佳实践
- 可访问性（a11y）合规性
- 响应式设计实现
- MUI 组件导入正确性
- Theme 自定义适当性
- 组件变体和尺寸使用

**输出**: MUI 规范问题和改进建议

### 步骤 6: 代码修正 (Correct Agent)

**输入**: 原始代码 + Review 结果

**功能**:
- 修复所有审查发现的问题
- 优先处理关键和高严重性问题
- 修复构建错误
- 修正安全漏洞
- 修复 MUI 使用问题
- 保持原有功能

**输出**: 修正后的代码

### 步骤 7: 循环优化

修正后的代码会再次进入 Review 阶段：
- 如果通过 → 结束
- 如果未通过 → 再次修正 → Review → ...
- 直到通过或达到最大迭代次数（默认 5 次）

## 配置选项

### 最大迭代次数

在运行 `main.py` 时可以设置最大审查迭代次数，默认是 5 次。

### 输出路径

可以指定生成的 React 组件输出路径，默认是 `./output`。

## 注意事项

1. **Token 限制**: AEM 分析 Agent 会逐个文件处理，避免一次性分析所有文件

2. **文件路径**: 确保提供的路径正确且可访问

3. **MUI 库路径**: 需要指向包含 MUI 组件源代码的目录

4. **构建环境**: Build Review Agent 会执行 `npm run build`，确保输出目录有必要的构建配置

5. **API Key**: 需要有效的 OpenAI API Key

## 故障排除

### 问题: API Key 未找到

**解决**: 确保 `.env` 文件存在且包含 `OPENAI_API_KEY`

### 问题: 文件路径错误

**解决**: 检查路径是否正确，使用绝对路径更可靠

### 问题: 构建失败

**解决**: 
- 确保输出目录有 `package.json`
- 安装必要的依赖
- 检查生成的代码是否有语法错误

### 问题: Token 超限

**解决**: 
- AEM 分析 Agent 已经逐个文件处理
- 如果仍有问题，可以分批处理文件

## 扩展开发

### 添加新的审查维度

在 `agents/review_agents.py` 中添加新的 Review Agent 类，然后在 `workflow/graph.py` 的 `review_code` 函数中调用。

### 改进 MUI 组件选择

修改 `agents/mui_selection_agent.py` 中的 system prompt 和工具函数。

### 添加新的工具

在 `tools/file_tools.py` 中添加新工具，然后在相应的 Agent 中注册使用。

## 示例

参见 `example_usage.py` 了解如何在代码中使用工作流。
