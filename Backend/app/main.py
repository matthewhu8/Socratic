from fastapi import FastAPI, HTTPException, Depends, status, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import uuid
import time
import json

# Import our modules
from .database.database import get_db, engine
from .database.models import Base, YouTubeQuizResults, StudentUser, TeacherUser, NcertExamples, NcertExercises, PYQs, GradingSession, AITutorSession
from .auth.utils import verify_password, get_password_hash, create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM
from .auth.schemas import TokenResponse, UserLogin, StudentCreate, TeacherCreate, StudentResponse, TeacherResponse, RefreshToken
from .auth.dependencies import get_current_user, get_current_student, get_current_teacher
from .services.conversation_service import ConversationService
from jose import jwt, JWTError

# Imports for Google Sign-In
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

load_dotenv()

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Socratic Monolithic Backend")

# CORS middleware - Updated for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend in local development
        "http://localhost:80",    # Frontend in containerized environment
        "http://localhost",       # Frontend in containerized environment (default port 80)
        "http://frontend:80",     # Frontend service name in Docker network
        "http://frontend",
        "http://0.0.0.0:3000",
        "0.0.0.0:3000",
        "http://0.0.0.0:8000",
        "http://10.147.120.71:3000",
        "http://10.147.120.71:8000",
        "http://Matthews-MacBook-Pro.local:3000",
        "http://Matthews-MacBook-Pro.local:8000",
        # Add your production domains here
        "https://*.up.railway.app",  # All Railway subdomains
        "https://*.netlify.app",  # In case you use Netlify for frontend
        "https://*.vercel.app",   # In case you use Vercel for frontend 
        "https://frontend-production-81e0.up.railway.app",
        "https://socratic.up.railway.app"      # Replace with your custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
convo_service = ConversationService(redis_url=REDIS_URL)

# Pydantic models for request/response
class OrmBaseModel(BaseModel):
    class Config:
        from_attributes = True

# Pydantic model for Google token
class GoogleToken(BaseModel):
    token: str

@app.post("/api/auth/google/login", response_model=TokenResponse)
async def google_login(request: GoogleToken, db: Session = Depends(get_db)):
    """Handle Google Sign-In using Google ID as primary identifier."""
    try:
        # Get the Google Client ID from environment variables
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not google_client_id:
            raise HTTPException(status_code=500, detail="Google Client ID not configured")
            
        # Verify the ID token with Google
        id_info = id_token.verify_oauth2_token(
            request.token, google_requests.Request(), google_client_id
        )
        
        # Extract user information from Google token
        user_email = id_info.get("email")
        user_name = id_info.get("name")
        google_user_id = id_info.get("sub")  # This is Google's unique ID for the user

        if not user_email or not google_user_id:
            raise HTTPException(status_code=400, detail="Invalid Google token")

        # Try to find existing user by email
        student = db.query(StudentUser).filter(StudentUser.email == user_email).first()
        
        if not student:
            # Create new user with a placeholder password (they'll never use it)
            student = StudentUser(
                name=user_name,
                email=user_email,
                hashed_password="google_auth_user",  # Placeholder - they won't use password login
                grade=None  # They can set this later in their profile
            )
            db.add(student)
            db.commit()
            db.refresh(student)

        # Here's the key: Use Google ID in the JWT token, not database ID
        token_data = {
            "sub": google_user_id,      # Google's unique ID
            "type": "student",
            "db_id": str(student.id)    # Store database ID for internal use
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return {"access_token": access_token, "refresh_token": refresh_token}

    except ValueError as e:
        print(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google authentication token",
        )
    except Exception as e:
        print(f"Error during Google login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )

@app.post("/api/auth/student/register", response_model=StudentResponse)
async def register_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Register a new student user."""
    # Check if email already exists
    db_student = db.query(StudentUser).filter(StudentUser.email == student.email).first()
    if db_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new student user with hashed password
    hashed_password = get_password_hash(student.password)
    db_student = StudentUser(
        name=student.name,
        email=student.email,
        hashed_password=hashed_password,
        grade=student.grade
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student

@app.post("/api/auth/teacher/register", response_model=TeacherResponse)
async def register_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    """Register a new teacher user."""
    # Check if email already exists
    db_teacher = db.query(TeacherUser).filter(TeacherUser.email == teacher.email).first()
    if db_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new teacher user with hashed password
    hashed_password = get_password_hash(teacher.password)
    db_teacher = TeacherUser(
        name=teacher.name,
        email=teacher.email,
        hashed_password=hashed_password,
        subject=teacher.subject,
        school=teacher.school
    )
    
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    
    return db_teacher

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return JWT tokens."""
    # Try to find user in student table
    student = db.query(StudentUser).filter(StudentUser.email == login_data.email).first()
    if student and verify_password(login_data.password, student.hashed_password):
        # Create token data for student
        token_data = {"sub": str(student.id), "type": "student"}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {"access_token": access_token, "refresh_token": refresh_token}
    
    # If not found in student table, try teacher table
    teacher = db.query(TeacherUser).filter(TeacherUser.email == login_data.email).first()
    if teacher and verify_password(login_data.password, teacher.hashed_password):
        # Create token data for teacher
        token_data = {"sub": str(teacher.id), "type": "teacher"}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {"access_token": access_token, "refresh_token": refresh_token}
    
    # If not found in either table, raise exception
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"}
    )

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh: RefreshToken, db: Session = Depends(get_db)):
    """Use a refresh token to get a new access token."""
    try:
        # Decode refresh token
        payload = jwt.decode(refresh.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if it's a refresh token
        if not payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user ID and type from token
        user_id = payload.get("sub")
        user_type = payload.get("type")
        
        if not user_id or not user_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token data",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify user still exists
        if user_type == "student":
            user = db.query(StudentUser).filter(StudentUser.id == int(user_id)).first()
        elif user_type == "teacher":
            user = db.query(TeacherUser).filter(TeacherUser.id == int(user_id)).first()
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user type",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create new tokens
        token_data = {"sub": user_id, "type": user_type}
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return {"access_token": access_token, "refresh_token": new_refresh_token}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

@app.get("/api/auth/student/me", response_model=StudentResponse)
async def get_student_profile(current_user: StudentUser = Depends(get_current_student)):
    """Get current student profile."""
    return current_user

@app.get("/api/auth/teacher/me", response_model=TeacherResponse)
async def get_teacher_profile(current_user: TeacherUser = Depends(get_current_teacher)):
    """Get current teacher profile."""
    return current_user

# Pydantic model for profile updates
class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None

@app.patch("/api/auth/student/profile")
async def update_student_profile(
    profile_data: StudentProfileUpdate,
    current_user: StudentUser = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Update current student profile."""
    try:
        # Update fields if provided
        if profile_data.name is not None:
            current_user.name = profile_data.name
        if profile_data.grade is not None:
            current_user.grade = profile_data.grade
        
        # Save changes
        db.commit()
        db.refresh(current_user)
        
        return {
            "status": "success",
            "message": "Profile updated successfully",
            "user": {
                "id": current_user.id,
                "name": current_user.name,
                "email": current_user.email,
                "grade": current_user.grade
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/video/load-transcript")
async def load_video_transcript(
    request: dict,
    current_user = Depends(get_current_user)
):
    """Load and cache transcript when user loads video."""
    video_id = request.get("video_id")
    video_url = request.get("video_url")
    print(f"loading transcript for video {video_id} and url {video_url}")
    
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")
    if not video_url:
        raise HTTPException(status_code=400, detail="video_url is required")
    
    try:
        success = await convo_service.load_and_cache_transcript(video_id, video_url)
        
        if success:
            return {
                "status": "success", 
                "message": f"Transcript cached for video {video_id}",
                "video_id": video_id
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to load transcript"
            )
            
    except Exception as e:
        print(f"Error in load_video_transcript endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error loading transcript: {str(e)}"
        )
    
@app.post("/api/youtube-video-quiz")
async def youtube_video_quiz(request: dict, current_user = Depends(get_current_user)):
    """Generate a quiz for a YouTube video."""
    try:
        video_id = request.get("video_id")
        video_url = request.get("video_url")
        user_id = current_user.id

        if not video_id or not video_url:
            raise HTTPException(status_code=400, detail="video_id and video_url are required")
        
        # get session data from redis about this video to find previous messages
        session_data = await convo_service.get_video_session(user_id, video_id)
        print(f"SESSION DATA RECEIVED: {session_data}")
        previous_messages = session_data.get("messages", [])

        # get entire video transcript from redis
        entire_transcript = convo_service.get_transcript_context(video_id, 0, 1000000)
        print(f"ENTIRE TRANSCRIPT RECEIVED: {entire_transcript[0:100]}")
        print(f"PREVIOUS MESSAGES RECEIVED: {previous_messages}")

        # Generate quiz using Gemini
        quiz_response = convo_service.gemini_service.generate_quiz(
            entire_transcript=entire_transcript,
            previous_messages=previous_messages
        )

        return {"quiz": quiz_response}
    except Exception as e:
        print(f"Error in youtube_video_quiz endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")

@app.post("/chat-video")
async def chat_video(request: dict, current_user = Depends(get_current_user)):
    """Handle chat requests about YouTube videos with context awareness and optional image"""
    try:
        print(f"REQUEST RECEIVED: {request}")
        query = request.get("query", "")
        video_id = request.get("video_id", "")
        video_url = request.get("video_url", "")
        timestamp = request.get("timestamp")
        user_id = current_user.id
        
        if not query or not video_id:
            raise HTTPException(status_code=400, detail="Query and video_id are required")
        
        # Get or create session history from Redis
        session_data = await convo_service.get_video_session(user_id, video_id)
        print(f"SESSION DATA RECEIVED: {session_data}")
        print(f"ATTEMPTING TO ANSWER: {query}")
        
        if timestamp:
            print(f"VIDEO TIMESTAMP: {timestamp}")
       
        
        # Process the query and update session with timestamp context and image
        response_text = await convo_service.process_video_chat(
            user_id=user_id,   
            video_id=video_id,
            video_url=video_url,
            query=query,  
            session_data=session_data,
            timestamp=timestamp,
        )

        return {"response": response_text, "video_id": video_id}
        
    except Exception as e:
        print(f"Error in chat_video endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to process video chat request") 

@app.post("/api/store-youtube-quiz-results")
async def store_youtube_quiz_results(request: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Store the results of a YouTube quiz."""
    try:
        video_title = request.get("video_title", "YouTube Video")
        youtube_url = request.get("youtube_url")
        youtube_id = request.get("youtube_id")
        time_spent = request.get("time_spent", 10) # units should be in seconds
        raw_quiz = request.get("raw_quiz") #JSON format identitcal to how the quiz is returned from the youtube_video_quiz endpoint
        student_answers = request.get("student_answers") # JSON format, question number as key, answer and True/false boolean for right or wrong as two values
        score = request.get("score", 0) # score as a percentage
        
        db_quiz_result = YouTubeQuizResults(
            student_id=current_user.id,
            video_title=video_title,
            youtube_url=youtube_url,
            youtube_id=youtube_id,
            time_spent=time_spent,
            raw_quiz=raw_quiz,
            student_answers=student_answers,
            score=score
        )
        db.add(db_quiz_result)
        db.commit()
        db.refresh()

        return {"status": "success", "message": "Quiz results stored successfully"}
    
    except Exception as e:
       print(f"Error in store_youtube_quiz_results endpoint: {e}")
       raise HTTPException(status_code=500, detail="At some point during the storage of the quiz results, something went wrong")

@app.get("/api/get-youtube-quiz-results")
async def get_youtube_quiz_results(db: Session = Depends(get_db), current_user = Depends(get_current_student)) -> str:
    pass

# Pydantic model for question response
class QuestionResponse(OrmBaseModel):
    id: int
    question_text: str
    solution: str
    topic: str
    question_number: Optional[float] = None
    max_marks: Optional[int] = 3  # Default marks
    difficulty: Optional[str] = None
    year: Optional[int] = None
    # Solution data for NCERT Examples (contains steps, introduction, etc.)
    solution_data: Optional[Dict[str, Any]] = None
    # Mark scheme fields (for exercises and PYQs)
    marking_criteria: Optional[List[Dict[str, Any]]] = None
    common_mistakes: Optional[List[Dict[str, Any]]] = None
    teacher_notes: Optional[List[str]] = None

@app.get("/api/questions", response_model=List[QuestionResponse])
async def get_questions(
    practice_mode: str,
    grade: str, 
    topic: str,
    subject: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get questions based on practice mode, grade, topic, and subject."""
    try:
        # The 'topic' parameter now contains the full chapter name
        # e.g., "Chapter 5: Arithmetic Progressions"
        chapter_name = topic
        
        questions = []
        
        if practice_mode == "ncert-examples":
            print(grade, chapter_name)
            # Query NCERT Examples table by chapter
            db_questions = db.query(NcertExamples).filter(
                NcertExamples.grade == grade,
                NcertExamples.chapter == chapter_name
            ).all()
            
            # Convert to standard format
            for i, q in enumerate(db_questions):
                questions.append(QuestionResponse(
                    id=q.id,
                    question_text=q.question_text,
                    solution=q.answer,  # The answer field contains the final answer
                    topic=q.topic or "",
                    question_number=q.source_example_number,
                    max_marks=3,  # Default for examples
                    solution_data=q.solution,  # The new solution field with steps
                    marking_criteria=None,  # NCERT Examples don't have marking criteria
                    common_mistakes=q.common_mistakes,
                    teacher_notes=q.teacher_notes
                ))
                
        elif practice_mode == "ncert-exercises":
            # Query NCERT Exercises table by chapter
            print(grade, chapter_name)
            db_questions = db.query(NcertExercises).filter(
                NcertExercises.grade == grade,
                NcertExercises.chapter == chapter_name
            ).all()
            
            print(f"Found {len(db_questions)} exercises for grade={grade}, chapter={chapter_name}")
    
            
            # Convert to standard format
            for i, q in enumerate(db_questions):
                questions.append(QuestionResponse(
                    id=q.id,
                    question_text=q.question_text or q.exercise,  # Use new field if available
                    solution=q.answer or q.solution or "Solution not available",  # Use new field if available
                    topic=q.topic or "",
                    question_number=q.source_question_number or q.exercise_number,
                    max_marks=5,  # Default for exercises
                    solution_data=q.solution,
                    marking_criteria=None,
                    common_mistakes=q.common_mistakes,
                    teacher_notes=q.teacher_notes
                ))
                
        elif practice_mode == "previous-year-questions" or practice_mode == "smart-practice":
            # Query Previous Year Questions table
            if chapter_name and chapter_name.lower() != "general":
                # Filter by specific chapter
                db_questions = db.query(PYQs).filter(
                    PYQs.chapter == chapter_name
                ).all()
            else:
                # Get all PYQs regardless of chapter (for direct access)
                db_questions = db.query(PYQs).limit(50).all()  # Limit to prevent too many results
            
            # Convert to standard format
            for i, q in enumerate(db_questions):
                questions.append(QuestionResponse(
                    id=q.id,
                    question_text=q.question_text or q.question,  # Use new field if available
                    solution=q.answer,
                    topic=q.topic or "",
                    question_number=q.source_question_number,
                    max_marks=q.max_marks or q.total_marks or 6,  # Use actual marks if available
                    difficulty=q.difficulty,
                    year=q.source_year or q.year,
                    marking_criteria=q.marking_criteria,
                    common_mistakes=q.common_mistakes,
                    teacher_notes=q.teacher_notes
                ))
        
        else:
            raise HTTPException(status_code=400, detail="Invalid practice mode")
        
        if not questions:
            # Return empty list if no questions found
            return []
            
        return questions
        
    except Exception as e:
        print(f"Error in get_questions endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch questions: {str(e)}"
        )

# Pydantic models for grading sessions
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

@app.post("/api/create-grading-session", response_model=GradingSessionResponse)
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

@app.get("/api/validate-grading-session/{session_id}")
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

@app.patch("/api/grading-session/{session_id}/connect-mobile")
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

@app.post("/api/submit-grading-image")
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
        # Use absolute path relative to the app directory
        app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        upload_dir = os.path.join(app_dir, "temp_uploads")
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

@app.get("/api/grading-session/{session_id}/result")
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

# Pydantic model for question chat
class QuestionChatRequest(BaseModel):
    question_text: str
    question_solution: str
    student_query: str
    practice_mode: Optional[str] = None
    subject: Optional[str] = None

@app.post("/api/question-chat")
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
    canvasImage: Optional[str] = None  # Base64 encoded image

@app.post("/api/ai-tutor/create-session", response_model=AITutorSessionResponse)
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
        sdk_token = os.getenv("AGORA_SDK_TOKEN", "your-sdk-token")
        
        # Create room via Agora API
        headers = {
            "token": sdk_token,
            "Content-Type": "application/json",
            "region": "us-sv"
        }
        
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

@app.post("/api/ai-tutor/process-query")
async def process_ai_tutor_query(
    request: AITutorQueryRequest,
    current_user = Depends(get_current_user)
):
    """Process a query from the AI tutor interface."""
    try:
        # Get session from Redis
        session_data = convo_service.redis_client.get(f"ai_tutor:{request.sessionId}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_info = json.loads(session_data)
        
        # Verify user owns this session
        if session_info["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        # Build complete message history
        messages = request.messages.copy() if request.messages else []
        
        # Generate AI response with drawing commands
        response_data = await convo_service.gemini_service.generate_tutor_response(
            query=request.query,
            messages=messages,
            include_drawing_commands=True,
            canvas_image=request.canvasImage
        )
        
        print(f"Response from Gemini service: {response_data}")
        print(f"Drawing commands: {response_data.get('drawing_commands', [])}")
        
        # Update session with new messages
        session_info["messages"] = messages + [{"role": "assistant", "content": response_data["response"]}]
        convo_service.redis_client.setex(
            f"ai_tutor:{request.sessionId}",
            3600,
            json.dumps(session_info)
        )
        
        return {
            "response": response_data["response"],
            "drawingCommands": response_data.get("drawing_commands", [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing AI tutor query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@app.get("/api/ai-tutor/session/{session_id}")
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
