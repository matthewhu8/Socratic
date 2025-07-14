"""
AI Whiteboard Orchestrator Service
Coordinates multiple specialized AI calls to create comprehensive tutoring responses
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class PedagogicalApproach(Enum):
    GUIDED_DISCOVERY = "guided_discovery"
    WORKED_EXAMPLE = "worked_example"
    ERROR_CORRECTION = "error_correction"
    CONCEPT_EXPLANATION = "concept_explanation"

@dataclass
class AnalysisResult:
    topic: str
    student_intent: str
    misconceptions: List[str]
    approach: PedagogicalApproach
    requires_visual: bool
    visual_elements: List[str]

@dataclass
class VisualPlan:
    layout_zones: List[Dict[str, Any]]
    drawing_sequence: List[str]
    content_mapping: Dict[str, str]

class AIWhiteboardOrchestrator:
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        
    async def process_student_query(
        self, 
        query: str, 
        canvas_image: Optional[str],
        chat_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Orchestrates the multi-stage processing of student queries
        """
        
        # Stage 1: Analyze query and determine approach
        analysis = await self._analyze_query(query, canvas_image, chat_history)
        
        # Stage 2 & 3 can run in parallel
        response_task = self._generate_teaching_response(analysis, query)
        visual_task = self._plan_visuals(analysis, canvas_image) if analysis.requires_visual else None
        
        # Wait for both tasks
        teaching_response = await response_task
        visual_plan = await visual_task if visual_task else None
        
        # Stage 4: Generate drawing commands if needed
        drawing_commands = []
        if visual_plan:
            drawing_commands = await self._generate_drawing_commands(
                visual_plan, 
                analysis,
                teaching_response
            )
        
        return {
            "response": teaching_response,
            "drawing_commands": drawing_commands,
            "metadata": {
                "topic": analysis.topic,
                "approach": analysis.approach.value,
                "misconceptions": analysis.misconceptions
            }
        }
    
    async def _analyze_query(
        self, 
        query: str, 
        canvas_image: Optional[str],
        chat_history: List[Dict[str, str]]
    ) -> AnalysisResult:
        """
        Stage 1: Quick analysis to understand the learning context
        """
        prompt = f"""
Analyze this math tutoring scenario. Be concise and specific.

Student Query: {query}
Canvas Content: {"Student has drawn something" if canvas_image else "No drawing"}
Recent Context: {self._summarize_chat_history(chat_history)}

Respond with JSON only:
{{
    "topic": "specific math topic",
    "student_intent": "what they're trying to do",
    "misconceptions_detected": ["any errors or misunderstandings"],
    "pedagogical_approach": "guided_discovery|worked_example|error_correction|concept_explanation",
    "requires_visual": true/false,
    "visual_elements_needed": ["list of visual aids needed"]
}}
"""
        
        # Use simplified analysis method
        result = await self.gemini_service.generate_simple_response(prompt, canvas_image)
        
        return self._parse_analysis_result(result)
    
    async def _generate_teaching_response(
        self, 
        analysis: AnalysisResult,
        original_query: str
    ) -> str:
        """
        Stage 2: Generate focused pedagogical response
        """
        approach_prompts = {
            PedagogicalApproach.GUIDED_DISCOVERY: """
Help the student discover the solution themselves. Ask one specific question 
that will guide them to the next step. Don't reveal the answer.
""",
            PedagogicalApproach.ERROR_CORRECTION: """
Gently point out where they went wrong without being discouraging. 
Ask them to reconsider that specific step.
""",
            PedagogicalApproach.WORKED_EXAMPLE: """
Show them the next step only, explaining why. Then ask if they can 
continue from there.
""",
            PedagogicalApproach.CONCEPT_EXPLANATION: """
Explain the concept they're struggling with using simple terms and 
an analogy if helpful. Then relate it back to their problem.
"""
        }
        
        prompt = f"""
You're tutoring {analysis.topic}. The student asked: "{original_query}"

{approach_prompts[analysis.approach]}

{"Address these misconceptions: " + ", ".join(analysis.misconceptions) if analysis.misconceptions else ""}

Respond in 2-3 sentences max. Be encouraging and specific.
"""
        
        return await self.gemini_service.generate_text_only(prompt)
    
    async def _plan_visuals(
        self, 
        analysis: AnalysisResult,
        canvas_image: Optional[str]
    ) -> VisualPlan:
        """
        Stage 3: Plan the visual layout
        """
        prompt = f"""
Plan visual elements for teaching {analysis.topic}.
Elements needed: {', '.join(analysis.visual_elements)}

Create a layout that:
1. Doesn't overlap with existing student work
2. Organizes information clearly
3. Uses color coding for different concepts

Output JSON with layout zones and drawing sequence:
{{
    "layout_zones": [
        {{"id": "problem", "x": 50, "y": 50, "width": 300, "height": 100}},
        {{"id": "work_area", "x": 50, "y": 200, "width": 400, "height": 300}}
    ],
    "drawing_sequence": ["problem_statement", "step1_hint"],
    "content_mapping": {{"problem_statement": "x + 5 = 10", "step1_hint": "Subtract 5 from both sides"}}
}}
"""
        
        result = await self.gemini_service.generate_simple_response(prompt, canvas_image)
        return self._parse_visual_plan(result)
    
    async def _generate_drawing_commands(
        self,
        visual_plan: VisualPlan,
        analysis: AnalysisResult,
        teaching_response: str
    ) -> List[Dict[str, Any]]:
        """
        Stage 4: Generate specific drawing commands
        """
        commands = []
        
        # Generate commands for each element in sequence
        for element in visual_plan.drawing_sequence:
            zone = self._get_zone_for_element(element, visual_plan)
            content = visual_plan.content_mapping.get(element, "")
            
            element_commands = await self._generate_element_commands(
                element, zone, content, analysis.topic
            )
            commands.extend(element_commands)
        
        return commands
    
    async def _generate_element_commands(
        self,
        element: str,
        zone: Dict[str, Any],
        content: str,
        topic: str
    ) -> List[Dict[str, Any]]:
        """
        Generate drawing commands for a specific element
        """
        prompt = f"""
Generate precise drawing commands for {element} in a {topic} lesson.
Zone: x={zone['x']}, y={zone['y']}, width={zone['width']}, height={zone['height']}
Content: {content}

Use clear fonts, appropriate colors (blue for new concepts, green for correct, red for errors).
Output JSON array of drawing commands only.

Example format:
[
    {{"type": "text", "text": "{content}", "position": {{"x": {zone['x']}, "y": {zone['y']}}}, "options": {{"color": "#000000"}}}},
    {{"type": "shape", "shape": "rectangle", "options": {{"x": {zone['x']}, "y": {zone['y'] + 30}, "width": 200, "height": 40, "color": "#0000FF"}}}}
]
"""
        
        return await self.gemini_service.generate_drawing_commands_only(prompt)
    
    def _summarize_chat_history(self, history: List[Dict[str, str]]) -> str:
        """Summarize recent chat history for context"""
        if not history:
            return "No previous conversation"
        
        recent = history[-3:]  # Last 3 exchanges
        summary = []
        for msg in recent:
            role = "Student" if msg['role'] == 'user' else "Tutor"
            # Truncate long messages
            content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
            summary.append(f"{role}: {content}")
        
        return "\n".join(summary)
    
    def _parse_analysis_result(self, result: Dict) -> AnalysisResult:
        """Parse JSON result into AnalysisResult dataclass"""
        approach_map = {
            "guided_discovery": PedagogicalApproach.GUIDED_DISCOVERY,
            "worked_example": PedagogicalApproach.WORKED_EXAMPLE,
            "error_correction": PedagogicalApproach.ERROR_CORRECTION,
            "concept_explanation": PedagogicalApproach.CONCEPT_EXPLANATION
        }
        
        return AnalysisResult(
            topic=result.get("topic", "general math"),
            student_intent=result.get("student_intent", "solving problem"),
            misconceptions=result.get("misconceptions_detected", []),
            approach=approach_map.get(
                result.get("pedagogical_approach", "guided_discovery"),
                PedagogicalApproach.GUIDED_DISCOVERY
            ),
            requires_visual=result.get("requires_visual", True),
            visual_elements=result.get("visual_elements_needed", [])
        )
    
    def _parse_visual_plan(self, result: Dict) -> VisualPlan:
        """Parse JSON result into VisualPlan dataclass"""
        return VisualPlan(
            layout_zones=result.get("layout_zones", []),
            drawing_sequence=result.get("drawing_sequence", []),
            content_mapping=result.get("content_mapping", {})
        )
    
    def _get_zone_for_element(self, element: str, visual_plan: VisualPlan) -> Dict[str, Any]:
        """Find the appropriate zone for an element"""
        # Simple mapping - could be more sophisticated
        for zone in visual_plan.layout_zones:
            if element.startswith(zone['id']):
                return zone
        
        # Default zone if not found
        return {"x": 50, "y": 50, "width": 400, "height": 200}