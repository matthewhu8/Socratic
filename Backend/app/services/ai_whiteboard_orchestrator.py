"""
AI Whiteboard Orchestrator Service
Coordinates 2-stage AI workflow 
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
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
        Orchestrates the processing of student queries - two stage workflow
        """
        
        teaching_response = await self._generate_teaching_response(query, canvas_image, chat_history)
        print(teaching_response)
        svg_content = None
        if await self._should_generate_visual(query, teaching_response, canvas_image):
            svg_content = await self._generate_svg_visual(teaching_response, canvas_image, teaching_response, chat_history)
            print(f"Step 2: Generated visual for current step with teaching_response: {teaching_response}\n")
        

        return {
            "response": teaching_response,
            "svgContent": svg_content
        }
    
    async def _should_generate_visual(
        self, 
        query: str, 
        teaching_response: str, 
        canvas_image: Optional[str]
    ) -> bool:
        """
        Stage 1: Quick analysis to understand the learning context
        """
        prompt = f"""
Determ if a visual aid would help explain this teaching reponse. 
Student Query: {query}
Teaching Response: {teaching_response}
Canvas State: {"Student has drawn something" if canvas_image else "Empty canvas"}

Respond with only: true/false

A visual aid is helpful (true) for graphing, geometric conepts, step-by-step complex problem solving, diagrams, visualizing concepts if the student asks for it, correcting visual errors. 
A visual aid not not needed (false) if the explanation is straight forward, simple encouragement, or questions that don't involve visual elements. 
"""
        
        result = await self.gemini_service.generate_text_only(prompt, visual=True)
        return result == "true"
    
    async def _generate_teaching_response(
        self, 
        query: str, 
        canvas_image: Optional[str],
        chat_history: List[Dict[str, str]]
    ) -> str:
        """
Generate a teaching response for the student's query. 
        """
        
        # Include chat history in prompt
        history_context = ""
        if chat_history:
            lengthChatHistory = -1 * len(chat_history)
            recent_history = chat_history[lengthChatHistory:]  # Last 2 exchanges
            history_context = "Recent conversation:\n"
            for msg in recent_history:
                role = "Student" if msg['role'] == 'user' else "Tutor"
                history_context += f"{role}: {msg['content']}\n"
        
        prompt = f"""
You are an expert math tutor meant ot help the student eventually learn and master the concept. Analyze the student's query and provide an appropriate pedagogical response

{history_context}

Student Query: "{query}"
Canvas State: {"Student may have drawn something using their hand-writtenblack marker as shown in the image" if canvas_image else "Empty canvas"}
Analyze the student's query and provide an appropriate pedagogical response to encourage the student to think and learn without giving too much away while also providing help to prevent frustration. 
"""
        
        return await self.gemini_service.generate_text_only(prompt, visual=False)
    
    async def _generate_svg_visual(
        self, 
        query: str, 
        canvas_image: Optional[str],
        teaching_response: str, 
        chat_history: List[Dict[str, str]]
    ) -> Optional[str]:
        prompt = f"""
You are an expert visualization tutor who pays attention to every close detail of your response. Create an SVG visual to support this math tutoring response. 
Student's Query: {query}
Teaching Response: {teaching_response}
Canvas State: {"Student has drawn something" if canvas_image else "Empty canvas"}

Create a clear, education SVG that directly support the teaching response. 

GUIDELINES:
1. Use a 600x400 viewBox for consistency
2. Focus ONLY on the immediate step being taught
3. Use appropriate colors: blue (#2563eb) for new concepts, green (#16a34a) for correct steps, red (#dc2626) for errors
4. Include clear text labels with readable font sizes (14 px or larger)
5 Keep it simple - don't overcrowd the visual
6. Position elements logically (equations horizantally steps vertically)

Respond with ONLY the complete SVG markup (starting with <svg> and ending with </svg>)!!!
"""
        
        return await self.gemini_service.generate_svg_content(prompt, canvas_image)
    
    
 