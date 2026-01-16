# AEM to React Component Converter

使用 LangChain 和 LangGraph 构建的工作流，将 AEM (Adobe Experience Manager) HTL 组件转换为基于 MUI 的 React 组件。

## 功能特性

- **文件收集**: 自动收集 AEM 组件目录下的所有文件
- **AEM 分析**: 逐个文件分析 AEM 组件源代码，避免 token 限制
- **MUI 组件选择**: 智能选择匹配的 MUI 组件
- **代码生成**: 生成等价的 React 组件代码
- **多维度审查**: 
  - 安全审查 (Security Review)
  - 构建审查 (Build Review)
  - MUI 规范审查 (MUI Review)
- **自动修正**: 根据审查结果自动修正代码
- **循环优化**: Review -> Correct -> Review 循环，直到通过或达到最大迭代次数

## 项目结构

```
multiple-agents/
├── agents/              # 各个 Agent 实现
│   ├── base_agent.py
│   ├── file_collection_agent.py
│   ├── aem_analysis_agent.py
│   ├── mui_selection_agent.py
│   ├── code_writing_agent.py
│   ├── review_agents.py
│   └── correct_agent.py
├── tools/               # 工具函数
│   ├── file_tools.py
│   └── __init__.py
├── workflow/            # 工作流定义
│   ├── graph.py
│   └── __init__.py
├── main.py              # 主入口
├── requirements.txt      # 依赖
└── README.md
```

## 安装

1. 克隆或下载项目

2. 安装依赖:
```bash
pip install -r requirements.txt
```

3. 配置环境变量:
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
```

## 使用方法

运行主程序:
```bash
python main.py
```

程序会提示你输入:
1. AEM 组件路径 (例如: `/path/to/aem/components/my-component`)
2. MUI 组件库路径 (例如: `/path/to/mui/packages`)
3. 输出路径 (默认: `./output`)
4. 最大审查迭代次数 (默认: 5)

## 工作流步骤

1. **文件收集** (File Collection Agent)
   - 列出指定 AEM 组件目录下的所有文件（包括子目录）

2. **AEM 分析** (AEM Analysis Agent)
   - 逐个文件分析 AEM 组件源代码
   - 识别文件类型、功能、依赖关系
   - 生成结构化分析摘要

3. **MUI 组件选择** (MUI Selection Agent)
   - 根据 AEM 组件分析结果
   - 在 MUI 组件库中搜索匹配的组件
   - 返回选定的 MUI 组件文件路径

4. **代码生成** (Code Writing Agent)
   - 基于 AEM 源代码和选定的 MUI 组件
   - 生成等价的 React 组件代码
   - 使用 MUI 组件实现相同功能

5. **代码审查** (Review Agents - Subagents)
   - **Security Agent**: 检查安全问题（XSS、注入攻击等）
   - **Build Agent**: 检查构建错误和代码质量问题
   - **MUI Agent**: 检查 MUI 使用规范和最佳实践
   - 汇总所有审查结果

6. **代码修正** (Correct Agent)
   - 根据审查结果修正代码
   - 修正后返回步骤 5 重新审查
   - 循环直到通过或达到最大迭代次数

7. **完成**
   - 输出最终生成的 React 组件代码

## Agent 类型

本项目使用 LangGraph 的 subagents 模式:
- **主工作流**: 使用 StateGraph 管理整体流程
- **子 Agents**: 每个步骤使用专门的 Agent，职责明确
- **Review Subagents**: 三个独立的审查 Agent，分别负责不同维度

## 工具函数

项目提供了以下工具函数供 Agents 使用:

- `list_files()`: 列出目录下的所有文件
- `read_file()`: 读取文件内容
- `write_file()`: 写入文件内容
- `file_exists()`: 检查文件是否存在
- `create_directory()`: 创建目录
- `run_command()`: 执行命令（如 npm run build）
- `get_file_info()`: 获取文件信息

## 注意事项

1. **Token 限制**: AEM 分析 Agent 逐个文件处理，避免一次性分析所有文件导致 token 超限

2. **API Key**: 需要有效的 OpenAI API Key

3. **文件路径**: 确保提供的 AEM 组件路径和 MUI 库路径正确

4. **构建环境**: Build Review Agent 会执行 `npm run build`，确保目标目录有 package.json 和必要的依赖

5. **迭代限制**: 默认最大迭代次数为 5，可以在运行时调整

## 依赖版本

项目使用最新的稳定版本：

- **langgraph**: >=1.0.0,<2.0.0
- **langchain**: >=1.0.0,<2.0.0
- **langchain-openai**: >=1.0.0,<2.0.0
- **langchain-core**: >=1.0.0,<2.0.0
- **langchain-community**: >=0.3.0
- **langgraph-checkpoint**: >=2.0.0
- **langgraph-checkpoint-postgres**: >=2.0.0
- **pydantic**: >=2.10.0
- **pydantic-settings**: >=2.5.0
- **python-dotenv**: >=1.0.0

> 注意：项目已更新为 LangChain/LangGraph 1.0+ 版本，详情请查看 [VERSION_UPDATE.md](VERSION_UPDATE.md)

## 扩展

你可以根据需要扩展:
- 添加更多的审查维度
- 支持更多的 AEM 组件类型
- 改进 MUI 组件选择逻辑
- 添加代码格式化工具
- 支持 TypeScript

## 许可证

MIT License
