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
        Orchestrates the processing of student queries - generates one step at a time
        """
        
        # Stage 1: Analyze query and determine approach
        analysis = await self._analyze_query(query, canvas_image, chat_history)
        print(f"Step 1: Classifying the prompt {analysis}\n")
        
        # Stage 2: Generate teaching response for ONE step
        teaching_response = await self._generate_teaching_response(analysis, query, chat_history)
        print(f"Step 2: Generated teaching response: {teaching_response}\n")
        
        # Stage 3: Plan visual for this specific step using the teaching response
        drawing_commands = []
        if analysis.requires_visual:
            visual_plan = await self._plan_visuals(analysis, canvas_image, teaching_response)
            print(f"Step 3: Created visual plan for current step\n")
            
            # Stage 4: Generate drawing commands for this single visual
            if visual_plan:
                drawing_commands = await self._generate_drawing_commands(
                    visual_plan, 
                    analysis,
                    teaching_response
                )
                print(f"Step 4: Generated {len(drawing_commands)} drawing commands\n")
        
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
        original_query: str,
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
        Stage 2: Generate focused pedagogical response for ONE STEP ONLY
        """
        approach_prompts = {
            PedagogicalApproach.GUIDED_DISCOVERY: """
Focus on the VERY NEXT STEP the student needs to understand. Ask ONE specific question 
that guides them toward this step. Don't reveal future steps or the final answer.
End with either:
- A specific question about what they think should happen next
- "Does this step make sense before we continue?"
""",
            PedagogicalApproach.ERROR_CORRECTION: """
Address ONLY the immediate error they made. Gently point out the issue and 
guide them to fix just that one mistake. 
End with either:
- A question about how to correct this specific error
- "Do you see why this step needs to be corrected?"
""",
            PedagogicalApproach.WORKED_EXAMPLE: """
Show them ONLY the next immediate step with a clear explanation of why.
DO NOT show multiple steps or the complete solution.
End with either:
- "Can you try the next step from here?"
- "Does this step make sense before we move on?"
""",
            PedagogicalApproach.CONCEPT_EXPLANATION: """
Explain ONLY the immediate concept needed for the current step.
Use simple terms and relate it directly to what they're working on right now.
End with either:
- A question to check their understanding of this concept
- "Does this concept make sense before we apply it?"
"""
        }
        
        # Include chat history in prompt
        history_context = ""
        if chat_history:
            recent_history = chat_history[-4:]  # Last 2 exchanges
            history_context = "Recent conversation:\n"
            for msg in recent_history:
                role = "Student" if msg['role'] == 'user' else "Tutor"
                history_context += f"{role}: {msg['content']}\n"
        
        prompt = f"""
You're tutoring {analysis.topic}. 

{history_context}

Current student query: "{original_query}"

IMPORTANT: Focus on explaining or guiding through ONLY THE NEXT SINGLE STEP.

{approach_prompts[analysis.approach]}

{"Address this specific misconception: " + analysis.misconceptions[0] if analysis.misconceptions else ""}

Respond in 2-4 sentences focusing on just the immediate next step.
"""
        
        return await self.gemini_service.generate_text_only(prompt)
    
    async def _plan_visuals(
        self, 
        analysis: AnalysisResult,
        canvas_image: Optional[str],
        teaching_response: str
    ) -> VisualPlan:
        """
        Stage 3: Plan ONE visual that matches the teaching response
        """
        prompt = f"""
Plan a SINGLE visual element for teaching {analysis.topic}.

Teaching response that needs visual support:
"{teaching_response}"

Current canvas state: {"Student has drawn something" if canvas_image else "Empty canvas"}

Create a simple layout for ONLY the visual that directly supports what was just explained.
Focus on the immediate step being taught, not future steps. 

Output JSON with a single visual element:
{{
    "layout_zones": [
        {{"id": "current_step", "x": 50, "y": 50, "width": 400, "height": 200}}
    ],
    "drawing_sequence": ["single_visual_element"],
    "content_mapping": {{"single_visual_element": "visual content that matches the teaching response"}}
}}

Examples:
- If teaching "subtract 5 from both sides", show: "x + 5 - 5 = 10 - 5"
- If explaining a concept, show ONE simple diagram
- If correcting an error, highlight JUST that error
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
        Stage 4: Generate drawing commands for the single visual element
        """
        # Since we now have only one visual element per response
        if not visual_plan.drawing_sequence:
            return []
            
        element = visual_plan.drawing_sequence[0]  # Should only be one element
        zone = visual_plan.layout_zones[0] if visual_plan.layout_zones else {"x": 50, "y": 50, "width": 400, "height": 200}
        content = visual_plan.content_mapping.get(element, "")
        
        # Generate all commands needed for this single visual in one API call
        prompt = f"""
Generate drawing commands for a {analysis.topic} visual.

Teaching context: "{teaching_response}"
Visual content to draw: "{content}"
Drawing area: x={zone['x']}, y={zone['y']}, width={zone['width']}, height={zone['height']}

Create clear, simple visuals that directly support the teaching response.
Use appropriate colors: blue for new concepts, green for correct steps, red for errors/corrections.

Output a JSON array of drawing commands. Include all necessary elements (text, shapes, lines) to create the complete visual.

Example commands:
[
    {{"type": "text", "text": "x + 5 = 10", "position": {{"x": 50, "y": 100}}, "options": {{"color": "#000000", "fontSize": 24}}}},
    {{"type": "shape", "shape": "line", "options": {{"x1": 50, "y1": 120, "x2": 150, "y2": 120, "color": "#0000FF", "strokeWidth": 2}}}},
    {{"type": "text", "text": "-5", "position": {{"x": 160, "y": 100}}, "options": {{"color": "#FF0000", "fontSize": 20}}}}
]
"""
        
        commands = await self.gemini_service.generate_drawing_commands_only(prompt)
        return commands if commands else []
    
    
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
    
