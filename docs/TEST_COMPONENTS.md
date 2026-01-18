# AEM 测试组件说明

## 测试组件列表

### 1. example-button (基础组件)

**路径**: `test_data/aem_components/example-button/`

**文件**:
- `button.html` - HTL 模板
- `_cq_dialog/.content.xml` - Dialog 配置
- `button.js` - JavaScript
- `button.css` - CSS 样式
- `ButtonModel.java` - Sling Model
- `.content.xml` - 组件定义

**特性**:
- 简单的按钮组件
- 支持文本和图标
- 支持链接和按钮两种模式
- @PostConstruct 数据转换

**ResourceType**: `example/components/button`

---

### 2. example-card (复杂组件，依赖 button)

**路径**: `test_data/aem_components/example-card/`

**文件**:
- `card.html` - HTL 模板（包含 data-sly-resource 依赖）
- `_cq_dialog/.content.xml` - Dialog 配置（多字段、multifield）
- `card.js` - JavaScript（事件处理、懒加载）
- `card.css` - CSS 样式
- `CardModel.java` - Sling Model（复杂逻辑、@PostConstruct）
- `.content.xml` - 组件定义
- `i18n/en.properties` - i18n 字典文件
- `clientlibs/.content.xml` - ClientLibs 配置
- `clientlibs/css/card.css` - ClientLibs CSS
- `clientlibs/js/card.js` - ClientLibs JS

**特性**:
- 复杂的卡片组件
- 依赖 button 组件（data-sly-resource）
- 使用模板片段（data-sly-call）
- i18n 国际化支持
- ClientLibs 配置
- 多字段 Dialog（包括 multifield）
- 复杂的 @PostConstruct 逻辑
- 懒加载图片
- 响应式设计

**ResourceType**: `example/components/card`

**依赖**:
- `example/components/button`

---

## 测试工作流

### 测试 1: 简单组件（button）

```bash
python main.py
# 输入 resourceType: example/components/button
# 输入 AEM_REPO_PATH: test_data/aem_components
# 输入 BDL_LIBRARY_PATH: test_data/mui_library
```

**预期结果**:
- ✅ 收集所有文件
- ✅ 分析 HTL、Dialog、JS、Java
- ✅ 生成 TypeScript 接口
- ✅ 转换 @PostConstruct 方法
- ✅ 生成 React 组件

---

### 测试 2: 复杂组件（card）

```bash
python main.py
# 输入 resourceType: example/components/card
# 输入 AEM_REPO_PATH: test_data/aem_components
# 输入 BDL_LIBRARY_PATH: test_data/mui_library
```

**预期结果**:
- ✅ 收集所有文件（包括依赖组件 button）
- ✅ 递归分析依赖组件
- ✅ 分析模板片段（data-sly-call）
- ✅ 分析 i18n（提取翻译键和字典文件）
- ✅ 分析 ClientLibs 配置
- ✅ 生成完整的 React 组件（包括依赖组件）
- ✅ 集成 i18n（react-i18next）
- ✅ 转换服务端逻辑（如果有）

---

## 组件特性覆盖

### ✅ HTL 特性
- [x] data-sly-use
- [x] data-sly-test
- [x] data-sly-repeat / data-sly-list
- [x] data-sly-resource（组件依赖）
- [x] data-sly-call（模板片段）
- [x] data-sly-attribute
- [x] data-sly-element
- [x] @i18n

### ✅ Dialog 特性
- [x] textfield
- [x] textarea
- [x] pathfield
- [x] checkbox
- [x] multifield
- [x] tabs
- [x] required fields
- [x] default values

### ✅ JavaScript 特性
- [x] 事件处理
- [x] DOM 操作
- [x] 懒加载（IntersectionObserver）
- [x] 动画效果

### ✅ Java Sling Model 特性
- [x] @Model 注解
- [x] @ValueMapValue
- [x] @PostConstruct
- [x] 数据转换逻辑
- [x] 默认值处理
- [x] 列表处理

### ✅ CSS 特性
- [x] 组件本地 CSS
- [x] ClientLibs 配置
- [x] 响应式设计
- [x] 伪类（:hover, :active）

### ✅ i18n 特性
- [x] 翻译键提取
- [x] 字典文件解析
- [x] @i18n 使用

### ✅ 依赖处理
- [x] data-sly-resource 依赖
- [x] 递归依赖解析
- [x] 依赖组件的 CSS

---

## 验证检查清单

### 文件收集
- [ ] 收集了所有 HTL 文件
- [ ] 收集了所有 Dialog 文件
- [ ] 收集了所有 JS 文件
- [ ] 收集了所有 Java 文件
- [ ] 收集了所有 CSS 文件
- [ ] 收集了依赖组件的文件
- [ ] 收集了 i18n 字典文件
- [ ] 收集了 ClientLibs 配置

### 分析
- [ ] HTL 分析完整
- [ ] Dialog 分析完整
- [ ] JS 分析完整
- [ ] Java 分析完整（包括服务依赖）
- [ ] CSS 查找完整（包括 ClientLibs）
- [ ] 模板片段分析完整
- [ ] i18n 分析完整
- [ ] 依赖组件分析完整

### 代码生成
- [ ] 生成了正确的 TypeScript 接口
- [ ] 转换了 @PostConstruct 方法
- [ ] 处理了模板片段
- [ ] 集成了 i18n
- [ ] 处理了依赖组件
- [ ] 应用了 CSS 样式
- [ ] 转换了事件处理

---

## 注意事项

1. **路径配置**: 确保 `AEM_REPO_PATH` 指向 `test_data/aem_components`
2. **依赖组件**: card 组件依赖 button 组件，确保两个组件都在同一目录下
3. **ClientLibs**: ClientLibs 配置在 `clientlibs/.content.xml`，CSS/JS 在子目录中
4. **i18n**: i18n 字典文件在 `i18n/en.properties`
5. **Java 包**: Java 文件需要正确的包结构（`com.example.components.models`）

---

## 预期输出

### Button 组件输出
- React 组件文件
- TypeScript 接口
- Props 定义（text, href, element, icon, iconAlt）
- @PostConstruct 逻辑转换为 useEffect

### Card 组件输出
- React 组件文件
- TypeScript 接口（包含所有字段）
- 依赖 Button 组件的导入
- i18n 集成（useTranslation hook）
- 懒加载图片逻辑（useEffect + IntersectionObserver）
- 模板片段处理（移除或转换）
- 所有 CSS 类应用
