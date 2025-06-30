import os
import google.generativeai as genai
from typing import Dict, List, Optional
from dotenv import load_dotenv
import base64
from PIL import Image
import io
import json

load_dotenv()

class GeminiService:
    def __init__(self):
        """Initialize the Gemini service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="You are a helpful English AI assistant to answer students' questions about this YouTube video. Please answer in English. The student may also be referencing a specific part from the video transcript around their current video timestamp. The image attached shows the video at the point where the student is currently watching the video. When necessary, you can use the image to help you answer their question.")
        self.video_quiz_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="You are quiz maker that will test the student's retention of the video. The query will contain a video transcript and a list of their previous messages, create questions in JSON format that tests the user on general subject matter related concepts discussed in the transcript, and place a particular emphasis on the topics the student seemed to be confused about based on the chatlog. Make 5 total questions.")
        self.photo_grading_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="You are a detailed oriented CBSE style grader for 10th grade math questions. Utilize the attached question and 'solution' to ensure the student's work is fully correct. The student's work will be provided in the query as a photo. Please provide your response in the JSON format shown in the prompt. Do no hesitate to leave fields blank if there are no comments needed. ")
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
    
    async def generate_photo_grading(self, question_text: str, correct_solution: str, image_path: str) -> Dict:
        '''
        Grades a photo of a student's work against the correct solution.
        Returns a dictionary with grade, feedback, corrections, and strengths.
        '''
        try:
            # Load the image from file path
            pil_image = Image.open(image_path)
            
            # Create a structured prompt that will get us the desired output
            prompt = f"""
You are grading a student's handwritten solution to this math problem.

QUESTION: {question_text}

CORRECT SOLUTION: {correct_solution}

Please analyze the student's work in the attached image and provide your assessment in the following JSON format. All field are optional meaning if there are no strengths or no corrections needed, do no hesitate to leave those blank. It is very possible the student's work is completely wrong or completely correct:

{{
  "grade": "[score]/10",
  "feedback": "[A detailed paragraph about their work, max 100 words]",
  "corrections": [
    "[Specific error 1 with line/step reference]",
    "[Specific error 2 with line/step reference]"
  ],
  "strengths": [
    "[Positive aspect 1 of their work]",
    "[Positive aspect 2 of their work]"
  ]
}}

IMPORTANT:
- Give a numerical grade out of 10
- Feedback should be encouraging but honest
- List specific corrections if there are errors (empty list if perfect)
- Always find at least 2 strengths to highlight
- Reference specific steps or lines when pointing out errors
- Focus on mathematical accuracy and problem-solving approach

Respond with ONLY the JSON, no additional text.
"""
            
            # Send to Gemini with the image
            response = self.photo_grading_model.generate_content([prompt, pil_image])
            
            # Parse the JSON response
            response_text = response.text.strip()
            
            # Clean up response if it has markdown code blocks
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON to dictionary
            grading_result = json.loads(response_text)
            
            # Ensure all required fields are present with defaults
            if 'grade' not in grading_result:
                grading_result['grade'] = '0/10'
            if 'feedback' not in grading_result:
                grading_result['feedback'] = 'Unable to assess the work properly.'
            if 'corrections' not in grading_result:
                grading_result['corrections'] = []
            if 'strengths' not in grading_result:
                grading_result['strengths'] = []
            
            return grading_result
            
        except json.JSONDecodeError as e:
            print(f"Error parsing Gemini response as JSON: {e}")
            print(f"Raw response: {response_text if 'response_text' in locals() else 'No response'}")
            # Return a default grading result
            return {
                "grade": "0/10",
                "feedback": "Error processing the grading. Please try again.",
                "corrections": ["Unable to process the image properly"],
                "strengths": ["Attempted the problem"]
            }
        except Exception as e:
            print(f"Error in generate_photo_grading: {e}")
            import traceback
            traceback.print_exc()
            return {
                "grade": "0/10",
                "feedback": f"Error grading the work: {str(e)}",
                "corrections": ["Technical error occurred"],
                "strengths": ["Submitted work for grading"]
            }
    
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
                    
                    # Decode base64 image
                    image_data = base64.b64decode(video_frame)
                    
                    # Convert to PIL Image for google-generativeai library
                    pil_image = Image.open(io.BytesIO(image_data))
                    
                    # Add PIL image directly to content parts (works with google-generativeai)
                    content_parts.append(pil_image)
                    
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
            
            
            return response.text
            
        except Exception as e:
            print(f"❌ Failed to answer the video question: {e}")
            print(f"🔍 Exception type: {type(e)}")
            import traceback
            print(f"🔍 Full traceback:")
            traceback.print_exc()
            return "I'm sorry, I encountered an error while processing your request. Please try again."
    
    def generate_quiz(self, entire_transcript: str, previous_messages: List[Dict]) -> str:
        """Generate a multiple choice quiz for a YouTube video."""
        try:
            # Build chat context
            chat_context = ""
            if previous_messages:
                chat_context = "\n--- STUDENT CHAT HISTORY ---\n"
                for msg in previous_messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    chat_context += f"{role.upper()}: {content}\n"
            
            # Simple, strict prompt with example
            quiz_prompt = f"""
You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.

Based on the transcript and chat history, generate exactly 5 multiple choice quiz questions.

TRANSCRIPT:
{entire_transcript}

{chat_context}

REQUIRED JSON FORMAT (respond with EXACTLY this structure):
{{
  "quiz_title": "Quiz: [extract main topic from video]",
  "total_questions": 5,
  "questions": [
    {{
      "id": 1,
      "question": "What is the main concept discussed in the video?",
      "option1": "Machine Learning",
      "option2": "Data Science", 
      "option3": "Web Development",
      "correct_answer": "Machine Learning"
    }},
    {{
      "id": 2,
      "question": "Which algorithm was mentioned first?",
      "option1": "Linear Regression",
      "option2": "Neural Networks",
      "option3": "Decision Trees", 
      "correct_answer": "Linear Regression"
    }},
    {{
      "id": 3,
      "question": "What did the student ask about most?",
      "option1": "Backpropagation",
      "option2": "Overfitting",
      "option3": "Training Data",
      "correct_answer": "Backpropagation"
    }},
    {{
      "id": 4,
      "question": "What is supervised learning?",
      "option1": "Learning without labels",
      "option2": "Learning with labeled data",
      "option3": "Learning through rewards",
      "correct_answer": "Learning with labeled data"
    }},
    {{
      "id": 5,
      "question": "Why is validation data important?",
      "option1": "To train the model",
      "option2": "To test model performance",
      "option3": "To increase accuracy",
      "correct_answer": "To test model performance"
    }}
  ]
}}

RULES:
- Focus on topics the student seemed confused about from chat history, if any.
- Make sure correct_answer exactly matches one of the three options
- Return ONLY the JSON, nothing else
"""
            
            response = self.video_quiz_model.generate_content(quiz_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating quiz: {e}")
            # Simple fallback JSON
            return '''{
  "quiz_title": "General Video Quiz",
  "total_questions": 5,
  "questions": [
    {
      "id": 1,
      "question": "What was the main topic of this video?",
      "option1": "Educational Content",
      "option2": "Entertainment",
      "option3": "News",
      "correct_answer": "Educational Content"
    }
  ]
}'''

if __name__ == "__main__":
    import asyncio
    
    async def main():
        gemini_service = GeminiService()
        # Get the path to the image relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "testimage.png")
        
        result = await gemini_service.generate_photo_grading("What is the square root of 16?", "The square root of 16 is 4.", image_path)
        print(result)
    
    asyncio.run(main())
