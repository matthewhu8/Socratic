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
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        print(f"GEMINI MODEL: {self.model}")
    
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
    
    async def generate_chat_session(self):
        '''
        Answer a question about the YouTube video.
        '''
        try:    
            return self.model.start_chat()
        except: 
            print("failed to return a chat session")
    
    async def answer_video_question(self, message, session_data, video_context=None):
        '''
        Answer a question about the YouTube video with system instructions, chat history, and video context.
        '''
        try:
            # Enhanced system instructions with video context awareness
            if video_context.get("video_context") is not None:
                context = video_context.get("video_context")
                video_title = context.get("title")
                video_author = context.get("author")
                system_instructions = f"""You are a helpful AI assistant to answer students' questions about this YouTube video. The video title is: {video_title}, by {video_author}. The student may also be referencing this specific part from the video transcript.""" 
            else:
                system_instructions = f"""You are a helpful AI assistant to answer students' questions about this YouTube video. The student may also be referencing this specific part from the video transcript.""" 
                
            video_transcript = video_context.get("transcript")
            print(f"VIDEO TRANSCRIPT: {video_transcript}")
            # Extract chat history from session_data
            chat_history = session_data.get("messages", []) if session_data else []

            # Build the enhanced prompt with video context
            prompt_parts = [system_instructions]
            prompt_parts.append(f"\n--- VIDEO TRANSCRIPT CONTEXT ---\n{video_transcript}")
            
            # Add video context if available
            # if video_context and video_context.get("video_context"):
            #     prompt_parts.append(f"\n--- VIDEO TRANSCRIPT CONTEXT ---\n{video_context['video_context']}")
            #     if video_context.get("video_timestamp"):
            #         prompt_parts.append(f"\nStudent is currently at timestamp: {video_context['video_timestamp']:.1f} seconds")
            
            prompt_parts.append(f"\nStudent question: {message}")
            
            full_prompt = "\n".join(prompt_parts)
            print(f"FULL PROMPT: {full_prompt}")
            
            # Use chat history if available
            if chat_history:
                # Format the last 10 messages for context
                formatted_history = self.format_chat_history(chat_history[-10:])
                chat = self.model.start_chat(history=formatted_history)
                response = chat.send_message(full_prompt)
            else:
                # Generate without history for new sessions
                response = self.model.generate_content(full_prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Failed to answer the video question: {e}")
            return "I'm sorry, I encountered an error while processing your request. Please try again."
     
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
            
           
            system_message = """You are a helpful teaching assistant using Socratic questioning. 
            If the student appears to be stuck on this problem, ask them a question that will help guide their thinking. 
            DO NOT provide direct answers."""
            is_hidden_value_response = False
            
            # Create context message
            context_message = f"Problem: {public_question}\n\n"
            
            # Prepare the prompt
            full_prompt = f"{system_message}\n\n{context_message}Student question: {query}"
            
            # Format chat history for Gemini
            if chat_history:
                formatted_history = self.format_chat_history(chat_history[-4:])  # Last 4 messages
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
