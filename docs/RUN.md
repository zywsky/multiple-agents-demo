# 运行指南

## 快速开始

### 1. 配置环境变量

**方法一：使用 .env.example（推荐）**

```bash
cp .env.example .env
# 然后编辑 .env 文件，将 your_openai_api_key_here 替换为你的实际 API Key
```

**方法二：直接创建 .env 文件**

```bash
echo 'OPENAI_API_KEY=your_actual_api_key_here' > .env
```

或者手动创建 `.env` 文件，内容如下：

```
OPENAI_API_KEY=your_actual_api_key_here
```

### 2. 准备路径

运行前请准备好：
- **AEM 组件路径**: 包含 AEM HTL 组件源代码的目录路径
- **MUI 库路径**: 包含 MUI 组件源代码的目录路径
- **输出路径** (可选): 生成的 React 组件保存位置，默认为 `./output`

### 3. 运行程序

```bash
python main.py
```

程序会提示你输入：
1. AEM component path: 输入 AEM 组件目录路径
2. MUI library path: 输入 MUI 组件库路径
3. Output path: 输入输出路径（直接回车使用默认值 `./output`）
4. Max review iterations: 输入最大审查迭代次数（直接回车使用默认值 5）

### 4. 查看结果

工作流完成后，生成的 React 组件会保存在指定的输出路径中。

## 示例

```bash
# 1. 配置 API Key
echo 'OPENAI_API_KEY=sk-...' > .env

# 2. 运行程序
python main.py

# 3. 按提示输入路径
# Enter AEM component path: /path/to/aem/components/my-component
# Enter MUI library path: /path/to/mui/packages
# Enter output path (default: ./output): 
# Enter max review iterations (default: 5): 
```

## 故障排除

### 错误: OPENAI_API_KEY not found

**解决**: 确保 `.env` 文件存在且包含正确的 API Key

### 错误: ModuleNotFoundError

**解决**: 安装依赖
```bash
pip install -r requirements.txt
```

### 错误: 文件路径不存在

**解决**: 检查输入的路径是否正确，建议使用绝对路径

## 注意事项

1. 确保 OpenAI API Key 有效且有足够的额度
2. 文件路径建议使用绝对路径
3. 首次运行可能需要一些时间来下载模型（如果使用本地模型）
4. 工作流执行时间取决于文件数量和复杂度
