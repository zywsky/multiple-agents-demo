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
