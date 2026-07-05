from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, ForeignKey, DateTime, Text, Table, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


# ── IB Math Content Layer ────────────────────────────────────────────────────

class DifficultyTier(str, enum.Enum):
    SL_FOUNDATION = "SL_foundation"
    SL_CHALLENGE = "SL_challenge"


class CommandTerm(str, enum.Enum):
    FIND = "find"
    CALCULATE = "calculate"
    HENCE = "hence"
    DEDUCE = "deduce"
    SHOW = "show"
    WRITE_DOWN = "write_down"
    DETERMINE = "determine"
    SOLVE = "solve"


seed_problem_kc = Table(
    "seed_problem_kc",
    Base.metadata,
    Column("seed_problem_id", Integer, ForeignKey("seed_problems.id"), primary_key=True),
    Column("knowledge_component_id", Integer, ForeignKey("knowledge_components.id"), primary_key=True),
)

kc_prerequisite = Table(
    "kc_prerequisite",
    Base.metadata,
    Column("kc_id", Integer, ForeignKey("knowledge_components.id"), primary_key=True),
    Column("prereq_id", Integer, ForeignKey("knowledge_components.id"), primary_key=True),
)


class KnowledgeComponent(Base):
    __tablename__ = "knowledge_components"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    ib_topic_ref = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    difficulty_tier = Column(String, nullable=False)
    curriculum = Column(String, nullable=False, default="IB_Math_AA_SL")

    prerequisites = relationship(
        "KnowledgeComponent",
        secondary=kc_prerequisite,
        primaryjoin=id == kc_prerequisite.c.kc_id,
        secondaryjoin=id == kc_prerequisite.c.prereq_id,
        backref="dependents",
    )
    seed_problems = relationship("SeedProblem", secondary=seed_problem_kc, back_populates="knowledge_components")


class SeedProblem(Base):
    __tablename__ = "seed_problems"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    content = Column(Text, nullable=False)
    command_term = Column(String, nullable=False)
    ib_topic_ref = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    difficulty_tier = Column(String, nullable=False)
    difficulty_estimate = Column(Float, nullable=False)  # 1.0–5.0
    answer = Column(Text, nullable=False)
    worked_solution = Column(Text, nullable=False)
    distractors = Column(JSON, nullable=True)  # list of {value, misconception_label}
    hint_l1 = Column(Text, nullable=False)
    hint_l2 = Column(Text, nullable=False)
    hint_l3 = Column(Text, nullable=False)
    re_solve_verified = Column(Boolean, nullable=False, default=False)
    curriculum = Column(String, nullable=False, default="IB_Math_AA_SL")
    created_at = Column(DateTime, default=datetime.utcnow)

    knowledge_components = relationship("KnowledgeComponent", secondary=seed_problem_kc, back_populates="seed_problems")


# ── Existing models ───────────────────────────────────────────────────────────

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
    learning_goals = Column(JSON, nullable=True)
    knowledge_profile = Column(JSON, nullable=True)
    learning_style = Column(String, nullable=True)
    preferred_session_length = Column(Integer, nullable=True)  # in minutes
    last_active = Column(DateTime, nullable=True)

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
    difficulty = Column(Float, nullable=True) # e.g., 0.5, 1.0, 1.5
    
    # Solution information (stored as JSON)
    solution = Column(JSON, nullable=True)  # Object with introduction, steps array, learning_tip, related_concepts
    
    # Additional information (stored as JSON)
    common_mistakes = Column(JSON, nullable=True)  # Array of common mistakes
    teacher_notes = Column(JSON, nullable=True)  # Array of teacher notes

    # More data to be used for AI personalization
    prerequisites = Column(JSON, nullable=True)
    skills_tested = Column(JSON, nullable=True)

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
    difficulty = Column(Float, nullable=True) # e.g., 0.5, 1.0, 1.5

    # Solution information (stored as JSON)
    solution = Column(JSON, nullable=True)  # Object with introduction, steps array, learning_tip, related_concepts
    
    # Mark scheme information (stored as JSON)
    common_mistakes = Column(JSON, nullable=True)  # Array of common mistakes
    teacher_notes = Column(JSON, nullable=True)  # Array of teacher notes

    # More data to be used for AI personalization
    prerequisites = Column(JSON, nullable=True)
    skills_tested = Column(JSON, nullable=True)

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
    difficulty = Column(Float, nullable=True) # e.g., 0.5, 1.0, 1.5
    
    # Mark scheme information (stored as JSON)
    total_marks = Column(Integer, nullable=True)
    marking_criteria = Column(JSON, nullable=True)  # Array of marking criteria with marks
    common_mistakes = Column(JSON, nullable=True)  # Array of common mistakes with deductions
    teacher_notes = Column(JSON, nullable=True)  # Array of teacher notes

    # More data to be used for AI personalization
    prerequisites = Column(JSON, nullable=True)
    skills_tested = Column(JSON, nullable=True)

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
    attempts = Column(Integer, default=0, nullable=True)
    time_spent = Column(Integer, nullable=True)
    hint_used = Column(Boolean, default=False, nullable=True)
    solution_viewed = Column(Boolean, default=False, nullable=True)
    image_path = Column(String, nullable=True)
    image_uploaded_at = Column(DateTime, nullable=True)
    mobile_connected_at = Column(DateTime, nullable=True)
    grading_result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    confidence_level = Column(Integer, nullable=True)
    
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
    skills_tested = Column(JSON, nullable=True)
    confidence_level = Column(Integer, nullable=True)
    
    # Relationships
    student = relationship("StudentUser", foreign_keys=[student_id])

class AITutorSession(Base):
    __tablename__ = "ai_tutor_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("student_users.id"), nullable=False)
    room_uuid = Column(String, nullable=False)
    whiteboard_data = Column(JSON, nullable=True)  # Store whiteboard state
    chat_history = Column(JSON, nullable=True)  # Store conversation history
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    session_summary = Column(Text, nullable=True)
    identified_misconceptions = Column(JSON, nullable=True)
    learning_goals_achieved = Column(JSON, nullable=True)
    
    # Relationship
    student = relationship("StudentUser", back_populates="ai_tutor_sessions")


# Add the relationship to StudentUser
StudentUser.ai_tutor_sessions = relationship("AITutorSession", back_populates="student")

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # suggestion, feature, bug, other
    description = Column(Text, nullable=False)
    email = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("student_users.id"), nullable=True)
    status = Column(String, default="pending")  # pending, reviewed, resolved
    
    # Relationship
    student = relationship("StudentUser", back_populates="feedbacks")

# Add the relationship to StudentUser
StudentUser.feedbacks = relationship("UserFeedback", back_populates="student")


# ── TASA Knowledge Model ──────────────────────────────────────────────────────
# Replaces the static StudentUser.knowledge_profile JSON with a dynamic, per-KC
# probabilistic model (BKT + forgetting curve) plus narrative persona / event
# memory banks. See docs/tasa-knowledge-model.md.


class QuestionKC(Base):
    """Maps a graded question to one or more knowledge components.

    `question_id` is polymorphic across the graded-question tables (NCERT
    examples/exercises, PYQs, …), so `practice_mode` disambiguates which table
    the id refers to — there is no single FK target.
    """
    __tablename__ = "question_kc"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, nullable=False, index=True)
    practice_mode = Column(String, nullable=False)
    kc_id = Column(Integer, ForeignKey("knowledge_components.id"), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)

    kc = relationship("KnowledgeComponent")

    __table_args__ = (
        UniqueConstraint("question_id", "practice_mode", "kc_id", name="uq_question_kc"),
    )


class KCMastery(Base):
    """L1: BKT mastery state for one (student, knowledge component)."""
    __tablename__ = "kc_mastery"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("student_users.id"), nullable=False, index=True)
    kc_id = Column(Integer, ForeignKey("knowledge_components.id"), nullable=False, index=True)
    p_mastery = Column(Float, nullable=False)          # BKT posterior in [0, 1]
    n_attempts = Column(Integer, nullable=False, default=0)
    n_correct = Column(Integer, nullable=False, default=0)
    last_practiced_at = Column(DateTime, nullable=True)  # drives the forgetting curve
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    kc = relationship("KnowledgeComponent")

    __table_args__ = (
        UniqueConstraint("user_id", "kc_id", name="uq_kc_mastery_user_kc"),
    )


class StudentPersona(Base):
    """L2: an embedded natural-language persona line for a student."""
    __tablename__ = "student_personas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("student_users.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    concept_keywords = Column(JSON, nullable=True)   # list of KC slugs
    embedding = Column(JSON, nullable=True)          # text-embedding-004 vector
    created_at = Column(DateTime, default=datetime.utcnow)


class StudentMemoryEvent(Base):
    """L3: an embedded, timestamped learning episode (usually a mistake)."""
    __tablename__ = "student_memory_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("student_users.id"), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    concept_keywords = Column(JSON, nullable=True)   # list of KC slugs
    embedding = Column(JSON, nullable=True)
    event_at = Column(DateTime, default=datetime.utcnow)
    source_grading_id = Column(Integer, ForeignKey("grading_sessions.id"), nullable=True)
