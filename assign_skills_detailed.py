import psycopg2
import json

# Database connection
conn_string = "postgresql://postgres:ymCIpwSPBraGkdaGRFjACfGJOojfzpOz@shinkansen.proxy.rlwy.net:25660/railway"

def analyze_question_and_assign_skills(question_id, chapter, question_text, solution_text=""):
    """
    Analyze question content and assign appropriate skills with difficulties
    Each skill gets its own difficulty rating based on how that specific skill is tested
    """
    skills_json = {"skills": [], "primary_skill": ""}
    
    # Chapter 1: Real Numbers
    if "Chapter 1" in chapter:
        if "prime factor" in question_text.lower():
            if "lcm" in question_text.lower() or "hcf" in question_text.lower():
                # Both prime factorization and HCF/LCM
                if "three" in question_text.lower() or "120" in question_text or "72" in question_text:
                    # Multiple numbers make it harder
                    skills_json["skills"].append({
                        "topic": "Real Numbers",
                        "skill_name": "Prime Factorization",
                        "difficulty": 0.35,
                        "weight": 0.4
                    })
                    skills_json["skills"].append({
                        "topic": "Real Numbers",
                        "skill_name": "HCF and LCM",
                        "difficulty": 0.45,
                        "weight": 0.6
                    })
                else:
                    skills_json["skills"].append({
                        "topic": "Real Numbers",
                        "skill_name": "Prime Factorization",
                        "difficulty": 0.25,
                        "weight": 0.4
                    })
                    skills_json["skills"].append({
                        "topic": "Real Numbers",
                        "skill_name": "HCF and LCM",
                        "difficulty": 0.30,
                        "weight": 0.6
                    })
                skills_json["primary_skill"] = "HCF and LCM"
            else:
                # Just prime factorization
                if any(num in question_text for num in ["7429", "5005", "3825"]):
                    difficulty = 0.35  # Larger numbers
                else:
                    difficulty = 0.20
                skills_json["skills"].append({
                    "topic": "Real Numbers",
                    "skill_name": "Prime Factorization",
                    "difficulty": difficulty,
                    "weight": 1.0
                })
                skills_json["primary_skill"] = "Prime Factorization"
                
        elif "irrational" in question_text.lower() or "√" in question_text:
            # Irrational numbers
            if "prove" in question_text.lower():
                if any(op in question_text for op in ["+", "-", "*"]):
                    # Operations with irrationals are harder
                    difficulty = 0.70
                else:
                    difficulty = 0.60
            else:
                difficulty = 0.65
            skills_json["skills"].append({
                "topic": "Real Numbers",
                "skill_name": "Irrational Numbers",
                "difficulty": difficulty,
                "weight": 1.0
            })
            skills_json["primary_skill"] = "Irrational Numbers"
            
        elif "end" in question_text.lower() and "digit" in question_text.lower():
            # Divisibility and termination
            skills_json["skills"].append({
                "topic": "Real Numbers",
                "skill_name": "Divisibility and Termination",
                "difficulty": 0.40,
                "weight": 0.7
            })
            skills_json["skills"].append({
                "topic": "Real Numbers",
                "skill_name": "Prime Factorization",
                "difficulty": 0.35,
                "weight": 0.3
            })
            skills_json["primary_skill"] = "Divisibility and Termination"
            
        elif "composite" in question_text.lower():
            # Composite numbers
            skills_json["skills"].append({
                "topic": "Real Numbers",
                "skill_name": "Divisibility and Termination",
                "difficulty": 0.50,
                "weight": 0.6
            })
            skills_json["skills"].append({
                "topic": "Real Numbers",
                "skill_name": "Prime Factorization",
                "difficulty": 0.40,
                "weight": 0.4
            })
            skills_json["primary_skill"] = "Divisibility and Termination"
            
        elif "circular path" in question_text.lower() or "meet again" in question_text.lower():
            # Word problem using LCM
            skills_json["skills"].append({
                "topic": "Real Numbers",
                "skill_name": "HCF and LCM",
                "difficulty": 0.50,
                "weight": 0.7
            })
            skills_json["skills"].append({
                "topic": "Real Numbers",
                "skill_name": "Word Problems",
                "difficulty": 0.45,
                "weight": 0.3
            })
            skills_json["primary_skill"] = "HCF and LCM"
    
    # Chapter 2: Polynomials
    elif "Chapter 2" in chapter:
        if "graph" in question_text.lower() and "zero" in question_text.lower():
            # Finding zeros from graphs
            parts = ["part 1", "part 2", "part 3", "part 4", "part 5", "part 6"]
            difficulty_map = [0.20, 0.20, 0.25, 0.20, 0.20, 0.30]
            
            part_idx = 0
            for i, part in enumerate(parts):
                if part in question_id.lower():
                    part_idx = i
                    break
                    
            skills_json["skills"].append({
                "topic": "Polynomials",
                "skill_name": "Zeros of Polynomials",
                "difficulty": difficulty_map[part_idx],
                "weight": 1.0
            })
            skills_json["primary_skill"] = "Zeros of Polynomials"
            
        elif "cubic" in question_text.lower():
            # Cubic polynomials
            skills_json["skills"].append({
                "topic": "Polynomials",
                "skill_name": "Cubic Polynomials",
                "difficulty": 0.60,
                "weight": 0.6
            })
            skills_json["skills"].append({
                "topic": "Polynomials",
                "skill_name": "Relationship Between Zeros and Coefficients",
                "difficulty": 0.55,
                "weight": 0.4
            })
            skills_json["primary_skill"] = "Cubic Polynomials"
            
        elif "quadratic" in question_text.lower() or "x2" in question_text:
            # Quadratic polynomials
            if "find a quadratic" in question_text.lower():
                # Forming quadratics
                skills_json["skills"].append({
                    "topic": "Polynomials",
                    "skill_name": "Quadratic Polynomials",
                    "difficulty": 0.45,
                    "weight": 0.5
                })
                skills_json["skills"].append({
                    "topic": "Polynomials",
                    "skill_name": "Relationship Between Zeros and Coefficients",
                    "difficulty": 0.45,
                    "weight": 0.5
                })
            else:
                # Finding zeros
                if "x2 – 3" in question_text:
                    difficulty = 0.40  # Irrational zeros
                else:
                    difficulty = 0.35
                skills_json["skills"].append({
                    "topic": "Polynomials",
                    "skill_name": "Quadratic Polynomials",
                    "difficulty": difficulty,
                    "weight": 0.5
                })
                skills_json["skills"].append({
                    "topic": "Polynomials",
                    "skill_name": "Relationship Between Zeros and Coefficients",
                    "difficulty": difficulty,
                    "weight": 0.5
                })
            skills_json["primary_skill"] = "Quadratic Polynomials"
    
    # Chapter 3: Pair of Linear Equations
    elif "Chapter 3" in chapter:
        method_skills = []
        
        # Identify the method
        if "graph" in question_text.lower():
            method_skills.append({
                "topic": "Pair of Linear Equations",
                "skill_name": "Graphical Method",
                "difficulty": 0.40 if "consistent" in question_text.lower() else 0.45,
                "weight": 0.0  # Will be adjusted
            })
            skills_json["primary_skill"] = "Graphical Method"
            
        elif "substitution" in question_text.lower() or "substitute" in question_text.lower():
            method_skills.append({
                "topic": "Pair of Linear Equations",
                "skill_name": "Substitution Method",
                "difficulty": 0.45,
                "weight": 0.0
            })
            skills_json["primary_skill"] = "Substitution Method"
            
        elif "elimination" in question_text.lower():
            method_skills.append({
                "topic": "Pair of Linear Equations",
                "skill_name": "Elimination Method",
                "difficulty": 0.50,
                "weight": 0.0
            })
            skills_json["primary_skill"] = "Elimination Method"
            
        else:
            # Default to substitution for general solving
            if "solve" in question_text.lower():
                method_skills.append({
                    "topic": "Pair of Linear Equations",
                    "skill_name": "Substitution Method",
                    "difficulty": 0.45,
                    "weight": 0.0
                })
                skills_json["primary_skill"] = "Substitution Method"
        
        # Check for word problems
        word_problem_keywords = ["age", "cost", "price", "income", "expenditure", "bought", 
                               "purchase", "skirt", "pant", "digit", "ratio", "save", "pencil", "eraser"]
        if any(word in question_text.lower() for word in word_problem_keywords):
            difficulty = 0.55 if "age" in question_text.lower() else 0.50
            if "digit" in question_text.lower() and "reversing" in question_text.lower():
                difficulty = 0.65
            
            method_skills.append({
                "topic": "Pair of Linear Equations",
                "skill_name": "Word Problems",
                "difficulty": difficulty,
                "weight": 0.0
            })
            if not skills_json["primary_skill"]:
                skills_json["primary_skill"] = "Word Problems"
        
        # Check for system classification
        if any(word in question_text.lower() for word in ["parallel", "infinitely many", "no solution", "cross", "rails"]):
            method_skills.append({
                "topic": "Pair of Linear Equations",
                "skill_name": "System Classification",
                "difficulty": 0.45,
                "weight": 0.0
            })
            if not skills_json["primary_skill"]:
                skills_json["primary_skill"] = "System Classification"
        
        # Assign weights
        if len(method_skills) == 1:
            method_skills[0]["weight"] = 1.0
        elif len(method_skills) == 2:
            if any(s["skill_name"] == "Word Problems" for s in method_skills):
                # Word problems get higher weight when combined
                for skill in method_skills:
                    if skill["skill_name"] == "Word Problems":
                        skill["weight"] = 0.5
                    else:
                        skill["weight"] = 0.5
            else:
                method_skills[0]["weight"] = 0.7
                method_skills[1]["weight"] = 0.3
        elif len(method_skills) == 3:
            # Method, word problem, and classification
            weights = [0.4, 0.4, 0.2]
            for i, skill in enumerate(method_skills):
                skill["weight"] = weights[i]
        
        skills_json["skills"] = method_skills
    
    # Set overall difficulty for the question
    if skills_json["skills"]:
        weighted_difficulty = sum(s["difficulty"] * s["weight"] for s in skills_json["skills"])
        overall_difficulty = round(weighted_difficulty, 2)
    else:
        overall_difficulty = 0.5
    
    return skills_json, overall_difficulty

def update_database():
    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Process ncert_examples
        print("Processing NCERT Examples...")
        cursor.execute("""
            SELECT id, question_id, chapter, question_text, solution 
            FROM ncert_examples 
            WHERE chapter IN ('Chapter 1: Real Numbers', 'Chapter 2: Polynomials', 
                            'Chapter 3: Pair of Linear Equations in Two Variables')
            ORDER BY id
        """)
        
        examples = cursor.fetchall()
        updates = []
        
        for ex in examples:
            solution_text = json.dumps(ex[4]) if ex[4] else ""
            skills_json, difficulty = analyze_question_and_assign_skills(ex[1], ex[2], ex[3], solution_text)
            updates.append((json.dumps(skills_json), difficulty, ex[0]))
            print(f"Example {ex[1]}: {skills_json['primary_skill']} (difficulty: {difficulty})")
        
        # Batch update examples
        cursor.executemany("""
            UPDATE ncert_examples 
            SET skills_tested = %s, difficulty = %s
            WHERE id = %s
        """, updates)
        
        # Process ncert_exercises
        print("\nProcessing NCERT Exercises...")
        cursor.execute("""
            SELECT id, question_id, chapter, question_text, solution 
            FROM ncert_exercises 
            WHERE chapter IN ('Chapter 1: Real Numbers', 'Chapter 2: Polynomials', 
                            'Chapter 3: Pair of Linear Equations in Two Variables')
            ORDER BY id
        """)
        
        exercises = cursor.fetchall()
        updates = []
        
        for ex in exercises:
            solution_text = json.dumps(ex[4]) if ex[4] else ""
            skills_json, difficulty = analyze_question_and_assign_skills(ex[1], ex[2], ex[3], solution_text)
            updates.append((json.dumps(skills_json), difficulty, ex[0]))
            print(f"Exercise {ex[1]}: {skills_json['primary_skill']} (difficulty: {difficulty})")
        
        # Batch update exercises
        cursor.executemany("""
            UPDATE ncert_exercises 
            SET skills_tested = %s, difficulty = %s
            WHERE id = %s
        """, updates)
        
        conn.commit()
        print(f"\nSuccessfully updated {len(examples)} examples and {len(exercises)} exercises")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        if conn:
            conn.rollback()

if __name__ == "__main__":
    update_database()