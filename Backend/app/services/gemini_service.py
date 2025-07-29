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
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20', 
            system_instruction="""You are a helpful English AI assistant to answer students' questions about this YouTube video. 
            Please answer in English. The student may also be referencing a specific part from the video transcript around their current video timestamp. 
            The image attached shows the video at the point where the student is currently watching the video. 
            Use your best judgement when using the image to help you answer their question.
            
            STYLE & LENGTH:
• Keep each response concise—ideally. No more than 120 words maximum, the shorter the better.
• Explain in simple and efficient language, don't over talk. 
• Skip filler; dive straight into substance. Do not use asteriks. If the student is struggling with the subject, explain with short and to-the-point example. 
            """)
        self.video_quiz_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="You are quiz maker that will test the student's retention of the video. The query will contain a video transcript and a list of their previous messages, create questions in JSON format that tests the user on general subject matter related concepts discussed in the transcript, and place a particular emphasis on the topics the student seemed to be confused about based on the chatlog. Make 5 total questions.")
        self.photo_grading_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="You are a detailed oriented CBSE style grader for 10th grade math questions. Utilize the attached question and 'solution' to ensure the student's work is fully correct. The student's work will be provided in the query as a photo. Please provide your response in the JSON format shown in the prompt. Do no hesitate to leave fields blank if there are no comments needed. ")
        self.question_chat_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20', system_instruction="The student is asking a question about a math problem. Return a short response to the question, addressing the student's concerns and explaining the concept in a simple, understandable way if possible. The student's question will be provided in the query. The math problem will be provided in the query. We will provide the step-by-step solution to the problem in the query but blatantly reveal the solution, it is only so you don't give out incorrect information and guide the student towards the correct path.")
        
        # Optimized text model with enhanced system instructions
        self.text_model = genai.GenerativeModel(
            'gemini-1.5-pro', 
            system_instruction="""You are Socratic‑Tutor, a fast, patient math coach who provides concise explanations.

STYLE & LENGTH:
• Keep each response concise—ideally ≤ 200 words / 25 seconds of speech
• Include at most one guiding question per turn
• Skip filler; dive straight into substance. Do not use asteriks. 


TEACHING APPROACH:
• For new problems:
  1. Copy or paraphrase the question
  2. List givens / knowns (e.g., a = …, b = …, n = …)
  3. Show a skeleton of the relevant formula
  4. Invite the student to supply missing pieces
• For ongoing problems:
  • Confirm or gently correct student work
  • Reveal only the next step if student is stuck
  • Give the full answer only when explicitly requested
• Acknowledge specific student marks when helpful
• Focus on understanding, not just answers""",
            generation_config=genai.GenerationConfig(
                temperature=0.35,
                top_p=0.9,
                max_output_tokens=500
            )
        )
         
        # Optimized SVG model with comprehensive system instructions and generation config
        # Optimized SVG model with comprehensive system instructions and generation config
        self.svg_model = genai.GenerativeModel(
            'gemini-1.5-pro',
            system_instruction="""You create educational SVG visualizations for math tutoring.

TECHNICAL SPECIFICATIONS:
• viewBox STRICTLY "0 0 600 400"
• Colours (tutor only):
    #2563eb  new concept / neutral text
    #16a34a  correct confirmation
    #dc2626  highlight an error
  Student strokes are always black (#000000); tutor must NEVER draw in black
• Font: Arial 16px or 18px, text-anchor="start"

OUTPUT RULES:
• Output ONLY valid SVG markup
• Start with <svg> tag, end with </svg> tag
• No explanations or text outside SVG tags
• Keep drawings simple—use blank boxes □, ellipses … or arrows ⬇︎ to reserve space
• Do NOT draw rigid dashed rectangles that confine student work
• Never erase or overwrite student ink; add beside or below it
• Do not show the complete numeric/expanded answer unless explicitly requested

INTERPRETING THE CANVAS:
• You receive a full-image PNG of the current board each turn
• Acknowledge specific student marks when helpful
• If uncertain what a drawing is, suggest a clarification

SELF-CHECK BEFORE SENDING:
• Valid XML that fits the viewBox
• Using only tutor colors (#2563eb, #16a34a, #dc2626), NEVER black
• No spoilers: full answers hidden unless requested""",
            generation_config=genai.GenerationConfig(
                temperature=0.3,  # More consistent output
                top_p=0.8,
                max_output_tokens=1200,
                response_mime_type="text/plain"
            )
        )
        
        # Keep existing tutor model for backward compatibility
        self.tutor_model = genai.GenerativeModel(
                'gemini-2.5-flash-preview-05-20',
                system_instruction="""You are a math tutor. Respond with JSON containing 'response' and 'drawing_commands' fields."""
            )
        
        sally_response_schema = {
    "type": "object",
    "properties": {
        "response": {"type": "string"},
        "svgContent": {"type": "string"}
    },
    "required": ["response", "svgContent"]
}
        
        # Combined model for single-prompt AI tutor (new approach)
        self.combined_model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20',
            system_instruction="""OUTPUT ONLY VALID JSON. No text before or after the JSON object. Svg mark must go in the svgContent field. No exceptions.

You are Socratic‑Tutor, a fast, patient math coach who can DRAW on a shared
whiteboard and SPEAK concise explanations.  The student sees and hears each
response in real time. 

────────────────  OUTPUT CONTRACT  ────────────────
• Your ENTIRE response must be a single JSON object - nothing else
• Output EXACTLY this JSON structure:
  {
    "response":    "<tutor's spoken/written line>",
    "svgContent":  "<complete SVG markup>"  // or null when no drawing needed
  }
• Do NOT include any explanatory text outside the JSON
• Do NOT wrap the JSON in markdown code blocks
• Just output the raw JSON object

────────────────  STYLE & LENGTH  ────────────────
• Keep each "response" concise—ideally ≤ 200 words / 25 seconds of speech.  
• Include **at most one guiding question** (hence ≤ 1 "?") per turn.  
• Skip filler such as "Let's break this down"; dive straight into substance.

────────────────  TEACHING FLOW  ────────────────
★ FIRST RESPONSE for any new problem  
  1. Copy or paraphrase the question on the board.  
  2. List givens / knowns (e.g., a = …, b = …, n = …).  
  3. Show a skeleton of the relevant formula with blank spaces or boxes.  
  4. Invite the student to supply the missing pieces (≤ 1 question).

★ SUBSEQUENT RESPONSES  
  • Confirm or gently correct student work.  
  • Reveal only the next step if the student is stuck.  
  • Give the full answer only when explicitly requested.

────────────────  VISUAL RULES  ────────────────
• viewBox **strictly** "0 0 600 400".  
• Colours (tutor only):  
    #2563eb  new concept / neutral text  
    #16a34a  correct confirmation  
    #dc2626  highlight an error  
  Student strokes are always **black (#000000)**; tutor must never draw in black.  
• Font: **strictly** Arial 24px, text‑anchor="start".  
• Keep drawings simple—use blank boxes □, ellipses … or arrows ⬇︎ to reserve
  space. Do **not** draw rigid dashed rectangles that confine student work.  
• Never erase or overwrite student ink; add beside or below it.

────────────────  ANSWER‑HIDING POLICY  ────────────────
• Do not show the complete numeric/expanded answer in `svgContent`
  unless the student explicitly asks for it.

────────────────  INTERPRETING THE CANVAS IMAGE  ────────────────
• You receive a full‑image PNG of the current board each turn.  
• Acknowledge specific student marks when helpful.  
• If uncertain what a drawing is, ask a clarifying question.

────────────────  SELF‑CHECK BEFORE SENDING  ────────────────
1. JSON has exactly the two required keys.  
2. SVG (if present) is valid XML and fits the viewBox.  
3. "response" is concise (≈ ≤ 25 s) and has ≤ 1 "?".  
4. Tutor colours only (#2563eb, #16a34a, #dc2626); no black ink from tutor.  
5. No spoilers: full answers hidden unless requested.  
If any check fails, silently fix and re‑emit.

────────────────  FEW‑SHOT EXAMPLES  ────────────────
Example A — first turn for a binomial expansion  
{
  "response": "In (2x + 1)⁴ our givens are a = 2x, b = 1, n = 4. Which row of Pascal's triangle gives those coefficients?",
  "svgContent": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 600 400\"> \
    <text x=\"25\" y=\"35\" fill=\"#2563eb\" font-family=\"Arial\" font-size=\"24px\">Expand (2x + 1)<tspan dy=\"-5\" font-size=\"11px\">4</tspan> in descending powers of x.</text> \
    <text x=\"25\" y=\"75\" fill=\"#2563eb\" font-family=\"Arial\" font-size=\"24px\">Given: a = 2x,  b = 1,  n = 4</text> \
    <text x=\"25\" y=\"115\" fill=\"#2563eb\" font-family=\"Arial\" font-size=\"24px\">(a + b)<tspan dy=\"-5\" font-size=\"11px\">n</tspan> = Σ C<tspan dy=\"5\" font-size=\"11px\">n</tspan><tspan dy=\"-5\" font-size=\"11px\">k</tspan> a<tspan dy=\"-5\" font-size=\"11px\">n−k</tspan> b<tspan dy=\"-5\" font-size=\"11px\">k</tspan></text> \
    <rect x=\"155\" y=\"137\" width=\"34\" height=\"25\" fill=\"none\" stroke=\"#2563eb\" stroke-width=\"2\"/> \
    <text x=\"195\" y=\"155\" fill=\"#2563eb\" font-family=\"Arial\" font-size=\"24px\">(2x)<tspan dy=\"-5\" font-size=\"11px\">4</tspan> + …</text> \
    <text x=\"25\" y=\"205\" fill=\"#2563eb\" font-family=\"Arial\" font-size=\"24px\">Pascal's Triangle — draw row n = 4 anywhere below ⬇︎</text> \
    <text x=\"285\" y=\"230\" fill=\"#2563eb\" font-family=\"Arial\" font-size=\"24px\">⬇︎</text> \
  </svg>"
}

Example B — correcting an exponent  
{
  "response": "Check that exponent—you wrote 3; should it be 4?",
  "svgContent": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 600 400\"> \
    <line x1=\"100\" y1=\"80\" x2=\"130\" y2=\"80\" stroke=\"#dc2626\" stroke-width=\"2\"/> \
    <text x=\"135\" y=\"85\" fill=\"#dc2626\" font-family=\"Arial\" font-size=\"24px\">← exponent should be 4</text> \
  </svg>"
}""",
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                top_p=0.4,
                max_output_tokens=1000,
                response_mime_type="application/json",
                response_schema=sally_response_schema
            )
        )
        
        print(f"GEMINI MODEL: {self.combined_model}")
    
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
        """Generate SVG content for educational visualizations (legacy method)"""
        """Generate SVG content for educational visualizations (legacy method)"""
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
    
    async def generate_svg_with_chat_history(self, query: str, teaching_response: str, 
                                           chat_history: List[Dict], canvas_image: Optional[str] = None) -> Optional[str]:
        """Generate SVG content using chat history for context (optimized method)"""
        try:
            # Convert chat history to Gemini format (only recent messages)
            formatted_history = []
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            
            for msg in recent_history:
                role = "user" if msg.get("role") == "user" else "model"
                formatted_history.append({
                    "role": role,
                    "parts": [msg.get("content", "")]
                })
            
            # Start chat with history pre-loaded
            chat = self.svg_model.start_chat(history=formatted_history)
            
            # MINIMAL prompt - all rules are in system instruction
            minimal_prompt = f"Create visual for: {teaching_response}\n Student's original question: {query}"
            
            # Prepare content parts
            content_parts = [minimal_prompt]
            
            # Add canvas image if provided
            if canvas_image:
                try:
                    if canvas_image.startswith('data:image'):
                        canvas_image = canvas_image.split(',')[1]
                    image_data = base64.b64decode(canvas_image)
                    pil_image = Image.open(io.BytesIO(image_data))
                    content_parts.append(pil_image)
                except Exception as e:
                    print(f"Error processing canvas image for optimized SVG generation: {e}")
            
            # Send minimal prompt to chat session
            response = await chat.send_message_async(content_parts)
            response_text = response.text.strip()
            
            # Clean up markdown if present
            if response_text.startswith('```'):
                end_index = response_text.rfind('```')
                if end_index > 3:
                    response_text = response_text[3:end_index]
                if response_text.startswith('svg') or response_text.startswith('xml'):
                    lines = response_text.split('\n')
                    response_text = '\n'.join(lines[1:])
                response_text = response_text.strip()
            
            # Validate that response contains SVG
            if not response_text.startswith('<svg') or not response_text.endswith('</svg>'):
                print(f"Invalid SVG response from optimized method: {response_text[:100]}...")
                return None
            
            return response_text
            
        except Exception as e:
            print(f"Error in optimized SVG generation: {e}")
            # Fallback to original method
            print("Falling back to original SVG generation method")
            return await self.generate_svg_content(
                f"Create visual for: {query}\nTeaching context: {teaching_response}",
                canvas_image
            )
    

    # New combined approach methods
    async def generate_combined_response(
        self, 
        query: str, 
        canvas_image: Optional[str] = None,
        chat_history: List[Dict] = None,
        previous_canvas_image: Optional[str] = None,
        has_annotation: bool = False
    ) -> Dict[str, str]:
        """Generate combined teaching response and SVG content in a single call."""
        try:
            # Convert chat history to Gemini format
            formatted_history = []
            if chat_history:
                recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
                for msg in recent_history:
                    role = "user" if msg.get("role") == "user" else "model"
                    formatted_history.append({
                        "role": role,
                        "parts": [msg.get("content", "")]
                    })
            
            # Start chat with history pre-loaded
            chat = self.combined_model.start_chat(history=formatted_history)
            
            # Build prompt based on annotation context
            if has_annotation and previous_canvas_image and canvas_image:
                annotation_context = "IMPORTANT: The student has made new annotations/drawings on the whiteboard since our last interaction. Two images are provided - the previous state and current state. The student is likely referencing their new markings when asking this question. Pay close attention to what they've added."
                prompt = f"Student asks: \"{query}\"\nCanvas: Has student annotations in black\n{annotation_context}\nProvide guidance."
            else:
                canvas_state = "Has student drawing" if canvas_image else "Empty"
                prompt = f"Student asks: \"{query}\"\nCanvas: {canvas_state}\nProvide guidance."
            
            # Prepare content parts
            content_parts = [prompt]
            
            # Add images if available
            if has_annotation and previous_canvas_image:
                try:
                    if previous_canvas_image.startswith('data:image'):
                        previous_canvas_image = previous_canvas_image.split(',')[1]
                    prev_image_data = base64.b64decode(previous_canvas_image)
                    prev_pil_image = Image.open(io.BytesIO(prev_image_data))
                    content_parts.append("Previous canvas state before the student drew anything:")
                    content_parts.append(prev_pil_image)
                except Exception as e:
                    print(f"Error processing previous canvas image: {e}")
            
            if canvas_image:
                try:
                    if canvas_image.startswith('data:image'):
                        canvas_image = canvas_image.split(',')[1]
                    image_data = base64.b64decode(canvas_image)
                    pil_image = Image.open(io.BytesIO(image_data))
                    if has_annotation:
                        content_parts.append("Current canvas state (with new annotations in black drawing):")
                    content_parts.append(pil_image)
                except Exception as e:
                    print(f"Error processing canvas image: {e}")

            content_parts.append('Respond exactly in this JSON format with no text outside the brackets: {"response": "[text response]","svgContent": "<svg [svg content] </svg>"}')
            
            # Send request to Gemini
            response = await chat.send_message_async(content_parts)
            raw_response = response.text.strip()
            print(f"\nraw response straight from the model: {raw_response}\n")
            
            # Parse and validate response
            return await self._parse_and_validate_combined_response(raw_response, query, canvas_image, chat_history)
            
        except Exception as e:
            print(f"Critical error in generate_combined_response: {e}")
            return {
                "response": "I'm sorry, I encountered an error. Please try again.",
                "svgContent": None
            }
    
    async def _parse_and_validate_combined_response(
        self, 
        raw_response: str, 
        original_query: str = None,
        canvas_image: Optional[str] = None,
        chat_history: List[Dict] = None
    ) -> Dict[str, str]:
        """Parse and validate the combined response, with retry logic for SVG errors."""
        try:
            # Try to parse as JSON
            parsed_response = json.loads(raw_response)
            
            # Validate required fields
            if "response" not in parsed_response:
                print("response not in the parsed response")
                raise ValueError("Missing required 'response' field")
            
            if "svgContent" in parsed_response and not parsed_response["svgContent"]:
                pass
                # 
            
            # Clean asterisks from the response text (for TTS)
            cleaned_response = self._remove_markdown_asterisks(parsed_response["response"])
            
            # Validate and process SVG content
            svg_content = parsed_response.get("svgContent")
            svg_content = self._validate_svg_content(svg_content)
            
            # If SVG validation failed, try to retry with error feedback
            if parsed_response.get("svgContent") and svg_content is None:
                print("SVG validation failed, attempting retry with error feedback")
                retry_response = await self._retry_with_svg_error_feedback(
                    raw_response, original_query, canvas_image, chat_history
                )
                if retry_response:
                    return retry_response
            print(f"parsed SVG: {svg_content}")
            return {
                "response": cleaned_response,
                "svgContent": svg_content
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {raw_response[:200]}...")
            
            # Try to extract JSON from plain text (handles text before JSON)
            extracted_json = self._extract_json_from_text(raw_response)
            if extracted_json:
                try:
                    print("Successfully extracted JSON from mixed text response")
                    parsed_response = json.loads(extracted_json)
                    
                    # Validate and return the extracted JSON
                    if "response" in parsed_response:
                        cleaned_response = self._remove_markdown_asterisks(parsed_response["response"])
                        svg_content = self._validate_svg_content(parsed_response.get("svgContent"))
                        return {
                            "response": cleaned_response,
                            "svgContent": svg_content
                        }
                except (json.JSONDecodeError, ValueError) as extract_error:
                    print(f"Failed to parse extracted JSON: {extract_error}")
            
            # Check if the response contains embedded JSON
            if "```json" in raw_response and "```" in raw_response:
                try:
                    # Extract JSON from markdown code block
                    start_idx = raw_response.find("```json") + 7
                    end_idx = raw_response.find("```", start_idx)
                    if start_idx > 7 and end_idx > start_idx:
                        json_content = raw_response[start_idx:end_idx].strip()
                        parsed_response = json.loads(json_content)
                        
                        # Validate and return the extracted JSON
                        if "response" in parsed_response:
                            cleaned_response = self._remove_markdown_asterisks(parsed_response["response"])
                            svg_content = self._validate_svg_content(parsed_response.get("svgContent"))
                            return {
                                "response": cleaned_response,
                                "svgContent": svg_content
                            }
                except (json.JSONDecodeError, ValueError) as extract_error:
                    print(f"Failed to extract embedded JSON: {extract_error}")
            
            # Fallback to text-only response
            cleaned_response = self._remove_markdown_asterisks(raw_response)
            return {
                "response": cleaned_response,
                "svgContent": None
            }
        except Exception as e:
            print(f"Error in response validation: {e}")
            return {
                "response": "I'm sorry, I encountered an error processing the response. Please try again.",
                "svgContent": None
            }
    
    def _validate_svg_content(self, svg_content) -> Optional[str]:
        """Validate SVG content format."""
        if not svg_content:
            return None
        
        svg_content = str(svg_content).strip()
        
        # Handle null/empty values
        if svg_content.lower() in ["null", "none", ""]:
            return None
        
        # Basic SVG format validation
        if not svg_content.startswith("<svg"):
            print(f"Invalid SVG format - doesn't start with <svg: {svg_content[:50]}...")
            return None
        
        if not svg_content.endswith("</svg>"):
            print(f"Invalid SVG format - doesn't end with </svg>: {svg_content[-50:]}")
            return None
        
        return svg_content
    
    def _extract_json_from_text(self, text: str) -> Optional[str]:
        """Extract JSON object from text that may contain non-JSON content before/after."""
        try:
            # Find the first opening brace
            start_idx = text.find('{')
            if start_idx == -1:
                return None
            
            # Track brace depth to find matching closing brace
            brace_depth = 0
            in_string = False
            escape_next = False
            end_idx = start_idx
            
            for i in range(start_idx, len(text)):
                char = text[i]
                
                # Handle string literals to avoid counting braces inside strings
                if not escape_next:
                    if char == '"' and not in_string:
                        in_string = True
                    elif char == '"' and in_string:
                        in_string = False
                    elif char == '\\' and in_string:
                        escape_next = True
                        continue
                else:
                    escape_next = False
                    continue
                
                # Count braces only outside of strings
                if not in_string:
                    if char == '{':
                        brace_depth += 1
                    elif char == '}':
                        brace_depth -= 1
                        if brace_depth == 0:
                            end_idx = i
                            break
            
            # Extract the JSON substring
            if brace_depth == 0 and end_idx > start_idx:
                json_str = text[start_idx:end_idx + 1]
                # Validate it's actually JSON by trying to parse it
                json.loads(json_str)
                return json_str
            
            return None
            
        except Exception as e:
            print(f"Error extracting JSON from text: {e}")
            return None
    
    def _remove_markdown_asterisks(self, text: str) -> str:
        """Remove leading and trailing asterisks from words while preserving multiplication asterisks."""
        if not text:
            return text
        
        # Split by spaces to get individual words
        words = text.split(' ')
        cleaned_words = []
        
        for word in words:
            if not word:  # Handle multiple spaces
                cleaned_words.append(word)
                continue
            
            # If word is just asterisks, remove it entirely
            if word == '*' or all(c == '*' for c in word):
                cleaned_words.append('')
                continue
                
            # Remove leading asterisks
            while word.startswith('*') and len(word) > 1:
                word = word[1:]
            
            # Remove trailing asterisks  
            while word.endswith('*') and len(word) > 1:
                word = word[:-1]
            
            cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
    async def _retry_with_svg_error_feedback(
        self, 
        original_response: str, 
        query: str,
        canvas_image: Optional[str] = None,
        chat_history: List[Dict] = None,
        max_retries: int = 2
    ) -> Optional[Dict[str, str]]:
        """Retry the request with error feedback when SVG generation fails."""
        try:
            for attempt in range(max_retries):
                print(f"SVG retry attempt {attempt + 1}/{max_retries}")
                
                # Build retry prompt with error feedback
                retry_prompt = f"""There was an error with your previous response. The SVG content was invalid or malformed.

Original query: {query}
Your previous response: {original_response}

Please fix the SVG content and respond again with valid JSON format:
{{
  "response": "your teaching response",
  "svgContent": "valid SVG markup or null"
}}

Make sure the SVG starts with <svg and ends with </svg>."""
                
                # Prepare content parts
                content_parts = [retry_prompt]
                if canvas_image:
                    try:
                        if canvas_image.startswith('data:image'):
                            canvas_image = canvas_image.split(',')[1]
                        image_data = base64.b64decode(canvas_image)
                        pil_image = Image.open(io.BytesIO(image_data))
                        content_parts.append(pil_image)
                    except Exception as e:
                        print(f"Error processing canvas image in retry: {e}")
                
                # Send retry request
                response = await self.combined_model.generate_content(content_parts)
                retry_raw_response = response.text.strip()
                
                try:
                    # Parse retry response
                    retry_parsed = json.loads(retry_raw_response)
                    if "response" in retry_parsed:
                        cleaned_response = self._remove_markdown_asterisks(retry_parsed["response"])
                        svg_content = self._validate_svg_content(retry_parsed.get("svgContent"))
                        return {
                            "response": cleaned_response,
                            "svgContent": svg_content
                        }
                except json.JSONDecodeError:
                    print(f"Retry attempt {attempt + 1} also failed JSON parsing")
                    continue
            
            print("All retry attempts failed")
            return None
            
        except Exception as e:
            print(f"Error in retry with SVG feedback: {e}")
            return None
    
    
