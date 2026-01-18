"""
结构化输出模式定义
使用 Pydantic 确保 Agent 返回结构化数据
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class FileAnalysisResult(BaseModel):
    """文件分析结果"""
    file_path: str = Field(description="文件路径")
    file_type: str = Field(description="文件类型（HTL, Dialog, Script, CSS等）")
    purpose: str = Field(description="文件用途和功能")
    dependencies: List[str] = Field(default_factory=list, description="依赖的组件、服务、资源")
    key_features: List[str] = Field(default_factory=list, description="关键特性")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="配置信息")
    special_considerations: Optional[str] = Field(None, description="特殊注意事项")
    analysis: str = Field(description="完整分析文本")


class BDLComponentSelection(BaseModel):
    """BDL 组件选择结果"""
    selected_components: List[str] = Field(description="选定的 BDL 组件文件路径列表")
    reasoning: Dict[str, str] = Field(description="每个组件选择的理由，key为组件路径")
    additional_components: List[str] = Field(default_factory=list, description="额外需要的组件")
    component_mapping: Dict[str, str] = Field(
        default_factory=dict,
        description="AEM 功能到 BDL 组件的映射"
    )


class CodeGenerationResult(BaseModel):
    """代码生成结果"""
    component_code: str = Field(description="生成的 React 组件代码")
    css_code: Optional[str] = Field(None, description="生成的 CSS Module 代码（.module.css 或 .module.scss）")
    imports: List[str] = Field(default_factory=list, description="需要的导入语句")
    dependencies: List[str] = Field(default_factory=list, description="package.json 依赖")
    component_name: str = Field(description="组件名称")
    props_interface: Optional[str] = Field(None, description="Props 接口定义（TypeScript）")
    notes: Optional[str] = Field(None, description="生成说明和注意事项")


class ReviewResult(BaseModel):
    """审查结果"""
    passed: bool = Field(description="是否通过")
    issues: List[str] = Field(default_factory=list, description="发现的问题列表")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")
    severity: str = Field(default="medium", description="问题严重程度：critical, high, medium, low")
    details: str = Field(description="详细审查结果文本")


class SecurityReviewResult(ReviewResult):
    """安全审查结果"""
    vulnerabilities: List[str] = Field(default_factory=list, description="发现的安全漏洞")
    risk_level: str = Field(default="low", description="风险级别")


class BuildReviewResult(ReviewResult):
    """构建审查结果"""
    build_status: str = Field(description="构建状态：success, failed, warnings")
    errors: List[str] = Field(default_factory=list, description="构建错误")
    warnings: List[str] = Field(default_factory=list, description="构建警告")
    build_output: Optional[str] = Field(None, description="构建输出")


class BDLReviewResult(ReviewResult):
    """BDL 规范审查结果"""
    compliance_issues: List[str] = Field(default_factory=list, description="规范违反问题")
    best_practice_violations: List[str] = Field(default_factory=list, description="最佳实践违反")
    api_usage_issues: List[str] = Field(default_factory=list, description="API 使用问题")


class BuildExecutionReviewResult(ReviewResult):
    """构建执行审查结果"""
    build_status: str = Field(description="构建状态：success, failed, warnings, not_executed")
    errors: List[str] = Field(default_factory=list, description="构建错误列表")
    warnings: List[str] = Field(default_factory=list, description="构建警告列表")
    build_output: Optional[str] = Field(None, description="构建输出文本")
    exit_code: Optional[int] = Field(None, description="构建命令退出码")


class BDLComponentUsageReviewResult(ReviewResult):
    """BDL组件使用审查结果"""
    invalid_props: List[str] = Field(default_factory=list, description="使用了不存在的属性")
    missing_required_props: List[str] = Field(default_factory=list, description="缺少必需属性")
    incorrect_prop_types: List[str] = Field(default_factory=list, description="属性类型错误")
    bdl_component_usage: Dict[str, Any] = Field(default_factory=dict, description="BDL组件使用详情")


class CSSImportReviewResult(ReviewResult):
    """CSS导入审查结果"""
    css_file_exists: bool = Field(description="CSS文件是否存在")
    css_imported: bool = Field(description="CSS是否被导入")
    css_import_path: Optional[str] = Field(None, description="CSS导入路径")
    css_modules_used: bool = Field(description="是否使用CSS Modules")
    missing_css_classes: List[str] = Field(default_factory=list, description="使用了但未定义的CSS类")
    unused_css_classes: List[str] = Field(default_factory=list, description="定义了但未使用的CSS类")


class ComponentReferenceReviewResult(ReviewResult):
    """组件引用审查结果"""
    should_use_existing: List[str] = Field(default_factory=list, description="应该使用但未使用的已生成组件")
    incorrect_imports: List[str] = Field(default_factory=list, description="错误的import路径")
    missing_imports: List[str] = Field(default_factory=list, description="缺失的import")
    incorrect_props: List[str] = Field(default_factory=list, description="错误的props传递")


class ComponentCompletenessReviewResult(ReviewResult):
    """组件完整性审查结果"""
    missing_htl_elements: List[str] = Field(default_factory=list, description="缺失的HTL元素")
    missing_dialog_fields: List[str] = Field(default_factory=list, description="缺失的Dialog字段")
    missing_java_fields: List[str] = Field(default_factory=list, description="缺失的Java字段")
    missing_template_calls: List[str] = Field(default_factory=list, description="缺失的模板调用")
    completeness_score: float = Field(description="完整性得分（0-1）")


class PropsConsistencyReviewResult(ReviewResult):
    """Props一致性审查结果"""
    inconsistent_field_types: List[str] = Field(default_factory=list, description="字段类型不一致")
    inconsistent_required_fields: List[str] = Field(default_factory=list, description="必填字段不一致")
    inconsistent_default_values: List[str] = Field(default_factory=list, description="默认值不一致")
    inconsistent_field_names: List[str] = Field(default_factory=list, description="字段名称不一致")
    consistency_score: float = Field(description="一致性得分（0-1）")


class StyleConsistencyReviewResult(ReviewResult):
    """样式一致性审查结果"""
    missing_css_classes: List[str] = Field(default_factory=list, description="缺失的CSS类")
    inconsistent_css_rules: List[str] = Field(default_factory=list, description="不一致的CSS规则")
    missing_responsive_styles: List[str] = Field(default_factory=list, description="缺失的响应式样式")
    style_consistency_score: float = Field(description="样式一致性得分（0-1）")


class FunctionalityConsistencyReviewResult(ReviewResult):
    """功能一致性审查结果"""
    missing_event_handlers: List[str] = Field(default_factory=list, description="缺失的事件处理")
    missing_interactions: List[str] = Field(default_factory=list, description="缺失的交互")
    missing_initialization: List[str] = Field(default_factory=list, description="缺失的初始化逻辑")
    functionality_consistency_score: float = Field(description="功能一致性得分（0-1）")
