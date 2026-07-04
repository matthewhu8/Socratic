import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_student, get_current_teacher
from ..auth.schemas import (
    RefreshToken,
    StudentCreate,
    StudentResponse,
    TeacherCreate,
    TeacherResponse,
    TokenResponse,
    UserLogin,
)
from ..auth.utils import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from ..database.database import get_db
from ..database.models import StudentUser, TeacherUser

router = APIRouter()


class GoogleToken(BaseModel):
    token: str


class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None


@router.post("/api/auth/google/login", response_model=TokenResponse)
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

@router.post("/api/auth/student/register", response_model=StudentResponse)
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

@router.post("/api/auth/teacher/register", response_model=TeacherResponse)
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

@router.post("/api/auth/login", response_model=TokenResponse)
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

@router.post("/api/auth/refresh", response_model=TokenResponse)
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

@router.get("/api/auth/student/me", response_model=StudentResponse)
async def get_student_profile(current_user: StudentUser = Depends(get_current_student)):
    """Get current student profile."""
    return current_user

@router.get("/api/auth/teacher/me", response_model=TeacherResponse)
async def get_teacher_profile(current_user: TeacherUser = Depends(get_current_teacher)):
    """Get current teacher profile."""
    return current_user

@router.patch("/api/auth/student/profile")
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
