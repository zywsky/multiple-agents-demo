# AEM CSS 全面支持

## 概述

本文档总结了系统对AEM中所有可能的CSS场景的全面支持。

## 已支持的CSS场景

### 1. ✅ 组件本地CSS文件
- **位置**: `components/example-button/button.css`
- **支持格式**: `.css`, `.less`, `.scss`, `.module.css`, `.module.scss`
- **实现**: `find_component_css_files()`

### 2. ✅ 组件子目录CSS
- **位置**: 
  - `components/example-button/styles/button.css`
  - `components/example-button/clientlibs/css/button.css`
- **实现**: `find_component_css_files()`

### 3. ✅ ClientLibs（组件目录下）
- **位置**: `components/example-button/clientlibs/.content.xml`
- **功能**: 解析ClientLibs配置，提取CSS文件
- **实现**: `parse_clientlib_config()`, `find_css_for_classes()`

### 4. ✅ 独立的ClientLibs（通过category）
- **位置**: `clientlibs/base/`, `clientlibs/shared/`
- **功能**: 通过category查找ClientLibs
- **实现**: `find_clientlib_by_category()`

### 5. ✅ 递归处理embeds和dependencies
- **功能**: 递归处理嵌套的ClientLibs embeds和dependencies
- **实现**: `process_embeds_recursive()`, `process_dependencies_recursive()`

### 6. ✅ HTL中的样式引用
- **格式**: 
  - `data-sly-call="${template.styles @ path='button.css'}"`
  - `data-sly-call="${template.styles @ categories='example.components.base'}"`
- **实现**: `find_css_for_classes()` 中的策略3

### 7. ✅ 专门的CSS目录（保持相同层级）
- **位置**: 
  - `styles/components/example-button/button.css`
  - `css/components/example-button/button.css`
- **功能**: 保持与组件相同的层级结构
- **实现**: `find_css_in_dedicated_styles_directory()`

### 8. ✅ CSS变量/自定义属性 ⭐ 新增
- **位置**: `styles/variables.css`
- **内容**: CSS自定义属性（`--variable-name`）
- **实现**: `find_css_for_classes()` 中的策略5
- **测试数据**: `test_data/aem_components/styles/variables.css`

### 9. ✅ 主题CSS文件 ⭐ 新增
- **位置**: 
  - `styles/themes/light.css`
  - `styles/themes/dark.css`
- **功能**: 主题特定的样式覆盖
- **实现**: `find_css_for_classes()` 中的策略5
- **测试数据**: 
  - `test_data/aem_components/styles/themes/light.css`
  - `test_data/aem_components/styles/themes/dark.css`

### 10. ✅ 响应式CSS文件 ⭐ 新增
- **位置**: `styles/responsive/mobile.css`
- **功能**: 响应式样式（媒体查询）
- **实现**: `find_css_for_classes()` 中的策略5
- **测试数据**: `test_data/aem_components/styles/responsive/mobile.css`

### 11. ✅ 内联样式 ⭐ 新增
- **格式**: 
  - `style="color: red;"`
  - `data-sly-attribute.style="${variable}"`
- **功能**: 提取HTL中的内联样式
- **实现**: `extract_inline_styles_from_htl()`
- **测试数据**: `test_data/aem_components/example-button/button-inline.html`

### 12. ✅ CSS-in-JS ⭐ 新增
- **位置**: JavaScript文件中的CSS代码
- **格式**: 
  - `style.textContent = "..."`
  - `style.innerHTML = "..."`
- **功能**: 从JavaScript中提取CSS
- **实现**: `extract_css_from_javascript()`
- **测试数据**: `test_data/aem_components/example-button/button.js`

### 13. ✅ 动态CSS类 ⭐ 新增
- **位置**: JavaScript文件
- **格式**: 
  - `classList.add("class-name")`
  - `className += "class-name"`
- **功能**: 提取动态添加的CSS类
- **实现**: `extract_css_from_javascript()`

### 14. ✅ CSS Modules ⭐ 新增
- **格式**: `.module.css`, `.module.scss`
- **功能**: 支持CSS Modules格式
- **实现**: `find_component_css_files()` 中支持 `*.module.css` 和 `*.module.scss`

## CSS查找策略（完整优先级）

1. **组件目录下** - `components/example-button/button.css`
2. **组件子目录** - `components/example-button/styles/button.css`
3. **ClientLibs（组件目录下）** - `components/example-button/clientlibs/css/button.css`
4. **HTL样式引用（path）** - `data-sly-call="${template.styles @ path='...'}"`
5. **HTL样式引用（categories）** - `data-sly-call="${template.styles @ categories='...'}"`
6. **递归处理embeds** - 嵌入的ClientLibs
7. **递归处理dependencies** - 依赖的ClientLibs
8. **专门的CSS目录** - `styles/components/example-button/button.css`
9. **CSS变量文件** - `styles/variables.css`
10. **主题CSS文件** - `styles/themes/*.css`
11. **响应式CSS文件** - `styles/responsive/*.css`
12. **CSS-in-JS** - JavaScript中的CSS代码
13. **全局搜索** - 最后手段

## 新增的测试数据

### 1. CSS变量文件
```
test_data/aem_components/styles/variables.css
```
- 包含全局CSS变量定义
- 组件特定的CSS变量

### 2. 主题CSS文件
```
test_data/aem_components/styles/themes/
├── light.css  (浅色主题)
└── dark.css   (深色主题)
```

### 3. 响应式CSS文件
```
test_data/aem_components/styles/responsive/
└── mobile.css  (移动端样式)
```

### 4. 内联样式示例
```
test_data/aem_components/example-button/button-inline.html
```
- 包含 `style` 属性
- 包含 `data-sly-attribute.style`

### 5. JavaScript中的CSS
```
test_data/aem_components/example-button/button.js
```
- CSS-in-JS代码
- 动态CSS类操作
- 样式操作

## 新增的函数

### 1. `extract_inline_styles_from_htl(htl_content: str) -> Dict[str, str]`
- 从HTL中提取内联样式
- 返回 `{element_identifier: style_string}` 字典

### 2. `extract_css_from_javascript(js_content: str) -> Dict[str, str]`
- 从JavaScript中提取CSS相关代码
- 返回包含 `css_in_js`, `dynamic_classes`, `style_operations` 的字典

### 3. `find_css_for_classes()` 增强
- 新增参数 `js_content` 用于处理CSS-in-JS
- 新增策略5：查找CSS变量、主题、响应式文件
- 新增策略6：从JavaScript中提取CSS

## 使用示例

### 提取内联样式
```python
from utils.css_resolver import extract_inline_styles_from_htl

htl_content = '''
<button class="example-button" style="background-color: #007bff;">
'''
inline_styles = extract_inline_styles_from_htl(htl_content)
# 返回: {'example-button': 'background-color: #007bff;'}
```

### 提取JavaScript中的CSS
```python
from utils.css_resolver import extract_css_from_javascript

js_content = '''
const style = document.createElement("style");
style.textContent = `.example-button--clicked { transform: scale(0.95); }`;
button.classList.add("example-button--clicked");
'''
css_info = extract_css_from_javascript(js_content)
# 返回: {
#   'css_in_js': ['.example-button--clicked { transform: scale(0.95); }'],
#   'dynamic_classes': ['example-button--clicked'],
#   'style_operations': []
# }
```

### 完整的CSS查找
```python
from utils.css_resolver import find_css_for_classes

# 读取HTL和JS内容
with open('button.html', 'r') as f:
    htl_content = f.read()
with open('button.js', 'r') as f:
    js_content = f.read()

# 提取CSS类
css_classes = extract_css_classes_from_htl(htl_content)

# 查找CSS（包括所有场景）
css_results = find_css_for_classes(
    component_path='components/example-button',
    css_classes=css_classes,
    aem_repo_path='.',
    htl_content=htl_content,
    js_content=js_content  # 新增参数
)
```

## 总结

### ✅ 已支持的场景（14种）

1. ✅ 组件本地CSS文件
2. ✅ 组件子目录CSS
3. ✅ ClientLibs（组件目录下）
4. ✅ 独立的ClientLibs（通过category）
5. ✅ 递归处理embeds和dependencies
6. ✅ HTL中的样式引用
7. ✅ 专门的CSS目录（保持相同层级）
8. ✅ CSS变量/自定义属性 ⭐
9. ✅ 主题CSS文件 ⭐
10. ✅ 响应式CSS文件 ⭐
11. ✅ 内联样式 ⭐
12. ✅ CSS-in-JS ⭐
13. ✅ 动态CSS类 ⭐
14. ✅ CSS Modules ⭐

### 📊 覆盖范围

- **CSS文件位置**: ✅ 完整支持（组件目录、ClientLibs、专门目录、主题、响应式）
- **CSS格式**: ✅ 完整支持（.css, .less, .scss, .module.css, .module.scss）
- **CSS变量**: ✅ 完整支持
- **内联样式**: ✅ 完整支持
- **CSS-in-JS**: ✅ 完整支持
- **动态CSS类**: ✅ 完整支持
- **主题支持**: ✅ 完整支持
- **响应式支持**: ✅ 完整支持

现在系统可以处理AEM中所有常见的CSS场景！🎉
