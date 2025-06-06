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
    """Get current authenticated user (student or teacher)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if user_id is None or user_type is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user based on type
    if user_type == "student":
        user = db.query(StudentUser).filter(StudentUser.id == int(user_id)).first()
    elif user_type == "teacher":
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
        
        if user_id is None or user_type != "student":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
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
        
        if user_id is None or user_type != "teacher":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    user = db.query(TeacherUser).filter(TeacherUser.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    return user 