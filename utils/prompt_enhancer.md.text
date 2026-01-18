"""
Prompt 增强工具
用于增强和优化 Agent prompts，提高生成质量
"""
from typing import Dict, List, Any


def enhance_code_generation_prompt(base_prompt: str, context: Dict[str, Any]) -> str:
    """
    增强代码生成 prompt，添加质量控制要点
    
    Args:
        base_prompt: 基础 prompt
        context: 上下文信息
    
    Returns:
        增强后的 prompt
    """
    quality_checks = """
=== QUALITY ASSURANCE REQUIREMENTS ===

Before finalizing the code, ensure:

1. CODE COMPLETENESS:
   ✓ Component is fully functional (all imports included)
   ✓ All props are defined and typed
   ✓ All logic from AEM component is implemented
   ✓ All BDL components are properly imported and used

2. CODE CORRECTNESS:
   ✓ No syntax errors
   ✓ No missing imports
   ✓ JSX syntax is valid (proper closing tags, correct brace usage)
   ✓ Props are correctly passed to BDL components
   ✓ Event handlers are properly defined

3. CODE STRUCTURE:
   ✓ Proper component declaration (functional component)
   ✓ Props interface/PropTypes defined
   ✓ Hooks used correctly (useState, useEffect, etc.)
   ✓ Component returns JSX

4. BDL COMPLIANCE:
   ✓ BDL components imported from correct paths
   ✓ BDL component props match API
   ✓ BDL styling approach used correctly
   ✓ BDL composition patterns followed

5. REACT BEST PRACTICES:
   ✓ Functional component with hooks
   ✓ Proper state management
   ✓ Event handlers defined correctly
   ✓ Conditional rendering implemented correctly
   ✓ Lists use .map() with proper keys

OUTPUT REQUIREMENTS:
- Output COMPLETE, COMPILABLE code
- No placeholders or TODOs
- No explanations mixed with code
- Code should be production-ready
"""
    
    enhanced_prompt = f"""{base_prompt}

{quality_checks}

Remember: Output ONLY the complete React component code. The code must compile and run without errors."""
    
    return enhanced_prompt


def build_iteration_context(iteration: int, previous_review: Dict[str, Any] = None) -> str:
    """
    构建迭代上下文信息
    
    Args:
        iteration: 当前迭代次数
        previous_review: 前一次 review 结果
    
    Returns:
        迭代上下文字符串
    """
    if iteration == 0:
        return """
=== INITIAL GENERATION ===
This is the first code generation. Focus on:
- Complete, accurate conversion from AEM to React
- Proper BDL component usage
- Following all conversion requirements
- Production-ready code quality
"""
    else:
        context = f"""
=== ITERATION {iteration} - CORRECTION ===
This is correction iteration {iteration}. Previous reviews found issues.

Previous Review Summary:"""
        
        if previous_review:
            security = previous_review.get('security', {})
            build = previous_review.get('build', {})
            bdl = previous_review.get('bdl', {})
            
            context += f"""
- Security: {'PASSED' if security.get('passed') else 'FAILED'} ({len(security.get('issues', []))} issues)
- Build: {'PASSED' if build.get('passed') else 'FAILED'} ({len(build.get('errors', []))} errors, {len(build.get('warnings', []))} warnings)
- BDL: {'PASSED' if bdl.get('passed') else 'FAILED'} ({len(bdl.get('issues', []))} issues)
"""
        
        context += """
Focus on:
- Fixing ALL identified issues
- Not introducing new issues
- Maintaining original functionality
- Improving code quality

Ensure the corrected code addresses ALL previous review findings."""
        
        return context
