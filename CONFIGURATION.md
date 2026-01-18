# 配置说明

本项目使用环境变量进行配置管理，方便在不同环境中迁移和使用。

## 快速开始

1. **复制配置模板**
   ```bash
   cp .env.example .env
   ```

2. **编辑 `.env` 文件**
   根据你的实际环境设置路径：
   ```bash
   AEM_REPO_PATH=/path/to/your/aem/components
   BDL_LIBRARY_PATH=/path/to/your/bdl/library
   ```

3. **验证配置**
   ```bash
   python -c "from utils.config import load_config; load_config().print_config()"
   ```

## 配置项说明

### 必需配置

#### `AEM_REPO_PATH`
- **说明**: AEM组件仓库的根路径
- **示例**: `/Users/username/projects/aem-components` 或 `C:\projects\aem-components`
- **用途**: 用于查找和读取AEM组件源文件

#### `BDL_LIBRARY_PATH`
- **说明**: BDL组件库的根路径
- **示例**: `/Users/username/projects/bdl-library` 或 `C:\projects\bdl-library`
- **用途**: 用于查找和匹配BDL组件

### 可选配置

#### `OUTPUT_DIR`
- **默认值**: `./output`
- **说明**: 生成的React组件输出目录
- **示例**: `./output` 或 `/path/to/output`

#### `COMPONENT_REGISTRY_FILE`
- **默认值**: `.component_registry.json`
- **说明**: 组件注册表文件名（相对于输出目录）
- **用途**: 存储已生成的组件映射关系

#### `MAX_ITERATIONS`
- **默认值**: `5`
- **说明**: 代码审查-修正循环的最大迭代次数
- **类型**: 整数

#### `LOG_LEVEL`
- **默认值**: `INFO`
- **可选值**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **说明**: 日志输出级别

#### `LOG_FILE`
- **默认值**: 空（仅输出到控制台）
- **说明**: 日志文件路径（可选）
- **示例**: `./logs/converter.log`

## 跨平台路径支持

配置支持以下路径格式：
- Unix/Linux/macOS: `/path/to/directory`
- Windows: `C:\path\to\directory` 或 `C:/path/to/directory`
- 相对路径: `./relative/path` 或 `../parent/path`
- 用户目录: `~/projects/directory` (会被展开为完整路径)

## 测试数据路径

如果未设置环境变量，测试脚本会自动使用项目内的测试数据路径：
- AEM组件: `./test_data/aem_components`
- BDL库: `./test_data/mui_library`
- 输出目录: `./output`

## 配置验证

项目启动时会自动验证必需配置：

```python
from utils.config import load_config

try:
    config = load_config()
    print("配置验证通过！")
except ValueError as e:
    print(f"配置错误: {e}")
```

## 示例配置

### 开发环境
```bash
AEM_REPO_PATH=./test_data/aem_components
BDL_LIBRARY_PATH=./test_data/mui_library
OUTPUT_DIR=./output
MAX_ITERATIONS=3
LOG_LEVEL=DEBUG
```

### 生产环境
```bash
AEM_REPO_PATH=/var/aem/components
BDL_LIBRARY_PATH=/var/bdl/library
OUTPUT_DIR=/var/output/components
MAX_ITERATIONS=5
LOG_LEVEL=INFO
LOG_FILE=/var/logs/converter.log
```

### Windows环境
```bash
AEM_REPO_PATH=C:\Projects\AEM\components
BDL_LIBRARY_PATH=C:\Projects\BDL\library
OUTPUT_DIR=C:\Projects\output
```

## 环境变量优先级

1. `.env` 文件中的配置
2. 系统环境变量
3. 默认值（如果配置了的话）

## 注意事项

1. **路径分隔符**: 项目会自动处理不同操作系统的路径分隔符
2. **路径验证**: 启动时会验证路径是否存在（如果设置了）
3. **相对路径**: 相对路径会相对于项目根目录解析
4. **安全性**: `.env` 文件不应提交到版本控制系统，已包含在 `.gitignore` 中

## 故障排除

### 配置未生效
- 检查 `.env` 文件是否在项目根目录
- 检查 `.env` 文件格式是否正确（无多余空格，每行一个配置）
- 重启Python进程（环境变量在进程启动时加载）

### 路径找不到
- 使用绝对路径而不是相对路径
- 检查路径中是否有特殊字符需要转义
- 在Windows上使用正斜杠 `/` 或双反斜杠 `\\`

### 权限问题
- 确保对配置的路径有读取权限
- 确保对输出目录有写入权限
