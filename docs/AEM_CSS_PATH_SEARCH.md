# AEM CSS 路径搜索增强

## 问题

在 AEM 中，CSS 文件可能不在组件目录下，而是在路径相似的文件夹中。例如：

**组件路径**: `/apps/example/components/button`

**可能的 CSS 路径**:
1. `/apps/example/components/button/button.css` ✅ (组件目录下)
2. `/apps/example/components/button/styles/button.css` ✅ (styles 子目录)
3. `/apps/example/components/button/clientlibs/button.css` ✅ (clientlibs 子目录)
4. `/apps/example/components/styles/button/button.css` ✅ (同级 styles 目录)
5. `/apps/example/components/styles/button.css` ✅ (同级 styles 目录)
6. `/apps/example/styles/components/button/button.css` ✅ (父级 styles 目录)
7. `/apps/example/styles/button.css` ✅ (共享 styles 目录)

## 解决方案

### 1. CSS 路径查找器 (`utils/css_path_finder.py`) ⭐ 新增

#### 核心功能

**`find_css_in_similar_paths(component_path, css_filename=None)`**
- 在组件路径的相似位置查找 CSS 文件
- 支持 6 种搜索策略（按优先级）
- 自动推断可能的 CSS 位置

**`find_css_by_component_name(base_path, component_name, max_depth=5)`**
- 根据组件名称在相似路径中查找
- 支持多种路径模式
- 限制搜索深度

**`find_files_by_name_pattern(base_path, name_pattern, file_extension=None, max_depth=5)`**
- 通用的文件查找工具
- 根据文件名模式在相似路径中搜索
- 支持文件扩展名过滤

**`infer_css_path_from_component(component_path)`**
- 从组件路径推断可能的 CSS 文件路径
- 考虑路径结构（components → styles）
- 向上查找多级目录

### 2. CSS Resolver 增强

**`find_component_css_files()` 增强**:
- ✅ 原来：只在组件目录下查找
- ✅ 现在：在组件目录 + 相似路径中查找

**搜索策略**:
1. 组件目录下直接查找
2. 组件 styles/clientlibs 子目录
3. 使用路径查找器在相似路径中查找
4. 根据组件名称查找
5. 推断可能的 CSS 路径

### 3. 工具增强

**新增工具**:
- `find_files_in_similar_paths()` - 在相似路径中查找文件
- `find_css_for_component_in_similar_paths()` - 查找组件的 CSS 文件

**Agent 配置**:
- `AEMAnalysisAgent` 现在可以使用这些工具主动搜索 CSS 文件

## 搜索策略详解

### 策略 1: 组件目录下
```
/apps/example/components/button/button.css
```

### 策略 2: 组件 styles 子目录
```
/apps/example/components/button/styles/button.css
```

### 策略 3: 组件 clientlibs 子目录
```
/apps/example/components/button/clientlibs/button.css
```

### 策略 4: 同级 styles 目录（按组件名）
```
/apps/example/components/styles/button/button.css
```

### 策略 5: 同级 styles 目录（直接）
```
/apps/example/components/styles/button.css
```

### 策略 6: 父级 styles 目录（向上查找最多 3 层）
```
/apps/example/styles/components/button/button.css
/apps/example/styles/button.css
/apps/styles/example/button.css
```

### 策略 7: 路径结构推断
如果组件在 `/apps/example/components/button`，推断：
- `/apps/example/styles/components/button/*.css`
- `/apps/example/styles/button/*.css`

## 使用示例

### 示例 1: 查找组件 CSS

```python
from utils.css_path_finder import find_css_in_similar_paths

# 查找 button 组件的 CSS
css_files = find_css_in_similar_paths(
    "/apps/example/components/button",
    css_filename="button.css"
)

# 返回所有可能的 CSS 文件路径
```

### 示例 2: 根据组件名称查找

```python
from utils.css_path_finder import find_css_by_component_name

# 在相似路径中查找 button 相关的 CSS
css_files = find_css_by_component_name(
    "/apps/example/components",
    "button",
    max_depth=5
)
```

### 示例 3: 通用文件查找

```python
from tools import find_files_in_similar_paths

# 查找所有 button 相关的 CSS 文件
css_files = find_files_in_similar_paths(
    "/apps/example/components",
    "button",
    file_extension="css",
    max_depth=5
)
```

## 工作流集成

### 自动增强

在 `find_css_for_classes()` 中：
1. 首先在组件目录下查找（原有逻辑）
2. **新增**：在相似路径中查找（使用 `find_css_in_similar_paths`）
3. **新增**：根据组件名称查找（使用 `find_css_by_component_name`）
4. **新增**：推断可能的 CSS 路径（使用 `infer_css_path_from_component`）

### Agent 使用

`AEMAnalysisAgent` 现在可以：
- 使用 `find_css_for_component_in_similar_paths()` 主动搜索 CSS
- 使用 `find_files_in_similar_paths()` 查找相关文件

## 路径匹配示例

### 场景 1: 标准结构

**组件**: `/apps/example/components/button`
**CSS**: `/apps/example/components/button/button.css`

✅ **找到**

### 场景 2: Styles 子目录

**组件**: `/apps/example/components/button`
**CSS**: `/apps/example/components/button/styles/button.css`

✅ **找到**

### 场景 3: 共享 Styles 目录

**组件**: `/apps/example/components/button`
**CSS**: `/apps/example/components/styles/button.css`

✅ **找到**

### 场景 4: 父级 Styles 目录

**组件**: `/apps/example/components/button`
**CSS**: `/apps/example/styles/components/button/button.css`

✅ **找到**

### 场景 5: 路径结构替换

**组件**: `/apps/example/components/button`
**CSS**: `/apps/example/styles/button/button.css`

✅ **找到**（通过路径结构推断）

## 性能考虑

- **搜索深度限制**: 默认最多 5 层，避免过深搜索
- **去重**: 自动去除重复的文件路径
- **优先级**: 按距离组件路径的远近排序

## 总结

### ✅ 已实现

- ✅ 在相似路径中查找 CSS 文件
- ✅ 根据组件名称查找
- ✅ 路径结构推断
- ✅ 多种搜索策略
- ✅ Agent 工具支持

### 🎯 覆盖范围

现在可以找到 CSS 文件，无论它们位于：
- ✅ 组件目录下
- ✅ 组件子目录（styles, clientlibs）
- ✅ 同级 styles 目录
- ✅ 父级 styles 目录
- ✅ 路径相似的任何位置

### 📊 效果

**之前**: 只能找到组件目录下的 CSS
**现在**: 可以找到所有路径相似的 CSS 文件

这大大提高了 CSS 查找的准确性和完整性！🎉
