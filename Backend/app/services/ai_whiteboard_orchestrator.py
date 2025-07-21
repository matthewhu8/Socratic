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
        chat_history: List[Dict[str, str]],
        previous_canvas_image: Optional[str] = None,
        has_annotation: bool = False
    ) -> Dict[str, Any]:
        """
        Orchestrates the processing of student queries - two stage workflow
        """
        
        teaching_response = await self._generate_teaching_response(query, canvas_image, chat_history, previous_canvas_image, has_annotation)
        print(f"step 1 generated: {teaching_response}")
        # eventually would like a step to decide if we want new drawing (svg content), annotation on current image (JSON drawing with coordinates), or no drawing at all. For the purposes of speed for now, this step does not exist. 
        # look into classification models etc.
        svg_content = None
        svg_content = await self._generate_svg_visual(teaching_response, canvas_image, teaching_response, chat_history, previous_canvas_image, has_annotation)
        print(f"Step 2: Generated visual for current step with teaching_response: {teaching_response}\n")
        return {
            "response": teaching_response,
            "svgContent": svg_content
        }
    
    
    async def _generate_teaching_response(
        self, 
        query: str, 
        canvas_image: Optional[str],
        chat_history: List[Dict[str, str]],
        previous_canvas_image: Optional[str] = None,
        has_annotation: bool = False
    ) -> str:
        """
        Generate a teaching response using optimized chat-based approach.
        """
        
        # Use optimized approach with chat history instead of building prompt
        if has_annotation and previous_canvas_image and canvas_image:
            # For annotation queries, still use comparison method
            annotation_context = "IMPORTANT: The student has made new annotations/drawings on the whiteboard since our last interaction. Two images are provided - the previous state and current state. The student is likely referencing their new markings when asking this question. Pay close attention to what they've added."
            
            minimal_prompt = f"Student Query: \"{query}\"\nCanvas: Student has drawn something\n{annotation_context}\nProvide encouraging guidance."
            
            return await self.gemini_service.generate_comparison_text_response(minimal_prompt, previous_canvas_image, canvas_image)
        else:
            # Use chat history approach for regular queries
            # Convert chat history to Gemini format
            formatted_history = []
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            
            for msg in recent_history:
                role = "user" if msg.get("role") == "user" else "model"
                formatted_history.append({
                    "role": role,
                    "parts": [msg.get("content", "")]
                })
            
            # Start chat with history pre-loaded
            chat = self.gemini_service.text_model.start_chat(history=formatted_history)
            
            # MINIMAL prompt - system instruction handles the rest
            canvas_state = "Has student drawing" if canvas_image else "Empty"
            minimal_prompt = f"Student asks: \"{query}\"\nCanvas: {canvas_state}\nProvide guidance."
            
            # Prepare content parts
            content_parts = [minimal_prompt]
            if canvas_image:
                try:
                    import base64
                    from PIL import Image
                    import io
                    
                    if canvas_image.startswith('data:image'):
                        canvas_image = canvas_image.split(',')[1]
                    image_data = base64.b64decode(canvas_image)
                    pil_image = Image.open(io.BytesIO(image_data))
                    content_parts.append(pil_image)
                except Exception as e:
                    print(f"Error processing canvas image in teaching response: {e}")
            
            response = await chat.send_message_async(content_parts)
            return response.text.strip()
    
    async def _generate_svg_visual(
        self, 
        query: str, 
        canvas_image: Optional[str],
        teaching_response: str, 
        chat_history: List[Dict[str, str]],
        previous_canvas_image: Optional[str] = None,
        has_annotation: bool = False
    ) -> Optional[str]:
        """
        Generate SVG visual using optimized chat history method.
        """
        
        # Use the new optimized SVG generation method
        return await self.gemini_service.generate_svg_with_chat_history(
            query=query,
            teaching_response=teaching_response,
            chat_history=chat_history,
            canvas_image=canvas_image
        )
    
    
 