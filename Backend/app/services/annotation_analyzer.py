"""
Student Annotation Analysis
Analyzes student annotations and determines appropriate responses
"""

from typing import Dict, List, Optional, Any
import json

class AnnotationAnalyzer:
    """Analyzes student annotations and determines appropriate responses"""
    
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
    
    async def analyze_annotations(self, 
                                 canvas_before: Optional[str], 
                                 canvas_after: str,
                                 context: Dict) -> Dict:
        """Compare canvas states to detect new annotations"""
        
        if not canvas_before:
            # First time - analyze the whole canvas
            prompt = f"""
Analyze this canvas and identify what the student has drawn/written:

Context: Student is working on {context.get('topic', 'math problem')}

Identify:
1. All marks/writing by the student
2. What these marks represent (problem setup, solution attempt, question, etc.)
3. Location of annotations
4. Suggested AI response type

Output JSON:
{{
    "annotations": [
        {{
            "location": {{"x": 0, "y": 0, "width": 100, "height": 50}},
            "type": "solution_attempt|question_mark|problem_setup|calculation",
            "content": "detected content",
            "confidence": 0.9
        }}
    ],
    "student_intent": "trying_to_solve|asking_for_help|showing_work|setting_up_problem",
    "suggested_response": "provide_hint|check_work|explain_concept|acknowledge_setup"
}}
"""
            result = await self.gemini_service.generate_simple_response(prompt, canvas_after)
        else:
            # Compare before and after
            prompt = f"""
Compare these two canvas states and identify what the student added:

Context: Student is working on {context.get('topic', 'math problem')}
Previous AI guidance: {context.get('last_ai_response', 'None')}

Identify:
1. New marks/writing by the student
2. What these marks represent (attempt at solution, question, correction, etc.)
3. Location of new annotations
4. Suggested AI response type

Output JSON:
{{
    "new_annotations": [
        {{
            "location": {{"x": 0, "y": 0, "width": 100, "height": 50}},
            "type": "solution_attempt|question_mark|correction|calculation",
            "content": "detected content",
            "confidence": 0.9
        }}
    ],
    "student_intent": "trying_to_solve|asking_for_help|showing_work|confused",
    "suggested_response": "provide_hint|check_work|explain_concept|encourage"
}}
"""
            result = await self.gemini_service.generate_comparison_response(
                prompt, canvas_before, canvas_after
            )
        
        return result
    
    async def analyze_student_attempt(self, content: str, problem_context: Dict) -> Dict:
        """Analyze if student's solution attempt is correct"""
        
        prompt = f"""
Analyze this student's work:
Student wrote: {content}
For problem: {problem_context.get('original_problem', 'Unknown problem')}
Topic: {problem_context.get('topic', 'math')}

Determine:
1. Is the attempt correct?
2. What's good about their approach?
3. What needs improvement?
4. Next step to guide them

Output JSON:
{{
    "is_correct": true/false,
    "strengths": ["what they did well"],
    "errors": ["specific mistakes"],
    "next_guidance": "specific next step or question to ask",
    "encouragement": "positive reinforcement message"
}}
"""
        
        return await self.gemini_service.generate_simple_response(prompt)