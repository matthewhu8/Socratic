import os
import google.generativeai as genai
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        """Initialize the Gemini service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    def format_chat_history(self, chat_history: List[Dict]) -> List[Dict]:
        """Convert chat history to Gemini format."""
        formatted_history = []
        for msg in chat_history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                # Convert role names to Gemini format
                role = "user" if msg["role"] == "user" else "model"
                formatted_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })
        return formatted_history
    
    async def generate_response(
        self,
        query: str,
        context: Dict,
        chat_history: List[Dict] = None
    ) -> Dict[str, any]:
        """Generate a response using Gemini API."""
        try:
            # Extract context information
            public_question = context.get("public_question", "")
            is_practice_exam = context.get("isPracticeExam", False)
            question_id = context.get("question_id")
            test_id = context.get("test_id")
            
            # Check if this is a request for hidden values
            hidden_value = self._get_hidden_value(test_id, question_id, query)
            
            # Create system message based on context
            if hidden_value:
                system_message = """You are a helpful teaching assistant. The student is asking about a hidden value in the problem. 
                Since they specifically asked for it, you can provide the hidden value from the context. Be clear and informative."""
                is_hidden_value_response = True
            elif is_practice_exam:
                system_message = """You are a helpful teaching assistant using Socratic questioning. 
                If the student appears to be stuck on this problem, ask them a question that will help guide their thinking. 
                DO NOT provide direct answers. Review the chat history to avoid repeating questions."""
                is_hidden_value_response = False
            else:
                # For regular tests, be more restrictive
                return {
                    "response": "I can only help with understanding hidden values for this test question. Please rephrase your question to ask about a specific hidden value.",
                    "isHiddenValueResponse": False
                }
            
            # Create context message
            context_message = f"Problem: {public_question}\n\n"
            if hidden_value:
                context_message += f"Hidden value: {hidden_value}\n\n"
            
            # Prepare the prompt
            full_prompt = f"{system_message}\n\n{context_message}Student question: {query}"
            
            # Format chat history for Gemini
            if chat_history:
                formatted_history = self.format_chat_history(chat_history[-4:])  # Last 4 messages
                
                # Create a chat session with history
                chat = self.model.start_chat(history=formatted_history)
                response = chat.send_message(full_prompt)
            else:
                # Generate without history
                response = self.model.generate_content(full_prompt)
            
            return {
                "response": response.text,
                "isHiddenValueResponse": is_hidden_value_response
            }
            
        except Exception as e:
            print(f"Error generating Gemini response: {e}")
            return {
                "response": "I'm sorry, I encountered an error while processing your request. Please try again.",
                "isHiddenValueResponse": False
            }
    
    def _get_hidden_value(self, test_id: int, question_id: int, query: str) -> Optional[str]:
        """
        Check if the query is asking for a hidden value.
        This is a simplified version - in the original code this was handled by the vector service.
        For now, we'll return None and let the database handle hidden values directly.
        """
        # This would need to be implemented based on your specific hidden value logic
        # For now, returning None to maintain the same behavior as when vector service fails
        return None 