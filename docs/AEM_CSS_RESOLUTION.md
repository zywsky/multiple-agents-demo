# AEM CSS 样式解析方案

## 问题描述

在 AEM 中，CSS 样式是单独管理的，不是和组件定义放在一起。样式通过以下方式管理：

1. **组件本地 CSS 文件** - 组件目录下的 `.css` 文件
2. **ClientLibs (Client Libraries)** - 通过 `category` 和 `embed` 组织样式
3. **全局样式库** - 统一的样式管理

当从 HTL 模板中提取到使用的 CSS class（如 `class="example-button"`）时，需要找到对应的样式定义。

## AEM 样式管理机制

### 1. ClientLibs (Client Libraries)

AEM 使用 ClientLibs 机制管理 CSS 和 JS 文件：

```xml
<!-- .content.xml -->
<jcr:root xmlns:cq="http://www.day.com/jcr/cq/1.0" xmlns:jcr="http://www.jcp.org/jcr/1.0"
    jcr:primaryType="cq:ClientLibraryFolder"
    categories="[example.components]"
    embed="[core.wcm.components.base]"
    dependencies="[example.base]"/>
```

**关键属性**:
- `categories`: ClientLibs 的类别（用于引用）
- `embed`: 嵌入的其他 ClientLibs（合并样式）
- `dependencies`: 依赖的其他 ClientLibs（按顺序加载）

### 2. 样式文件位置

ClientLibs 通常在这些位置：
- `/apps/<project>/clientlibs/<category>/`
- `/etc/clientlibs/<category>/`
- `/libs/<project>/clientlibs/<category>/`

### 3. HTL 中的样式引用

```html
<!-- 方式 1: 直接引用组件 CSS -->
<sly data-sly-call="${template.styles @ path='button.css'}"/>

<!-- 方式 2: 通过 ClientLibs category -->
<sly data-sly-call="${template.styles @ categories='example.components'}"/>
```

## 解决方案

### 核心功能 (`utils/css_resolver.py`)

#### 1. 提取 CSS Classes

```python
extract_css_classes_from_htl(htl_content: str) -> Set[str]
```

从 HTL 内容中提取所有使用的 CSS class：
- 匹配 `class="..."` 属性
- 处理 `class="${variable}"` 动态 class
- 处理 `data-sly-attribute.class` 动态属性

#### 2. 查找组件 CSS 文件

```python
find_component_css_files(component_path: str) -> List[str]
```

在组件目录下查找 CSS 文件：
- `*.css`
- `*.less`
- `*.scss`

#### 3. 解析 ClientLibs 配置

```python
parse_clientlib_config(config_path: str) -> Dict[str, any]
```

解析 `.content.xml` 文件，提取：
- `categories`: ClientLibs 类别
- `embeds`: 嵌入的 ClientLibs
- `dependencies`: 依赖的 ClientLibs
- CSS/JS 文件路径

#### 4. 根据 Category 查找 ClientLibs

```python
find_clientlib_by_category(category: str, aem_repo_path: str) -> List[str]
```

在 AEM repository 中查找指定 category 的 ClientLibs 目录。

#### 5. 从 CSS 文件提取规则

```python
extract_css_rules_from_file(css_file_path: str, target_classes: Set[str]) -> Dict[str, str]
```

从 CSS 文件中提取指定 class 的样式规则：
- 精确匹配：`.class-name { ... }`
- 组合选择器：`.class-name, .other { ... }`
- 嵌套选择器：`.parent .class-name { ... }`

#### 6. 综合查找策略

```python
find_css_for_classes(
    component_path: str,
    css_classes: Set[str],
    aem_repo_path: str,
    htl_content: Optional[str] = None
) -> Dict[str, Dict[str, str]]
```

**查找策略（按优先级）**:

1. **组件目录下的 CSS 文件**
   - 直接在组件目录中查找 `*.css`, `*.less`, `*.scss`
   - 最直接，优先级最高

2. **组件目录下的 ClientLibs 配置**
   - 查找组件目录下的 `.content.xml`
   - 解析 ClientLibs 配置
   - 查找配置中引用的 CSS 文件
   - 处理 `embeds`（递归查找嵌入的 ClientLibs）

3. **HTL 中引用的样式文件**
   - 从 `data-sly-call="${template.styles @ path='...'}"` 提取路径
   - 查找对应的 CSS 文件

4. **根据 ClientLibs category 查找**
   - 如果 HTL 中使用了 `categories`，根据 category 查找 ClientLibs
   - 在常见的 ClientLibs 目录中搜索

5. **全局搜索（最后手段）**
   - 只在前面策略都没找到时才使用
   - 限制搜索范围（只在常见目录中）
   - 性能考虑

#### 7. 构建 CSS 摘要

```python
build_css_summary(
    component_path: str,
    htl_content: str,
    aem_repo_path: str
) -> Dict[str, any]
```

构建完整的 CSS 摘要：
- 使用的 CSS classes
- 找到的 CSS 定义
- 缺失的 CSS classes
- CSS 规则详情

## 工作流集成

### 在 `write_code` 节点中

1. **提取 CSS classes**
   - 从 HTL 分析结果中提取使用的 CSS classes

2. **查找 CSS 定义**
   - 调用 `build_css_summary()` 查找所有 CSS 规则

3. **添加到代码生成 prompt**
   - 将找到的 CSS 规则添加到 prompt 中
   - 提示 LLM 在生成 React 组件时考虑这些样式
   - 对于缺失的 CSS，提示 LLM 可能需要手动处理

### 示例 Prompt 片段

```
=== CSS STYLES (from AEM) ===

The component uses the following CSS classes:
- Used classes: example-button, example-button__text, example-button__icon
- Found CSS definitions: 3 classes
- Missing CSS definitions: 0 classes

CSS Rules Found:

.example-button:
  From: /path/to/button.css
  .example-button {
    display: inline-block;
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

.example-button__text:
  From: /path/to/button.css
  .example-button__text {
    font-weight: bold;
  }

⚠️ Note: When converting to React, you should:
1. Convert these CSS classes to BDL styling approach (sx prop, styled-components, or CSS modules)
2. Preserve the visual appearance and behavior
3. Handle responsive styles if present
```

## 使用示例

### 示例 1: 组件本地 CSS

```html
<!-- button.html -->
<button class="example-button">
    <span class="example-button__text">Click me</span>
</button>
```

**查找过程**:
1. 提取 classes: `example-button`, `example-button__text`
2. 在组件目录查找: `button.css`
3. 从 `button.css` 提取规则

### 示例 2: ClientLibs

```html
<!-- component.html -->
<div class="my-component">
    <button class="btn-primary">Button</button>
</div>
```

**查找过程**:
1. 提取 classes: `my-component`, `btn-primary`
2. 查找组件目录下的 `.content.xml`
3. 解析 ClientLibs 配置
4. 根据 `categories` 或 `embeds` 查找 ClientLibs
5. 从 ClientLibs 目录中的 CSS 文件提取规则

### 示例 3: HTL 样式引用

```html
<!-- component.html -->
<sly data-sly-call="${template.styles @ path='component.css'}"/>
<div class="my-component">...</div>
```

**查找过程**:
1. 提取 `data-sly-call` 中的路径: `component.css`
2. 构建完整路径: `<component_path>/component.css`
3. 从该文件提取规则

## 限制和注意事项

### 1. 动态 Class

如果 HTL 中使用变量动态生成 class：
```html
<div class="${model.className}">
```

这种情况下无法在静态分析时确定实际的 class 名称。

**解决方案**:
- 尝试从 Sling Model 推断可能的 class 值
- 在 prompt 中提示 LLM 注意动态 class

### 2. 编译后的样式

如果样式是编译后的（如从 LESS/SCSS 编译），可能需要：
- 查找源文件（`.less`, `.scss`）
- 或者使用编译后的 CSS

### 3. 性能考虑

全局搜索可能很慢，因此：
- 限制搜索范围
- 只在必要时使用
- 可以考虑缓存结果

### 4. 缺失的 CSS

如果某些 class 找不到定义：
- 在 prompt 中明确标注
- 提示 LLM 可能需要手动处理
- 或者从其他组件/全局样式中推断

## 总结

✅ **已实现**:
- CSS class 提取
- 多策略 CSS 查找
- ClientLibs 配置解析
- CSS 规则提取
- 工作流集成

✅ **查找策略**:
1. 组件本地 CSS
2. ClientLibs 配置
3. HTL 样式引用
4. Category 查找
5. 全局搜索（最后手段）

✅ **工作流集成**:
- 在代码生成阶段自动查找 CSS
- 将 CSS 规则添加到 prompt
- 提示 LLM 处理样式转换

现在系统可以自动查找组件使用的 CSS 样式，并在生成 React 组件时考虑这些样式！🎉
