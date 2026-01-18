# 快速测试指南

## 测试组件

已准备两个完整的 AEM 组件用于测试：

### 1. Button Component (简单组件)
- **ResourceType**: `example/components/button`
- **特性**: 基础按钮，包含 HTL、Dialog、JS、Java、CSS

### 2. Card Component (复杂组件)
- **ResourceType**: `example/components/card`
- **特性**: 
  - 复杂卡片组件
  - 依赖 button 组件
  - 使用模板片段（data-sly-call）
  - i18n 国际化
  - ClientLibs 配置
  - 复杂的 Java Sling Model

---

## 测试方法

### 方法 1: 使用测试脚本（推荐）

```bash
# 测试所有组件
python test_workflow.py

# 测试特定组件
python test_workflow.py 1  # Button 组件
python test_workflow.py 2  # Card 组件
```

### 方法 2: 使用主程序

```bash
python main.py
```

然后输入：
- **resourceType**: `example/components/button` 或 `example/components/card`
- **AEM_REPO_PATH**: `test_data/aem_components`（相对于项目根目录）
- **BDL_LIBRARY_PATH**: `test_data/mui_library`（相对于项目根目录）
- **输出路径**: `./output`（默认）

---

## 测试检查清单

### Button 组件测试

- [ ] 文件收集：收集了所有 6 个文件
- [ ] HTL 分析：识别了 data-sly-use, data-sly-test, data-sly-attribute, data-sly-element
- [ ] Dialog 分析：提取了所有字段（text, href, element, icon, iconAlt）
- [ ] Java 分析：解析了 ButtonModel，提取了 @PostConstruct 方法
- [ ] CSS 查找：找到了 button.css
- [ ] 代码生成：生成了 React 组件
- [ ] TypeScript 接口：生成了正确的 Props 接口
- [ ] @PostConstruct 转换：转换为 useEffect

### Card 组件测试

- [ ] 文件收集：收集了所有文件（包括依赖组件 button）
- [ ] 依赖解析：识别了 button 组件依赖
- [ ] 模板片段：识别了 template.placeholder, template.styles, template.scripts
- [ ] i18n：提取了翻译键，找到了字典文件
- [ ] ClientLibs：解析了 ClientLibs 配置
- [ ] Java 分析：解析了 CardModel，提取了复杂的 @PostConstruct 逻辑
- [ ] 代码生成：生成了包含依赖组件的 React 组件
- [ ] i18n 集成：集成了 react-i18next
- [ ] 懒加载：转换了图片懒加载逻辑

---

## 预期输出

### Button 组件输出

**文件**: `output/button/Button.jsx` 或类似

**内容应包含**:
- TypeScript 接口定义
- Props: text, href, element, icon, iconAlt
- @PostConstruct 逻辑转换为 useEffect
- 事件处理
- BDL 组件使用

### Card 组件输出

**文件**: `output/card/Card.jsx` 或类似

**内容应包含**:
- TypeScript 接口定义（所有字段）
- Props: title, description, imagePath, tags, etc.
- 依赖 Button 组件的导入
- i18n 集成（useTranslation）
- 懒加载图片逻辑
- 模板片段处理
- 所有 CSS 类应用

---

## 验证要点

1. **文件完整性**: 确保所有文件都被收集
2. **分析准确性**: 检查分析结果是否准确
3. **依赖处理**: 验证依赖组件是否被正确分析
4. **代码质量**: 生成的代码应该是可编译的
5. **功能完整性**: 生成的组件应该包含所有原始功能

---

## 常见问题

### 1. 找不到组件路径

**问题**: `Component path not found`

**解决**: 确保 `AEM_REPO_PATH` 指向 `test_data/aem_components`

### 2. 找不到 BDL 库

**问题**: `BDL library path not found`

**解决**: 这是警告，不影响测试。如果需要 BDL 组件选择，确保路径正确。

### 3. Java 文件解析失败

**问题**: Java 分析器无法解析文件

**解决**: 检查 Java 文件格式是否正确，包名是否正确。

### 4. 依赖组件未找到

**问题**: 依赖组件 button 未找到

**解决**: 确保 button 组件在 `example-button` 目录下。

---

## 调试技巧

1. **查看日志**: 工作流会输出详细的日志信息
2. **检查中间状态**: 查看 `file_analyses` 和 `dependency_analyses`
3. **验证文件路径**: 确保所有路径都是正确的
4. **检查分析结果**: 查看每个文件的分析结果

---

## 下一步

测试成功后，可以：
1. 检查生成的 React 组件代码
2. 验证功能是否完整
3. 测试编译和运行
4. 根据需要进行调整
