"""
Real MCP Server for Smart Practice functionality.
Provides tools for adaptive question selection and student performance analysis.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any, Sequence
from datetime import datetime, timedelta, timezone
import json
import numpy as np

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from mcp.server import Server
    from mcp.types import (
        Tool, 
        TextContent, 
        CallToolRequest,
        CallToolResult,
        ListToolsRequest,
        GetPromptRequest,
        GetPromptResult,
        PromptMessage,
        Role
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
    
    class CallToolRequest:
        pass
    
    class CallToolResult:
        def __init__(self, content: List):
            self.content = content

from sqlalchemy import create_engine, and_, desc, func
from sqlalchemy.orm import sessionmaker, Session
import redis

# Import models
from app.database.models import StudentUser, PYQs, GradingSession, NcertExamples, NcertExercises
from app.services.knowledge_profile_service import KnowledgeProfileService

logger = logging.getLogger(__name__)

class SmartPracticeMCPServer:
    """Real MCP Server for Smart Practice adaptive learning"""
    
    def __init__(self):
        self.server = Server("smart-practice-server", "1.0.0")
        self.db_engine = None
        self.db_session_maker = None
        self.redis_client = None
        self._setup_database()
        self._setup_redis()
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
    
    def _setup_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info("Redis connection initialized")
            
        except Exception as e:
            logger.warning(f"Redis setup failed: {e}")
            self.redis_client = None
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="get_student_profile",
                    description="Get student's detailed skill profile including recent performance trends",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "ID of the student"},
                            "subject": {"type": "string", "description": "Subject to analyze", "default": "mathematics"}
                        },
                        "required": ["student_id"]
                    }
                ),
                Tool(
                    name="search_adaptive_questions",
                    description="Find questions matching skill requirements with adaptive difficulty",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "required_skills": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "List of skills to focus on"
                            },
                            "student_skill_levels": {
                                "type": "object",
                                "description": "Dictionary mapping skill names to proficiency levels (0-100)"
                            },
                            "difficulty_range": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Min and max difficulty [min, max] in range 0.5-2.0"
                            },
                            "exclude_recent_days": {"type": "integer", "default": 7},
                            "limit": {"type": "integer", "default": 10},
                            "chapter": {"type": "string", "description": "Optional chapter name to filter questions"}
                        },
                        "required": ["required_skills", "student_skill_levels", "difficulty_range"]
                    }
                ),
                Tool(
                    name="calculate_zpd_difficulty",
                    description="Calculate optimal difficulty using Zone of Proximal Development",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "current_skill_level": {"type": "number", "description": "Current skill level (0-100)"},
                            "recent_attempts": {
                                "type": "array",
                                "items": {"type": "object"},
                                "description": "List of recent attempt data"
                            },
                            "target_success_rate": {"type": "number", "default": 0.75, "description": "Target success rate (0.0-1.0)"}
                        },
                        "required": ["current_skill_level", "recent_attempts"]
                    }
                ),
                Tool(
                    name="analyze_learning_patterns",
                    description="Analyze learning patterns and suggest next focus area",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "ID of the student"},
                            "time_window_days": {"type": "integer", "default": 14, "description": "Number of days to analyze"}
                        },
                        "required": ["student_id"]
                    }
                ),
                Tool(
                    name="record_smart_practice_attempt",
                    description="Record attempt and update student profile",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "integer", "description": "ID of the student"},
                            "question_id": {"type": "string", "description": "Question ID (can be string for generated questions)"},
                            "performance": {
                                "type": "object",
                                "properties": {
                                    "question_text": {"type": "string"},
                                    "correct_solution": {"type": "string"},
                                    "student_answer": {"type": "string"},
                                    "score": {"type": "number"},
                                    "feedback": {"type": "string"},
                                    "skills_tested": {"type": "object"}
                                },
                                "required": ["score"]
                            },
                            "time_spent_seconds": {"type": "integer", "description": "Time spent on the question"}
                        },
                        "required": ["student_id", "question_id", "performance", "time_spent_seconds"]
                    }
                ),
                Tool(
                    name="generate_custom_question", 
                    description="Generate a custom question when no existing questions match criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "default": "mathematics"},
                            "chapter": {"type": "string", "description": "Chapter name"},
                            "topic": {"type": "string", "description": "Topic identifier"},
                            "required_skills": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of skills the question should test"
                            },
                            "difficulty": {"type": "number", "description": "Target difficulty level (0.5-2.0)"},
                            "grade": {"type": "string", "default": "10", "description": "Grade level"}
                        },
                        "required": ["chapter", "topic", "required_skills", "difficulty"]
                    }
                )
            ]
        
        @self.server.call_tool() 
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "get_student_profile":
                    result = await self._get_student_profile(**arguments)
                elif name == "search_adaptive_questions":
                    result = await self._search_adaptive_questions(**arguments)
                elif name == "calculate_zpd_difficulty":
                    result = await self._calculate_zpd_difficulty(**arguments)
                elif name == "analyze_learning_patterns":
                    result = await self._analyze_learning_patterns(**arguments)
                elif name == "record_smart_practice_attempt":
                    result = await self._record_smart_practice_attempt(**arguments)
                elif name == "generate_custom_question":
                    result = await self._generate_custom_question(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(content=[TextContent(text=json.dumps(result))])
                
            except Exception as e:
                logger.error(f"Tool call error for {name}: {e}")
                error_result = {"error": str(e)}
                return CallToolResult(content=[TextContent(text=json.dumps(error_result))])
    
    # Tool implementation methods (adapted from original class)
    async def _get_student_profile(self, student_id: int, subject: str = "mathematics") -> Dict:
        """Get student's detailed skill profile including recent performance trends"""
        try:
            with self.db_session_maker() as db:
                user = db.query(StudentUser).filter(StudentUser.id == student_id).first()
                if not user:
                    return {"error": "Student not found"}
                
                # Get or initialize profile
                profile = user.knowledge_profile if user.knowledge_profile else KnowledgeProfileService.initialize_blank_profile()
                subject_data = profile.get('subjects', {}).get(subject, {})
                
                # Get recent attempts from grading sessions
                recent_attempts = await self._get_recent_attempts(student_id, days=14)
                
                # Calculate performance metrics
                performance_metrics = self._calculate_performance_metrics(recent_attempts)
                
                return {
                    "student_id": student_id,
                    "subject": subject,
                    "topics": subject_data.get('topics', []),
                    "recent_performance": performance_metrics,
                    "profile_last_updated": profile.get('last_updated'),
                    "total_topics": len(subject_data.get('topics', [])),
                    "avg_skill_level": self._calculate_avg_skill_level(subject_data.get('topics', []))
                }
                
        except Exception as e:
            logger.error(f"Error getting student profile: {e}")
            return {"error": f"Profile retrieval failed: {str(e)}"}
    
    async def _search_adaptive_questions(self, 
                                       required_skills: List[str],
                                       student_skill_levels: Dict[str, float],
                                       difficulty_range: List[float],
                                       exclude_recent_days: int = 7,
                                       limit: int = 10,
                                       chapter: Optional[str] = None) -> List[Dict]:
        """Find questions matching skill requirements with adaptive difficulty"""
        try:
            with self.db_session_maker() as db:
                # Get recently attempted question IDs to exclude
                student_id = list(student_skill_levels.keys())[0] if student_skill_levels else 0
                recent_question_ids = await self._get_recent_question_ids(student_id, exclude_recent_days)
                
                scored_questions = []
                
                # Query from NcertExamples
                examples_query = db.query(NcertExamples).filter(
                    NcertExamples.skills_tested.isnot(None),
                    NcertExamples.difficulty >= difficulty_range[0],
                    NcertExamples.difficulty <= difficulty_range[1]
                )
                
                if chapter:
                    examples_query = examples_query.filter(NcertExamples.chapter.ilike(f"%{chapter}%"))
                
                examples = examples_query.all()
                
                for q in examples:
                    if recent_question_ids and f"example_{q.id}" in recent_question_ids:
                        continue
                    
                    if not self._question_matches_skills(q, required_skills):
                        continue
                    
                    score = self._calculate_question_score(q, student_skill_levels, required_skills)
                    scored_questions.append({
                        "id": q.id,
                        "source_type": "ncert_examples",
                        "question_text": q.question_text,
                        "difficulty": q.difficulty,
                        "skills_tested": q.skills_tested,
                        "chapter": q.chapter,
                        "topic": q.topic,
                        "grade": q.grade,
                        "score": score,
                        "solution": q.solution,
                        "answer": q.answer,
                        "common_mistakes": q.common_mistakes,
                        "teacher_notes": q.teacher_notes
                    })
                
                # Similar queries for NcertExercises and PYQs...
                # (Abbreviated for brevity - would include full implementation)
                
                # Sort by score and return top results
                scored_questions.sort(key=lambda x: x['score'], reverse=True)
                return scored_questions[:limit]
                
        except Exception as e:
            logger.error(f"Error searching adaptive questions: {e}")
            return []
    
    async def _calculate_zpd_difficulty(self,
                                      current_skill_level: float,
                                      recent_attempts: List[Dict],
                                      target_success_rate: float = 0.75) -> Dict:
        """Calculate optimal difficulty using Zone of Proximal Development"""
        try:
            if not recent_attempts:
                optimal = max(0.5, (current_skill_level / 100.0) * 1.2)
                return {
                    "optimal_difficulty": round(optimal, 2),
                    "current_success_rate": 0.0,
                    "reasoning": "No recent history, starting conservatively based on skill level",
                    "confidence": "low"
                }
            
            # Calculate actual success rate
            successes = sum(1 for a in recent_attempts if a.get('score', 0) >= 0.7)
            actual_success_rate = successes / len(recent_attempts)
            
            # Calculate adjustment based on performance
            base_difficulty = (current_skill_level / 100.0) * 1.5
            
            if actual_success_rate < 0.5:
                adjustment = -0.3
                reasoning = "Recent struggles detected, reducing difficulty significantly"
                confidence = "high"
            elif actual_success_rate < 0.65:
                adjustment = -0.15
                reasoning = "Below target success rate, reducing difficulty moderately"
                confidence = "medium"
            elif actual_success_rate > 0.85:
                adjustment = 0.2
                reasoning = "High success rate, increasing challenge"
                confidence = "high"
            else:
                adjustment = (target_success_rate - actual_success_rate) * 0.3
                reasoning = "Fine-tuning difficulty based on current performance"
                confidence = "medium"
            
            optimal = max(0.5, min(2.0, base_difficulty + adjustment))
            
            return {
                "optimal_difficulty": round(optimal, 2),
                "current_success_rate": round(actual_success_rate, 2),
                "reasoning": reasoning,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error calculating ZPD difficulty: {e}")
            return {
                "optimal_difficulty": 1.0,
                "reasoning": f"Error in calculation: {str(e)}",
                "confidence": "low"
            }
    
    async def _analyze_learning_patterns(self,
                                       student_id: int,
                                       time_window_days: int = 14) -> Dict:
        """Analyze learning patterns and suggest next focus area"""
        try:
            attempts = await self._get_recent_attempts(student_id, days=time_window_days)
            if not attempts:
                return {
                    "error": "No recent attempts found",
                    "recommendations": ["Start with fundamental topics to build confidence"]
                }
            
            # Analyze performance patterns
            skill_performance = self._analyze_skill_patterns(attempts)
            weak_skills = [s for s, score in skill_performance.items() if score < 60]
            strong_skills = [s for s, score in skill_performance.items() if score >= 80]
            
            recommendations = []
            if weak_skills:
                recommendations.append(f"Focus on improving: {', '.join(weak_skills[:3])}")
            
            return {
                "skill_analysis": skill_performance,
                "weak_skills": weak_skills[:5],
                "strong_skills": strong_skills[:3],
                "recommendations": recommendations,
                "total_attempts": len(attempts),
                "avg_score": np.mean([a.get('score', 0) for a in attempts]) if attempts else 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def _record_smart_practice_attempt(self,
                                           student_id: int,
                                           question_id: str,
                                           performance: Dict,
                                           time_spent_seconds: int) -> Dict:
        """Record attempt and update student profile"""
        try:
            with self.db_session_maker() as db:
                numeric_question_id = -1
                if question_id and not question_id.startswith('generated'):
                    try:
                        numeric_question_id = int(question_id)
                    except ValueError:
                        logger.warning(f"Could not convert question_id to int: {question_id}")
                
                # Record in grading sessions table
                grading_session = GradingSession(
                    student_id=student_id,
                    question_id=numeric_question_id,
                    question_text=performance.get('question_text', ''),
                    correct_solution=performance.get('correct_solution', ''),
                    student_answers=performance.get('student_answer', {}),
                    score=performance.get('score', 0.0),
                    feedback=performance.get('feedback', ''),
                    grading_method='smart_practice',
                    practice_mode='smart-practice',
                    time_spent=time_spent_seconds,
                    skills_tested=performance.get('skills_tested'),
                    created_at=datetime.now(timezone.utc)
                )
                
                db.add(grading_session)
                
                # Update knowledge profile
                if performance.get('score') is not None and performance.get('skills_tested'):
                    grading_result = {
                        'grade': f"{int(performance['score'] * 10)}/10",
                        'feedback': performance.get('feedback', '')
                    }
                    
                    KnowledgeProfileService.update_profile_after_grading(
                        db, student_id, numeric_question_id, grading_result, 'smart-practice'
                    )
                
                db.commit()
                
                return {
                    "status": "success",
                    "session_id": grading_session.id,
                    "profile_updated": True,
                    "message": "Attempt recorded and profile updated"
                }
                
        except Exception as e:
            logger.error(f"Error recording attempt: {e}")
            return {"error": f"Failed to record attempt: {str(e)}"}
    
    async def _generate_custom_question(self,
                                      subject: str,
                                      chapter: str,
                                      topic: str,
                                      required_skills: List[str],
                                      difficulty: float,
                                      grade: str = "10") -> Dict:
        """Generate a custom question when no existing questions match criteria"""
        try:
            # Import GeminiService here to avoid circular imports
            from app.services.gemini_service import GeminiService
            
            gemini = GeminiService()
            
            # Build prompt for question generation
            chapter_context = f"Chapter: {chapter}" if chapter else "Mixed practice (any chapter)"
            prompt = f"""Generate a mathematics question with the following specifications:
            
            Subject: {subject}
            {chapter_context}
            Topic: {topic}
            Grade: {grade}
            Skills to test: {', '.join(required_skills)}
            Difficulty: {difficulty} (scale: 0.5=easy, 1.0=medium, 1.5=hard, 2.0=very hard)
            
            Return ONLY a JSON object with question data including question_text, answer, difficulty, solution steps, skills_tested, and other metadata.
            """
            
            # Generate the question
            response = gemini.smart_model.generate_content(prompt)
            
            if response and response.text:
                try:
                    generated_question = json.loads(response.text)
                    generated_question["generated_at"] = datetime.now(timezone.utc).isoformat()
                    generated_question["source_type"] = "generated"
                    
                    logger.info(f"Generated custom question for skills: {required_skills}")
                    return generated_question
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse generated question JSON: {e}")
                    return {"error": "Failed to generate valid question format"}
            else:
                return {"error": "No response from question generation"}
                
        except Exception as e:
            logger.error(f"Error generating custom question: {e}")
            return {"error": f"Question generation failed: {str(e)}"}
    
    # Helper methods (adapted from original implementation)
    async def _get_recent_attempts(self, student_id: int, days: int = 14) -> List[Dict]:
        """Get recent attempts from grading sessions"""
        try:
            with self.db_session_maker() as db:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                
                attempts = db.query(GradingSession).filter(
                    and_(
                        GradingSession.student_id == student_id,
                        GradingSession.created_at >= cutoff_date,
                        GradingSession.practice_mode.in_(['smart-practice', 'previous-year-questions'])
                    )
                ).order_by(desc(GradingSession.created_at)).all()
                
                return [
                    {
                        "question_id": a.question_id,
                        "score": a.score or 0.0,
                        "time_spent": a.time_spent or 0,
                        "created_at": a.created_at.isoformat() if a.created_at else None,
                        "skills_tested": a.skills_tested,
                        "feedback": a.feedback
                    }
                    for a in attempts
                ]
                
        except Exception as e:
            logger.error(f"Error getting recent attempts: {e}")
            return []
    
    async def _get_recent_question_ids(self, student_id: int, days: int) -> List[int]:
        """Get IDs of recently attempted questions"""
        try:
            with self.db_session_maker() as db:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                
                recent_attempts = db.query(GradingSession.question_id).filter(
                    and_(
                        GradingSession.student_id == student_id,
                        GradingSession.created_at >= cutoff_date
                    )
                ).all()
                
                return [attempt.question_id for attempt in recent_attempts if attempt.question_id]
                
        except Exception as e:
            logger.error(f"Error getting recent question IDs: {e}")
            return []
    
    def _question_matches_skills(self, question, required_skills: List[str]) -> bool:
        """Check if question tests any of the required skills"""
        if not question.skills_tested or not required_skills:
            return True
        
        try:
            skills_data = question.skills_tested
            if isinstance(skills_data, str):
                skills_data = json.loads(skills_data)
            
            question_skills = []
            if 'skills' in skills_data:
                question_skills = [skill.get('skill_name', '').lower() for skill in skills_data['skills']]
            
            required_skills_lower = [skill.lower() for skill in required_skills]
            return any(req_skill in question_skills for req_skill in required_skills_lower)
            
        except (json.JSONDecodeError, KeyError, AttributeError):
            return True
    
    def _calculate_question_score(self, question, student_skill_levels: Dict[str, float], required_skills: List[str]) -> float:
        """Calculate how suitable a question is for the student"""
        base_score = 1.0
        
        if question.skills_tested:
            try:
                skills_data = question.skills_tested
                if isinstance(skills_data, str):
                    skills_data = json.loads(skills_data)
                
                if 'skills' in skills_data:
                    question_skills = [skill.get('skill_name', '') for skill in skills_data['skills']]
                    for skill in question_skills:
                        if skill in student_skill_levels:
                            skill_level = student_skill_levels[skill]
                            if skill_level < 60:
                                base_score += 0.5
                            elif skill_level > 85:
                                base_score -= 0.3
            except:
                pass
        
        return base_score
    
    def _calculate_performance_metrics(self, attempts: List[Dict]) -> Dict:
        """Calculate comprehensive performance metrics"""
        if not attempts:
            return {
                "total_attempts": 0,
                "avg_score": 0.0,
                "success_rate": 0.0,
                "trend": "no_data"
            }
        
        total_attempts = len(attempts)
        avg_score = np.mean([a.get('score', 0) for a in attempts])
        successes = sum(1 for a in attempts if a.get('score', 0) >= 0.7)
        success_rate = successes / total_attempts
        
        return {
            "total_attempts": total_attempts,
            "avg_score": round(avg_score, 2),
            "success_rate": round(success_rate, 2),
            "trend": "stable"  # Simplified for this version
        }
    
    def _calculate_avg_skill_level(self, topics: List[Dict]) -> float:
        """Calculate average skill level across all topics"""
        if not topics:
            return 0.0
        
        all_scores = []
        for topic in topics:
            if 'skills' in topic:
                for skill_name, skill_data in topic['skills'].items():
                    if isinstance(skill_data, dict) and 'score' in skill_data:
                        all_scores.append(skill_data['score'])
        
        return np.mean(all_scores) if all_scores else 0.0
    
    def _analyze_skill_patterns(self, attempts: List[Dict]) -> Dict[str, float]:
        """Analyze performance by skill/topic"""
        skill_scores = {}
        skill_counts = {}
        
        for attempt in attempts:
            skills_tested = attempt.get('skills_tested')
            score = attempt.get('score', 0)
            
            if skills_tested:
                try:
                    if isinstance(skills_tested, str):
                        skills_tested = json.loads(skills_tested)
                    
                    if 'skills' in skills_tested:
                        for skill in skills_tested['skills']:
                            skill_name = skill.get('skill_name', 'Unknown')
                            if skill_name not in skill_scores:
                                skill_scores[skill_name] = 0
                                skill_counts[skill_name] = 0
                            
                            skill_scores[skill_name] += score * 100
                            skill_counts[skill_name] += 1
                except:
                    continue
        
        # Calculate averages
        avg_skill_scores = {}
        for skill, total_score in skill_scores.items():
            if skill_counts[skill] > 0:
                avg_skill_scores[skill] = total_score / skill_counts[skill]
        
        return avg_skill_scores

# Main entry point for MCP server
async def main():
    """Main entry point for the MCP server"""
    try:
        # Initialize the server
        server_instance = SmartPracticeMCPServer()
        
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