"""
重试机制工具
支持指数退避和错误分类
"""
import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Tuple, Optional, List
from langchain_core.exceptions import LangChainException

logger = logging.getLogger(__name__)

T = TypeVar('T')

# 可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    LangChainException,
    ConnectionError,
    TimeoutError,
    Exception  # 通用异常，但需要检查具体错误信息
)

# 不可重试的异常（立即失败）
NON_RETRYABLE_EXCEPTIONS = (
    ValueError,  # 配置错误等
    KeyError,    # 状态错误等
    TypeError,   # 类型错误等
)


def is_retryable_error(error: Exception) -> bool:
    """判断错误是否可重试"""
    # 检查是否是不可重试的异常
    if isinstance(error, NON_RETRYABLE_EXCEPTIONS):
        return False
    
    # 检查是否是可重试的异常
    if isinstance(error, RETRYABLE_EXCEPTIONS):
        # 对于通用 Exception，检查错误信息
        error_msg = str(error).lower()
        non_retryable_keywords = [
            "invalid", "not found", "permission denied", 
            "authentication", "authorization", "api key"
        ]
        if any(keyword in error_msg for keyword in non_retryable_keywords):
            return False
        return True
    
    return False


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """
    重试装饰器，支持指数退避
    
    Args:
        max_retries: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数基数
        jitter: 是否添加随机抖动
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # 检查是否可重试
                    if not is_retryable_error(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                        raise
                    
                    # 如果已经达到最大重试次数，抛出异常
                    if attempt >= max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    # 计算延迟时间
                    if jitter:
                        import random
                        delay = min(
                            initial_delay * (exponential_base ** attempt) + random.uniform(0, 1),
                            max_delay
                        )
                    else:
                        delay = min(
                            initial_delay * (exponential_base ** attempt),
                            max_delay
                        )
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            
            # 理论上不会到达这里
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Unexpected error in {func.__name__}")
        
        return wrapper
    return decorator
