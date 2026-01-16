"""
基础 Agent 类
适配 LangChain 1.2+
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os
from dotenv import load_dotenv

load_dotenv()


class BaseAgent:
    """基础 Agent 类，提供通用的 agent 创建功能（适配 LangChain 1.2+）"""
    
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: List = None,
        model_name: str = "gpt-4",
        temperature: float = 0.1
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model_name = model_name
        self.temperature = temperature
        self.model = None
        self.agent_graph = None
        self._initialize_model()
        self._build_agent()
    
    def _initialize_model(self):
        """初始化模型（延迟初始化，避免在没有 API key 时立即失败）"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Please set it in .env file or environment variables."
            )
        self.model = ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            api_key=api_key
        )
    
    def _build_agent(self):
        """构建 agent graph（使用 LangChain 1.2+ 的新 API）"""
        # 使用新的 create_agent API
        self.agent_graph = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            debug=False
        )
    
    def run(self, input_text: str, chat_history: List = None) -> str:
        """运行 agent"""
        # 构建输入消息
        messages = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        if chat_history:
            messages.extend(chat_history)
        messages.append(HumanMessage(content=input_text))
        
        # 使用新的 graph API 调用
        config = {"configurable": {"thread_id": f"{self.name}_thread"}}
        result = self.agent_graph.invoke({"messages": messages}, config=config)
        
        # 提取最后一条 AI 消息作为输出
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                return last_message.content
            elif isinstance(last_message, dict) and "content" in last_message:
                return last_message["content"]
        
        # 如果没有找到消息，返回整个结果
        return str(result) if result else ""
