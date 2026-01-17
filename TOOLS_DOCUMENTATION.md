# 工具文档

## 概述

本项目提供了丰富的工具集合，帮助 Agent 方便地查找、读取、分析和处理文件。

## 工具分类

### 1. 基础文件工具 (`tools/file_tools.py`)

#### 文件操作
- **`list_files(directory_path, recursive=True)`** - 列出目录下的所有文件
- **`read_file(file_path)`** - 读取文件内容
- **`write_file(file_path, content)`** - 写入文件
- **`file_exists(file_path)`** - 检查文件是否存在
- **`directory_exists(directory_path)`** - 检查目录是否存在
- **`create_directory(directory_path)`** - 创建目录

#### 文件信息
- **`get_file_info(file_path)`** - 获取文件信息（大小、修改时间等）

#### 命令执行
- **`run_command(command, working_directory=None, timeout=300)`** - 执行系统命令

### 2. 搜索工具 (`tools/search_tools.py`) ⭐ 新增

#### 文件搜索
- **`search_files_by_pattern(directory_path, pattern, recursive=True)`**
  - 根据文件名模式搜索文件
  - 支持通配符：`*.js`, `button.*`, `*test*`
  
- **`search_files_by_extension(directory_path, extension, recursive=True)`**
  - 根据文件扩展名搜索
  - 示例：`search_files_by_extension("/path", "js")` 查找所有 `.js` 文件

- **`find_files_by_name(directory_path, name_pattern, recursive=True)`**
  - 根据文件名模式查找文件
  - 支持部分匹配和通配符

#### 内容搜索
- **`search_text_in_files(directory_path, search_text, file_pattern="*", case_sensitive=False)`**
  - 在文件中搜索文本内容
  - 返回匹配的文件和行号
  - 示例：搜索所有 JS 文件中的 "useState"

#### 目录结构
- **`get_file_tree(directory_path, max_depth=3, include_files=True)`**
  - 获取目录树结构（文本格式）
  - 方便 Agent 了解目录结构

#### AEM 特定搜索
- **`find_component_by_resource_type(aem_repo_path, resource_type)`**
  - 根据 resourceType 查找组件路径
  
- **`find_clientlib_by_category(aem_repo_path, category)`**
  - 根据 ClientLibs category 查找 ClientLibs 目录
  
- **`find_css_for_class(aem_repo_path, component_path, css_class)`**
  - 查找指定 CSS class 的样式定义

### 3. AEM 特定工具 (`tools/aem_tools.py`) ⭐ 新增

#### 文件类型识别
- **`identify_aem_file_type_tool(file_path)`**
  - 识别 AEM 文件类型和优先级

#### 依赖提取
- **`extract_htl_dependencies(file_path)`**
  - 从 HTL 文件中提取组件依赖（data-sly-resource）

#### CSS 处理
- **`extract_css_classes_from_file(file_path)`**
  - 从 HTL 文件中提取使用的 CSS classes

- **`find_css_rules_for_component(component_path, aem_repo_path, css_classes)`**
  - 查找组件使用的 CSS classes 对应的样式规则

#### ClientLibs
- **`parse_clientlib_config(config_path)`**
  - 解析 ClientLibs 配置文件（.content.xml）

#### 文件分类
- **`get_component_files_by_type(component_path, file_type)`**
  - 获取组件中指定类型的文件（htl, dialog, js, css, java 等）

#### 路径解析
- **`resolve_resource_type(resource_type, aem_repo_path)`**
  - 将 resourceType 解析为文件系统路径

## Agent 工具配置

### AEMAnalysisAgent

**工具**:
- ✅ `analyze_htl_file` - 分析 HTL 文件
- ✅ `analyze_dialog_file` - 分析 Dialog 文件
- ✅ `analyze_script_file` - 分析脚本文件
- ✅ `read_file` - 读取文件
- ✅ `list_files` - 列出文件
- ✅ `search_files_by_pattern` - 按模式搜索文件
- ✅ `search_text_in_files` - 在文件中搜索文本
- ✅ `get_component_files_by_type` - 按类型获取文件
- ✅ `extract_css_classes_from_file` - 提取 CSS classes
- ✅ `extract_htl_dependencies` - 提取 HTL 依赖

**用途**: 分析 AEM 组件文件，提取关键信息

### BDLSelectionAgent

**工具**:
- ✅ `search_bdl_components` - 搜索 BDL 组件
- ✅ `read_bdl_component` - 读取 BDL 组件源代码
- ✅ `list_files` - 列出文件
- ✅ `read_file` - 读取文件
- ✅ `search_files_by_pattern` - 按模式搜索文件
- ✅ `find_files_by_name` - 按名称查找文件
- ✅ `search_text_in_files` - 在文件中搜索文本
- ✅ `get_file_tree` - 获取目录树

**用途**: 在 BDL 库中搜索和选择组件

### CodeWritingAgent

**工具**:
- ✅ `read_source_code` - 读取源代码
- ✅ `write_react_component` - 写入 React 组件
- ✅ `create_component_directory` - 创建目录
- ✅ `list_files` - 列出文件
- ✅ `search_files_by_pattern` - 按模式搜索文件
- ✅ `search_text_in_files` - 在文件中搜索文本
- ✅ `get_file_tree` - 获取目录树

**用途**: 生成和写入 React 组件代码

### SecurityReviewAgent / BuildReviewAgent / BDLReviewAgent

**工具**:
- ✅ `read_code_file` - 读取代码文件
- ✅ `check_file_exists_tool` - 检查文件是否存在
- ✅ `search_text_in_files` - 在文件中搜索文本（查找特定模式）
- ✅ `get_file_info` - 获取文件信息

**用途**: 审查代码，查找安全问题、构建错误、BDL 合规问题

### CorrectAgent

**工具**:
- ✅ `read_code_file` - 读取代码文件
- ✅ `write_corrected_code` - 写入修正后的代码
- ✅ `search_text_in_files` - 在文件中搜索文本
- ✅ `get_file_info` - 获取文件信息

**用途**: 修正代码问题

## 工具使用示例

### 示例 1: 搜索 BDL 组件

```python
# Agent 可以使用
search_files_by_pattern(
    bdl_library_path,
    "Button*.tsx",
    recursive=True
)

# 或
find_files_by_name(
    bdl_library_path,
    "button"
)
```

### 示例 2: 查找 CSS 样式

```python
# Agent 可以使用
extract_css_classes_from_file(htl_file_path)
# 返回: ['example-button', 'example-button__text']

find_css_for_class(
    aem_repo_path,
    component_path,
    'example-button'
)
# 返回: {file_path: css_rule}
```

### 示例 3: 搜索代码中的模式

```python
# Agent 可以使用
search_text_in_files(
    output_path,
    "dangerouslySetInnerHTML",
    "*.jsx",
    case_sensitive=False
)
# 返回: {file_path: [匹配的行]}
```

### 示例 4: 查找组件依赖

```python
# Agent 可以使用
extract_htl_dependencies(htl_file_path)
# 返回: ['core/wcm/components/button/v1/button', ...]

resolve_resource_type(
    'core/wcm/components/button/v1/button',
    aem_repo_path
)
# 返回: '/path/to/component'
```

### 示例 5: 获取目录结构

```python
# Agent 可以使用
get_file_tree(
    component_path,
    max_depth=2,
    include_files=True
)
# 返回: 目录树文本
```

## 工具优势

### 1. 丰富的搜索能力 ✅
- 按文件名模式搜索
- 按扩展名搜索
- 在文件中搜索文本
- 按名称查找文件

### 2. AEM 特定支持 ✅
- 识别 AEM 文件类型
- 提取 HTL 依赖
- 提取 CSS classes
- 查找 CSS 样式
- 解析 ClientLibs
- 解析 resourceType

### 3. 便利性 ✅
- 统一的工具接口
- 清晰的函数命名
- 详细的文档字符串
- 错误处理

### 4. 性能考虑 ✅
- 支持递归/非递归搜索
- 可限制搜索深度
- 可限制返回数量

## 可能的使用场景

### 场景 1: BDL 组件选择

Agent 需要：
1. 搜索 BDL 库中的组件
2. 读取组件源代码
3. 验证组件功能

**可用工具**:
- `search_files_by_pattern` - 搜索组件文件
- `read_bdl_component` - 读取源代码
- `search_text_in_files` - 搜索特定 API 使用

### 场景 2: CSS 样式查找

Agent 需要：
1. 从 HTL 提取 CSS classes
2. 查找对应的 CSS 规则

**可用工具**:
- `extract_css_classes_from_file` - 提取 classes
- `find_css_for_class` - 查找样式规则
- `find_clientlib_by_category` - 查找 ClientLibs

### 场景 3: 代码审查

Agent 需要：
1. 读取代码文件
2. 搜索安全问题（如 `dangerouslySetInnerHTML`）
3. 检查文件结构

**可用工具**:
- `read_code_file` - 读取代码
- `search_text_in_files` - 搜索问题模式
- `get_file_tree` - 查看文件结构

### 场景 4: 依赖分析

Agent 需要：
1. 从 HTL 提取依赖
2. 查找依赖组件路径
3. 分析依赖组件

**可用工具**:
- `extract_htl_dependencies` - 提取依赖
- `resolve_resource_type` - 解析路径
- `get_component_files_by_type` - 获取依赖组件文件

## 总结

### ✅ 已实现的工具

**基础工具** (8个):
- 文件操作（list, read, write, exists, create）
- 文件信息
- 命令执行

**搜索工具** (8个): ⭐ 新增
- 文件搜索（pattern, extension, name）
- 内容搜索
- 目录树
- AEM 特定搜索

**AEM 工具** (7个): ⭐ 新增
- 文件类型识别
- 依赖提取
- CSS 处理
- ClientLibs 解析
- 路径解析

**总计**: 23 个工具

### ✅ Agent 工具配置

所有 Agent 都已配置了合适的工具：
- **AEMAnalysisAgent**: 10 个工具
- **BDLSelectionAgent**: 8 个工具
- **CodeWritingAgent**: 7 个工具
- **ReviewAgents**: 4 个工具
- **CorrectAgent**: 4 个工具

### 🎯 工具优势

1. **全面性**: 覆盖文件操作、搜索、AEM 特定操作
2. **便利性**: Agent 可以方便地查找和访问所需内容
3. **专业性**: AEM 特定工具支持 AEM 组件分析
4. **灵活性**: 支持多种搜索模式和过滤条件

现在 Agent 拥有丰富的工具集，可以方便地查找、读取和分析所需的内容！🎉
