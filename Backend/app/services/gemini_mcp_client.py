"""
Gemini MCP Client
Uses Gemini's function calling to make intelligent decisions using MCP tools.
"""
import os
import google.generativeai as genai
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import json
from .education_mcp_server import EducationMCPServer

load_dotenv()


class GeminiMCPClient:
    """
    Client that uses Gemini with function calling to interact with MCP tools.

    Gemini decides which tools to call and when, based on the task at hand.
    This is the "intelligence layer" that orchestrates tool usage.
    """

    def __init__(self, mcp_server: EducationMCPServer):
        self.mcp_server = mcp_server

        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        genai.configure(api_key=api_key)

        # Convert MCP tools to Gemini function declarations
        gemini_tools = self._convert_tools_to_gemini_format()

        # Create model with function calling capabilities
        self.model = genai.GenerativeModel(
            'gemini-2.5-flash-preview-05-20',
            tools=gemini_tools,
            system_instruction="""You are an adaptive learning assistant that helps select optimal practice questions for students.

Your task is to:
1. Understand the student's current knowledge state using available tools
2. Identify what they should practice next based on their performance
3. Find appropriate questions at optimal difficulty
4. Explain your reasoning clearly

Available tools allow you to:
- Get student profiles and knowledge levels
- Search for questions by skill and difficulty
- Analyze recent performance patterns
- Calculate optimal difficulty (Zone of Proximal Development)
- Identify prerequisite skill gaps
- Predict success probability

Decision-making principles:
- If student is struggling (low accuracy), identify gaps and provide easier practice
- If student is excelling (high accuracy), increase challenge gradually
- Balance between confidence-building and stretching abilities
- Consider prerequisite skills before advancing to harder topics

IMPORTANT: When you've selected the best question, respond with JSON in this exact format:
{
  "question_id": <id>,
  "reasoning": "<clear explanation of why this question is optimal>",
  "learning_objective": "<what skill this develops>",
  "tools_used": ["<list of tools you called>"],
  "difficulty_rationale": "<why this difficulty level>"
}"""
        )

        print("✅ GeminiMCPClient initialized with function calling")

    def _convert_tools_to_gemini_format(self) -> List:
        """
        Convert MCP tool schema to Gemini function declaration format.

        Gemini uses a specific format for function declarations.
        """
        mcp_tools = self.mcp_server.get_tools_schema()

        gemini_function_declarations = []

        for tool in mcp_tools:
            function_declaration = genai.protos.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        param_name: genai.protos.Schema(
                            type=self._get_gemini_type(param_info.get("type", "string")),
                            description=param_info.get("description", "")
                        )
                        for param_name, param_info in tool["parameters"]["properties"].items()
                    },
                    required=tool["parameters"].get("required", [])
                )
            )
            gemini_function_declarations.append(function_declaration)

        # Wrap in Tool object
        return [genai.protos.Tool(function_declarations=gemini_function_declarations)]

    def _get_gemini_type(self, json_type: str):
        """Map JSON schema types to Gemini types"""
        type_mapping = {
            "string": genai.protos.Type.STRING,
            "integer": genai.protos.Type.INTEGER,
            "number": genai.protos.Type.NUMBER,
            "boolean": genai.protos.Type.BOOLEAN,
            "object": genai.protos.Type.OBJECT,
            "array": genai.protos.Type.ARRAY
        }
        return type_mapping.get(json_type, genai.protos.Type.STRING)

    async def find_next_question(
        self,
        user_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use Gemini with MCP tools to find the optimal next question.

        This is the main method that orchestrates the entire decision-making process.

        Args:
            user_id: Student's user ID
            context: Additional context (last question, performance, etc.)

        Returns:
            Dict with selected question and reasoning
        """
        try:
            # Build initial prompt for Gemini
            prompt = self._build_initial_prompt(user_id, context)

            print(f"\n🔵 Sending initial prompt to Gemini...")
            print(f"Prompt: {prompt}\n")

            # Start conversation with Gemini
            chat = self.model.start_chat(enable_automatic_function_calling=True)

            # Send initial message
            response = await chat.send_message_async(prompt)

            # Track tools used for debugging
            tools_used = []

            # Gemini may make multiple function calls before responding
            # We need to handle the conversation loop
            max_iterations = 10
            iteration = 0

            while iteration < max_iterations:
                print(f"\n📍 Iteration {iteration + 1}")

                # Check if Gemini wants to call functions
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        # Check if this part is a function call
                        if hasattr(part, 'function_call') and part.function_call:
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = dict(function_call.args)

                            print(f"🔧 Gemini calling tool: {function_name}")
                            print(f"   Arguments: {json.dumps(function_args, indent=2)}")

                            # Execute the tool
                            tool_result = self.mcp_server.execute_tool(
                                function_name,
                                function_args
                            )

                            print(f"   ✅ Tool result: {json.dumps(tool_result, indent=2)[:300]}...")

                            tools_used.append(function_name)

                            # Send tool result back to Gemini
                            function_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": tool_result}
                                )
                            )

                            # Continue conversation with tool result
                            response = await chat.send_message_async(function_response)
                            iteration += 1
                            continue

                        # Check if this part contains text (Gemini's final answer)
                        elif hasattr(part, 'text') and part.text:
                            print(f"\n✅ Gemini provided final answer:")
                            print(f"{part.text}\n")

                            # Parse the response
                            return self._parse_final_response(
                                part.text,
                                tools_used,
                                user_id
                            )

                # If we got here, no more function calls and no text
                # Try to get response text
                try:
                    final_text = response.text
                    return self._parse_final_response(final_text, tools_used, user_id)
                except:
                    break

            # Max iterations reached
            print(f"⚠️  Max iterations ({max_iterations}) reached")
            return {
                "error": "Could not determine next question within iteration limit",
                "tools_used": tools_used
            }

        except Exception as e:
            print(f"❌ Error in find_next_question: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": str(e),
                "fallback_question_id": 101  # Fallback to first question
            }

    def _build_initial_prompt(self, user_id: int, context: Dict) -> str:
        """Build the initial prompt for Gemini"""

        # Extract context information
        last_question_id = context.get("last_question_id")
        was_correct = context.get("correct", False)
        time_spent = context.get("time_spent")
        session_id = context.get("session_id")

        prompt_parts = [
            f"Find the optimal next practice question for student ID {user_id}."
        ]

        if last_question_id:
            prompt_parts.append(f"\nContext:")
            prompt_parts.append(f"- Just completed question ID: {last_question_id}")
            prompt_parts.append(f"- Result: {'✓ Correct' if was_correct else '✗ Incorrect'}")

            if time_spent:
                prompt_parts.append(f"- Time spent: {time_spent} seconds")

        prompt_parts.append("\nYour task:")
        prompt_parts.append("1. Use available tools to understand this student's knowledge state")
        prompt_parts.append("2. Determine what they should practice next")
        prompt_parts.append("3. Find an appropriate question at optimal difficulty")
        prompt_parts.append("4. Return your selection with clear reasoning")

        prompt_parts.append("\nIMPORTANT: Call any tools you need, then respond with JSON in this format:")
        prompt_parts.append("""{
  "question_id": <number>,
  "reasoning": "<why this question is best>",
  "learning_objective": "<what skill this develops>",
  "tools_used": <list of tools you called>,
  "difficulty_rationale": "<why this difficulty level>"
}""")

        return "\n".join(prompt_parts)

    def _parse_final_response(
        self,
        response_text: str,
        tools_used: List[str],
        user_id: int
    ) -> Dict:
        """Parse Gemini's final response into structured format"""
        try:
            # Clean up the response text
            cleaned_text = response_text.strip()

            # Remove markdown code blocks if present
            if cleaned_text.startswith("```"):
                # Find the actual JSON content
                lines = cleaned_text.split("\n")
                json_lines = []
                in_json = False

                for line in lines:
                    if line.startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json or (line.strip().startswith("{") or json_lines):
                        json_lines.append(line)

                cleaned_text = "\n".join(json_lines).strip()

            # Try to parse as JSON
            try:
                parsed_response = json.loads(cleaned_text)

                # Validate required fields
                if "question_id" in parsed_response:
                    # Add tools_used if not present
                    if "tools_used" not in parsed_response:
                        parsed_response["tools_used"] = tools_used

                    return parsed_response
                else:
                    print("⚠️  Response missing question_id field")

            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing failed: {e}")
                print(f"Response text: {cleaned_text[:200]}...")

                # Try to extract question_id from text
                import re
                question_id_match = re.search(r'"question_id":\s*(\d+)', cleaned_text)
                if question_id_match:
                    question_id = int(question_id_match.group(1))
                    return {
                        "question_id": question_id,
                        "reasoning": "Extracted from partial response",
                        "learning_objective": "Continue practice",
                        "tools_used": tools_used,
                        "raw_response": cleaned_text
                    }

            # Fallback: return a default question
            print("⚠️  Using fallback question")
            return {
                "question_id": 101,
                "reasoning": "Fallback: Could not parse Gemini response, using default question",
                "learning_objective": "Basic quadratic equations practice",
                "tools_used": tools_used,
                "raw_response": cleaned_text
            }

        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return {
                "question_id": 101,
                "error": str(e),
                "tools_used": tools_used
            }
