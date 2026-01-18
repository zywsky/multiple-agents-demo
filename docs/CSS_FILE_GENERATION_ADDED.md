# CSS文件生成功能已添加

## 问题确认

您说得对！之前的工作流虽然会解析AEM的CSS样式，但**只生成了React组件文件（.jsx），没有生成独立的样式文件**。

## 已完成的修改

### 1. ✅ 更新了CodeGenerationResult Schema

**文件**: `utils/schemas.py`

添加了 `css_code` 字段：
```python
class CodeGenerationResult(BaseModel):
    component_code: str
    css_code: Optional[str] = Field(None, description="生成的 CSS Module 代码")
    # ... 其他字段
```

### 2. ✅ 更新了代码生成Prompt

**文件**: `workflow/graph.py`

在代码生成prompt中明确要求：
- 生成React组件代码 **AND** CSS Module文件
- 使用CSS Modules格式（.module.css 或 .module.scss）
- 在React组件中导入CSS模块：`import styles from './Button.module.css'`
- 使用CSS Modules语法：`className={styles.className}`

### 3. ✅ 添加了CSS代码提取逻辑

**文件**: `workflow/graph.py`

在 `write_code()` 函数中：
- 从结构化输出中提取 `css_code`
- 如果结构化输出失败，从文本中提取CSS代码块
- 支持提取 ````css` 和 ````scss` 代码块

### 4. ✅ 添加了CSS文件保存逻辑

**文件**: `workflow/graph.py`

- 自动检测CSS文件类型（.module.css 或 .module.scss）
- 保存CSS文件到输出目录
- 文件名格式：`{component_name}.module.css` 或 `{component_name}.module.scss`
- 将CSS文件路径添加到工作流状态

### 5. ✅ 更新了WorkflowState

**文件**: `workflow/graph.py`, `test_workflow.py`, `main.py`

添加了 `css_file_path` 字段到工作流状态。

## 生成的文件结构

现在工作流会生成：

```
output/
└── Button Component (Simple)/
    ├── Button.jsx          # React组件代码
    └── Button.module.css   # CSS Module样式文件（或.module.scss）
```

## CSS转换规则

从AEM CSS转换为React CSS Modules：

1. **类名转换**：
   - AEM: `.example-button` → React: `.exampleButton` (camelCase)
   - AEM: `.example-button__text` → React: `.exampleButtonText`

2. **导入方式**：
   ```jsx
   import styles from './Button.module.css';
   ```

3. **使用方式**：
   ```jsx
   <button className={styles.exampleButton}>
     <span className={styles.exampleButtonText}>Text</span>
   </button>
   ```

4. **保留所有样式**：
   - 伪类（:hover, :active等）
   - 媒体查询
   - 动画和过渡
   - 所有CSS属性

## 工作流程

1. **CSS解析阶段**（已有）：
   - 从AEM HTL模板提取CSS类名
   - 查找对应的CSS文件
   - 提取CSS规则

2. **代码生成阶段**（新增）：
   - LLM生成React组件代码
   - **同时生成CSS Module文件**
   - 在组件中正确导入和使用CSS模块

3. **文件保存阶段**（新增）：
   - 保存 `.jsx` 文件
   - **保存 `.module.css` 或 `.module.scss` 文件**

## 测试建议

运行测试后，检查：
1. ✅ 是否生成了CSS文件
2. ✅ CSS文件内容是否正确
3. ✅ React组件是否正确导入CSS模块
4. ✅ 类名是否正确转换（camelCase）
5. ✅ 所有样式规则是否保留

## 注意事项

1. **CSS Modules命名**：
   - 类名会自动转换为camelCase
   - 如果AEM使用BEM命名（如 `button__text`），会转换为 `buttonText`

2. **样式完整性**：
   - 如果某些CSS类找不到定义，会在prompt中标注
   - LLM需要推断或使用BDL默认样式

3. **依赖组件的样式**：
   - 依赖组件的CSS也会被包含
   - 需要确保样式不冲突

## 下一步

现在可以重新运行测试，验证：
- ✅ CSS文件是否生成
- ✅ CSS内容是否正确
- ✅ React组件是否正确使用CSS模块
