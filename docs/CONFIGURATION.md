# 配置说明

## .env 文件配置

项目使用 `.env` 文件进行配置管理。请复制 `.env.example` 并填入实际值：

```bash
cp .env.example .env
```

### 必需配置项

#### 1. OPENAI_API_KEY
OpenAI API 密钥，用于 LLM 调用。

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

#### 2. AEM_REPO_PATH
AEM 组件仓库的根路径（绝对路径）。

**Windows 示例**:
```env
AEM_REPO_PATH=C:\projects\aem-repository
```

**Linux/macOS 示例**:
```env
AEM_REPO_PATH=/home/user/projects/aem-repository
```

**支持格式**:
- 绝对路径: `/path/to/repo` 或 `C:\path\to\repo`
- 环境变量: `$HOME/projects/aem-repo` 或 `%USERPROFILE%\projects\aem-repo`
- 用户目录: `~/projects/aem-repo`

#### 3. BDL_LIBRARY_PATH
BDL 组件库的根路径（绝对路径）。

**Windows 示例**:
```env
BDL_LIBRARY_PATH=C:\projects\bdl-library
```

**Linux/macOS 示例**:
```env
BDL_LIBRARY_PATH=/home/user/projects/bdl-library
```

### 完整示例

```env
# OpenAI API Key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# AEM Repository Path
AEM_REPO_PATH=/Users/zyw/projects/aem-components

# BDL Library Path
BDL_LIBRARY_PATH=/Users/zyw/projects/bdl-components
```

## 使用 resourceType

### resourceType 格式

resourceType 是相对于 AEM repository 根路径的相对路径，支持两种格式：

1. **点分隔格式**（AEM 标准）:
   ```
   example.components.button
   ```

2. **路径格式**:
   ```
   example/components/button
   ```

程序会自动处理两种格式。

### 示例

假设 AEM_REPO_PATH 是 `/projects/aem-repo`，resourceType 是 `example/components/button`：

完整路径将是：`/projects/aem-repo/example/components/button`

### 验证

程序会在运行前验证：
- ✅ AEM repository 路径存在
- ✅ BDL library 路径存在
- ✅ resourceType 对应的组件目录存在

如果验证失败，程序会显示清晰的错误信息。

## 路径规范

### 跨平台支持

所有路径都支持跨平台格式：
- Windows: `C:\path\to\repo` 或 `C:/path/to/repo`
- Linux/macOS: `/path/to/repo`

### 相对路径

`.env` 文件中的路径应该是**绝对路径**，以确保在不同工作目录下都能正确运行。

### 环境变量

支持使用环境变量：
- Unix: `$HOME`, `$USER`, 等
- Windows: `%USERPROFILE%`, `%APPDATA%`, 等

## 故障排除

### 错误: Missing or invalid configuration

**原因**: `.env` 文件中缺少必需的配置项或路径无效。

**解决**:
1. 检查 `.env` 文件是否存在
2. 确认所有必需配置项都已填写
3. 验证路径是否正确（使用绝对路径）

### 错误: Invalid AEM_REPO_PATH

**原因**: AEM repository 路径不存在或不是目录。

**解决**:
1. 检查路径是否正确
2. 确认路径指向的是目录而不是文件
3. 检查文件系统权限

### 错误: Component not found

**原因**: resourceType 对应的组件目录不存在。

**解决**:
1. 检查 resourceType 是否正确
2. 确认组件在 AEM repository 中存在
3. 验证 resourceType 格式（点分隔或路径格式）

## 最佳实践

1. **使用绝对路径**: 避免相对路径带来的问题
2. **定期验证**: 确保路径仍然有效
3. **版本控制**: 不要将 `.env` 文件提交到版本控制（已在 `.gitignore` 中）
4. **文档化**: 在团队中共享路径规范
