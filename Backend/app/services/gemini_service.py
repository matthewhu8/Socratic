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
        self.question_chat_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="The student is asking a question about a math problem. Return a short response to the question, addressing the student's concerns and explaining the concept in a simple, understandable way if possible. The student's question will be provided in the query. The math problem will be provided in the query. We will provide the step-by-step solution to the problem in the query but blatantly reveal the solution, it is only so you don't give out incorrect information and guide the student towards the correct path.")
        
        # Create simplified models for multi-stage processing
        self.analysis_model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20',
            system_instruction="You analyze student queries and canvas images to determine learning context. Always respond with valid JSON only."
        )
        
        self.text_model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20', 
            system_instruction="You are a patient math tutor. Provide encouraging, step-by-step guidance. Keep responses concise and engaging."
        )

        self.determine_necessary_visual_model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20',
            system_instruction="You determine if a visual aid is necessary for the student's query. Respond according to prompt. Should be one word: 'true' or 'false'"
        )
        
        self.visual_model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20',
            system_instruction="You generate drawing commands for educational whiteboard visualizations. Always respond with valid JSON arrays of drawing commands only."
        )
        
        self.svg_model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20',
            system_instruction="You generate SVG content for educational math visualizations. Always respond with valid SVG markup only, starting with <svg> and ending with </svg>."
        )
        
        # Keep existing tutor model for backward compatibility
        self.tutor_model = genai.GenerativeModel(
                'gemini-2.5-flash-preview-05-20',
                system_instruction="""You are a math tutor. Respond with JSON containing 'response' and 'drawing_commands' fields."""
            )
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
            
            if chat_history:
                formatted_history = self.format_chat_history(chat_history[-10:])
                print(f"💬 Using chat history with {len(formatted_history)} messages")
                chat = self.model.start_chat(history=formatted_history)
                response = chat.send_message(content_parts)
            else:
                print(f"💬 No chat history, generating fresh response")
                response = self.model.generate_content(content_parts)
            
            print(f"RESPONSE: {response.text}")
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
      "question": "Error Generating Quiz",
      "option1": "Sorry",
      "option2": "Sorry",
      "option3": "Sorry",
      "correct_answer": "Sorry"
    }
  ]
}'''

    async def generate_question_chat_response(
        self, 
        question_text: str, 
        question_solution: str, 
        student_query: str,
        practice_mode: Optional[str] = None,
        subject: Optional[str] = None
    ) -> str:
        """Generate a response to a student's question about a math problem."""
        try:
            # Build the prompt with all the context
            prompt = f"""
A student is working on this math problem and has a question.

PROBLEM:
{question_text}

STEP-BY-STEP SOLUTION (for your reference only - don't reveal this directly):
{question_solution}

STUDENT'S QUESTION:
{student_query}

Please provide a helpful, educational response that:
1. Addresses the student's specific question
2. Guides them towards understanding without giving away the answer
3. Uses simple, clear language appropriate for a 10th grade student
4. If they're stuck, provide a hint or ask a guiding question
5. If they're asking about a concept, explain it clearly with examples
6. Keep the response concise (1-2 paragraphs maximum)

Remember: You're a tutor helping them learn, not just giving answers.
"""

            # Add context about practice mode and subject if available
            if practice_mode:
                prompt += f"\nContext: This is a {practice_mode} problem"
            if subject:
                prompt += f" in {subject}."
            
            print(f"Sending question chat prompt to Gemini")
            response = self.question_chat_model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating question chat response: {e}")
            return "I'm sorry, I encountered an error while processing your question. Please try again or rephrase your question."

    async def generate_tutor_response(
        self,
        query: str,
        messages: List[Dict[str, str]],
        include_drawing_commands: bool = True,
        canvas_image: Optional[str] = None
    ) -> Dict:
        """Generate an AI tutor response with optional drawing commands for the whiteboard."""
        try:
            # Build conversation history
            conversation = "Previous conversation:\n"
            for msg in messages[-5:]:  # Last 5 messages for context
                conversation += f"{msg['role'].upper()}: {msg['content']}\n"
            
            # Create content parts for the prompt
            content_parts = []
            
            # Create the prompt
            prompt = f"""
{conversation}

STUDENT: {query}

You MUST respond with ONLY a valid JSON object as noted in the system instructions. Be specific and helpful in your response!
"""
            
            content_parts.append(prompt)
            
            # Add canvas image if provided
            if canvas_image:
                try:
                    print(f"Canvas image received, length: {len(canvas_image)}")
                    
                    # Remove data URL prefix if present
                    if canvas_image.startswith('data:image'):
                        canvas_image = canvas_image.split(',')[1]
                    
                    # Decode base64 image
                    image_data = base64.b64decode(canvas_image)
                    print(f"Decoded image data length: {len(image_data)}")
                    
                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_data))
                    print(f"PIL Image size: {pil_image.size}, mode: {pil_image.mode}")
                    content_parts.append(pil_image)
                    print("Canvas image successfully added to content parts")
                    
                except Exception as e:
                    print(f"Error processing canvas image: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("No canvas image provided in request")
            
            # Generate response
            response = self.tutor_model.generate_content(content_parts)
            print(f"RESPONSE: {response.text}")
            response_text = response.text.strip()
            
            # Parse JSON response
            try:
                # Clean up markdown if present
                if response_text.startswith('```'):
                    # Find the end of the code block
                    end_index = response_text.rfind('```')
                    if end_index > 3:
                        response_text = response_text[3:end_index]
                    if response_text.startswith('json'):
                        response_text = response_text[4:]
                    response_text = response_text.strip()
                
                print(f"Attempting to parse JSON response: {response_text[:200]}...")
                result = json.loads(response_text)
                
                # Ensure required fields exist and normalize field names
                if 'response' not in result:
                    result['response'] = "I'm here to help! Could you please clarify your question?"
                
                # Handle both 'drawing_commands' and 'drawingCommands'
                if 'drawing_commands' not in result and 'drawingCommands' not in result:
                    result['drawing_commands'] = []
                
                print(f"Successfully parsed response with {len(result.get('drawing_commands', []))} drawing commands")
                return result
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Failed to parse: {response_text[:500]}...")
                
                # Try to extract a meaningful response
                if "I'll help you" in response_text or "Let me" in response_text:
                    # Extract the first paragraph as the response
                    lines = response_text.split('\n')
                    response_content = lines[0] if lines else response_text[:200]
                else:
                    response_content = "I can see you're working on a problem. Could you tell me specifically what you'd like help with? Would you like me to guide you through it, check your work, or explain a concept?"
                
                # Fallback if JSON parsing fails
                return {
                    "response": response_content,
                    "drawing_commands": []
                }
            
        except Exception as e:
            print(f"Error generating tutor response: {e}")
            return {
                "response": "I apologize, but I encountered an error. Please try rephrasing your question or let me know if you'd like me to solve it step-by-step, guide you through it, or check your work.",
                "drawing_commands": []
            }
    
    # New methods for multi-stage processing
    async def generate_simple_response(self, prompt: str, image: Optional[str] = None) -> Dict:
        """Generate a simple response for analysis and planning"""
        try:
            content_parts = [prompt]
            if image:
                try:
                    if image.startswith('data:image'):
                        image = image.split(',')[1]
                    image_data = base64.b64decode(image)
                    pil_image = Image.open(io.BytesIO(image_data))
                    content_parts.append(pil_image)
                except Exception as e:
                    print(f"Error processing image: {e}")
            
            response = self.analysis_model.generate_content(content_parts)
            response_text = response.text.strip()
            
            # Clean up markdown if present
            if response_text.startswith('```'):
                end_index = response_text.rfind('```')
                if end_index > 3:
                    response_text = response_text[3:end_index]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error in simple response: {e}")
            return {}
    
    async def generate_text_only(self, prompt: str, visual: bool = False) -> str:
        """Generate text-only response for teaching"""
        try:
            if visual: response = self.determine_necessary_visual_model.generate_content(prompt)
            if not visual: response = self.text_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating text response: {e}")
            return "I'm here to help! Could you please clarify your question?"
    
    async def generate_comparison_text_response(self, prompt: str, image1: str, image2: str) -> str:
        """Generate text response comparing two canvas images"""
        try:
            content_parts = [prompt]
            
            # Process first image (previous state)
            try:
                if image1.startswith('data:image'):
                    image1 = image1.split(',')[1]
                image1_data = base64.b64decode(image1)
                pil_image1 = Image.open(io.BytesIO(image1_data))
                content_parts.append("Previous canvas state:")
                content_parts.append(pil_image1)
            except Exception as e:
                print(f"Error processing previous image: {e}")
            
            # Process second image (current state)
            try:
                if image2.startswith('data:image'):
                    image2 = image2.split(',')[1]
                image2_data = base64.b64decode(image2)
                pil_image2 = Image.open(io.BytesIO(image2_data))
                content_parts.append("Current canvas state (with student's new annotations):")
                content_parts.append(pil_image2)
            except Exception as e:
                print(f"Error processing current image: {e}")
            
            response = self.text_model.generate_content(content_parts)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error in comparison text response: {e}")
            return "I can see you've made some annotations! Could you tell me more about what you'd like help with?"
    
        
    
    
    async def generate_drawing_commands_only(self, prompt: str) -> List[Dict]:
        """Generate drawing commands only"""
        try:
            response = self.visual_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up markdown if present
            if response_text.startswith('```'):
                end_index = response_text.rfind('```')
                if end_index > 3:
                    response_text = response_text[3:end_index]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error generating drawing commands: {e}")
            return []
    
    async def generate_comparison_response(self, prompt: str, image1: str, image2: str) -> Dict:
        """Generate response comparing two images"""
        try:
            content_parts = [prompt]
            
            # Process first image
            try:
                if image1.startswith('data:image'):
                    image1 = image1.split(',')[1]
                image1_data = base64.b64decode(image1)
                pil_image1 = Image.open(io.BytesIO(image1_data))
                content_parts.append(pil_image1)
            except Exception as e:
                print(f"Error processing image1: {e}")
            
            # Process second image
            try:
                if image2.startswith('data:image'):
                    image2 = image2.split(',')[1]
                image2_data = base64.b64decode(image2)
                pil_image2 = Image.open(io.BytesIO(image2_data))
                content_parts.append(pil_image2)
            except Exception as e:
                print(f"Error processing image2: {e}")
            
            response = self.analysis_model.generate_content(content_parts)
            response_text = response.text.strip()
            
            # Clean up markdown if present
            if response_text.startswith('```'):
                end_index = response_text.rfind('```')
                if end_index > 3:
                    response_text = response_text[3:end_index]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error in comparison response: {e}")
            return {}
    
    async def generate_svg_content(self, prompt: str, canvas_image: Optional[str] = None) -> Optional[str]:
        """Generate SVG content for educational visualizations"""
        try:
            content_parts = [prompt]
            
            # Add canvas image if provided
            if canvas_image:
                try:
                    if canvas_image.startswith('data:image'):
                        canvas_image = canvas_image.split(',')[1]
                    image_data = base64.b64decode(canvas_image)
                    pil_image = Image.open(io.BytesIO(image_data))
                    content_parts.append(pil_image)
                except Exception as e:
                    print(f"Error processing canvas image for SVG generation: {e}")
            
            response = self.svg_model.generate_content(content_parts)
            response_text = response.text.strip()
            
            # Clean up markdown if present
            if response_text.startswith('```'):
                end_index = response_text.rfind('```')
                if end_index > 3:
                    response_text = response_text[3:end_index]
                if response_text.startswith('svg') or response_text.startswith('xml'):
                    # Remove language identifier
                    lines = response_text.split('\n')
                    response_text = '\n'.join(lines[1:])
                response_text = response_text.strip()
            
            # Validate that response contains SVG
            if not response_text.startswith('<svg') or not response_text.endswith('</svg>'):
                print(f"Invalid SVG response: {response_text[:100]}...")
                return None
            
            return response_text
            
        except Exception as e:
            print(f"Error generating SVG content: {e}")
            return None

