from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database.database import get_db
from ..database.models import NcertExamples, NcertExercises, PYQs

router = APIRouter()


class OrmBaseModel(BaseModel):
    class Config:
        from_attributes = True


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

@router.get("/api/questions", response_model=List[QuestionResponse])
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
