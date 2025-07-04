#!/usr/bin/env python3
"""
Script to insert NCERT exercise questions from JSON file into PostgreSQL database.
Run this script once to populate the ncert_exercises table.
"""

import json
import psycopg2
from psycopg2.extras import Json
import sys
from typing import Dict, Any, Optional

# Database connection parameters
DATABASE_URL = "postgresql://postgres:ymCIpwSPBraGkdaGRFjACfGJOojfzpOz@shinkansen.proxy.rlwy.net:25660/railway"

def connect_to_database():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def load_json_data(file_path: str) -> Dict[str, Any]:
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)

def insert_question(cursor, question: Dict[str, Any]) -> bool:
    """Insert a single question into the database."""
    try:
        # Extract source information
        source = question.get('source', {})
        
        # Map JSON fields to database columns
        insert_query = """
        INSERT INTO ncert_exercises (
            question_id, subject, chapter, topic, question_type, grade,
            source_exercise_number, source_question_number, source_part_number,
            question_text, answer, solution, common_mistakes, teacher_notes
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        # Extract grade from chapter or set default
        grade = question.get('grade', 'grade-10')  # Default to grade-10 if not specified
        
        # Prepare values with proper JSON handling
        values = (
            question.get('id'),                              # question_id
            question.get('subject'),                         # subject
            question.get('chapter'),                         # chapter
            question.get('topic'),                           # topic
            question.get('questionType'),                    # question_type
            grade,                                           # grade
            source.get('exerciseNumber'),                    # source_exercise_number
            source.get('questionNumber'),                    # source_question_number
            source.get('partNumber'),                        # source_part_number
            question.get('questionText'),                    # question_text
            question.get('answer'),                          # answer
            Json(question.get('solution')) if question.get('solution') else None,  # solution (JSON)
            Json(question.get('commonMistakes')) if question.get('commonMistakes') else None,  # common_mistakes (JSON)
            Json(question.get('teacherNotes')) if question.get('teacherNotes') else None       # teacher_notes (JSON)
        )
        
        cursor.execute(insert_query, values)
        return True
        
    except psycopg2.Error as e:
        print(f"Error inserting question {question.get('id', 'unknown')}: {e}")
        return False

def main():
    """Main function to process and insert all questions."""
    print("Starting NCERT exercises insertion...")
    
    # Load JSON data
    json_data = load_json_data('ncert_exercises_complete.json')
    questions = json_data.get('questions', [])
    
    if not questions:
        print("No questions found in JSON file.")
        return
    
    print(f"Found {len(questions)} questions to insert.")
    
    # Connect to database
    conn = connect_to_database()
    
    try:
        with conn.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'ncert_exercises'
                );
            """)
            
            table_exists = cursor.fetchone()[0]
            if not table_exists:
                print("Error: ncert_exercises table does not exist.")
                return
            
            # Clear existing data (optional - remove if you want to keep existing data)
            print("Clearing existing data...")
            cursor.execute("DELETE FROM ncert_exercises")
            
            # Insert questions
            success_count = 0
            failure_count = 0
            
            for i, question in enumerate(questions, 1):
                print(f"Processing question {i}/{len(questions)}: {question.get('id', 'unknown')}")
                
                if insert_question(cursor, question):
                    success_count += 1
                else:
                    failure_count += 1
            
            # Commit the transaction
            conn.commit()
            
            print(f"\nInsertion completed!")
            print(f"Successfully inserted: {success_count} questions")
            print(f"Failed to insert: {failure_count} questions")
            
            # Verify insertion
            cursor.execute("SELECT COUNT(*) FROM ncert_exercises")
            total_count = cursor.fetchone()[0]
            print(f"Total questions in database: {total_count}")
            
            # Show sample of inserted data
            cursor.execute("SELECT question_id, subject, chapter, topic FROM ncert_exercises LIMIT 5")
            sample_data = cursor.fetchall()
            print("\nSample of inserted data:")
            for row in sample_data:
                print(f"  ID: {row[0]}, Subject: {row[1]}, Chapter: {row[2]}, Topic: {row[3]}")
            
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main() 