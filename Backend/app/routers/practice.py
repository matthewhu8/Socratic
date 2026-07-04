import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_student
from ..database.database import get_db
from ..database.models import StudentUser
from ..services.education_mcp_server import EducationMCPServer
from ..services.gemini_mcp_client import GeminiMCPClient

router = APIRouter()

# ==================== MCP-POWERED SMART PRACTICE ====================

class SmartPracticeRequest(BaseModel):
    last_question_id: Optional[int] = None
    correct: Optional[bool] = None
    time_spent: Optional[int] = None
    session_id: Optional[str] = None

@router.post("/api/smart-practice/next-question-mcp")
async def get_next_question_mcp(
    request: SmartPracticeRequest,
    current_user: StudentUser = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    MCP-Powered Smart Practice: Gemini intelligently selects next question.

    This endpoint demonstrates MCP (Model Context Protocol) where:
    1. Gemini acts as the decision engine
    2. MCP Server provides educational tools
    3. Gemini decides which tools to call and when
    4. Returns optimal question with reasoning
    """
    try:
        print("\n" + "="*60)
        print("🚀 MCP-POWERED SMART PRACTICE REQUEST")
        print("="*60)

        # Initialize MCP server and Gemini client
        mcp_server = EducationMCPServer(db)
        gemini_client = GeminiMCPClient(mcp_server)

        # Build context for Gemini
        context = {
            "user_id": current_user.id,
            "last_question_id": request.last_question_id,
            "correct": request.correct,
            "time_spent": request.time_spent,
            "session_id": request.session_id or f"session_{int(time.time())}"
        }

        print(f"👤 User ID: {current_user.id}")
        print(f"📋 Context: {json.dumps(context, indent=2)}")

        # Let Gemini + MCP decide the next question
        print("\n🧠 Asking Gemini to find optimal next question...")
        result = await gemini_client.find_next_question(
            user_id=current_user.id,
            context=context
        )

        print(f"\n✅ Gemini's decision:")
        print(json.dumps(result, indent=2))

        # Check for errors
        if "error" in result:
            # Return fallback question
            print(f"⚠️  Error occurred, using fallback")
            question_id = result.get("fallback_question_id", 101)
        else:
            question_id = result.get("question_id")

        # Fetch the actual question from database
        # For now, return mocked question data since we're using mocked tools
        mocked_questions = {
            101: {
                "id": 101,
                "question_text": "Solve for x: x² + 5x + 6 = 0",
                "difficulty": 0.4,
                "topic": "Quadratic Equations",
                "skill": "solving_by_factoring"
            },
            102: {
                "id": 102,
                "question_text": "Find the roots of 2x² - 7x + 3 = 0 using the quadratic formula",
                "difficulty": 0.6,
                "topic": "Quadratic Equations",
                "skill": "quadratic_formula"
            },
            103: {
                "id": 103,
                "question_text": "Solve by completing the square: x² + 8x - 9 = 0",
                "difficulty": 0.7,
                "topic": "Quadratic Equations",
                "skill": "completing_the_square"
            },
            104: {
                "id": 104,
                "question_text": "Find the 10th term of the AP: 5, 9, 13, 17, ...",
                "difficulty": 0.3,
                "topic": "Arithmetic Progressions",
                "skill": "finding_nth_term"
            },
            105: {
                "id": 105,
                "question_text": "Find the sum of first 20 terms of AP: 2, 5, 8, 11, ...",
                "difficulty": 0.5,
                "topic": "Arithmetic Progressions",
                "skill": "sum_of_terms"
            }
        }

        question = mocked_questions.get(question_id, mocked_questions[101])

        print(f"\n📖 Returning question: {question['question_text']}")
        print("="*60 + "\n")

        return {
            "status": "success",
            "question": question,
            "mcp_decision": {
                "reasoning": result.get("reasoning", "No reasoning provided"),
                "learning_objective": result.get("learning_objective", "Practice"),
                "tools_used": result.get("tools_used", []),
                "difficulty_rationale": result.get("difficulty_rationale", "")
            },
            "session_id": context["session_id"]
        }

    except Exception as e:
        print(f"\n❌ ERROR in MCP endpoint: {e}")
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to get next question: {str(e)}"
        )
