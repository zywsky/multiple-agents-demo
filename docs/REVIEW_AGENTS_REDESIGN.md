# Review Agents 重新设计

## 当前状态分析

### 现有的Review Agents

1. **SecurityReviewAgent** ✅
   - 检查安全漏洞
   - 功能完整

2. **BuildReviewAgent** ⚠️
   - 检查构建错误
   - 已有`run_build_command`工具
   - **需要增强**：更专注于实际执行npm run build

3. **BDLReviewAgent** ⚠️
   - 检查BDL规范
   - **需要增强**：更专注于BDL组件属性使用检查

### 缺失的Review Agents

4. **CSSImportReviewAgent** ❌
   - 检查CSS导入是否正确

5. **ComponentReferenceReviewAgent** ❌
   - 检查是否正确引用了已生成的依赖组件

6. **ComponentCompletenessReviewAgent** ❌
   - 检查组件各部分完整性

7. **PropsConsistencyReviewAgent** ❌
   - 检查可配置项参数一致性（AEM Dialog vs React Props）

8. **StyleConsistencyReviewAgent** ❌
   - 检查样式一致性（AEM CSS vs React CSS）

9. **FunctionalityConsistencyReviewAgent** ❌
   - 检查JS功能一致性（AEM JS vs React逻辑）

## 重新设计方案

### 方案：职责明确的细粒度Agents

**原则**：每个Agent专注于一个特定的检查维度，职责单一，易于维护和扩展。

### 新的Review Agents结构

#### 1. SecurityReviewAgent ✅ (保留)
- **职责**：安全检查
- **检查项**：XSS、注入攻击、敏感数据暴露等
- **状态**：已实现，无需修改

#### 2. BuildExecutionReviewAgent (从BuildReviewAgent拆分)
- **职责**：执行npm run build并检查结果
- **检查项**：
  - 执行`npm run build`命令
  - 解析构建输出
  - 识别构建错误和警告
  - 检查编译是否成功
- **工具**：`run_build_command`
- **输出**：构建状态、错误列表、警告列表

#### 3. SyntaxQualityReviewAgent (从BuildReviewAgent拆分)
- **职责**：代码语法和质量检查（不执行build）
- **检查项**：
  - 语法错误
  - 类型错误
  - Import错误
  - 代码质量问题
- **工具**：静态分析工具
- **输出**：语法问题、代码质量问题

#### 4. BDLComponentUsageReviewAgent (增强BDLReviewAgent)
- **职责**：检查BDL组件属性使用是否正确
- **检查项**：
  - 读取BDL组件源码
  - 提取BDL组件的可用属性
  - 检查生成的组件是否使用了不存在的属性
  - 检查属性值类型是否正确
  - 检查必需属性是否提供
- **工具**：`read_code_file`, `search_text_in_files`
- **输出**：属性使用错误、API使用问题

#### 5. CSSImportReviewAgent (新增)
- **职责**：检查CSS导入和使用
- **检查项**：
  - CSS文件是否存在
  - CSS是否正确导入（import语句）
  - CSS Modules使用是否正确
  - className使用是否正确
  - CSS类名是否在CSS文件中定义
- **工具**：`read_code_file`, `check_file_exists_tool`
- **输出**：CSS导入问题、CSS使用问题

#### 6. ComponentReferenceReviewAgent (新增)
- **职责**：检查依赖组件引用
- **检查项**：
  - 检查是否应该引用已生成的组件
  - 检查import路径是否正确
  - 检查组件使用是否正确
  - 检查props传递是否正确
- **工具**：`read_code_file`, `check_file_exists_tool`, 组件注册表
- **输出**：引用问题、import问题

#### 7. ComponentCompletenessReviewAgent (新增)
- **职责**：检查组件完整性
- **检查项**：
  - 检查AEM组件的所有部分是否都在React组件中实现
  - HTL结构 → JSX结构
  - Dialog字段 → React Props
  - Java字段 → React Props
  - 模板片段 → React组件/函数
- **工具**：需要访问AEM分析结果
- **输出**：缺失的部分、不完整的实现

#### 8. PropsConsistencyReviewAgent (新增)
- **职责**：检查Props一致性
- **检查项**：
  - AEM Dialog字段 vs React Props
  - 字段类型是否一致
  - 必填字段是否一致
  - 默认值是否一致
  - 字段名称是否一致
- **工具**：需要访问AEM Dialog分析结果
- **输出**：Props不一致问题

#### 9. StyleConsistencyReviewAgent (新增)
- **职责**：检查样式一致性
- **检查项**：
  - AEM CSS类 vs React CSS类
  - CSS规则是否一致
  - 样式效果是否一致
  - 响应式样式是否一致
- **工具**：需要访问AEM CSS分析结果
- **输出**：样式不一致问题

#### 10. FunctionalityConsistencyReviewAgent (新增)
- **职责**：检查功能一致性
- **检查项**：
  - AEM JS逻辑 vs React逻辑
  - 事件处理是否一致
  - 交互行为是否一致
  - 初始化逻辑是否一致
- **工具**：需要访问AEM JS分析结果
- **输出**：功能不一致问题

## 实施建议

### 阶段1：核心功能（必须实现）

1. **BuildExecutionReviewAgent** - 执行build检查
2. **BDLComponentUsageReviewAgent** - BDL属性检查
3. **CSSImportReviewAgent** - CSS导入检查
4. **ComponentReferenceReviewAgent** - 组件引用检查

### 阶段2：一致性检查（重要）

5. **ComponentCompletenessReviewAgent** - 完整性检查
6. **PropsConsistencyReviewAgent** - Props一致性
7. **StyleConsistencyReviewAgent** - 样式一致性
8. **FunctionalityConsistencyReviewAgent** - 功能一致性

### 阶段3：优化（可选）

9. **SyntaxQualityReviewAgent** - 代码质量（如果BuildExecution不够）

## 优势

1. **职责明确**：每个Agent专注于一个检查维度
2. **易于维护**：修改一个Agent不影响其他
3. **易于扩展**：可以轻松添加新的检查Agent
4. **并行执行**：可以并行运行多个Agent提高效率
5. **结果清晰**：每个检查结果独立，便于定位问题

## 注意事项

1. **需要访问AEM分析结果**：一致性检查Agent需要访问原始AEM组件信息
2. **需要访问组件注册表**：ComponentReferenceReviewAgent需要访问组件注册表
3. **需要访问BDL组件源码**：BDLComponentUsageReviewAgent需要读取BDL组件源码
4. **性能考虑**：多个Agent可能增加执行时间，但可以并行执行
