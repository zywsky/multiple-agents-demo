# AEM to React Component Converter - 工作流可视化

## 🔄 完整工作流程图 (Mermaid)

```mermaid
graph TD
    Start([开始<br/>输入: resourceType, AEM_REPO_PATH, BDL_LIBRARY_PATH]) --> CollectFiles[1. collect_files<br/>收集文件<br/>- 当前组件文件<br/>- 构建依赖树<br/>- 递归收集依赖组件]
    
    CollectFiles --> AnalyzeFiles[2. analyze_aem_files<br/>分析 AEM 文件<br/>- 分析当前组件<br/>- 递归分析依赖组件<br/>- 提取关键信息]
    
    AnalyzeFiles --> SelectBDL[3. select_bdl_components<br/>选择 BDL 组件<br/>- 分析 AEM 功能<br/>- 搜索 BDL 匹配<br/>- 验证相关性]
    
    SelectBDL --> WriteCode[4. write_code<br/>编写代码<br/>- 生成 React 组件<br/>- 使用 AEM 分析<br/>- 使用 BDL 组件]
    
    WriteCode --> ReviewCode[5. review_code<br/>审查代码<br/>- Security Review<br/>- Build Review<br/>- BDL Review]
    
    ReviewCode --> ShouldContinue{should_continue<br/>判断是否继续}
    
    ShouldContinue -->|通过| End([结束<br/>✓ 所有审查通过])
    ShouldContinue -->|未通过且未达上限| CorrectCode[6. correct_code<br/>修正代码<br/>- 修正所有问题<br/>- 按优先级处理<br/>- 更新代码]
    
    CorrectCode --> ReviewCode
    
    ShouldContinue -->|达到最大迭代| EndMax([结束<br/>⚠ 达到最大迭代次数])
    
    style Start fill:#e1f5ff
    style End fill:#c8e6c9
    style EndMax fill:#ffccbc
    style CollectFiles fill:#fff9c4
    style AnalyzeFiles fill:#fff9c4
    style SelectBDL fill:#fff9c4
    style WriteCode fill:#fff9c4
    style ReviewCode fill:#e1bee7
    style CorrectCode fill:#ffccbc
    style ShouldContinue fill:#b3e5fc
```

## 📊 数据流图

```mermaid
graph LR
    Input[输入<br/>resourceType<br/>Paths] --> Collect[文件收集]
    
    Collect --> Files[files[]<br/>dependency_tree{}]
    
    Files --> Analyze[文件分析]
    
    Analyze --> Analyses[file_analyses[]<br/>dependency_analyses{}]
    
    Analyses --> Select[BDL 选择]
    
    Select --> BDL[selected_bdl_components[]]
    
    BDL --> Generate[代码生成]
    
    Generate --> Code[generated_code<br/>code_file_path]
    
    Code --> Review[代码审查]
    
    Review --> Results[review_results{}<br/>review_passed]
    
    Results -->|通过| Output[输出<br/>React 组件]
    Results -->|未通过| Correct[代码修正]
    
    Correct --> Generate
    
    style Input fill:#e1f5ff
    style Output fill:#c8e6c9
    style Collect fill:#fff9c4
    style Analyze fill:#fff9c4
    style Select fill:#fff9c4
    style Generate fill:#fff9c4
    style Review fill:#e1bee7
    style Correct fill:#ffccbc
```

## 🏗️ 依赖处理流程图

```mermaid
graph TD
    Start([开始分析组件]) --> ReadHTL[读取 HTL 文件]
    
    ReadHTL --> ExtractDeps[提取 data-sly-resource]
    
    ExtractDeps --> HasDeps{有依赖?}
    
    HasDeps -->|否| End([结束])
    
    HasDeps -->|是| ResolvePath[解析 resourceType 路径]
    
    ResolvePath --> PathExists{路径存在?}
    
    PathExists -->|否| Skip[跳过该依赖]
    
    PathExists -->|是| CheckVisited{已访问?}
    
    CheckVisited -->|是| SkipCircular[跳过循环依赖]
    
    CheckVisited -->|否| CheckDepth{深度 < 5?}
    
    CheckDepth -->|否| SkipDepth[跳过过深依赖]
    
    CheckDepth -->|是| CollectDepFiles[收集依赖组件文件]
    
    CollectDepFiles --> AnalyzeDep[分析依赖组件]
    
    AnalyzeDep --> Recursive[递归处理依赖的依赖]
    
    Recursive --> HasDeps
    
    Skip --> HasDeps
    SkipCircular --> HasDeps
    SkipDepth --> HasDeps
    
    style Start fill:#e1f5ff
    style End fill:#c8e6c9
    style ExtractDeps fill:#fff9c4
    style AnalyzeDep fill:#fff9c4
    style Skip fill:#ffccbc
    style SkipCircular fill:#ffccbc
    style SkipDepth fill:#ffccbc
```

## 🔍 审查循环流程图

```mermaid
graph TD
    Start([代码生成完成]) --> Security[Security Review<br/>安全检查]
    
    Security --> Build[Build Review<br/>构建检查]
    
    Build --> BDL[BDL Review<br/>BDL 合规检查]
    
    BDL --> Aggregate[汇总审查结果]
    
    Aggregate --> AllPassed{所有审查通过?}
    
    AllPassed -->|是| Success([✓ 成功<br/>输出代码])
    
    AllPassed -->|否| CheckIteration{迭代次数 < 最大?}
    
    CheckIteration -->|否| MaxReached([⚠ 达到最大迭代<br/>输出当前代码])
    
    CheckIteration -->|是| Prioritize[按优先级组织问题<br/>Critical > High > Medium > Low]
    
    Prioritize --> Correct[修正代码]
    
    Correct --> WriteFile[写入文件]
    
    WriteFile --> Increment[迭代计数 +1]
    
    Increment --> Start
    
    style Start fill:#e1f5ff
    style Success fill:#c8e6c9
    style MaxReached fill:#ffccbc
    style Security fill:#e1bee7
    style Build fill:#e1bee7
    style BDL fill:#e1bee7
    style Correct fill:#ffccbc
```

## 🎯 Agent 交互图

```mermaid
graph TD
    Workflow[Workflow Graph] --> AEMAgent[AEMAnalysisAgent<br/>分析 AEM 文件]
    
    Workflow --> BDLAgent[BDLSelectionAgent<br/>选择 BDL 组件]
    
    Workflow --> CodeAgent[CodeWritingAgent<br/>生成 React 代码]
    
    Workflow --> SecurityAgent[SecurityReviewAgent<br/>安全检查]
    
    Workflow --> BuildAgent[BuildReviewAgent<br/>构建检查]
    
    Workflow --> BDLAgent2[BDLReviewAgent<br/>BDL 合规检查]
    
    Workflow --> CorrectAgent[CorrectAgent<br/>修正代码]
    
    AEMAgent --> Tools[Tools<br/>read_file<br/>list_files]
    
    BDLAgent --> Tools
    
    CodeAgent --> Tools
    
    SecurityAgent --> Tools
    
    BuildAgent --> Tools
    
    BDLAgent2 --> Tools
    
    CorrectAgent --> Tools
    
    style Workflow fill:#e1f5ff
    style AEMAgent fill:#fff9c4
    style BDLAgent fill:#fff9c4
    style CodeAgent fill:#fff9c4
    style SecurityAgent fill:#e1bee7
    style BuildAgent fill:#e1bee7
    style BDLAgent2 fill:#e1bee7
    style CorrectAgent fill:#ffccbc
    style Tools fill:#c8e6c9
```

## 📦 状态流转图

```mermaid
stateDiagram-v2
    [*] --> 文件收集: 输入 resourceType
    
    文件收集 --> 文件分析: files[], dependency_tree{}
    
    文件分析 --> BDL选择: file_analyses[], dependency_analyses{}
    
    BDL选择 --> 代码生成: selected_bdl_components[]
    
    代码生成 --> 代码审查: generated_code, code_file_path
    
    代码审查 --> 判断: review_results{}, review_passed
    
    判断 --> [*]: 通过
    判断 --> 代码修正: 未通过且未达上限
    判断 --> [*]: 达到最大迭代
    
    代码修正 --> 代码审查: generated_code (更新), iteration_count++
    
    note right of 文件收集
        递归收集依赖组件
    end note
    
    note right of 文件分析
        分析当前组件和依赖组件
    end note
    
    note right of 代码审查
        三个维度审查:
        Security, Build, BDL
    end note
```

## 🔄 迭代优化循环

```mermaid
sequenceDiagram
    participant W as Workflow
    participant C as CodeWritingAgent
    participant S as SecurityReviewAgent
    participant B as BuildReviewAgent
    participant D as BDLReviewAgent
    participant Cor as CorrectAgent
    
    W->>C: 生成代码
    C-->>W: generated_code
    
    W->>S: 安全检查
    S-->>W: security_results
    
    W->>B: 构建检查
    B-->>W: build_results
    
    W->>D: BDL 检查
    D-->>W: bdl_results
    
    W->>W: 汇总结果
    
    alt 未通过
        W->>Cor: 修正代码 (包含所有问题)
        Cor-->>W: corrected_code
        W->>W: iteration_count++
        W->>S: 再次审查
    else 通过
        W->>W: 结束流程
    end
```

---

## 📝 关键节点说明

### 1. 文件收集 (collect_files)
- **输入**: component_path, resource_type, aem_repo_path
- **处理**: 
  - 收集当前组件文件
  - 提取依赖关系
  - 递归收集依赖组件文件
- **输出**: files[], dependency_tree{}

### 2. 文件分析 (analyze_aem_files)
- **输入**: files[], dependency_tree{}
- **处理**:
  - 分析 HTL 模板（UI 结构）
  - 分析 Dialog XML（Props 定义）
  - 分析 JavaScript（交互逻辑）
  - 递归分析依赖组件
- **输出**: file_analyses[], dependency_analyses{}

### 3. BDL 选择 (select_bdl_components)
- **输入**: file_analyses[], bdl_library_path
- **处理**:
  - 构建 AEM 组件摘要
  - 搜索匹配的 BDL 组件
  - 验证相关性
  - 重新搜索（如需要）
- **输出**: selected_bdl_components[], aem_component_summary{}

### 4. 代码生成 (write_code)
- **输入**: file_analyses[], dependency_analyses{}, selected_bdl_components[]
- **处理**:
  - 构建转换要求
  - 生成 React 代码
  - 基本验证
- **输出**: generated_code, code_file_path

### 5. 代码审查 (review_code)
- **输入**: generated_code, code_file_path
- **处理**:
  - Security Review
  - Build Review
  - BDL Review
- **输出**: review_results{}, review_passed

### 6. 代码修正 (correct_code)
- **输入**: generated_code, review_results{}, iteration_count
- **处理**:
  - 按优先级修正问题
  - 更新代码
- **输出**: generated_code (更新), iteration_count++

---

## 🎯 总结

整个工作流是一个**自动化的、迭代优化的**转换系统：

1. **收集阶段**: 递归收集所有相关文件
2. **分析阶段**: 深入分析 AEM 组件和依赖
3. **选择阶段**: 智能匹配 BDL 组件
4. **生成阶段**: 生成 React 代码
5. **审查阶段**: 多维度质量检查
6. **优化阶段**: 迭代修正直到通过

整个过程**自动化**、**智能化**、**可迭代**，确保生成高质量的 React 组件！🎉
