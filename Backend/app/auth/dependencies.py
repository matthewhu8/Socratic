from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from .utils import SECRET_KEY, ALGORITHM
from ..database.database import get_db
from ..database.models import StudentUser, TeacherUser

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user (handles both Google and regular auth)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        db_id: str = payload.get("db_id")  # For Google users
        
        if user_id is None or user_type is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user based on type
    if user_type == "student":
        if db_id:
            # Google user - use database ID to find user
            user = db.query(StudentUser).filter(StudentUser.id == int(db_id)).first()
        else:
            # Regular user - user_id is the database ID
            user = db.query(StudentUser).filter(StudentUser.id == int(user_id)).first()
    elif user_type == "teacher":
        if db_id:
            user = db.query(TeacherUser).filter(TeacherUser.id == int(db_id)).first()
        else:
            user = db.query(TeacherUser).filter(TeacherUser.id == int(user_id)).first()
    else:
        raise credentials_exception
        
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> StudentUser:
    """Get current authenticated student user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        db_id: str = payload.get("db_id")  # For Google users
        
        if user_id is None or user_type != "student":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    if db_id:
        # Google user
        user = db.query(StudentUser).filter(StudentUser.id == int(db_id)).first()
    else:
        # Regular user
        user = db.query(StudentUser).filter(StudentUser.id == int(user_id)).first()
        
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_teacher(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TeacherUser:
    """Get current authenticated teacher user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        db_id: str = payload.get("db_id")  # For Google users
        
        if user_id is None or user_type != "teacher":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    if db_id:
        # Google user
        user = db.query(TeacherUser).filter(TeacherUser.id == int(db_id)).first()
    else:
        # Regular user
        user = db.query(TeacherUser).filter(TeacherUser.id == int(user_id)).first()
        
    if user is None:
        raise credentials_exception
        
    return user 