# 版本更新说明

## 已更新到 LangChain/LangGraph 1.0+

项目已更新为使用最新的稳定版本：

### 依赖版本

- **langgraph**: >=1.0.0,<2.0.0
- **langchain**: >=1.0.0,<2.0.0
- **langchain-openai**: >=1.0.0,<2.0.0
- **langchain-core**: >=1.0.0,<2.0.0
- **langchain-community**: >=0.3.0
- **langgraph-checkpoint**: >=2.0.0
- **langgraph-checkpoint-postgres**: >=2.0.0
- **pydantic**: >=2.10.0
- **pydantic-settings**: >=2.5.0

### 代码更新

#### 1. 导入路径更新

**之前 (LangChain 0.x)**:
```python
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate
```

**现在 (LangChain 1.0+)**:
```python
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
```

#### 2. 更新的文件

- `agents/base_agent.py`: 更新了导入路径
- `agents/file_collection_agent.py`: 更新了 tool 导入
- `agents/aem_analysis_agent.py`: 更新了 tool 导入
- `agents/mui_selection_agent.py`: 更新了 tool 导入
- `agents/code_writing_agent.py`: 更新了 tool 导入
- `agents/review_agents.py`: 更新了 tool 导入
- `agents/correct_agent.py`: 更新了 tool 导入
- `requirements.txt`: 更新了所有依赖版本

### 安装新版本

```bash
# 卸载旧版本（可选）
pip uninstall langchain langchain-openai langgraph langchain-core

# 安装新版本
pip install -r requirements.txt
```

### 兼容性说明

- LangChain 1.0 是稳定版本，承诺在 v2.0 之前不会有破坏性变更
- 所有现有功能保持不变
- API 调用方式基本一致，主要是导入路径的调整

### 验证安装

运行以下命令验证安装：

```bash
python -c "from langchain_core.tools import tool; print('OK')"
python -c "from langgraph.graph import StateGraph; print('OK')"
python -c "from agents.base_agent import BaseAgent; print('OK')"
```

### 注意事项

1. 如果之前使用的是 LangChain 0.x 版本，需要重新安装依赖
2. 确保 Python 版本 >= 3.10
3. 新版本可能需要更多的磁盘空间（包含更多功能）

### 新功能

LangChain 1.0+ 带来的改进：
- 更稳定的 API
- 更好的类型支持
- 改进的中间件支持
- 统一的工具调用接口
- 更好的错误处理
