# 快速开始指南

## 测试数据已准备就绪！

### 📁 AEM 组件路径

**跨平台路径示例**:

**Windows**:
```
C:\Users\YourName\projects\multiple-agents\test_data\aem_components\example-button
```
或相对路径：
```
test_data\aem_components\example-button
```

**Linux/macOS**:
```
/Users/zyw/projects/0-ai-projects/multiple-agents/test_data/aem_components/example-button
```
或相对路径：
```
test_data/aem_components/example-button
```

**包含的文件**:
- `button.html` - HTL 模板
- `button.css` - 样式文件
- `button.js` - JavaScript
- `.content.xml` - 组件定义
- `_cq_dialog/.content.xml` - 编辑对话框
- `ButtonModel.java` - Sling Model

### 📁 MUI 库路径

**跨平台路径示例**:

**Windows**:
```
C:\Users\YourName\projects\multiple-agents\test_data\mui_library\packages\mui-material\src
```
或相对路径：
```
test_data\mui_library\packages\mui-material\src
```

**Linux/macOS**:
```
/Users/zyw/projects/0-ai-projects/multiple-agents/test_data/mui_library/packages/mui-material/src
```
或相对路径：
```
test_data/mui_library/packages/mui-material/src
```

**包含的组件**:
- `Button/` - Button 组件（TypeScript）
- `TextField/` - TextField 组件（TypeScript）

### 🚀 运行测试

1. **确保已配置 API Key**:
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 OPENAI_API_KEY
   ```

2. **运行主程序**:
   ```bash
   python main.py
   ```

3. **输入路径**（支持跨平台格式）:

   **Windows 示例**:
   ```
   Enter AEM component path: test_data\aem_components\example-button
   Enter MUI library path: test_data\mui_library\packages\mui-material\src
   ```

   **Linux/macOS 示例**:
   ```
   Enter AEM component path: test_data/aem_components/example-button
   Enter MUI library path: test_data/mui_library/packages/mui-material/src
   ```

   **绝对路径（所有平台）**:
   ```
   Enter AEM component path: C:\Users\YourName\projects\multiple-agents\test_data\aem_components\example-button
   Enter MUI library path: C:\Users\YourName\projects\multiple-agents\test_data\mui_library\packages\mui-material\src
   ```

   **使用环境变量（所有平台）**:
   ```
   Enter AEM component path: $HOME/projects/multiple-agents/test_data/aem_components/example-button
   Enter MUI library path: %USERPROFILE%\projects\multiple-agents\test_data\mui_library\packages\mui-material\src
   ```

   **使用波浪号（所有平台）**:
   ```
   Enter AEM component path: ~/projects/multiple-agents/test_data/aem_components/example-button
   ```

4. **其他输入**:
   ```
   Enter output path (default: ./output): ./output
   Enter max review iterations (default: 5): 5
   ```

### ✨ 路径特性

程序自动支持：
- ✅ **相对路径** - `./test` 或 `test_data/...`
- ✅ **绝对路径** - `/home/user/...` 或 `C:\Users\...`
- ✅ **环境变量** - `$HOME/...` 或 `%USERPROFILE%\...`
- ✅ **用户目录** - `~/projects/...`
- ✅ **跨平台分隔符** - 自动处理 `/` 和 `\`
- ✅ **路径验证** - 自动检查路径是否存在

### 📝 路径格式说明

- **Windows**: 可以使用 `\` 或 `/`，程序会自动处理
- **Linux/macOS**: 使用 `/` 作为分隔符
- **混合格式**: 程序会自动规范化路径

### ✅ 验证路径

运行以下命令验证路径是否正确：

```bash
# Windows
dir test_data\aem_components\example-button

# Linux/macOS
ls -la test_data/aem_components/example-button/
```

### 🔄 下载完整 MUI 库（可选）

如果你想使用完整的 MUI 库而不是示例组件：

```bash
cd test_data
./setup_mui.sh
```

如果网络允许，这将从 GitHub 下载完整的 MUI Material-UI 库。

### 📚 更多信息

查看 `README.md` 了解详细的测试数据说明。
