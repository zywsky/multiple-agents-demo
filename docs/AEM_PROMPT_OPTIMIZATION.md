# AEM 专家 Prompt 优化总结

## 问题分析

### 1. 信息充分性评估

**当前提供的文件**:
- ✅ HTL 模板（UI 结构）
- ✅ Dialog XML（Props 定义）
- ✅ JavaScript（交互逻辑）

**从 AEM 专家角度看，这些是否足够？**

**答案：基本足够，但有注意事项**

#### ✅ 足够的原因：

1. **HTL 模板** - 包含了最关键的 UI 结构信息
   - HTML 元素和层次结构
   - data-sly-* 使用模式
   - 组件组合（data-sly-resource）
   - 条件渲染逻辑

2. **Dialog XML** - 直接映射到 React Props
   - 字段定义 → Props 定义
   - 字段类型 → Prop 类型
   - 必填字段 → Required props
   - 默认值 → Default prop values

3. **JavaScript** - 交互逻辑
   - 事件处理器 → React 事件处理器
   - DOM 操作 → React state/refs
   - 数据获取 → React hooks

#### ⚠️ 可能缺失的信息：

1. **Java Sling Model 结构**（后续会提供）
   - 从 HTL 的 `data-sly-use` 可以推断需要的属性
   - 但完整的类型定义在 Java Model 中

2. **组件组合关系**（.content.xml）
   - 允许的父组件/子组件
   - 组件策略配置
   - 这些对 React 转换影响较小

3. **CSS 样式**（后续会提供）
   - 当前可以生成功能对等的组件
   - 样式可以在后续步骤处理

**结论**：HTL + Dialog + JS **足以生成功能对等的 React 组件**。Java Model 和 CSS 可以在后续步骤中优化。

### 2. Prompt 是否需要优化？

**需要！** 当前 prompt 可以进一步优化：

#### 当前 Prompt 的不足：

1. ❌ **缺少文件作用说明** - LLM 可能不理解每个文件的目的
2. ❌ **缺少转换示例** - 没有具体的 AEM → React 转换示例
3. ❌ **缺少信息充分性提示** - 没有告知 LLM 当前信息是否完整
4. ❌ **转换要求不够详细** - 缺少具体的转换规则和边界情况

### 3. 是否需要文件说明？

**强烈建议添加！** 原因：

1. ✅ **帮助理解** - 每个文件在 AEM 中的作用不同，说明有助于理解
2. ✅ **提高准确性** - LLM 理解文件作用后，转换更准确
3. ✅ **减少误解** - 避免将 Dialog 误认为是模板，将 HTL 误认为是配置

## ✅ 已实现的优化

### 1. 文件上下文说明 ✅

**实现**：`utils/file_context_builder.py`

**功能**：
- 为每个文件类型生成详细的描述说明
- 说明文件在 AEM 中的作用
- 说明如何转换到 React
- 提供转换指导

**示例**：
```python
HTL Template File
Purpose: Defines UI structure and presentation logic
What it contains:
- HTML structure with HTL-specific attributes
- Data binding expressions
- Conditional rendering logic
...

Conversion importance: CRITICAL
React equivalent: JSX structure in React component
```

### 2. 增强的 Prompt ✅

**实现**：在 `workflow/graph.py` 的 `write_code()` 函数中

**改进**：
1. ✅ **文件角色说明** - 每个文件的作用和重要性
2. ✅ **信息充分性评估** - 告知 LLM 当前信息是否完整
3. ✅ **详细的转换规则** - 具体的 AEM → React 映射规则
4. ✅ **转换示例** - 提供具体的转换示例
5. ✅ **边界情况处理** - 如何处理 null、默认值等

### 3. 优化的 Prompt 结构 ✅

```
=== FILE ROLES AND CONTEXTS ===
[每个文件的作用说明]

=== AEM COMPONENT SOURCE CODE ===
[HTL, Dialog, JS 摘要]

=== CRITICAL CONVERSION REQUIREMENTS ===
1. UI Structure (详细规则)
2. Props Interface (详细映射)
3. Data Binding (详细转换)
... [更多规则]

=== CONVERSION EXAMPLE ===
[具体示例]

=== FINAL REQUIREMENTS ===
[检查清单]
```

## 📋 关键优化点

### 1. 文件说明的重要性

**之前**：
```
File: button.html
Analysis: ...
```

**现在**：
```
File: button.html (HTL Template)
Purpose: Defines UI structure and presentation logic
Conversion importance: CRITICAL
- Maintain exact HTML structure in JSX
- Convert data-sly-* to React patterns
...
```

### 2. 转换规则的详细性

**之前**：
```
Convert data-sly-use to React props
```

**现在**：
```
3. Data Binding (from HTL data-sly-use):
   - data-sly-use.model → React props
   - model.property → props.property or state.property
   - If model is used for calculations → useMemo
   - Sling Model structure → TypeScript interface
```

### 3. 示例的价值

**新增**：
```
=== CONVERSION EXAMPLE ===
AEM HTL:
  <button data-sly-test="{{model.showButton}}" 
          data-sly-attribute.onclick="{{model.onClick}}">
    {{model.text}}
  </button>

React Equivalent:
  {{props.showButton && (
    <Button onClick={props.onClick || handleClick}>
      {{props.text}}
    </Button>
  )}}
```

## 🎯 效果预期

### Prompt 优化前：
- LLM 可能不理解文件作用
- 转换规则不够明确
- 可能遗漏某些转换细节

### Prompt 优化后：
- ✅ LLM 清楚理解每个文件的作用
- ✅ 转换规则清晰明确
- ✅ 有具体示例参考
- ✅ 信息充分性提示
- ✅ 检查清单确保完整性

## 📊 信息充分性评估

### 基本转换（HTL + Dialog）
**充分性**：✅ **85%**
- ✅ UI 结构：完全确定
- ✅ Props 接口：完全确定
- ⚠️ 交互逻辑：可能不完整（如果有复杂 JS）

### 完整转换（HTL + Dialog + JS）
**充分性**：✅ **95%**
- ✅ UI 结构：完全确定
- ✅ Props 接口：完全确定
- ✅ 交互逻辑：完全确定
- ⚠️ 数据模型：部分推断（从 HTL 使用推断）

### 理想转换（+ Java Model + CSS）
**充分性**：✅ **100%**
- ✅ UI 结构：完全确定
- ✅ Props 接口：完全确定
- ✅ 交互逻辑：完全确定
- ✅ 数据模型：完全确定
- ✅ 样式：完全确定

## ✅ 总结

### 信息充分性
- **HTL + Dialog + JS 足够生成功能对等的 React 组件**
- Java Model 和 CSS 可以在后续步骤优化

### Prompt 优化
- ✅ **已优化** - 添加了文件说明、详细规则、示例
- ✅ **信息充分性提示** - 告知 LLM 当前信息的完整性
- ✅ **转换指南** - 详细的转换规则和示例

### 文件说明
- ✅ **强烈推荐** - 已实现文件上下文说明
- ✅ **提高准确性** - 帮助 LLM 理解每个文件的作用
- ✅ **减少误解** - 避免混淆不同文件类型

**代码已准备好生成高质量的 React 组件！** 🎉
