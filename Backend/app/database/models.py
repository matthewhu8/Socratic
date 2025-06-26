from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# New models for authentication
class StudentUser(Base):
    __tablename__ = "student_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  
    grade = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class TeacherUser(Base):
    __tablename__ = "teacher_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    subject = Column(String)
    school = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class NcertExamples(Base):
    __tablename__ = "ncert_examples"
    
    id = Column(Integer, primary_key=True, index=True)
    example = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)
    topic = Column(String, nullable=True)
    example_number = Column(Float, nullable=True)
    grade = Column(String, nullable=True)

class NcertExcersizes(Base):
    __tablename__ = "ncert_excersizes"
    
    id = Column(Integer, primary_key=True, index=True)
    excersize = Column(Text, nullable=False)
    solution = Column(Text, nullable=True)
    topic = Column(String, nullable=True)
    excersize_number = Column(Float, nullable=True)
    grade = Column(String, nullable=True)

class PYQs(Base):
    __tablename__ = "pyqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    topic = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    year = Column(Integer, nullable=True)


class YouTubeQuizResults(Base):
    __tablename__ = "youtube_quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_users.id"), nullable=False)
    youtube_url = Column(String) 
    youtube_id = Column(String) 
    video_title = Column(String, nullable=True) 
    time_spent = Column(Integer, nullable=True) 
    raw_quiz = Column(JSON)
    student_answers = Column(JSON)
    score = Column(Float)
    difficulty_rating = Column(String, nullable=True)
    
    # Relationships
    student = relationship("StudentUser", foreign_keys=[student_id]) 