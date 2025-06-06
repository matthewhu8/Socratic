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
    hashed_password = Column(String, nullable=False)
    grade = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship to test results
    test_results = relationship("TestResult", back_populates="student")

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

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    isPracticeExam = Column(Boolean, default=False)
    
    # Relationships
    test_questions = relationship("TestQuestion", back_populates="test")
    test_results = relationship("TestResult", back_populates="test")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    public_question = Column(Text, nullable=False)
    hidden_values = Column(JSON, default={})
    answer = Column(Text, nullable=False)
    formula = Column(Text)
    teacher_instructions = Column(Text)
    hint_level = Column(String)
    subject = Column(String)
    topic = Column(String)
    
    # Relationships
    test_questions = relationship("TestQuestion", back_populates="question")
    question_results = relationship("QuestionResult", back_populates="question")

class TestQuestion(Base):
    __tablename__ = "test_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    position = Column(Integer, nullable=False)
    
    # Relationships
    test = relationship("Test", back_populates="test_questions")
    question = relationship("Question", back_populates="test_questions")

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("student_users.id"), nullable=False)
    test_code = Column(String, nullable=False)
    username = Column(String, nullable=False)
    score = Column(Float)
    total_questions = Column(Integer)
    correct_questions = Column(Integer)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    
    # Relationships
    test = relationship("Test", back_populates="test_results")
    student = relationship("StudentUser", back_populates="test_results")
    question_results = relationship("QuestionResult", back_populates="test_result")

class QuestionResult(Base):
    __tablename__ = "question_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    student_answer = Column(Text)
    isCorrect = Column(Boolean, default=False)
    time_spent = Column(Integer)  # in seconds
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    
    # Relationships
    test_result = relationship("TestResult", back_populates="question_results")
    question = relationship("Question", back_populates="question_results")
    chat_messages = relationship("ChatMessage", back_populates="question_result")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    question_result_id = Column(Integer, ForeignKey("question_results.id"), nullable=False)
    sender = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Relationships
    question_result = relationship("QuestionResult", back_populates="chat_messages") 