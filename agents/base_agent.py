"""
基础 Agent 类
适配 LangChain 1.2+
支持结构化输出、重试机制、错误处理
"""
from typing import List, Dict, Any, Optional, TypeVar, Generic, Type
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, ValidationError
import os
import logging
from dotenv import load_dotenv

from utils.retry import retry_with_backoff

load_dotenv()

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseAgent:
    """基础 Agent 类，提供通用的 agent 创建功能（适配 LangChain 1.2+）"""

    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: List = None,
        model_name: str = "gpt-4",
        temperature: float = 0.1,
        output_schema: Optional[Type[BaseModel]] = None,
        max_retries: int = 3
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model_name = model_name
        self.temperature = temperature
        self.output_schema = output_schema
        self.max_retries = max_retries
        self.model = None
        self.agent_graph = None
        self.output_parser = None

        self._initialize_model()
        self._setup_output_parser()
        self._build_agent()

    def _initialize_model(self):
        """初始化模型（延迟初始化，避免在没有 API key 时立即失败）"""
        # api_key = os.getenv("OPENAI_API_KEY")
        # if not api_key:
        #     raise ValueError(
        #         "OPENAI_API_KEY not found. Please set it in .env file or environment variables."
        #     )
        self.model =  ChatOpenAI(
                api_key="181cc99c-f9d5-4a80-af1d-3296e7a371af",
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                model="ep-20250721151616-bkfms",
                temperature=0,
                max_tokens=2048,
            )

    
    def _setup_output_parser(self):
        """设置输出解析器（如果提供了 schema）"""
        if self.output_schema:
            self.output_parser = PydanticOutputParser(pydantic_object=self.output_schema)
            # 更新 system prompt 以包含输出格式说明
            format_instructions = self.output_parser.get_format_instructions()
            self.system_prompt = f"{self.system_prompt}\n\n{format_instructions}"
    
    def _build_agent(self):
        """构建 agent graph（使用 LangChain 1.2+ 的新 API）"""
        # 使用新的 create_agent API
        self.agent_graph = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            debug=False
        )
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    def _invoke_agent(self, messages: List) -> Dict[str, Any]:
        """调用 agent（带重试）"""
        config = {"configurable": {"thread_id": f"{self.name}_thread"}}
        result = self.agent_graph.invoke({"messages": messages}, config=config)
        return result
    
    def _extract_content(self, result: Dict[str, Any]) -> str:
        """从 agent 结果中提取文本内容"""
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                return last_message.content
            elif isinstance(last_message, dict) and "content" in last_message:
                return last_message["content"]
        
        # 如果没有找到消息，返回整个结果
        return str(result) if result else ""
    
    def _parse_structured_output(self, content: str) -> Optional[BaseModel]:
        """解析结构化输出"""
        if not self.output_parser or not self.output_schema:
            return None
        
        try:
            parsed = self.output_parser.parse(content)
            return parsed
        except ValidationError as e:
            logger.warning(f"Failed to parse structured output for {self.name}: {str(e)}")
            logger.debug(f"Raw content: {content[:500]}...")
            # 尝试从文本中提取 JSON
            import json
            import re
            # 查找 JSON 块
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group())
                    return self.output_schema(**json_data)
                except (json.JSONDecodeError, ValidationError):
                    pass
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing output for {self.name}: {str(e)}")
            return None
    
    def run(
        self, 
        input_text: str, 
        chat_history: List = None,
        return_structured: bool = True
    ) -> Any:
        """
        运行 agent
        
        Args:
            input_text: 输入文本
            chat_history: 聊天历史
            return_structured: 是否返回结构化输出（如果定义了 schema）
        
        Returns:
            如果定义了 output_schema 且 return_structured=True，返回解析后的 Pydantic 模型
            否则返回字符串
        """
        # 构建输入消息
        messages = []
        if self.system_prompt:
            messages.append(SystemMessage(content=self.system_prompt))
        if chat_history:
            messages.extend(chat_history)
        messages.append(HumanMessage(content=input_text))
        
        try:
            # 调用 agent（带重试）
            result = self._invoke_agent(messages)
            content = self._extract_content(result)
            
            # 如果定义了 schema 且需要结构化输出，尝试解析
            if return_structured and self.output_schema:
                structured = self._parse_structured_output(content)
                if structured:
                    return structured
                # 如果解析失败，记录警告但返回原始内容
                logger.warning(
                    f"Failed to parse structured output for {self.name}, "
                    f"returning raw content. Consider improving the prompt."
                )
            
            return content
        except Exception as e:
            logger.error(f"Error running {self.name}: {str(e)}")
            raise
