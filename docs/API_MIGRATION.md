# LangChain 1.2+ API 迁移说明

## 主要变更

### 1. Agent 创建 API 变更

**旧版本 (LangChain < 1.0)**:
```python
from langchain.agents import create_openai_tools_agent, AgentExecutor

agent = create_openai_tools_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)
result = agent_executor.invoke({"input": "..."})
```

**新版本 (LangChain 1.2+)**:
```python
from langchain.agents import create_agent

agent_graph = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt
)
result = agent_graph.invoke({"messages": [HumanMessage(...)]})
```

### 2. 主要差异

1. **不再需要 `AgentExecutor`**: `create_agent` 直接返回一个可执行的 graph
2. **输入格式改变**: 不再使用 `{"input": "..."}`，而是使用 `{"messages": [...]}`
3. **输出格式改变**: 返回的是包含 `messages` 的状态，而不是直接的 `output`
4. **不再需要 `ChatPromptTemplate`**: `system_prompt` 直接作为参数传入

### 3. 代码更新

已更新的文件：
- `agents/base_agent.py`: 完全重写以使用新的 `create_agent` API

### 4. 使用示例

```python
from agents.base_agent import BaseAgent

agent = BaseAgent(
    name="MyAgent",
    system_prompt="You are a helpful assistant.",
    tools=[...],
    model_name="gpt-4"
)

result = agent.run("Hello!")
```

## 注意事项

- LangChain 1.2+ 的 API 更加简洁和统一
- 所有 agents 现在都返回 graph，而不是 executor
- 消息格式统一使用 `messages` 列表
- 需要配置 `thread_id` 用于状态管理
