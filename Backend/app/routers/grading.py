import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..auth.utils import ALGORITHM, SECRET_KEY
from ..database.database import get_db
from ..database.models import GradingSession
from ..service_instances import convo_service
from ..services.knowledge_profile_service import KnowledgeProfileService

router = APIRouter()


class GradingSessionCreate(BaseModel):
    questionId: int
    questionText: str
    correctSolution: str
    practiceMode: str
    subject: str
    grade: str
    topic: Optional[str] = None

class GradingSessionResponse(BaseModel):
    sessionId: str
    qrCodeUrl: str
    expiresIn: int

# Temporary token creation for mobile access
def create_temp_token(session_id: str, user_id: int) -> str:
    """Create a temporary token for mobile access to a specific grading session."""
    token_data = {
        "sub": str(user_id),
        "session_id": session_id,
        "type": "grading_temp",
        "exp": datetime.utcnow() + timedelta(minutes=5)
    }
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/api/create-grading-session", response_model=GradingSessionResponse)
async def create_grading_session(
    session_data: GradingSessionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new grading session and return QR code URL."""
    try:
        # Generate unique session ID
        session_id = f"grade_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Create session record in database
        grading_session = GradingSession(
            session_id=session_id,
            user_id=current_user.id,
            question_id=session_data.questionId,
            question_text=session_data.questionText,
            correct_solution=session_data.correctSolution,
            practice_mode=session_data.practiceMode,
            subject=session_data.subject,
            grade=session_data.grade,
            topic=session_data.topic,
            status="waiting_for_submission",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            created_at=datetime.utcnow()
        )

        db.add(grading_session)
        db.commit()
        db.refresh(grading_session)

        # Generate mobile URL with temporary token
        temp_token = create_temp_token(session_id, current_user.id)
        # Use the actual frontend URL based on environment
        frontend_url = os.getenv("FRONTEND_URL", "http://Matthews-MacBook-Pro.local:3000")
        # For production, this would be your actual domain
        if os.getenv("RAILWAY_ENVIRONMENT"):
            frontend_url = "https://socratic.up.railway.app"
        mobile_url = f"{frontend_url}/mobile-grade/{session_id}?token={temp_token}"


        convo_service.redis_client.setex(
                f"session:{session_id}",
                600,  # 10 minutes TTL
                json.dumps({
                    "user_id": current_user.id,
                    "question_id": session_data.questionId,
                    "status": "waiting",
                    "created_at": datetime.utcnow().isoformat()
            })
        )

        return {
            "sessionId": session_id,
            "qrCodeUrl": mobile_url,
            "expiresIn": 600  # seconds
        }

    except Exception as e:
        print(f"Error creating grading session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/api/validate-grading-session/{session_id}")
async def validate_grading_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Validate a grading session for mobile access."""
    try:
        print(f"VALIDATING SESSION: {session_id}")

        # Extract and validate temporary token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_type = payload.get("type")
            token_session_id = payload.get("session_id")
            user_id = int(payload.get("sub"))

            # Verify it's a grading temp token for this session
            if token_type != "grading_temp" or token_session_id != session_id:
                raise HTTPException(status_code=401, detail="Invalid token for this session")

        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check Redis for fast lookup
        session_data = convo_service.redis_client.get(f"session:{session_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found or expired")
        session_info = json.loads(session_data)

        # Verify user ownership
        if session_info["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access")

        # Check database
        db_session = db.query(GradingSession).filter(
            GradingSession.session_id == session_id,
            GradingSession.expires_at > datetime.utcnow(),
            GradingSession.status.in_(["waiting_for_submission", "mobile_connected"])
        ).first()

        if not db_session:
            raise HTTPException(status_code=410, detail="Session expired")

        return {
            "sessionId": session_id,
            "questionText": db_session.question_text,
            "subject": db_session.subject,
            "grade": db_session.grade,
            "topic": db_session.topic,
            "status": db_session.status,
            "timeRemaining": int((db_session.expires_at - datetime.utcnow()).total_seconds())
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error validating session: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/api/grading-session/{session_id}/connect-mobile")
async def connect_mobile_to_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update session status when mobile connects."""
    try:
        # Extract and validate temporary token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_type = payload.get("type")
            token_session_id = payload.get("session_id")
            user_id = int(payload.get("sub"))

            # Verify it's a grading temp token for this session
            if token_type != "grading_temp" or token_session_id != session_id:
                raise HTTPException(status_code=401, detail="Invalid token for this session")

        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Update session status
        db_session = db.query(GradingSession).filter(
            GradingSession.session_id == session_id,
            GradingSession.user_id == user_id
        ).first()

        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        db_session.status = "mobile_connected"
        db_session.mobile_connected_at = datetime.utcnow()
        db.commit()

        # Update Redis cache
        if hasattr(convo_service, 'redis_client'):
            convo_service.redis_client.setex(
                f"session:{session_id}",
                 300,
                json.dumps({
                    "user_id": user_id,
                    "question_id": db_session.question_id,
                    "status": "mobile_connected",
                    "mobile_connected_at": datetime.utcnow().isoformat()
                })
            )

        # TODO: Notify computer via WebSocket

        return {"status": "connected"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error connecting mobile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/submit-grading-image")
async def submit_grading_image(
    request: Request,
    sessionId: str = Form(...),
    timestamp: str = Form(...),
    imageSize: int = Form(...),
    metadata: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Submit an image for grading."""
    try:
        # Extract and validate temporary token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_type = payload.get("type")
            token_session_id = payload.get("session_id")
            user_id = int(payload.get("sub"))

            # Verify it's a grading temp token for this session
            if token_type != "grading_temp" or token_session_id != sessionId:
                raise HTTPException(status_code=401, detail="Invalid token for this session")

        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Validate session
        db_session = db.query(GradingSession).filter(
            GradingSession.session_id == sessionId,
            GradingSession.user_id == user_id,
            GradingSession.status.in_(["mobile_connected", "waiting_for_submission"]),
            GradingSession.expires_at > datetime.utcnow()
        ).first()

        if not db_session:
            raise HTTPException(status_code=404, detail="Invalid or expired session")

        # Validate image file
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Invalid file type")

        if imageSize > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large")

        # Create uploads directory if it doesn't exist
        # Use absolute path relative to the Backend directory (three levels up from
        # this router module: routers/ -> app/ -> Backend/), matching the original
        # main.py location this handler was moved from.
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(backend_dir, "temp_uploads")
        os.makedirs(upload_dir, exist_ok=True)

        # Save image with unique filename
        filename = f"{sessionId}_{int(time.time())}.jpg"
        file_path = os.path.join(upload_dir, filename)

        # Save file
        content = await image.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Update session status
        db_session.status = "image_uploaded"
        db_session.image_path = file_path
        db_session.image_uploaded_at = datetime.utcnow()
        db.commit()

        # Update Redis if available
        if hasattr(convo_service, 'redis_client'):
            convo_service.redis_client.setex(
                f"session:{sessionId}",
                300,
                json.dumps({
                    "user_id": user_id,
                    "question_id": db_session.question_id,
                    "status": "image_uploaded",
                    "image_path": file_path,
                    "uploaded_at": datetime.utcnow().isoformat()
                })
            )

        # Trigger grading process
        grading_result = await convo_service.gemini_service.generate_photo_grading(
            db_session.question_text,
            db_session.correct_solution,
            file_path
        )

        # Update with grading result
        db_session.grading_result = grading_result
        db_session.status = "completed"
        db.commit()

        # Update knowledge profile after successful grading
        try:
            print(user_id, db_session.question_id, db_session.practice_mode, grading_result)
            updated_profile = KnowledgeProfileService.update_profile_after_grading(
                db=db,
                user_id=user_id,
                question_id=db_session.question_id,
                practice_mode=db_session.practice_mode,
                grading_result=grading_result
            )
            if updated_profile:
                print(f"Successfully updated knowledge profile for user {user_id}")
            else:
                print(f"Failed to update knowledge profile for user {user_id}")
        except Exception as profile_error:
            print(f"Error updating knowledge profile: {profile_error}")
            # Don't fail the grading if profile update fails

        # Clean up the uploaded image file after grading
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Cleaned up image file: {file_path}")
        except Exception as cleanup_error:
            print(f"Warning: Failed to clean up image file {file_path}: {cleanup_error}")
            # Don't fail the request if cleanup fails

        return {
            "status": "success",
            "message": "Image uploaded and graded successfully",
            "sessionId": sessionId,
            "result": grading_result
        }

    except HTTPException:
        raise
    except Exception as e:
        # Clean up uploaded file if error occurs
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        print(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/api/grading-session/{session_id}/result")
async def get_grading_result(
    session_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get the grading result for a session."""
    try:
        db_session = db.query(GradingSession).filter(
            GradingSession.session_id == session_id,
            GradingSession.user_id == current_user.id
        ).first()

        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")

        if db_session.status != "completed":
            return {
                "status": db_session.status,
                "result": None
            }

        return {
            "status": "completed",
            "result": db_session.grading_result
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting result: {e}")
        raise HTTPException(status_code=500, detail=str(e))
