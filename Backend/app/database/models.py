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
    question_id = Column(String, nullable=True)  # The custom id like "q_math_ch5_example_2"
    
    # Question metadata
    subject = Column(String, nullable=True)
    chapter = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    question_type = Column(String, nullable=True)
    grade = Column(String, nullable=True)
    
    # Source information
    source_example_number = Column(Integer, nullable=True)
    source_question_number = Column(Integer, nullable=True)
    source_part_number = Column(Integer, nullable=True)
    
    # Question and answer
    question_text = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    
    # Solution information (stored as JSON)
    solution = Column(JSON, nullable=True)  # Object with introduction, steps array, learning_tip, related_concepts
    
    # Additional information (stored as JSON)
    common_mistakes = Column(JSON, nullable=True)  # Array of common mistakes
    teacher_notes = Column(JSON, nullable=True)  # Array of teacher notes

class NcertExercises(Base):
    __tablename__ = "ncert_exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String, nullable=True)  # The custom id like "q_math_ch5_ex5.1_q1_part1"
    
    # Question metadata
    subject = Column(String, nullable=True)
    chapter = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    question_type = Column(String, nullable=True)
    grade = Column(String, nullable=True)
    
    # Source information
    source_exercise_number = Column(String, nullable=True)
    source_question_number = Column(Integer, nullable=True)
    source_part_number = Column(Integer, nullable=True)
    
    # Question and answer
    question_text = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    
    # Mark scheme information (stored as JSON)
    marking_criteria = Column(JSON, nullable=True)  # Array of marking criteria
    common_mistakes = Column(JSON, nullable=True)  # Array of common mistakes
    teacher_notes = Column(JSON, nullable=True)  # Array of teacher notes

class PYQs(Base):
    __tablename__ = "pyqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(String, nullable=True)  # The custom id like "q_math_pyq_2023_q15"
    
    # Question metadata
    subject = Column(String, nullable=True)
    chapter = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    question_type = Column(String, nullable=True)
    max_marks = Column(Integer, nullable=True)
    grade = Column(String, nullable=True)
    
    # Source information
    source_year = Column(Integer, nullable=True)
    source_question_number = Column(Integer, nullable=True)
    source_part_number = Column(Integer, nullable=True)
    
    # Question and answer
    question_text = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    
    # Mark scheme information (stored as JSON)
    total_marks = Column(Integer, nullable=True)
    marking_criteria = Column(JSON, nullable=True)  # Array of marking criteria with marks
    common_mistakes = Column(JSON, nullable=True)  # Array of common mistakes with deductions
    teacher_notes = Column(JSON, nullable=True)  # Array of teacher notes

class GradingSession(Base):
    __tablename__ = "grading_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("student_users.id"), nullable=False)
    question_id = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    correct_solution = Column(Text, nullable=False)
    practice_mode = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    grade = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    status = Column(String, default="waiting_for_submission")
    image_path = Column(String, nullable=True)
    image_uploaded_at = Column(DateTime, nullable=True)
    mobile_connected_at = Column(DateTime, nullable=True)
    grading_result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationship
    student = relationship("StudentUser", back_populates="grading_sessions")

# Add the relationship to StudentUser
StudentUser.grading_sessions = relationship("GradingSession", back_populates="student")


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