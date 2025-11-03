"""
MCP Server for Educational Tools
Provides tools that Gemini can use to make intelligent question selection decisions.
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import json


class EducationMCPServer:
    """
    MCP Server that exposes educational tools.
    These tools are called by Gemini to make intelligent decisions.

    For now, tool implementations return mocked data.
    Later, they can be connected to real database queries.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Return tool definitions in Gemini function calling format.

        Gemini will see these tools and decide which ones to call.
        """
        return [
            {
                "name": "get_student_profile",
                "description": "Retrieve complete student knowledge profile including all skill scores, recent performance history, and learning patterns. Use this to understand the student's current knowledge state.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The student's user ID"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "search_questions",
                "description": "Search question database to find practice problems. Can filter by skill, difficulty range, topic, and limit results. Returns list of matching questions with metadata.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill": {
                            "type": "string",
                            "description": "The skill or concept to find questions for (e.g., 'quadratic_equations', 'factoring')"
                        },
                        "difficulty_min": {
                            "type": "number",
                            "description": "Minimum difficulty level (0.0 to 1.0, where 0.0 is easiest)"
                        },
                        "difficulty_max": {
                            "type": "number",
                            "description": "Maximum difficulty level (0.0 to 1.0, where 1.0 is hardest)"
                        },
                        "topic": {
                            "type": "string",
                            "description": "Specific topic within the skill (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of questions to return"
                        }
                    },
                    "required": ["skill"]
                }
            },
            {
                "name": "analyze_recent_performance",
                "description": "Analyze student's recent question attempts to identify patterns, streaks, and areas of struggle. Returns accuracy, average score, and current streak.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The student's user ID"
                        },
                        "n_recent": {
                            "type": "integer",
                            "description": "Number of recent attempts to analyze (default 5)"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "calculate_zpd_difficulty",
                "description": "Calculate optimal Zone of Proximal Development difficulty level based on current skill score and recent accuracy. Returns target difficulty that challenges but doesn't overwhelm.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "current_skill_score": {
                            "type": "number",
                            "description": "Student's current proficiency score for this skill (0-100)"
                        },
                        "recent_accuracy": {
                            "type": "number",
                            "description": "Recent accuracy percentage on this skill (0-100)"
                        }
                    },
                    "required": ["current_skill_score", "recent_accuracy"]
                }
            },
            {
                "name": "identify_skill_gaps",
                "description": "Identify prerequisite skill gaps that may be preventing mastery of target skill. Returns list of weak prerequisite skills that should be strengthened first.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The student's user ID"
                        },
                        "target_skill": {
                            "type": "string",
                            "description": "The skill to check prerequisites for"
                        }
                    },
                    "required": ["user_id", "target_skill"]
                }
            },
            {
                "name": "get_skill_prerequisites",
                "description": "Get ordered list of prerequisite skills from knowledge graph. Returns the dependency chain needed to master a skill.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "The skill to get prerequisites for"
                        }
                    },
                    "required": ["skill_name"]
                }
            },
            {
                "name": "predict_success_probability",
                "description": "Predict likelihood of student answering a specific question correctly using performance modeling. Returns probability (0.0-1.0) and confidence level.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The student's user ID"
                        },
                        "question_id": {
                            "type": "integer",
                            "description": "The question ID to predict success for"
                        }
                    },
                    "required": ["user_id", "question_id"]
                }
            }
        ]

    # ==================== TOOL IMPLEMENTATIONS (MOCKED) ====================

    def execute_tool(self, tool_name: str, tool_args: Dict) -> Dict:
        """
        Execute a tool based on its name.
        This is called when Gemini decides to use a tool.
        """
        if tool_name == "get_student_profile":
            return self._get_student_profile(tool_args["user_id"])

        elif tool_name == "search_questions":
            return self._search_questions(
                skill=tool_args.get("skill"),
                difficulty_min=tool_args.get("difficulty_min", 0.0),
                difficulty_max=tool_args.get("difficulty_max", 1.0),
                topic=tool_args.get("topic"),
                limit=tool_args.get("limit", 10)
            )

        elif tool_name == "analyze_recent_performance":
            return self._analyze_recent_performance(
                tool_args["user_id"],
                tool_args.get("n_recent", 5)
            )

        elif tool_name == "calculate_zpd_difficulty":
            return self._calculate_zpd_difficulty(
                tool_args["current_skill_score"],
                tool_args["recent_accuracy"]
            )

        elif tool_name == "identify_skill_gaps":
            return self._identify_skill_gaps(
                tool_args["user_id"],
                tool_args["target_skill"]
            )

        elif tool_name == "get_skill_prerequisites":
            return self._get_skill_prerequisites(
                tool_args["skill_name"]
            )

        elif tool_name == "predict_success_probability":
            return self._predict_success_probability(
                tool_args["user_id"],
                tool_args["question_id"]
            )

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    # ==================== MOCKED TOOL IMPLEMENTATIONS ====================

    def _get_student_profile(self, user_id: int) -> Dict:
        """MOCKED: Get student's knowledge profile"""
        # Realistic mocked data
        return {
            "user_id": user_id,
            "grade": "10",
            "profile": {
                "last_updated": datetime.utcnow().isoformat(),
                "subjects": {
                    "mathematics": {
                        "topics": [
                            {
                                "topic_name": "Quadratic Equations",
                                "overall_proficiency": 65,
                                "skills": {
                                    "solving_by_factoring": {"score": 70, "questions": ["1", "2", "3"]},
                                    "quadratic_formula": {"score": 60, "questions": ["4", "5"]},
                                    "completing_the_square": {"score": 55, "questions": ["6"]}
                                }
                            },
                            {
                                "topic_name": "Linear Equations",
                                "overall_proficiency": 85,
                                "skills": {
                                    "solving_one_variable": {"score": 90, "questions": ["7", "8", "9"]},
                                    "solving_two_variables": {"score": 80, "questions": ["10", "11"]}
                                }
                            },
                            {
                                "topic_name": "Arithmetic Progressions",
                                "overall_proficiency": 45,
                                "skills": {
                                    "finding_nth_term": {"score": 50, "questions": ["12"]},
                                    "sum_of_terms": {"score": 40, "questions": []}
                                }
                            }
                        ]
                    }
                }
            }
        }

    def _search_questions(self, skill: str, difficulty_min: float = 0.0,
                         difficulty_max: float = 1.0, topic: str = None,
                         limit: int = 10) -> Dict:
        """MOCKED: Search for questions"""
        # Realistic mocked question data
        all_questions = [
            {
                "id": 101,
                "question_text": "Solve for x: x² + 5x + 6 = 0",
                "difficulty": 0.4,
                "topic": "Quadratic Equations",
                "skill": "solving_by_factoring",
                "skills_tested": {
                    "skills": [
                        {"skill_name": "solving_by_factoring", "difficulty": 0.4, "weight": 1.0}
                    ]
                }
            },
            {
                "id": 102,
                "question_text": "Find the roots of 2x² - 7x + 3 = 0 using the quadratic formula",
                "difficulty": 0.6,
                "topic": "Quadratic Equations",
                "skill": "quadratic_formula",
                "skills_tested": {
                    "skills": [
                        {"skill_name": "quadratic_formula", "difficulty": 0.6, "weight": 1.0}
                    ]
                }
            },
            {
                "id": 103,
                "question_text": "Solve by completing the square: x² + 8x - 9 = 0",
                "difficulty": 0.7,
                "topic": "Quadratic Equations",
                "skill": "completing_the_square",
                "skills_tested": {
                    "skills": [
                        {"skill_name": "completing_the_square", "difficulty": 0.7, "weight": 1.0}
                    ]
                }
            },
            {
                "id": 104,
                "question_text": "Find the 10th term of the AP: 5, 9, 13, 17, ...",
                "difficulty": 0.3,
                "topic": "Arithmetic Progressions",
                "skill": "finding_nth_term",
                "skills_tested": {
                    "skills": [
                        {"skill_name": "finding_nth_term", "difficulty": 0.3, "weight": 1.0}
                    ]
                }
            },
            {
                "id": 105,
                "question_text": "Find the sum of first 20 terms of AP: 2, 5, 8, 11, ...",
                "difficulty": 0.5,
                "topic": "Arithmetic Progressions",
                "skill": "sum_of_terms",
                "skills_tested": {
                    "skills": [
                        {"skill_name": "sum_of_terms", "difficulty": 0.5, "weight": 1.0}
                    ]
                }
            }
        ]

        # Filter questions based on criteria
        filtered_questions = []
        for q in all_questions:
            # Check skill match
            if skill and skill.lower() not in q["skill"].lower():
                continue

            # Check difficulty range
            if q["difficulty"] < difficulty_min or q["difficulty"] > difficulty_max:
                continue

            # Check topic match
            if topic and topic.lower() not in q["topic"].lower():
                continue

            filtered_questions.append(q)

            if len(filtered_questions) >= limit:
                break

        return {
            "questions": filtered_questions,
            "count": len(filtered_questions),
            "total_available": len(all_questions)
        }

    def _analyze_recent_performance(self, user_id: int, n_recent: int = 5) -> Dict:
        """MOCKED: Analyze recent performance"""
        # Simulated recent session data
        return {
            "user_id": user_id,
            "n_analyzed": 5,
            "accuracy": 0.6,  # 60% correct
            "average_score": 6.5,  # out of 10
            "streak": 2,  # 2 correct in a row
            "recent_sessions": [
                {"question_id": 98, "skill": "quadratic_formula", "score": 8.0, "correct": True},
                {"question_id": 99, "skill": "quadratic_formula", "score": 7.0, "correct": True},
                {"question_id": 100, "skill": "completing_the_square", "score": 4.0, "correct": False},
                {"question_id": 97, "skill": "solving_by_factoring", "score": 9.0, "correct": True},
                {"question_id": 96, "skill": "solving_by_factoring", "score": 5.0, "correct": False}
            ],
            "struggling_skills": ["completing_the_square"],
            "strong_skills": ["solving_by_factoring"]
        }

    def _calculate_zpd_difficulty(self, current_skill_score: float,
                                  recent_accuracy: float) -> Dict:
        """MOCKED: Calculate optimal difficulty"""
        # Zone of Proximal Development algorithm
        base_difficulty = current_skill_score / 100.0

        if recent_accuracy >= 80:
            # Doing well, increase difficulty
            target = min(1.0, base_difficulty + 0.15)
            reasoning = "Student performing well, increasing challenge level"
        elif recent_accuracy >= 60:
            # Steady performance, slight increase
            target = min(1.0, base_difficulty + 0.05)
            reasoning = "Steady progress, maintaining moderate challenge"
        elif recent_accuracy >= 40:
            # Struggling, maintain level
            target = base_difficulty
            reasoning = "Some difficulty detected, maintaining current level"
        else:
            # Failing, decrease difficulty
            target = max(0.1, base_difficulty - 0.15)
            reasoning = "Significant struggle detected, reducing difficulty to rebuild confidence"

        return {
            "target_difficulty": round(target, 2),
            "current_skill_score": current_skill_score,
            "recent_accuracy": recent_accuracy,
            "reasoning": reasoning,
            "recommended_range": {
                "min": max(0.0, round(target - 0.05, 2)),
                "max": min(1.0, round(target + 0.05, 2))
            }
        }

    def _identify_skill_gaps(self, user_id: int, target_skill: str) -> Dict:
        """MOCKED: Identify prerequisite gaps"""
        # Simulated gap analysis
        skill_gap_data = {
            "quadratic_formula": [
                {"skill": "algebraic_manipulation", "current_score": 55, "target_score": 70, "gap": 15},
                {"skill": "square_roots", "current_score": 65, "target_score": 70, "gap": 5}
            ],
            "completing_the_square": [
                {"skill": "algebraic_manipulation", "current_score": 55, "target_score": 75, "gap": 20},
                {"skill": "perfect_squares", "current_score": 50, "target_score": 70, "gap": 20}
            ],
            "sum_of_terms": [
                {"skill": "finding_nth_term", "current_score": 50, "target_score": 70, "gap": 20},
                {"skill": "basic_arithmetic", "current_score": 80, "target_score": 70, "gap": 0}
            ]
        }

        gaps = skill_gap_data.get(target_skill, [])

        return {
            "target_skill": target_skill,
            "gaps": [g for g in gaps if g["gap"] > 0],
            "total_gaps": len([g for g in gaps if g["gap"] > 0]),
            "recommendation": "Focus on prerequisite skills before advancing" if gaps else "No major gaps detected"
        }

    def _get_skill_prerequisites(self, skill_name: str) -> Dict:
        """MOCKED: Get skill prerequisites"""
        # Simulated knowledge graph
        prerequisite_map = {
            "quadratic_equations": ["linear_equations", "factoring", "algebraic_manipulation"],
            "quadratic_formula": ["quadratic_equations", "square_roots", "algebraic_manipulation"],
            "completing_the_square": ["quadratic_equations", "perfect_squares", "algebraic_manipulation"],
            "solving_by_factoring": ["quadratic_equations", "factoring", "zero_product_property"],
            "sum_of_terms": ["finding_nth_term", "arithmetic_progressions", "basic_arithmetic"],
            "finding_nth_term": ["arithmetic_progressions", "patterns", "basic_arithmetic"]
        }

        prerequisites = prerequisite_map.get(skill_name, [])

        return {
            "skill": skill_name,
            "prerequisites": prerequisites,
            "prerequisite_count": len(prerequisites),
            "learning_order": prerequisites  # In order of importance
        }

    def _predict_success_probability(self, user_id: int, question_id: int) -> Dict:
        """MOCKED: Predict success probability"""
        # Simulated prediction model
        # In reality, this would use ML or statistical model

        # Mock: Use question difficulty and student skill level
        question_difficulties = {
            101: 0.4,
            102: 0.6,
            103: 0.7,
            104: 0.3,
            105: 0.5
        }

        question_difficulty = question_difficulties.get(question_id, 0.5)

        # Simple heuristic: probability = 1 - abs(student_level - question_difficulty)
        # Assuming student at 0.65 level overall
        student_level = 0.65
        probability = max(0.1, min(0.9, 1 - abs(student_level - question_difficulty)))

        return {
            "question_id": question_id,
            "predicted_probability": round(probability, 2),
            "confidence": "medium",
            "factors": {
                "question_difficulty": question_difficulty,
                "student_skill_level": student_level,
                "recent_performance": 0.6
            },
            "recommendation": "Good challenge level" if 0.4 <= probability <= 0.7 else
                            ("Too easy" if probability > 0.7 else "Too difficult")
        }
