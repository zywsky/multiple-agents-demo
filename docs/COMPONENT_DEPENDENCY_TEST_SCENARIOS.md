# 组件依赖测试场景

## 测试数据层次结构

本测试数据设计用于测试多层次的组件依赖关系，验证组件复用功能。

### 组件层次

```
Level 4: example-page (超大组件)
    ├── 直接依赖: example-container (大组件)
    ├── 直接依赖: example-card (中等组件)
    └── 直接依赖: example-button (小组件)

Level 3: example-container (大组件)
    ├── 直接依赖: example-card (中等组件)
    └── 直接依赖: example-button (小组件)

Level 2: example-card (中等组件)
    └── 直接依赖: example-button (小组件)

Level 1: example-button (小组件)
    └── 无依赖（最底层）
```

## 测试场景

### 场景1: 顺序生成（推荐）

**目的**: 测试当按依赖顺序生成组件时，组件复用功能是否正常工作。

**步骤**:
1. 生成 `example-button` (Level 1)
   - 无依赖，使用BDL组件生成
   - 注册到组件注册表

2. 生成 `example-card` (Level 2)
   - 依赖 `example-button`
   - 检测到 `example-button` 已生成
   - 使用已生成的 `Button` 组件
   - 注册到组件注册表

3. 生成 `example-container` (Level 3)
   - 依赖 `example-card` 和 `example-button`
   - 检测到两者都已生成
   - 使用已生成的 `Card` 和 `Button` 组件
   - 注册到组件注册表

4. 生成 `example-page` (Level 4)
   - 依赖 `example-container`、`example-card`、`example-button`
   - 检测到三者都已生成
   - 使用已生成的 `Container`、`Card`、`Button` 组件
   - 注册到组件注册表

**预期结果**:
- 每个组件都正确检测到已生成的依赖组件
- 每个组件都使用已生成的组件而不是BDL组件
- 组件注册表正确记录所有组件

### 场景2: 逆序生成

**目的**: 测试当按逆依赖顺序生成组件时，系统如何处理。

**步骤**:
1. 生成 `example-page` (Level 4)
   - 依赖 `example-container`、`example-card`、`example-button`
   - 检测到依赖组件未生成
   - 使用BDL组件生成
   - 注册到组件注册表

2. 生成 `example-container` (Level 3)
   - 依赖 `example-card`、`example-button`
   - 检测到依赖组件未生成
   - 使用BDL组件生成
   - 注册到组件注册表

3. 生成 `example-card` (Level 2)
   - 依赖 `example-button`
   - 检测到依赖组件未生成
   - 使用BDL组件生成
   - 注册到组件注册表

4. 生成 `example-button` (Level 1)
   - 无依赖
   - 使用BDL组件生成
   - 注册到组件注册表

**预期结果**:
- 每个组件在生成时，依赖组件都未生成
- 每个组件都使用BDL组件
- 组件注册表正确记录所有组件
- 后续可以重新生成依赖组件，但不会影响已生成的组件

### 场景3: 混合顺序生成

**目的**: 测试当按混合顺序生成组件时，组件复用功能是否正常工作。

**步骤**:
1. 生成 `example-button` (Level 1)
   - 注册到组件注册表

2. 生成 `example-container` (Level 3)
   - 依赖 `example-card`、`example-button`
   - 检测到 `example-button` 已生成，`example-card` 未生成
   - 使用已生成的 `Button` 组件和BDL组件生成 `Card`
   - 注册到组件注册表

3. 生成 `example-card` (Level 2)
   - 依赖 `example-button`
   - 检测到 `example-button` 已生成
   - 使用已生成的 `Button` 组件
   - 注册到组件注册表

4. 生成 `example-page` (Level 4)
   - 依赖 `example-container`、`example-card`、`example-button`
   - 检测到三者都已生成
   - 使用已生成的所有组件
   - 注册到组件注册表

**预期结果**:
- 部分依赖已生成时，正确使用已生成的组件
- 部分依赖未生成时，使用BDL组件
- 组件注册表正确记录所有组件

## 组件详细信息

### Level 1: example-button (小组件)

**Resource Type**: `example/components/button`

**依赖**: 无

**文件**:
- `button.html` - HTL模板
- `ButtonModel.java` - Java Sling Model
- `button.css` - 样式文件
- `button.js` - JavaScript文件
- `_cq_dialog/.content.xml` - Dialog配置

**功能**: 基础按钮组件，支持文本、图标、链接等功能

### Level 2: example-card (中等组件)

**Resource Type**: `example/components/card`

**依赖**: 
- `example/components/button` (在footer中使用)

**文件**:
- `card.html` - HTL模板（第31行使用data-sly-resource引用button）
- `CardModel.java` - Java Sling Model
- `card.css` - 样式文件
- `card.js` - JavaScript文件
- `_cq_dialog/.content.xml` - Dialog配置

**功能**: 卡片组件，包含标题、描述、图片、标签、按钮等

### Level 3: example-container (大组件)

**Resource Type**: `example/components/container`

**依赖**:
- `example/components/button` (在actions中使用)
- `example/components/card` (在content中使用)

**文件**:
- `container.html` - HTL模板（第10行和第15行使用data-sly-resource）
- `ContainerModel.java` - Java Sling Model
- `container.css` - 样式文件
- `_cq_dialog/.content.xml` - Dialog配置

**功能**: 容器组件，包含header、actions、content、footer等部分

### Level 4: example-page (超大组件)

**Resource Type**: `example/components/page`

**依赖**:
- `example/components/container` (在main中使用)
- `example/components/card` (在sidebar中使用)
- `example/components/button` (在navigation和footer中使用)

**文件**:
- `page.html` - HTL模板（多处使用data-sly-resource）
- `PageModel.java` - Java Sling Model
- `page.css` - 样式文件
- `page.js` - JavaScript文件
- `_cq_dialog/.content.xml` - Dialog配置

**功能**: 页面组件，包含header、navigation、main、sidebar、footer等完整页面结构

## 验证点

### 组件复用验证

1. **检测已生成组件**
   - 组件注册表是否正确查询
   - 是否检测到已生成的依赖组件

2. **使用已生成组件**
   - Prompt中是否提供已生成组件信息
   - 生成的代码是否使用已生成的组件
   - Import路径是否正确

3. **组件注册**
   - 新生成的组件是否正确注册
   - 注册表路径是否正确

### Review Agents验证

1. **ComponentReferenceReviewAgent**
   - 是否正确检测到应该使用已生成的组件
   - 是否正确检测到import路径
   - 是否正确检测到组件使用

2. **ComponentCompletenessReviewAgent**
   - 是否正确检测到所有依赖组件
   - 完整性得分是否准确

## 使用说明

### 测试顺序生成场景

```bash
# 1. 生成button
python main.py --resource-type example/components/button --output-path output/button

# 2. 生成card
python main.py --resource-type example/components/card --output-path output/card

# 3. 生成container
python main.py --resource-type example/components/container --output-path output/container

# 4. 生成page
python main.py --resource-type example/components/page --output-path output/page
```

### 测试逆序生成场景

```bash
# 按逆序生成
python main.py --resource-type example/components/page --output-path output/page
python main.py --resource-type example/components/container --output-path output/container
python main.py --resource-type example/components/card --output-path output/card
python main.py --resource-type example/components/button --output-path output/button
```

## 总结

这个测试数据设计覆盖了：
- ✅ 单层依赖（card -> button）
- ✅ 多层依赖（container -> card -> button）
- ✅ 多依赖（container依赖card和button）
- ✅ 复杂依赖（page依赖container、card、button）
- ✅ 直接和间接依赖（page直接依赖button，也通过container间接依赖）

可以全面测试组件复用功能的正确性！
