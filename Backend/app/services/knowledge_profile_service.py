"""
Service for managing and updating student knowledge profiles
"""
import json
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.database.models import StudentUser, NcertExamples, NcertExercises, PYQs

class KnowledgeProfileService:
    
    @staticmethod
    def initialize_blank_profile() -> Dict:
        """Initialize a blank knowledge profile for any student"""
        return {
            "last_updated": datetime.utcnow().isoformat(),
            "subjects": {
                "mathematics": {
                    "topics": []
                }
            }
        }
    
    @staticmethod
    def get_question_skills_tested(db: Session, question_id: int, practice_mode: str) -> Optional[Dict]:
        """Get the skills_tested JSON for a given question"""
        try:
            if practice_mode == "ncert-examples":
                question = db.query(NcertExamples).filter(NcertExamples.id == question_id).first()
            elif practice_mode == "ncert-exercises":
                question = db.query(NcertExercises).filter(NcertExercises.id == question_id).first()
            elif practice_mode in ["previous-year-questions", "smart-practice"]:
                question = db.query(PYQs).filter(PYQs.id == question_id).first()
            else:
                return None
            
            if question and question.skills_tested:
                print(question.skills_tested)
                return question.skills_tested
            return None
        except Exception as e:
            print(f"Error getting question skills: {e}")
            return None
    
    @staticmethod
    def calculate_expected_performance(current_score: int, difficulty: float) -> float:
        """
        Calculate what score we expect based on student skill vs question difficulty
        
        current_score: 0-100 (student's skill level)
        difficulty: 0.0-1.0 (question difficulty)
        
        Returns: Expected score 0-100
        """
        # Convert student score to 0-1 scale
        student_ability = current_score / 100.0
        
        # Calculate ability gap
        ability_gap = student_ability - difficulty
        
        if ability_gap >= 0.3:      # Much easier than student level
            return min(95, 85 + (ability_gap - 0.3) * 30)
        elif ability_gap >= 0:      # Easier than student level  
            return 70 + ability_gap * 50
        elif ability_gap >= -0.3:   # Harder than student level
            return max(10, 40 + (ability_gap + 0.3) * 100)
        else:                       # Much harder than student level
            return max(5, 10 + (ability_gap + 0.6) * 100)
    
    @staticmethod
    def get_difficulty_multiplier(difficulty: float, actual_score: float) -> float:
        """
        Adjust learning rate based on difficulty and performance
        
        - Solving hard questions correctly gives bigger boosts
        - Failing easy questions gives bigger penalties
        """
        if actual_score >= 0.7:  # Good performance
            # Reward more for harder questions
            return 1.0 + difficulty * 0.5  # 1.0 to 1.5x multiplier
        else:  # Poor performance
            # Penalize more for easier questions  
            return 1.0 + (1.0 - difficulty) * 0.3  # 1.0 to 1.3x multiplier
    
    @staticmethod
    def update_profile_after_grading(
        db: Session,
        user_id: int,
        question_id: int,
        practice_mode: str,
        grading_result: Dict
    ) -> Dict:
        """
        Update knowledge profile after a grading session
        Uses difficulty-aware scoring algorithm
        """
        try:
            # Get the student
            user = db.query(StudentUser).filter(StudentUser.id == user_id).first()
            if not user:
                print(f"User {user_id} not found")
                return None
            print(user.email)
            
            # Get or initialize profile
            profile = user.knowledge_profile
            if not profile:
                print("no profile found, creating new blank profile")
                profile = KnowledgeProfileService.initialize_blank_profile()
                user.knowledge_profile = profile
            
            # Get skills tested for this question
            skills_tested = KnowledgeProfileService.get_question_skills_tested(db, question_id, practice_mode)
            if not skills_tested or 'skills' not in skills_tested:
                print(f"No skills_tested found for question {question_id}")
                return profile
            print(skills_tested)
            
            # Extract score from grading result
            if 'grade' not in grading_result:
                print("No grade found in grading result")
                return profile
            print(grading_result["grade"])
            grade_parts = grading_result["grade"].split('/')
            print(f"Grade parts: {grade_parts}")
            print(f"First part: '{grade_parts[0]}'")
            print(f"Type: {type(grade_parts[0])}")

            numerator = float(grade_parts[0])
            actual_score = numerator / 10
            print(actual_score)
            
            # Update timestamp
            profile['last_updated'] = datetime.utcnow().isoformat()
            
            # Ensure mathematics subject exists
            if 'mathematics' not in profile['subjects']:
                print("math not in profile for some weird reason")
                profile['subjects']['mathematics'] = {'topics': []}
            
            # Process each skill tested
            for skill_data in skills_tested['skills']:
                topic_name = skill_data.get('topic', 'General')
                skill_name = skill_data.get('skill_name', 'Unknown')
                skill_difficulty = skill_data.get('difficulty', 0.5)
                weight = skill_data.get('weight', 1.0)
                
                if topic_name == "Pair of Linear Equations":
                    topic_name = "Pair of Linear Equations in Two Variables"
                
                # Find or create topic
                topic_found = False
                for topic_obj in profile['subjects']['mathematics']['topics']:
                    if topic_obj['topic_name'] == topic_name:
                        topic_found = True
                        
                        # Update or create skill
                        if skill_name not in topic_obj['skills']:
                            topic_obj['skills'][skill_name] = {
                                'score': 50,  # Default starting score
                                'questions': []
                            }
                        
                        # Get current skill score
                        current_score = topic_obj['skills'][skill_name]['score']
                        
                        # Calculate expected performance
                        expected_score = KnowledgeProfileService.calculate_expected_performance(
                            current_score, skill_difficulty
                        )
                        
                        # Calculate performance gap
                        performance_gap = (actual_score * 100) - expected_score
                        
                        # Get difficulty multiplier
                        difficulty_multiplier = KnowledgeProfileService.get_difficulty_multiplier(
                            skill_difficulty, actual_score
                        )
                        
                        # Update score using difficulty-aware algorithm
                        learning_rate = 0.2
                        score_change = learning_rate * weight * performance_gap * difficulty_multiplier
                        new_score = current_score + score_change
                        
                        # Clamp to 0-100 range
                        new_score = max(0, min(100, int(new_score)))
                        
                        # Update skill data
                        topic_obj['skills'][skill_name]['score'] = new_score
                        topic_obj['skills'][skill_name]['questions'].append(str(question_id))
                        
                        print(f"Updated {skill_name}: {current_score} -> {new_score} (gap: {performance_gap:.1f}, mult: {difficulty_multiplier:.2f})")
                        
                        # Update topic overall proficiency (average of all skills)
                        skill_scores = [s['score'] for s in topic_obj['skills'].values()]
                        topic_obj['overall_proficiency'] = int(sum(skill_scores) / len(skill_scores))
                        
                        break
                
                # Create new topic if not found
                if not topic_found:
                    initial_score = max(10, min(60, int(actual_score * 100)))
                    new_topic = {
                        'topic_name': topic_name,
                        'overall_proficiency': initial_score,
                        'skills': {
                            skill_name: {
                                'score': initial_score,
                                'questions': [str(question_id)]
                            }
                        }
                    }
                    print(type(profile["subjects"]["mathematics"]["topics"]))
                    profile['subjects']['mathematics']['topics'].append(new_topic)
                    print(f"Created new topic: {topic_name} with skill: {skill_name} (score: {initial_score})")
            
            # Save updated profile
            print("established profile")
            user.knowledge_profile = profile
            db.commit()
            
            return profile
            
        except Exception as e:
            print(f"Error updating knowledge profile: {e}")
            db.rollback()
            return None
    
    @staticmethod
    def get_student_profile(db: Session, user_id: int) -> Dict:
        """Get student's current knowledge profile"""
        try:
            user = db.query(StudentUser).filter(StudentUser.id == user_id).first()
            if not user:
                return None
            
            if not user.knowledge_profile:
                # Initialize blank profile
                profile = KnowledgeProfileService.initialize_blank_profile()
                user.knowledge_profile = profile
                db.commit()
                return profile
            
            return user.knowledge_profile
            
        except Exception as e:
            print(f"Error getting student profile: {e}")
            return None