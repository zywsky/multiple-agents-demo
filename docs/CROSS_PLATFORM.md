# 跨平台支持说明

## 概述

本项目完全支持跨平台运行，可以在 Windows、Linux 和 macOS 上使用。

## 路径处理

### 支持的路径格式

程序自动处理以下路径格式：

1. **相对路径**
   ```
   ./test_data/aem_components/example-button
   test_data/aem_components/example-button
   ```

2. **绝对路径**
   ```
   /home/user/projects/multiple-agents/test_data/...
   C:\Users\YourName\projects\multiple-agents\test_data\...
   ```

3. **用户目录（~）**
   ```
   ~/projects/multiple-agents/test_data/...
   ```

4. **环境变量**
   ```
   $HOME/projects/multiple-agents/test_data/...
   %USERPROFILE%\projects\multiple-agents\test_data\...
   ```

5. **混合分隔符**
   - Windows 路径可以使用 `/` 或 `\`
   - 程序会自动规范化

### 路径规范化

所有输入的路径都会经过以下处理：

1. 移除首尾空格和引号
2. 展开用户目录（`~`）
3. 展开环境变量（`$VAR` 或 `%VAR%`）
4. 转换为绝对路径
5. 使用系统原生路径分隔符

### 路径验证

程序会自动验证：
- 路径是否存在
- 是否为目录（当需要时）
- 是否有读取权限

## 使用示例

### Windows

```bash
python main.py
```

输入：
```
Enter AEM component path: test_data\aem_components\example-button
Enter MUI library path: test_data\mui_library\packages\mui-material\src
```

或使用绝对路径：
```
Enter AEM component path: C:\Users\YourName\projects\multiple-agents\test_data\aem_components\example-button
```

### Linux/macOS

```bash
python main.py
```

输入：
```
Enter AEM component path: test_data/aem_components/example-button
Enter MUI library path: test_data/mui_library/packages/mui-material/src
```

或使用绝对路径：
```
Enter AEM component path: /home/user/projects/multiple-agents/test_data/aem_components/example-button
```

## 技术实现

### 使用的库

- **pathlib**: Python 标准库，提供跨平台路径操作
- **os.path**: 用于路径展开和环境变量处理

### 关键函数

- `normalize_path()`: 规范化路径
- `validate_path()`: 验证路径
- `format_path_for_display()`: 格式化显示
- `join_paths()`: 跨平台路径拼接

## 测试

运行测试脚本验证跨平台支持：

```bash
python test_paths.py
```

## 注意事项

1. **路径分隔符**: 虽然程序支持混合使用 `/` 和 `\`，但建议使用系统原生的分隔符
2. **大小写**: Windows 文件系统不区分大小写，Linux/macOS 区分
3. **长路径**: Windows 支持长路径（需要启用），Linux/macOS 无限制
4. **权限**: 确保有读取源路径和写入目标路径的权限

## 常见问题

### Q: Windows 上可以使用正斜杠吗？

A: 可以！程序会自动处理。例如：
```
test_data/aem_components/example-button  # ✓ 可以
test_data\aem_components\example-button  # ✓ 也可以
```

### Q: 如何输入包含空格的路径？

A: 直接输入即可，程序会自动处理。如果路径包含特殊字符，可以用引号包裹：
```
"C:\Users\My Name\projects\test_data\..."
```

### Q: 相对路径是相对于哪里？

A: 相对于当前工作目录（运行 `python main.py` 时的目录）。

### Q: 如何知道路径是否正确？

A: 程序会在输入后显示规范化后的路径，并验证路径是否存在。

## 示例输出

```
=== AEM to React Component Converter ===

Note: Paths support Windows, Linux, and macOS formats
      You can use relative or absolute paths

Enter AEM component path: test_data/aem_components/example-button
✓ AEM component path: /Users/zyw/projects/0-ai-projects/multiple-agents/test_data/aem_components/example-button

Enter MUI library path: test_data/mui_library/packages/mui-material/src
✓ MUI library path: /Users/zyw/projects/0-ai-projects/multiple-agents/test_data/mui_library/packages/mui-material/src

Enter output path (default: ./output): ./output
✓ Output path: /Users/zyw/projects/0-ai-projects/multiple-agents/output
```
