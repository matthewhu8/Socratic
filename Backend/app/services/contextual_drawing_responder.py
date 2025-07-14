"""
Contextual Drawing Response System
Generates drawing commands that respond to student annotations
"""

from typing import Dict, List, Optional, Any
import json

class ContextualDrawingResponder:
    """Generates drawing commands that respond to student annotations"""
    
    def __init__(self, gemini_service, drawing_generator):
        self.gemini_service = gemini_service
        self.drawing_generator = drawing_generator
    
    async def respond_to_annotation(self, annotation: Dict, context: Dict) -> Dict:
        """Generate appropriate visual response to student annotation"""
        
        response_strategies = {
            "question_mark": self._respond_to_question,
            "solution_attempt": self._respond_to_attempt,
            "correction": self._acknowledge_correction,
            "calculation": self._check_calculation,
            "problem_setup": self._acknowledge_setup
        }
        
        strategy = response_strategies.get(
            annotation['type'], 
            self._default_response
        )
        
        return await strategy(annotation, context)
    
    async def _respond_to_question(self, annotation: Dict, context: Dict) -> Dict:
        """When student draws a question mark or circles something"""
        
        # Position response near the question
        response_zone = self._calculate_response_zone(annotation['location'])
        
        prompt = f"""
Student marked a question at {annotation['location']} 
regarding {annotation['content']}.

Generate helpful visual hint at {response_zone}:
- Arrow pointing to relevant part
- Brief text hint
- Visual cue (e.g., highlighting a pattern)

Don't give away the answer, guide them.

Output JSON array of drawing commands only.
"""
        
        drawing_commands = await self.gemini_service.generate_drawing_commands_only(prompt)
        
        return {
            "response": "I see you have a question about that part. Let me give you a hint...",
            "drawing_commands": drawing_commands
        }
    
    async def _respond_to_attempt(self, annotation: Dict, context: Dict) -> Dict:
        """When student writes a solution attempt"""
        
        # First analyze if the attempt is correct
        analysis = await self._analyze_student_work(annotation['content'], context)
        
        if analysis.get('is_correct', False):
            return await self._generate_success_response(annotation, analysis)
        else:
            return await self._generate_guided_correction(annotation, analysis)
    
    async def _acknowledge_correction(self, annotation: Dict, context: Dict) -> Dict:
        """When student makes a correction"""
        
        response_zone = self._calculate_response_zone(annotation['location'])
        
        # Generate encouraging visual feedback
        prompt = f"""
Student made a correction at {annotation['location']}.
Generate encouraging visual feedback at {response_zone}:
- Green checkmark or thumbs up
- Encouraging text like "Good catch!" or "Much better!"

Output JSON array of drawing commands only.
"""
        
        drawing_commands = await self.gemini_service.generate_drawing_commands_only(prompt)
        
        return {
            "response": "Great job making that correction! You're on the right track.",
            "drawing_commands": drawing_commands
        }
    
    async def _check_calculation(self, annotation: Dict, context: Dict) -> Dict:
        """When student shows calculation work"""
        
        analysis = await self._analyze_student_work(annotation['content'], context)
        
        response_zone = self._calculate_response_zone(annotation['location'])
        
        if analysis.get('is_correct', False):
            prompt = f"""
Generate positive feedback for correct calculation at {response_zone}:
- Green checkmark
- Text: "Correct!"
- Maybe a star or smiley face

Output JSON array of drawing commands only.
"""
        else:
            prompt = f"""
Generate gentle correction for calculation error at {response_zone}:
- Yellow circle around the error (not harsh red)
- Text with hint: "{analysis.get('next_guidance', 'Check this step')}"
- Encouraging tone

Output JSON array of drawing commands only.
"""
        
        drawing_commands = await self.gemini_service.generate_drawing_commands_only(prompt)
        
        return {
            "response": analysis.get('encouragement', "Let me help you with that calculation."),
            "drawing_commands": drawing_commands
        }
    
    async def _acknowledge_setup(self, annotation: Dict, context: Dict) -> Dict:
        """When student sets up the problem"""
        
        response_zone = self._calculate_response_zone(annotation['location'])
        
        prompt = f"""
Student set up problem: {annotation['content']}
Generate encouraging acknowledgment at {response_zone}:
- Positive text like "Good start!" or "Nice setup!"
- Maybe an arrow pointing to next step area
- Encouraging visual element

Output JSON array of drawing commands only.
"""
        
        drawing_commands = await self.gemini_service.generate_drawing_commands_only(prompt)
        
        return {
            "response": "Great job setting up the problem! Now what's your next step?",
            "drawing_commands": drawing_commands
        }
    
    async def _generate_success_response(self, annotation: Dict, analysis: Dict) -> Dict:
        """Generate positive reinforcement for correct work"""
        
        response_zone = self._calculate_response_zone(annotation['location'])
        
        prompt = f"""
Generate celebration for correct work at {response_zone}:
- Big green checkmark
- Text: "Excellent work!"
- Maybe confetti or stars
- Highlight what they did well: {', '.join(analysis.get('strengths', []))}

Output JSON array of drawing commands only.
"""
        
        drawing_commands = await self.gemini_service.generate_drawing_commands_only(prompt)
        
        return {
            "response": f"Excellent! {analysis.get('encouragement', 'You got it right!')}",
            "drawing_commands": drawing_commands
        }
    
    async def _generate_guided_correction(self, annotation: Dict, analysis: Dict) -> Dict:
        """Generate helpful correction guidance"""
        
        response_zone = self._calculate_response_zone(annotation['location'])
        
        prompt = f"""
Generate gentle correction guidance at {response_zone}:
- Highlight the error area (yellow, not red)
- Show the correction: {analysis.get('next_guidance', 'Try again')}
- Encouraging visual elements
- Point to what they did well: {', '.join(analysis.get('strengths', []))}

Output JSON array of drawing commands only.
"""
        
        drawing_commands = await self.gemini_service.generate_drawing_commands_only(prompt)
        
        return {
            "response": f"Good effort! {analysis.get('next_guidance', 'Let me help you with this step.')}",
            "drawing_commands": drawing_commands
        }
    
    async def _default_response(self, annotation: Dict, context: Dict) -> Dict:
        """Default response for unrecognized annotation types"""
        
        return {
            "response": "I see you're working on something. Can you tell me what you're thinking?",
            "drawing_commands": []
        }
    
    def _calculate_response_zone(self, annotation_location: Dict) -> Dict:
        """Calculate where to place AI response relative to annotation"""
        
        # Place response to the right and slightly below the annotation
        return {
            "x": annotation_location.get("x", 50) + annotation_location.get("width", 100) + 20,
            "y": annotation_location.get("y", 50) + 10,
            "width": 200,
            "height": 100
        }
    
    async def _analyze_student_work(self, content: str, context: Dict) -> Dict:
        """Analyze student work for correctness"""
        
        prompt = f"""
Analyze this student work: {content}
Context: {context.get('topic', 'math problem')}

Determine:
1. Is it correct?
2. What's good about it?
3. What needs work?
4. Encouraging next step

Output JSON:
{{
    "is_correct": true/false,
    "strengths": ["what they did well"],
    "errors": ["mistakes"],
    "next_guidance": "helpful next step",
    "encouragement": "positive message"
}}
"""
        
        return await self.gemini_service.generate_simple_response(prompt)