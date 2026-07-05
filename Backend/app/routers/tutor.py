import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pylatexenc.latex2text import LatexNodes2Text
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_student, get_current_user
from ..database.database import get_db
from ..database.models import AITutorSession, StudentUser
from ..service_instances import convo_service
from ..services.ai_whiteboard_orchestrator import AIWhiteboardOrchestrator
from ..services.knowledge_profile_service import KnowledgeProfileService
from ..services.providers.base import TutoringState

router = APIRouter()


class QuestionChatRequest(BaseModel):
    question_text: str
    question_solution: str
    student_query: str
    practice_mode: Optional[str] = None
    subject: Optional[str] = None

class QuestionChatResponse(BaseModel):
    response: str
    timestamp: str

@router.post("/api/question-chat", response_model=QuestionChatResponse)
async def question_chat(
    request: QuestionChatRequest,
    current_user = Depends(get_current_user)
):
    """Handle student questions about a problem they're solving."""
    try:
        # Log the request for debugging
        print(f"Question chat request from user {current_user.id}")
        print(f"Student query: {request.student_query}")

        # Generate response using Gemini
        response = await convo_service.gemini_service.generate_question_chat_response(
            question_text=request.question_text,
            question_solution=request.question_solution,
            student_query=request.student_query,
            practice_mode=request.practice_mode,
            subject=request.subject
        )

        return {
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        print(f"Error in question_chat endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )

# AI Tutor Endpoints
class AITutorSessionCreate(BaseModel):
    userId: int
    userName: str

class AITutorSessionResponse(BaseModel):
    sessionId: str
    roomUUID: str
    roomToken: str
    appIdentifier: str

class AITutorQueryRequest(BaseModel):
    sessionId: str
    query: str
    messages: List[Dict[str, str]]
    canvasImage: Optional[str] = None  # Grid-stamped base64 PNG of boardRegion (spec §1)
    boardRegion: Optional[Dict[str, float]] = None  # {x, y, width, height} capture frame
    boardElements: Optional[List[Dict[str, Any]]] = None  # symbolic board listing (spec §2)
    previousCanvasImage: Optional[str] = None  # DEPRECATED: accepted, ignored
    hasAnnotation: bool = False  # DEPRECATED: accepted, ignored
    mode: Optional[str] = "jess"  # DEPRECATED: accepted, ignored (Claude only)

@router.post("/api/ai-tutor/create-session", response_model=AITutorSessionResponse)
async def create_ai_tutor_session(
    session_data: AITutorSessionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new AI tutor whiteboard session."""
    try:
        import requests as req

        # Generate session ID
        session_id = f"tutor_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Get Agora credentials from environment
        app_identifier = os.getenv("AGORA_APP_IDENTIFIER", "your-app-identifier")

        # For development, we'll mock the response
        # In production, you would make actual API calls to Agora
        room_uuid = f"room_{uuid.uuid4().hex}"
        room_token = f"token_{uuid.uuid4().hex}"

        # Store session in database
        session_info = {
            "session_id": session_id,
            "user_id": current_user.id,
            "room_uuid": room_uuid,
            "created_at": datetime.utcnow().isoformat(),
            "messages": []
        }

        # Store in Redis for quick access
        convo_service.redis_client.setex(
            f"ai_tutor:{session_id}",
            3600,  # 1 hour TTL
            json.dumps(session_info)
        )

        return {
            "sessionId": session_id,
            "roomUUID": room_uuid,
            "roomToken": room_token,
            "appIdentifier": app_identifier
        }

    except Exception as e:
        print(f"Error creating AI tutor session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

l2t = LatexNodes2Text()

# Delay between draw SSE frames — the "being drawn by hand" reveal cadence (spec §5).
DRAW_FRAME_PACING_SECONDS = 0.15

def _sse_frame(event: str, data: Dict[str, Any]) -> str:
    """Build one SSE frame. ``data`` must serialize to single-line JSON (no raw newlines)."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _persist_ai_tutor_turn(
    db: Session,
    session_id: str,
    session_info: Dict[str, Any],
    messages: List[Dict[str, str]],
    display_response: str,
    new_state: TutoringState,
) -> None:
    """Persist the turn to Redis (source of truth) then mirror to the DB row.

    Redis is updated with the appended assistant message and the new tutoring_state.
    The DB mirror is best-effort: any failure is logged and swallowed so a DB hiccup
    never breaks the live stream (CONTRACTS.md "Persistence").
    """
    updated_messages = messages + [{"role": "assistant", "content": display_response}]
    session_info["messages"] = updated_messages
    session_info["tutoring_state"] = new_state.to_dict()
    convo_service.redis_client.setex(
        f"ai_tutor:{session_id}",
        3600,
        json.dumps(session_info),
    )

    try:
        row = (
            db.query(AITutorSession)
            .filter(AITutorSession.session_id == session_id)
            .first()
        )
        if row is None:
            row = AITutorSession(
                session_id=session_id,
                user_id=session_info.get("user_id"),
                room_uuid=session_info.get("room_uuid", ""),
            )
            db.add(row)

        row.chat_history = updated_messages
        row.session_summary = new_state.as_prompt_block()

        if new_state.current_misconception:
            misconceptions = list(row.identified_misconceptions or [])
            if not misconceptions or misconceptions[-1] != new_state.current_misconception:
                misconceptions.append(new_state.current_misconception)
            row.identified_misconceptions = misconceptions

        db.commit()
    except Exception as e:
        print(f"AI tutor DB mirror failed (Redis remains source of truth): {e}")
        try:
            db.rollback()
        except Exception:
            pass


@router.post("/api/ai-tutor/process-query")
async def process_ai_tutor_query(
    request: AITutorQueryRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Process a query from the AI tutor interface as an SSE stream.

    Streams ``text`` deltas, then one ``draw`` event per drawing action (paced ~150ms
    for the hand-drawn reveal), then a ``state`` event, then a terminal ``done`` (or
    ``error``) event. See CONTRACTS.md "SSE event schema" and
    docs/specs/whiteboard-draw-protocol-v1.md.
    """
    print(f"Received request: sessionId={request.sessionId}, query={request.query[:50]}...")
    print(f"Has canvas image: {request.canvasImage is not None}, mode={request.mode}")

    # Validate session + ownership BEFORE the stream starts so we can return HTTP errors.
    session_data = convo_service.redis_client.get(f"ai_tutor:{request.sessionId}")
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    session_info = json.loads(session_data)
    if session_info["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Build the message history (existing + current query) for persistence.
    messages = request.messages.copy() if request.messages else []
    messages.append({"role": "user", "content": request.query})

    state = TutoringState.from_dict(session_info.get("tutoring_state"))
    provider = convo_service.make_provider(request.mode)
    orchestrator = AIWhiteboardOrchestrator()

    async def event_stream():
        try:
            full_text = ""
            new_state = state
            draw_index = 0
            async for channel, payload in orchestrator.run_turn(
                provider=provider,
                query=request.query,
                canvas_image=request.canvasImage,
                previous_canvas_image=request.previousCanvasImage,
                has_annotation=request.hasAnnotation,
                state=state,
                board_elements=request.boardElements,
            ):
                if channel == "text":
                    yield _sse_frame("text", {"delta": payload})
                elif channel == "draw":
                    yield _sse_frame("draw", {"action": payload.to_dict(), "index": draw_index})
                    draw_index += 1
                    await asyncio.sleep(DRAW_FRAME_PACING_SECONDS)
                elif channel == "state":
                    new_state = payload
                    yield _sse_frame("state", payload.to_dict())
                elif channel == "full_text":
                    full_text = payload

            # Convert LaTeX in the assembled message to plain text for display/TTS,
            # falling back to raw on any conversion error (matches Phase 0 behavior).
            try:
                display_response = l2t.latex_to_text(full_text)
            except Exception as e:
                print(f"LaTeX-to-text conversion failed, using raw response: {e}")
                display_response = full_text

            _persist_ai_tutor_turn(
                db, request.sessionId, session_info, messages, display_response, new_state
            )

            yield _sse_frame("done", {"provider": provider.name})
        except Exception as e:
            print(f"Error processing AI tutor query: {e}")
            yield _sse_frame("error", {"message": f"Failed to process query: {str(e)}"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")



@router.get("/api/ai-tutor/session/{session_id}")
async def get_ai_tutor_session(
    session_id: str,
    current_user = Depends(get_current_user)
):
    """Get AI tutor session details."""
    try:
        session_data = convo_service.redis_client.get(f"ai_tutor:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")

        session_info = json.loads(session_data)

        # Verify user owns this session
        if session_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        return {
            "sessionId": session_id,
            "messages": session_info.get("messages", []),
            "createdAt": session_info.get("created_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting AI tutor session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@router.get("/api/student/knowledge-profile")
async def get_student_knowledge_profile(
    current_user: StudentUser = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Get the current student's knowledge profile.

    Prefers the live TASA projection built from decaying per-KC mastery; falls
    back to the legacy stored JSON for students with no mastery rows yet.
    """
    try:
        profile = KnowledgeProfileService.project_profile_from_mastery(db, current_user.id)
        if not profile:
            profile = KnowledgeProfileService.get_student_profile(db, current_user.id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        return {
            "status": "success",
            "profile": profile
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting knowledge profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")
