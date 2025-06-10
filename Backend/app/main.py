from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
from dotenv import load_dotenv

# Import our modules
from .database.database import get_db, engine
from .database.models import Base, Test, Question, TestQuestion, TestResult, QuestionResult, ChatMessage, StudentUser, TeacherUser
from .auth.utils import verify_password, get_password_hash, create_access_token, create_refresh_token, SECRET_KEY, ALGORITHM
from .auth.schemas import TokenResponse, UserLogin, StudentCreate, TeacherCreate, StudentResponse, TeacherResponse, RefreshToken
from .auth.dependencies import get_current_user, get_current_student, get_current_teacher
from .services.conversation_service import ConversationService
from jose import jwt, JWTError

load_dotenv()

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Socratic Monolithic Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend in local development
        "http://localhost:80",    # Frontend in containerized environment
        "http://localhost",       # Frontend in containerized environment (default port 80)
        "http://frontend:80",     # Frontend service name in Docker network
        "http://frontend",
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

class TestBase(OrmBaseModel):
    test_name: Optional[str] = None
    code: str
    isPracticeExam: Optional[bool] = False

class TestCreate(TestBase):
    questions: List[Dict[str, Any]]

class QuestionBase(OrmBaseModel):
    public_question: str
    hidden_values: Dict[str, Any]
    answer: str
    formula: Optional[str] = None
    teacher_instructions: Optional[str] = None
    hint_level: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None

class TestQuestionCreate(OrmBaseModel):
    test_id: int
    question_id: int
    position: int

class TestResultBase(OrmBaseModel):
    test_code: str
    username: str
    score: Optional[float] = None
    total_questions: Optional[int] = None
    correct_questions: Optional[int] = None
    end_time: Optional[datetime] = None

class QuestionResultBase(OrmBaseModel):
    question_id: int
    student_answer: Optional[str] = None
    isCorrect: Optional[bool] = False
    time_spent: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None

class ChatMessageBase(OrmBaseModel):
    sender: str
    content: str
    timestamp: Optional[datetime] = None

# Response models
class ChatMessageResponse(ChatMessageBase):
    id: int
    question_result_id: int

class QuestionResultResponse(QuestionResultBase):
    id: int
    test_result_id: int
    chat_messages: List[ChatMessageResponse] = []

class TestResultResponse(TestResultBase):
    id: int
    start_time: datetime
    question_results: List[QuestionResultResponse] = []

class QuestionResponse(QuestionBase):
    id: int

class TestResponse(TestBase):
    id: int
    test_name: str
    code: str
    isPracticeExam: bool = False
    questions: List[QuestionResponse] = []

# Request models
class ChatQuery(BaseModel):
    test_id: int
    test_code: str
    question_id: int
    public_question: str
    query: str
    user_id: int
    isPracticeExam: bool = False

class Question(BaseModel):
    public_question: str
    hidden_values: Optional[Dict[str, Any]] = {}
    answer: str
    formula: Optional[str] = None
    teacher_instructions: Optional[str] = None
    hint_level: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None

class TestCreateRequest(BaseModel):
    name: str
    code: str
    isPracticeExam: bool = False
    questions: List[Question]

class AnswerSubmission(BaseModel):
    user_id: int
    test_code: str
    question_id: int
    question_index: int
    answer: str

class TestFinishRequest(BaseModel):
    user_id: str
    test_id: Optional[int] = None
    test_code: str

class TestSessionStart(BaseModel):
    user_id: int
    test_id: int
    test_code: str
    question_ids: List[int]
    total_questions: int

# Authentication endpoints
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

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Chat endpoint
@app.post("/chat")
async def chat(query: ChatQuery):
    """Process a chat query using Gemini."""
    try:
        response = await convo_service.process_query(
            query=query.query,
            user_id=query.user_id,
            test_code=query.test_code,
            question_id=query.question_id,
            public_question=query.public_question,
            test_id=query.test_id,
            is_practice_exam=query.isPracticeExam
        )
        return {"response": response}
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat query")

# Test management endpoints
@app.post("/tests", response_model=TestResponse)
async def create_test(test: TestCreateRequest, db: Session = Depends(get_db)):
    """Create a new test with questions."""
    # Create the test
    db_test = Test(
        test_name=test.name,
        code=test.code,
        isPracticeExam=test.isPracticeExam
    )
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    
    # Create questions and link them to the test
    for position, question_data in enumerate(test.questions):
        # Create the question
        db_question = Question(
            public_question=question_data.public_question,
            hidden_values=question_data.hidden_values or {},
            answer=question_data.answer,
            formula=question_data.formula,
            teacher_instructions=question_data.teacher_instructions,
            hint_level=question_data.hint_level,
            subject=question_data.subject,
            topic=question_data.topic
        )
        db.add(db_question)
        db.commit()
        db.refresh(db_question)
        
        # Create the test-question relationship
        db_test_question = TestQuestion(
            test_id=db_test.id,
            question_id=db_question.id,
            position=position
        )
        db.add(db_test_question)
    
    db.commit()
    
    # Return the test with questions
    return get_test_by_code(test.code, db)

@app.get("/tests/{code}", response_model=TestResponse)
async def get_test_by_code(code: str, db: Session = Depends(get_db), user_id: Optional[str] = None):
    """Get a test by its code."""
    # Get the test and join with questions through TestQuestion
    test = db.query(Test).filter(Test.code == code).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Get questions ordered by position
    test_questions = (
        db.query(TestQuestion, Question)
        .join(Question, TestQuestion.question_id == Question.id)
        .filter(TestQuestion.test_id == test.id)
        .order_by(TestQuestion.position)
        .all()
    )
    
    questions = []
    for test_question, question in test_questions:
        questions.append({
            "id": question.id,
            "public_question": question.public_question,
            "hidden_values": question.hidden_values,
            "answer": question.answer,
            "formula": question.formula,
            "teacher_instructions": question.teacher_instructions,
            "hint_level": question.hint_level,
            "subject": question.subject,
            "topic": question.topic
        })
    
    return {
        "id": test.id,
        "test_name": test.test_name,
        "code": test.code,
        "isPracticeExam": test.isPracticeExam,
        "questions": questions
    }

@app.get("/tests/{code}/questions/{index}")
async def get_question(code: str, index: int, db: Session = Depends(get_db)):
    """Get a specific question from a test by index."""
    # Get the test
    test = db.query(Test).filter(Test.code == code).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Get the question at the specified position
    test_question = (
        db.query(TestQuestion, Question)
        .join(Question, TestQuestion.question_id == Question.id)
        .filter(TestQuestion.test_id == test.id, TestQuestion.position == index)
        .first()
    )
    
    if not test_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    _, question = test_question
    
    return {
        "id": question.id,
        "public_question": question.public_question,
        "hidden_values": question.hidden_values,
        "answer": question.answer,
        "formula": question.formula,
        "teacher_instructions": question.teacher_instructions,
        "hint_level": question.hint_level,
        "subject": question.subject,
        "topic": question.topic
    }

# Test session management
@app.post("/start-test")
async def start_test(request: TestSessionStart):
    """Start a test session."""
    try:
        result = await convo_service.start_test(
            user_id=request.user_id,
            test_id=request.test_id,
            test_code=request.test_code,
            list_question_ids=request.question_ids,
            total_questions=request.total_questions
        )
        return result
    except Exception as e:
        print(f"Error starting test: {e}")
        raise HTTPException(status_code=500, detail="Failed to start test")

@app.post("/submit-answer")
async def submit_answer(submission: AnswerSubmission):
    """Submit an answer for a question."""
    try:
        result = await convo_service.submit_answer(
            user_id=submission.user_id,
            test_code=submission.test_code,
            question_id=submission.question_id,
            question_index=submission.question_index,
            answer=submission.answer
        )
        return result
    except Exception as e:
        print(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit answer")

@app.post("/finish-test")
async def finish_test(request: TestFinishRequest):
    """Finish a test session."""
    try:
        result = await convo_service.finish_test(
            user_id=request.user_id,
            test_id=str(request.test_id) if request.test_id else None,
            request_data=request.dict()
        )
        return result
    except Exception as e:
        print(f"Error finishing test: {e}")
        raise HTTPException(status_code=500, detail="Failed to finish test")

# Question management
@app.post("/create-question", response_model=QuestionResponse)
async def create_question(question: QuestionBase, db: Session = Depends(get_db)):
    """Create a new question."""
    db_question = Question(
        public_question=question.public_question,
        hidden_values=question.hidden_values,
        answer=question.answer,
        formula=question.formula,
        teacher_instructions=question.teacher_instructions,
        hint_level=question.hint_level,
        subject=question.subject,
        topic=question.topic
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

@app.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question_by_id(question_id: int, db: Session = Depends(get_db)):
    """Get a question by ID."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@app.post("/chat-video")
async def chat_video(request: dict, current_user = Depends(get_current_user)):
    """Handle chat requests about YouTube videos with context awareness"""
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
        
        # Process the query and update session with timestamp context
        response_text = await convo_service.process_video_chat(
            user_id=user_id,
            video_id=video_id,
            video_url=video_url,
            query=query,
            session_data=session_data,
            timestamp=timestamp
        )

        
        return {"response": response_text, "video_id": video_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process video chat request") 