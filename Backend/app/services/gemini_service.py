import os
import google.generativeai as genai
from typing import Dict, List, Optional
from dotenv import load_dotenv
import base64
from PIL import Image
import io

load_dotenv()

class GeminiService:
    def __init__(self):
        """Initialize the Gemini service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="You are a helpful English AI assistant to answer students' questions about this YouTube video. Please answer in English. The student may also be referencing a specific part from the video transcript around their current video timestamp. The image attached shows the video at the point where the student is currently watching the video. When necessary, you can use the image to help you answer their question.")
        self.video_quiz_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="You are video quiz maker who creates questions based on the video transcript. You will be given a video transcript and a question, and you will need to create a multiple choice questions based on the transcript and the question.")
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
        Answer a question about the YouTube video with system instructions, chat history, video context, and optional image.
        '''
        try:
            # Sometimes we'll receive title and author, sometimes we won't
            if video_context.get("video_context") is not None:
                context = video_context.get("video_context")
                video_title = context.get("title")
                video_author = context.get("author")
                title_and_author = f"""The video title is: {video_title}, by {video_author}."""
            else: 
                title_and_author = ""
            
            # getting the video transcript
            video_transcript = video_context.get("transcript")
            print(f"VIDEO TRANSCRIPT: {video_transcript}")
            # Extract chat history from session_data
            chat_history = session_data.get("messages", []) if session_data else []

            # Build the enhanced prompt with video context
            prompt_parts = [title_and_author]
            prompt_parts.append(f"\n--- VIDEO TRANSCRIPT CONTEXT ---\n{video_transcript}")
            
            # The actual student question
            prompt_parts.append(f"\nStudent question: {message}")
            
            full_prompt = "\n".join(prompt_parts)
            print(f"FULL PROMPT: {full_prompt}")
            
            # Prepare content parts for Gemini
            content_parts = [full_prompt]
            
            # Handle video frame if provided
            video_frame = video_context.get("video_frame")
            
            if video_frame:
                try:
                    # Extract base64 data (remove data:image/jpeg;base64, prefix if present)
                    original_frame = video_frame
                    if video_frame.startswith('data:image'):
                        video_frame = video_frame.split(',')[1]
                        print(f"✂️  Removed data URI prefix, new length: {len(video_frame)}")
                    else:
                        print(f"⚠️  No data URI prefix found, using raw data")
                    
                    print(f"📊 Base64 data length: {len(video_frame)}")
                    print(f"📊 Base64 data starts with: {video_frame[:50]}...")
                    
                    # Decode base64 image
                    print(f"🔄 Attempting to decode base64...")
                    image_data = base64.b64decode(video_frame)
                    print(f"✅ Base64 decode successful!")
                    print(f"📊 Decoded image data length: {len(image_data)} bytes")
                    
                    # Convert to PIL Image for google-generativeai library
                    print(f"🔄 Converting to PIL Image...")
                    pil_image = Image.open(io.BytesIO(image_data))
                    print(f"✅ PIL Image created successfully!")
                    print(f"📊 Image size: {pil_image.size}")
                    print(f"📊 Image mode: {pil_image.mode}")
                    print(f"📊 Image format: {pil_image.format}")
                    
                    # Add PIL image directly to content parts (works with google-generativeai)
                    content_parts.append(pil_image)
                    print("✅ Added PIL image to Gemini request")
                    print(f"📊 Final content_parts length: {len(content_parts)}")
                    print(f"📊 Content parts types: {[type(part) for part in content_parts]}")
                    
                except Exception as e:
                    print(f"❌ Error processing video frame: {e}")
                    print(f"🔍 Error type: {type(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print(f"ℹ️  No video frame provided, proceeding without image")
            
            # Use chat history if available
            print(f"🔄 Preparing to send request to Gemini...")
            print(f"📊 Final content_parts summary:")
            for i, part in enumerate(content_parts):
                if isinstance(part, Image.Image):
                    print(f"   Part {i}: PIL Image - {part.size} {part.mode}")
                else:
                    print(f"   Part {i}: {type(part)} - {str(part)[:100]}...")
            
            if chat_history:
                formatted_history = self.format_chat_history(chat_history[-10:])
                print(f"💬 Using chat history with {len(formatted_history)} messages")
                chat = self.model.start_chat(history=formatted_history)
                response = chat.send_message(content_parts)
            else:
                print(f"💬 No chat history, generating fresh response")
                response = self.model.generate_content(content_parts)
            
            print(f"✅ Successfully received response from Gemini!")
            print(f"📊 Response type: {type(response)}")
            print(f"📊 Response length: {len(response.text) if hasattr(response, 'text') else 'No text attr'}")
            
            return response.text
            
        except Exception as e:
            print(f"❌ Failed to answer the video question: {e}")
            print(f"🔍 Exception type: {type(e)}")
            import traceback
            print(f"🔍 Full traceback:")
            traceback.print_exc()
            return "I'm sorry, I encountered an error while processing your request. Please try again."

