"""
Interactive Whiteboard Session Manager
Manages the interactive session between student and AI
"""

from typing import Dict, List, Optional, Any
import json
from .whiteboard_layout_manager import WhiteboardLayoutManager
from .annotation_analyzer import AnnotationAnalyzer
from .contextual_drawing_responder import ContextualDrawingResponder
from .drawing_command_generator import DrawingCommandGenerator

class InteractiveWhiteboardSession:
    """Manages the interactive session between student and AI"""
    
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        self.layout_manager = WhiteboardLayoutManager()
        self.annotation_analyzer = AnnotationAnalyzer(gemini_service)
        self.drawing_generator = DrawingCommandGenerator(gemini_service)
        self.drawing_responder = ContextualDrawingResponder(gemini_service, self.drawing_generator)
        self.canvas_history = []
        
    async def process_interaction(self, 
                                 current_canvas: str,
                                 user_message: Optional[str],
                                 session_context: Dict) -> Dict:
        """Process each interaction in the session"""
        
        # 1. Detect what changed on canvas
        canvas_before = self.canvas_history[-1] if self.canvas_history else None
        changes = await self.annotation_analyzer.analyze_annotations(
            canvas_before,
            current_canvas,
            session_context
        )
        
        # 2. Analyze available space
        layout_analysis = await self.layout_manager.analyze_student_work(
            current_canvas, 
            self.gemini_service
        )
        
        # 3. Determine response strategy
        if changes.get('new_annotations') or changes.get('annotations'):
            # Respond to visual annotations
            response_strategy = "annotation_response"
            annotations = changes.get('new_annotations', changes.get('annotations', []))
            primary_annotation = annotations[0] if annotations else None
        elif user_message:
            # Respond to text query
            response_strategy = "text_response"
            primary_annotation = None
        else:
            # Continue previous guidance
            response_strategy = "continuation"
            primary_annotation = None
        
        # 4. Generate appropriate response
        response = await self._generate_response(
            response_strategy,
            primary_annotation,
            layout_analysis,
            user_message,
            session_context
        )
        
        # 5. Update canvas history
        self.canvas_history.append(current_canvas)
        
        return response
    
    async def _generate_response(self,
                                strategy: str,
                                annotation: Optional[Dict],
                                layout_analysis: Dict,
                                user_message: Optional[str],
                                context: Dict) -> Dict:
        """Generate appropriate response based on strategy"""
        
        if strategy == "annotation_response" and annotation:
            # Respond to student's visual annotation
            return await self.drawing_responder.respond_to_annotation(annotation, context)
            
        elif strategy == "text_response" and user_message:
            # Handle text-based query with potential visual response
            return await self._handle_text_query(user_message, layout_analysis, context)
            
        else:
            # Default continuation or encouragement
            return {
                "response": "I'm here to help! Feel free to draw your work or ask questions.",
                "drawing_commands": []
            }
    
    async def _handle_text_query(self, 
                                user_message: str,
                                layout_analysis: Dict,
                                context: Dict) -> Dict:
        """Handle text-based queries with appropriate visual responses"""
        
        # Determine if visual response is needed
        visual_keywords = ['draw', 'show', 'graph', 'diagram', 'picture', 'visual', 'see']
        needs_visual = any(keyword in user_message.lower() for keyword in visual_keywords)
        
        # Generate text response
        prompt = f"""
Student asked: "{user_message}"
Context: {context.get('topic', 'math tutoring')}

Provide helpful response as a math tutor. Be encouraging and guide them step by step.
Keep response to 2-3 sentences.
"""
        
        text_response = await self.gemini_service.generate_text_only(prompt)
        
        # Generate visual response if needed
        drawing_commands = []
        if needs_visual:
            # Find optimal zone for drawing
            empty_zones = layout_analysis.get('empty_zones', [])
            if empty_zones:
                drawing_zone = empty_zones[0]
                
                visual_prompt = f"""
Generate visual aid for: "{user_message}"
In zone: {drawing_zone}
Topic: {context.get('topic', 'math')}

Create helpful visual explanation.
Output JSON array of drawing commands only.
"""
                
                drawing_commands = await self.gemini_service.generate_drawing_commands_only(visual_prompt)
        
        return {
            "response": text_response,
            "drawing_commands": drawing_commands
        }