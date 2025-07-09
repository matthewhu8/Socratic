import psycopg2
import json
from datetime import datetime

# Database connection
conn_string = "postgresql://postgres:ymCIpwSPBraGkdaGRFjACfGJOojfzpOz@shinkansen.proxy.rlwy.net:25660/railway"

def extract_questions():
    try:
        # Connect to database
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()
        
        # Extract all questions from ncert_examples for chapters 1, 2, 3
        print("Extracting NCERT Examples...")
        cursor.execute("""
            SELECT id, question_id, subject, chapter, topic, question_type, grade,
                   source_example_number, source_question_number, source_part_number,
                   question_text, answer, difficulty, solution, skills_tested
            FROM ncert_examples 
            WHERE chapter IN ('Chapter 1: Real Numbers', 'Chapter 2: Polynomials', 'Chapter 3: Pair of Linear Equations in Two Variables')
            ORDER BY chapter, source_example_number, source_question_number, source_part_number
        """)
        
        examples = cursor.fetchall()
        
        # Extract all questions from ncert_exercises for chapters 1, 2, 3  
        print("Extracting NCERT Exercises...")
        cursor.execute("""
            SELECT id, question_id, subject, chapter, topic, question_type, grade,
                   source_exercise_number, source_question_number, source_part_number,
                   question_text, answer, difficulty, solution, skills_tested
            FROM ncert_exercises
            WHERE chapter IN ('Chapter 1: Real Numbers', 'Chapter 2: Polynomials', 'Chapter 3: Pair of Linear Equations in Two Variables')
            ORDER BY chapter, source_exercise_number, source_question_number, source_part_number
        """)
        
        exercises = cursor.fetchall()
        
        # Write to file
        with open('all_questions_ch1-3.txt', 'w', encoding='utf-8') as f:
            f.write(f"NCERT Questions Export - Chapters 1, 2, 3\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
            
            # Write Examples
            f.write(f"NCERT EXAMPLES ({len(examples)} questions)\n")
            f.write("-"*80 + "\n\n")
            
            for ex in examples:
                f.write(f"ID: {ex[0]}\n")
                f.write(f"Question ID: {ex[1]}\n")
                f.write(f"Subject: {ex[2]} | Chapter: {ex[3]} | Topic: {ex[4]}\n")
                f.write(f"Type: {ex[5]} | Grade: {ex[6]}\n")
                f.write(f"Source: Example {ex[7]}, Question {ex[8]}, Part {ex[9]}\n")
                f.write(f"Difficulty: {ex[12]}\n")
                f.write(f"Skills Tested: {ex[14]}\n")
                f.write(f"\nQuestion Text:\n{ex[10]}\n")
                f.write(f"\nAnswer: {ex[11]}\n")
                if ex[13]:  # Solution field
                    f.write(f"\nSolution: {json.dumps(ex[13], indent=2)}\n")
                f.write("-"*60 + "\n\n")
            
            # Write Exercises
            f.write(f"\n\nNCERT EXERCISES ({len(exercises)} questions)\n")
            f.write("-"*80 + "\n\n")
            
            for ex in exercises:
                f.write(f"ID: {ex[0]}\n")
                f.write(f"Question ID: {ex[1]}\n")
                f.write(f"Subject: {ex[2]} | Chapter: {ex[3]} | Topic: {ex[4]}\n")
                f.write(f"Type: {ex[5]} | Grade: {ex[6]}\n")
                f.write(f"Source: Exercise {ex[7]}, Question {ex[8]}, Part {ex[9]}\n")
                f.write(f"Difficulty: {ex[12]}\n")
                f.write(f"Skills Tested: {ex[14]}\n")
                f.write(f"\nQuestion Text:\n{ex[10]}\n")
                f.write(f"\nAnswer: {ex[11]}\n")
                if ex[13]:  # Solution field
                    f.write(f"\nSolution: {json.dumps(ex[13], indent=2)}\n")
                f.write("-"*60 + "\n\n")
        
        print(f"\nExtracted {len(examples)} examples and {len(exercises)} exercises")
        print("Data saved to: all_questions_ch1-3.txt")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    extract_questions()