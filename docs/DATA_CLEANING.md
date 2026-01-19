# 数据清洗指南

本文档说明如何使用数据清洗工具来清洗发送给大语言模型的数据。

## 为什么需要数据清洗？

在将数据发送给LLM之前，进行数据清洗可以：

1. **移除无效字符**：移除控制字符、零宽字符等可能导致问题的字符
2. **标准化格式**：统一换行符、空白字符等
3. **控制长度**：避免超出token限制
4. **保护隐私**：移除敏感信息（API密钥、密码等）
5. **提高质量**：确保发送给LLM的数据格式正确、内容完整

## 使用方法

### 基本用法

```python
from utils.prompt_cleaner import cleaner

# 清洗文本
text = "这是需要清洗的文本\n\n\n包含多余换行"
cleaned = cleaner.clean_text(text)
# 结果：多余的换行被标准化

# 清洗代码块（移除markdown标记）
code = "```jsx\nconst Component = () => {};\n```"
cleaned_code = cleaner.clean_code_block(code, language="jsx")
# 结果：移除了 ```jsx 和 ``` 标记

# 清洗文件内容
file_content = read_file("example.java")
cleaned_file = cleaner.clean_file_content(file_content, file_type="java")
# 结果：移除了注释，标准化了格式
```

### 清洗提示词数据

当需要清洗包含多个字段的数据字典时：

```python
from utils.prompt_cleaner import cleaner

prompt_data = {
    "code": code_content,  # 可能包含markdown标记
    "prompt": prompt_text,  # 可能包含控制字符
    "files": [
        {"path": "file1.js", "content": "..."},
        {"path": "file2.css", "content": "..."}
    ],
    "metadata": {"key": "value"}
}

cleaned_data = cleaner.clean_prompt_data(prompt_data, max_file_length=50000)
# 所有字符串字段都会被清洗，文件内容会被截断到指定长度
```

### 移除敏感信息

```python
from utils.prompt_cleaner import cleaner

text_with_secrets = """
api_key: sk-1234567890abcdef
password: mypassword123
token: abcdef123456
"""

safe_text = cleaner.remove_sensitive_info(text_with_secrets)
# 结果：敏感信息被替换为 ***
```

### 智能截断

当内容过长时，可以智能截断以保持结构完整：

```python
from utils.prompt_cleaner import cleaner

long_code = """function a() { ... }
function b() { ... }
function c() { ... }
... 更多代码 ...
"""

truncated = cleaner.truncate_long_content(
    long_code, 
    max_length=10000,
    preserve_structure=True  # 在函数/类/标签边界截断
)
# 结果：在最后一个完整函数后截断，而不是在中间截断
```

## 在Agent中使用

### 示例：在代码生成Agent中清洗数据

```python
from utils.prompt_cleaner import cleaner
from agents.base_agent import BaseAgent

class CodeWritingAgent(BaseAgent):
    def run(self, prompt: str, **kwargs):
        # 清洗输入提示词
        cleaned_prompt = cleaner.clean_text(prompt)
        
        # 清洗文件内容
        if 'file_content' in kwargs:
            kwargs['file_content'] = cleaner.clean_file_content(
                kwargs['file_content'],
                file_type=kwargs.get('file_type', 'text')
            )
        
        # 调用父类方法
        return super().run(cleaned_prompt, **kwargs)
```

### 示例：在工作流中清洗数据

```python
from utils.prompt_cleaner import cleaner

def write_code_node(state: WorkflowState):
    # 准备发送给LLM的数据
    prompt_data = {
        "aem_code": state.get("aem_code", ""),
        "bdl_components": state.get("selected_bdl_components", []),
        "file_analyses": state.get("file_analyses", [])
    }
    
    # 清洗数据
    cleaned_data = cleaner.clean_prompt_data(
        prompt_data,
        max_file_length=50000  # 限制单个文件最大长度
    )
    
    # 构建提示词
    prompt = build_prompt(cleaned_data)
    
    # 发送给LLM
    result = agent.run(prompt)
    
    return {"generated_code": result}
```

## 清洗功能详解

### 1. 文本清洗 (`clean_text`)

- 移除控制字符（\x00-\x1f, \x7f）
- 移除零宽字符（\u200b, \u200c等）
- 标准化换行符（统一为 \n）
- 移除多余空白行（最多保留2个连续换行）
- 移除行尾空白
- 可选长度限制

### 2. 代码块清洗 (`clean_code_block`)

- 移除markdown代码块标记（```language 和 ```）
- 移除代码块前后的空白
- 调用 `clean_text` 进行进一步清洗

### 3. 文件内容清洗 (`clean_file_content`)

根据文件类型进行特殊处理：

- **HTML/HTL**: 移除HTML注释
- **Java**: 移除Java注释（/* */ 和 //）
- **JavaScript/JSX**: 移除JavaScript注释
- **其他**: 通用文本清洗

### 4. 数据字典清洗 (`clean_prompt_data`)

递归清洗字典中的所有字符串值：

- 根据key名称判断类型（code/file → 文件清洗，prompt/message → 文本清洗）
- 递归处理嵌套的字典和列表
- 对文件内容应用长度限制

### 5. 智能截断 (`truncate_long_content`)

在保持结构完整的前提下截断：

- 查找最后一个完整的函数/类/标签
- 在该位置截断，而不是在中间截断
- 添加截断提示信息

### 6. 敏感信息移除 (`remove_sensitive_info`)

移除常见的敏感信息模式：

- API密钥：`api_key`, `api-key`, `apikey`
- 密码：`password`, `passwd`
- Token：`token`, `access_token`

## 最佳实践

1. **在发送给LLM前清洗**：
   ```python
   # 好的做法
   cleaned_prompt = cleaner.clean_text(prompt)
   result = llm.run(cleaned_prompt)
   
   # 不好的做法
   result = llm.run(prompt)  # 可能包含无效字符
   ```

2. **控制文件长度**：
   ```python
   # 限制单个文件最大长度，避免超出token限制
   cleaned_file = cleaner.clean_file_content(
       file_content,
       max_length=50000
   )
   ```

3. **移除敏感信息**：
   ```python
   # 在日志或发送给LLM前移除敏感信息
   safe_text = cleaner.remove_sensitive_info(text)
   ```

4. **保持结构完整**：
   ```python
   # 使用智能截断，保持代码结构
   truncated = cleaner.truncate_long_content(
       code,
       max_length=10000,
       preserve_structure=True
   )
   ```

5. **根据文件类型清洗**：
   ```python
   # 指定文件类型以获得最佳清洗效果
   cleaned = cleaner.clean_file_content(
       content,
       file_type="java"  # 会移除Java注释
   )
   ```

## 注意事项

1. **不要过度清洗**：某些特殊字符可能是代码的一部分
2. **保留重要信息**：确保清洗不会丢失关键信息
3. **测试清洗结果**：在应用清洗后测试LLM的输出质量
4. **性能考虑**：对于非常大的文件，清洗可能需要一些时间
