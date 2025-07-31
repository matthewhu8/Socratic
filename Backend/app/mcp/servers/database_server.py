"""
Database MCP Server for Socratic application.
Provides direct PostgreSQL database operations for AI models.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from mcp.server import Server
    from mcp.types import (
        Tool, 
        TextContent, 
        CallToolResult
    )
    from mcp.server.stdio import stdio_server
except ImportError:
    # Fallback for development
    class Server:
        def __init__(self, name: str, version: str):
            self.name = name
            self.version = version
        
        def list_tools(self):
            def decorator(func):
                return func
            return decorator
        
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
    
    def stdio_server():
        def decorator(func):
            return func
        return decorator
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema
    
    class TextContent:
        def __init__(self, text: str):
            self.text = text
    
    class CallToolResult:
        def __init__(self, content: List):
            self.content = content

from sqlalchemy import create_engine, and_, desc, func, text
from sqlalchemy.orm import sessionmaker, Session

# Import models
from app.database.models import StudentUser, PYQs, GradingSession, NcertExamples, NcertExercises
from app.services.knowledge_profile_service import KnowledgeProfileService

logger = logging.getLogger(__name__)

class DatabaseMCPServer:
    """MCP Server for direct database operations"""
    
    def __init__(self):
        self.server = Server("database-server", "1.0.0")
        self.db_engine = None
        self.db_session_maker = None
        self._setup_database()
        self._register_tools()
    
    def _setup_database(self):
        """Initialize database connection"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable required")
            
            self.db_engine = create_engine(database_url)
            self.db_session_maker = sessionmaker(bind=self.db_engine)
            logger.info("Database connection initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            raise
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="query_students",
                    description="Query student information and profiles",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "Specific student ID to query"},
                            "email": {"type": "string", "description": "Student email to search"},
                            "grade": {"type": "string", "description": "Filter by grade level"},
                            "limit": {"type": "integer", "default": 10, "description": "Maximum results to return"}
                        }
                    }
                ),
                Tool(
                    name="query_questions",
                    description="Query questions from various sources (NCERT, PYQs, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source_type": {
                                "type": "string", 
                                "enum": ["ncert_examples", "ncert_exercises", "pyqs"],
                                "description": "Type of questions to query"
                            },
                            "chapter": {"type": "string", "description": "Filter by chapter name"},
                            "topic": {"type": "string", "description": "Filter by topic"},
                            "difficulty_min": {"type": "number", "description": "Minimum difficulty level"},
                            "difficulty_max": {"type": "number", "description": "Maximum difficulty level"},
                            "skills": {"type": "array", "items": {"type": "string"}, "description": "Required skills"},
                            "limit": {"type": "integer", "default": 10}
                        },
                        "required": ["source_type"]
                    }
                ),
                Tool(
                    name="query_grading_sessions",
                    description="Query grading session history and performance data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "Filter by student ID"},
                            "practice_mode": {"type": "string", "description": "Filter by practice mode"},
                            "date_from": {"type": "string", "format": "date", "description": "Start date for filtering"},
                            "date_to": {"type": "string", "format": "date", "description": "End date for filtering"},
                            "min_score": {"type": "number", "description": "Minimum score filter"},
                            "limit": {"type": "integer", "default": 50}
                        }
                    }
                ),
                Tool(
                    name="update_knowledge_profile",
                    description="Update a student's knowledge profile",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "Student ID"},
                            "profile_updates": {
                                "type": "object",
                                "description": "Profile updates to apply"
                            },
                            "merge_strategy": {
                                "type": "string",
                                "enum": ["replace", "merge", "append"],
                                "default": "merge",
                                "description": "How to apply updates"
                            }
                        },
                        "required": ["student_id", "profile_updates"]
                    }
                ),
                Tool(
                    name="create_grading_session",
                    description="Create a new grading session record",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer"},
                            "question_id": {"type": "integer"},
                            "question_text": {"type": "string"},
                            "correct_solution": {"type": "string"},
                            "student_answers": {"type": "object"},
                            "score": {"type": "number"},
                            "feedback": {"type": "string"},
                            "practice_mode": {"type": "string"},
                            "time_spent": {"type": "integer"},
                            "skills_tested": {"type": "object"}
                        },
                        "required": ["student_id", "score"]
                    }
                ),
                Tool(
                    name="get_student_analytics",
                    description="Get comprehensive analytics for a student",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "Student ID"},
                            "time_window_days": {"type": "integer", "default": 30, "description": "Analysis window in days"},
                            "include_comparisons": {"type": "boolean", "default": false, "description": "Include peer comparisons"}
                        },
                        "required": ["student_id"]
                    }
                )
            ]
        
        @self.server.call_tool() 
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "query_students":
                    result = await self._query_students(**arguments)
                elif name == "query_questions":
                    result = await self._query_questions(**arguments)
                elif name == "query_grading_sessions":
                    result = await self._query_grading_sessions(**arguments)
                elif name == "update_knowledge_profile":
                    result = await self._update_knowledge_profile(**arguments)
                elif name == "create_grading_session":
                    result = await self._create_grading_session(**arguments)
                elif name == "get_student_analytics":
                    result = await self._get_student_analytics(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(content=[TextContent(text=json.dumps(result))])
                
            except Exception as e:
                logger.error(f"Tool call error for {name}: {e}")
                error_result = {"error": str(e)}
                return CallToolResult(content=[TextContent(text=json.dumps(error_result))])
    
    # Tool implementation methods
    async def _query_students(self, 
                            student_id: Optional[int] = None,
                            email: Optional[str] = None,
                            grade: Optional[str] = None,
                            limit: int = 10) -> Dict:
        """Query student information and profiles"""
        try:
            with self.db_session_maker() as db:
                query = db.query(StudentUser)
                
                if student_id:
                    query = query.filter(StudentUser.id == student_id)
                if email:
                    query = query.filter(StudentUser.email.ilike(f"%{email}%"))
                if grade:
                    query = query.filter(StudentUser.grade == grade)
                
                students = query.limit(limit).all()
                
                result = []
                for student in students:
                    student_data = {
                        "id": student.id,
                        "name": student.name,
                        "email": student.email,
                        "grade": student.grade,
                        "created_at": student.created_at.isoformat() if student.created_at else None,
                        "knowledge_profile": student.knowledge_profile
                    }
                    result.append(student_data)
                
                return {"students": result, "count": len(result)}
                
        except Exception as e:
            logger.error(f"Error querying students: {e}")
            return {"error": f"Query failed: {str(e)}"}
    
    async def _query_questions(self,
                             source_type: str,
                             chapter: Optional[str] = None,
                             topic: Optional[str] = None,
                             difficulty_min: Optional[float] = None,
                             difficulty_max: Optional[float] = None,
                             skills: Optional[List[str]] = None,
                             limit: int = 10) -> Dict:
        """Query questions from various sources"""
        try:
            with self.db_session_maker() as db:
                if source_type == "ncert_examples":
                    query = db.query(NcertExamples)
                elif source_type == "ncert_exercises":
                    query = db.query(NcertExercises)
                elif source_type == "pyqs":
                    query = db.query(PYQs)
                else:
                    return {"error": f"Invalid source_type: {source_type}"}
                
                # Apply filters
                if chapter:
                    query = query.filter(getattr(query.column_descriptions[0]['type'], 'chapter').ilike(f"%{chapter}%"))
                if topic:
                    query = query.filter(getattr(query.column_descriptions[0]['type'], 'topic').ilike(f"%{topic}%"))
                if difficulty_min is not None:
                    query = query.filter(getattr(query.column_descriptions[0]['type'], 'difficulty') >= difficulty_min)
                if difficulty_max is not None:
                    query = query.filter(getattr(query.column_descriptions[0]['type'], 'difficulty') <= difficulty_max)
                
                questions = query.limit(limit).all()
                
                result = []
                for q in questions:
                    question_data = {
                        "id": q.id,
                        "source_type": source_type,
                        "question_text": q.question_text,
                        "chapter": getattr(q, 'chapter', None),
                        "topic": getattr(q, 'topic', None),
                        "difficulty": getattr(q, 'difficulty', None),
                        "skills_tested": getattr(q, 'skills_tested', None),
                        "answer": getattr(q, 'answer', None),
                        "solution": getattr(q, 'solution', None)
                    }
                    
                    # Add source-specific fields
                    if source_type == "pyqs":
                        question_data.update({
                            "year": getattr(q, 'source_year', None),
                            "max_marks": getattr(q, 'max_marks', None)
                        })
                    
                    result.append(question_data)
                
                return {"questions": result, "count": len(result), "source_type": source_type}
                
        except Exception as e:
            logger.error(f"Error querying questions: {e}")
            return {"error": f"Query failed: {str(e)}"}
    
    async def _query_grading_sessions(self,
                                    student_id: Optional[int] = None,
                                    practice_mode: Optional[str] = None,
                                    date_from: Optional[str] = None,
                                    date_to: Optional[str] = None,
                                    min_score: Optional[float] = None,
                                    limit: int = 50) -> Dict:
        """Query grading session history and performance data"""
        try:
            with self.db_session_maker() as db:
                query = db.query(GradingSession)
                
                if student_id:
                    query = query.filter(GradingSession.student_id == student_id)
                if practice_mode:
                    query = query.filter(GradingSession.practice_mode == practice_mode)
                if date_from:
                    date_from_obj = datetime.fromisoformat(date_from)
                    query = query.filter(GradingSession.created_at >= date_from_obj)
                if date_to:
                    date_to_obj = datetime.fromisoformat(date_to)
                    query = query.filter(GradingSession.created_at <= date_to_obj)
                if min_score is not None:
                    query = query.filter(GradingSession.score >= min_score)
                
                sessions = query.order_by(desc(GradingSession.created_at)).limit(limit).all()
                
                result = []
                for session in sessions:
                    session_data = {
                        "id": session.id,
                        "student_id": session.student_id,
                        "question_id": session.question_id,
                        "question_text": session.question_text,
                        "score": session.score,
                        "feedback": session.feedback,
                        "practice_mode": session.practice_mode,
                        "time_spent": session.time_spent,
                        "skills_tested": session.skills_tested,
                        "created_at": session.created_at.isoformat() if session.created_at else None
                    }
                    result.append(session_data)
                
                return {"sessions": result, "count": len(result)}
                
        except Exception as e:
            logger.error(f"Error querying grading sessions: {e}")
            return {"error": f"Query failed: {str(e)}"}
    
    async def _update_knowledge_profile(self,
                                      student_id: int,
                                      profile_updates: Dict[str, Any],
                                      merge_strategy: str = "merge") -> Dict:
        """Update a student's knowledge profile"""
        try:
            with self.db_session_maker() as db:
                student = db.query(StudentUser).filter(StudentUser.id == student_id).first()
                if not student:
                    return {"error": "Student not found"}
                
                if merge_strategy == "replace":
                    student.knowledge_profile = profile_updates
                elif merge_strategy == "merge":
                    if student.knowledge_profile:
                        # Deep merge the profiles
                        current_profile = student.knowledge_profile.copy()
                        current_profile.update(profile_updates)
                        student.knowledge_profile = current_profile
                    else:
                        student.knowledge_profile = profile_updates
                elif merge_strategy == "append":
                    # Specific logic for appending to lists/arrays in profile
                    # Implementation would depend on profile structure
                    pass
                
                # Update timestamp
                if isinstance(student.knowledge_profile, dict):
                    student.knowledge_profile['last_updated'] = datetime.now(timezone.utc).isoformat()
                
                db.commit()
                
                return {
                    "status": "success",
                    "student_id": student_id,
                    "updated_profile": student.knowledge_profile
                }
                
        except Exception as e:
            logger.error(f"Error updating knowledge profile: {e}")
            return {"error": f"Update failed: {str(e)}"}
    
    async def _create_grading_session(self,
                                    student_id: int,
                                    score: float,
                                    question_id: Optional[int] = None,
                                    question_text: Optional[str] = None,
                                    correct_solution: Optional[str] = None,
                                    student_answers: Optional[Dict] = None,
                                    feedback: Optional[str] = None,
                                    practice_mode: Optional[str] = None,
                                    time_spent: Optional[int] = None,
                                    skills_tested: Optional[Dict] = None) -> Dict:
        """Create a new grading session record"""
        try:
            with self.db_session_maker() as db:
                grading_session = GradingSession(
                    student_id=student_id,
                    question_id=question_id,
                    question_text=question_text or "",
                    correct_solution=correct_solution or "",
                    student_answers=student_answers or {},
                    score=score,
                    feedback=feedback or "",
                    practice_mode=practice_mode or "unknown",
                    time_spent=time_spent or 0,
                    skills_tested=skills_tested,
                    created_at=datetime.now(timezone.utc)
                )
                
                db.add(grading_session)
                db.commit()
                db.refresh(grading_session)
                
                return {
                    "status": "success",
                    "session_id": grading_session.id,
                    "created_at": grading_session.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating grading session: {e}")
            return {"error": f"Creation failed: {str(e)}"}
    
    async def _get_student_analytics(self,
                                   student_id: int,
                                   time_window_days: int = 30,
                                   include_comparisons: bool = False) -> Dict:
        """Get comprehensive analytics for a student"""
        try:
            with self.db_session_maker() as db:
                student = db.query(StudentUser).filter(StudentUser.id == student_id).first()
                if not student:
                    return {"error": "Student not found"}
                
                # Get recent sessions
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_window_days)
                sessions = db.query(GradingSession).filter(
                    and_(
                        GradingSession.student_id == student_id,
                        GradingSession.created_at >= cutoff_date
                    )
                ).order_by(desc(GradingSession.created_at)).all()
                
                # Calculate analytics
                if not sessions:
                    return {
                        "student_id": student_id,
                        "time_window_days": time_window_days,
                        "total_sessions": 0,
                        "avg_score": 0.0,
                        "improvement_trend": "no_data"
                    }
                
                total_sessions = len(sessions)
                avg_score = sum(s.score or 0 for s in sessions) / total_sessions
                total_time_spent = sum(s.time_spent or 0 for s in sessions)
                
                # Calculate improvement trend
                if total_sessions >= 5:
                    first_half = sessions[total_sessions//2:]
                    second_half = sessions[:total_sessions//2]
                    
                    first_half_avg = sum(s.score or 0 for s in first_half) / len(first_half)
                    second_half_avg = sum(s.score or 0 for s in second_half) / len(second_half)
                    
                    if second_half_avg > first_half_avg + 0.1:
                        trend = "improving"
                    elif second_half_avg < first_half_avg - 0.1:
                        trend = "declining"
                    else:
                        trend = "stable"
                else:
                    trend = "insufficient_data"
                
                # Practice mode breakdown
                mode_stats = {}
                for session in sessions:
                    mode = session.practice_mode or "unknown"
                    if mode not in mode_stats:
                        mode_stats[mode] = {"count": 0, "avg_score": 0.0, "total_score": 0.0}
                    mode_stats[mode]["count"] += 1
                    mode_stats[mode]["total_score"] += session.score or 0
                
                for mode in mode_stats:
                    mode_stats[mode]["avg_score"] = mode_stats[mode]["total_score"] / mode_stats[mode]["count"]
                    del mode_stats[mode]["total_score"]
                
                analytics = {
                    "student_id": student_id,
                    "student_name": student.name,
                    "time_window_days": time_window_days,
                    "total_sessions": total_sessions,
                    "avg_score": round(avg_score, 3),
                    "total_time_spent_minutes": round(total_time_spent / 60, 1),
                    "improvement_trend": trend,
                    "practice_mode_breakdown": mode_stats,
                    "knowledge_profile": student.knowledge_profile
                }
                
                if include_comparisons:
                    # Add peer comparison data
                    # This would require more complex queries comparing with other students
                    analytics["peer_comparison"] = "Not implemented in this version"
                
                return analytics
                
        except Exception as e:
            logger.error(f"Error getting student analytics: {e}")
            return {"error": f"Analytics failed: {str(e)}"}

# Main entry point for MCP server
async def main():
    """Main entry point for the MCP server"""
    try:
        # Initialize the server
        server_instance = DatabaseMCPServer()
        
        # Run the server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run(
                read_stream,
                write_stream,
                server_instance.server.create_initialization_options()
            )
            
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the server
    asyncio.run(main())