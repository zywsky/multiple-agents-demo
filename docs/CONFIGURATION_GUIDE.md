# 配置指南

本文档说明如何配置项目，包括环境变量设置和路径配置。

## 环境变量配置

### 快速开始

1. 复制环境变量示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的配置：
```bash
# AEM组件仓库路径
AEM_REPO_PATH=./test_data/aem_components

# BDL组件库路径
BDL_LIBRARY_PATH=./test_data/mui_library

# 输出路径
OUTPUT_PATH=./output

# LLM API配置
LLM_API_BASE=https://ark.cn-beijing.volces.com/api/v3
LLM_API_KEY=your_api_key_here
LLM_MODEL=ep-20250118160000-xxxxx
```

### 配置项说明

#### 路径配置

- **AEM_REPO_PATH**: AEM组件仓库路径
  - 可以是绝对路径：`/path/to/aem/components`
  - 也可以是相对路径（相对于项目根目录）：`./test_data/aem_components`

- **BDL_LIBRARY_PATH**: BDL组件库路径
  - 用于查找和匹配BDL组件
  - 示例：`./test_data/mui_library`

- **OUTPUT_PATH**: 输出路径
  - 生成的React组件保存位置
  - 示例：`./output`

- **COMPONENT_REGISTRY_PATH**: 组件注册表路径
  - 用于跟踪已生成的组件，实现组件复用
  - 通常与OUTPUT_PATH相同

#### LLM API配置

- **LLM_API_BASE**: LLM API的基础URL
- **LLM_API_KEY**: API密钥（必需）
- **LLM_MODEL**: 使用的模型名称

#### 工作流配置

- **MAX_ITERATIONS**: 最大迭代次数（默认：5）
  - 代码修正的最大尝试次数

- **MAX_TOKENS**: 最大token数（默认：8192）
  - 单次请求的最大token数

- **TEMPERATURE**: 温度参数（默认：0.7）
  - 控制输出的随机性，范围：0.0-1.0

#### 日志配置

- **LOG_LEVEL**: 日志级别（默认：INFO）
  - 可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL

- **LOG_FILE**: 日志文件路径（可选）
  - 不设置则只输出到控制台

## 使用配置模块

### 在代码中使用配置

```python
from config import config

# 获取路径（自动标准化）
aem_path = config.get_aem_repo_path()
bdl_path = config.get_bdl_library_path()
output_path = config.get_output_path()

# 获取其他配置
max_iterations = config.MAX_ITERATIONS
llm_model = config.LLM_MODEL

# 验证配置
errors = config.validate()
if errors:
    print("配置错误：")
    for error in errors:
        print(f"  - {error}")

# 打印当前配置
config.print_config()
```

### 路径标准化

配置模块会自动处理路径：
- 相对路径会转换为相对于项目根目录的绝对路径
- 路径中的 `~` 会被展开为用户主目录
- 路径会被标准化（移除多余的斜杠等）

```python
from config import config

# 这些都会自动标准化
config.AEM_REPO_PATH = "./test_data/aem_components"  # 相对路径
config.AEM_REPO_PATH = "~/projects/aem/components"   # 使用~符号
config.AEM_REPO_PATH = "/absolute/path/to/components"  # 绝对路径
```

## 迁移项目

当需要迁移项目到新环境时：

1. **复制配置文件**：
   ```bash
   cp .env.example .env
   ```

2. **更新路径**：
   - 修改 `AEM_REPO_PATH` 指向新的AEM组件位置
   - 修改 `BDL_LIBRARY_PATH` 指向新的BDL库位置
   - 修改 `OUTPUT_PATH` 设置输出位置

3. **更新API配置**：
   - 更新 `LLM_API_KEY` 和 `LLM_MODEL`

4. **验证配置**：
   ```python
   from config import config
   errors = config.validate()
   if errors:
       # 处理错误
   ```

## 数据清洗

项目包含数据清洗工具，用于清洗发送给LLM的数据：

```python
from utils.prompt_cleaner import cleaner

# 清洗文本
cleaned_text = cleaner.clean_text(text)

# 清洗代码块
cleaned_code = cleaner.clean_code_block(code, language="jsx")

# 清洗文件内容
cleaned_file = cleaner.clean_file_content(content, file_type="java")

# 清洗提示词数据字典
cleaned_data = cleaner.clean_prompt_data({
    "code": code_content,
    "prompt": prompt_text,
    "files": file_list
})

# 移除敏感信息
safe_text = cleaner.remove_sensitive_info(text_with_secrets)
```

### 清洗功能

- **移除控制字符**：移除不可见的控制字符
- **标准化空白**：统一换行符和空白字符
- **移除零宽字符**：移除可能导致问题的零宽字符
- **截断过长内容**：智能截断，保持结构完整
- **移除敏感信息**：移除API密钥、密码等敏感信息

## 最佳实践

1. **不要提交 `.env` 文件**：
   - 确保 `.env` 在 `.gitignore` 中
   - 只提交 `.env.example` 作为模板

2. **使用相对路径**：
   - 在团队协作时，使用相对路径更方便
   - 配置模块会自动处理路径转换

3. **验证配置**：
   - 在应用启动时验证配置
   - 提供清晰的错误信息

4. **使用数据清洗**：
   - 在发送数据给LLM前进行清洗
   - 避免发送敏感信息
   - 控制数据长度，避免超出token限制
