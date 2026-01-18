# 专门的CSS目录支持

## 问题描述

在AEM项目中，CSS文件可能存放在专门的CSS/样式文件夹下，而不是组件目录下。这些CSS文件的层级结构和组件定义的层级结构保持一致。

### 示例场景

**组件路径**:
```
apps/example/components/example-button/button.html
```

**可能的CSS路径**:
1. `apps/example/components/example-button/button.css` ✅ (组件目录下)
2. `apps/example/styles/components/example-button/button.css` ✅ (专门的styles目录，保持相同层级)
3. `apps/example/css/components/example-button/button.css` ✅ (专门的css目录，保持相同层级)
4. `apps/example/styles/example-button/button.css` ✅ (简化层级)

## 解决方案

### 1. 新增函数：`find_css_in_dedicated_styles_directory()`

**位置**: `utils/css_path_finder.py`

**功能**: 在专门的CSS/样式目录中查找CSS文件，保持与组件相同的层级结构

**搜索策略**:

1. **保持完整层级结构**:
   - 组件：`components/example-button`
   - CSS：`styles/components/example-button/button.css`
   - CSS：`css/components/example-button/button.css`

2. **简化层级结构**:
   - 组件：`components/example-button`
   - CSS：`styles/example-button/button.css`
   - CSS：`css/example-button/button.css`

3. **路径替换**:
   - 将路径中的 `components` 替换为 `styles` 或 `css`
   - 保持其他路径部分不变

4. **全局搜索**:
   - 在AEM repository根目录下搜索所有 `styles/components/{component_name}` 和 `css/components/{component_name}` 目录

### 2. 集成到CSS查找流程

**文件**: `utils/css_resolver.py`

**修改**: `find_component_css_files()` 函数

- 添加了对 `find_css_in_dedicated_styles_directory()` 的调用
- 自动推断AEM repository根路径
- 将找到的CSS文件合并到结果中

### 3. 改进 `infer_css_path_from_component()`

**增强功能**:
- 支持 `css` 目录（不仅仅是 `styles`）
- 保持完整的层级结构（`styles/components/{component_name}`）
- 向上查找多级目录

## 测试数据

### 创建的测试数据

1. **styles目录结构**:
   ```
   test_data/aem_components/
   └── styles/
       └── components/
           ├── example-button/
           │   └── button.css
           └── example-card/
               └── card.css
   ```

2. **css目录结构**:
   ```
   test_data/aem_components/
   └── css/
       └── components/
           ├── example-button/
           │   └── button.css
           └── example-card/
               └── card.css
   ```

### CSS文件内容

- `styles/components/example-button/button.css` - 完整的按钮样式
- `styles/components/example-card/card.css` - 完整的卡片样式
- `css/components/example-button/button.css` - 额外的按钮样式（动画效果）
- `css/components/example-card/card.css` - 额外的卡片样式（动画效果）

## 使用示例

### 基本用法

```python
from utils.css_path_finder import find_css_in_dedicated_styles_directory
from utils.css_resolver import find_component_css_files

# 查找专门的CSS目录
component_path = 'test_data/aem_components/example-button'
aem_repo = 'test_data/aem_components'

dedicated_css = find_css_in_dedicated_styles_directory(component_path, aem_repo)
# 返回: [
#   'test_data/aem_components/styles/components/example-button/button.css',
#   'test_data/aem_components/css/components/example-button/button.css'
# ]

# 完整的CSS查找（包括所有位置）
all_css = find_component_css_files(component_path)
# 返回所有找到的CSS文件（组件目录、ClientLibs、专门的CSS目录等）
```

## 搜索优先级

CSS查找的完整优先级顺序：

1. **组件目录下** - `components/example-button/button.css`
2. **组件子目录** - `components/example-button/styles/button.css`
3. **ClientLibs** - `components/example-button/clientlibs/css/button.css`
4. **专门的styles目录（保持层级）** - `styles/components/example-button/button.css`
5. **专门的css目录（保持层级）** - `css/components/example-button/button.css`
6. **简化层级** - `styles/example-button/button.css`
7. **全局搜索** - 在AEM repository中搜索

## 支持的目录结构

### 场景1: 保持完整层级
```
components/example-button/button.html
styles/components/example-button/button.css  ✅
css/components/example-button/button.css     ✅
```

### 场景2: 简化层级
```
components/example-button/button.html
styles/example-button/button.css  ✅
css/example-button/button.css     ✅
```

### 场景3: 路径替换
```
apps/example/components/button/button.html
apps/example/styles/button/button.css  ✅
apps/example/css/button/button.css     ✅
```

### 场景4: 多级嵌套
```
apps/project/modules/components/button/button.html
apps/project/modules/styles/components/button/button.css  ✅
apps/project/modules/css/components/button/button.css     ✅
```

## 性能考虑

- 向上查找限制在5层以内
- 全局搜索只在提供 `aem_repo_path` 时执行
- 使用 `rglob` 进行递归搜索，但会限制深度
- 结果会自动去重

## 总结

✅ **已实现的功能**:
- 专门的CSS目录查找（styles和css）
- 保持相同的层级结构
- 支持完整层级和简化层级
- 路径替换功能
- 全局搜索支持
- 集成到完整的CSS查找流程

✅ **测试数据**:
- 创建了styles和css目录结构
- 包含完整的CSS文件示例
- 覆盖了多种场景

现在系统可以处理CSS文件存放在专门目录下的所有常见场景！🎉
