from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    grade: Optional[str] = None

class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    subject: Optional[str] = None
    school: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    name: str
    email: str
    grade: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TeacherResponse(BaseModel):
    id: int
    name: str
    email: str
    subject: Optional[str] = None
    school: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshToken(BaseModel):
    refresh_token: str 