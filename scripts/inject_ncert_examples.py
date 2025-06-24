#!/usr/bin/env python3
"""
Script to inject NCERT examples from JSON file into both local and production databases.

Usage: python inject_ncert_examples.py <json_file_path>
Example: python inject_ncert_examples.py ../Backend/data/ncert_examples_10_realnumbers.json
"""

import json
import sys
import os
from pathlib import Path

# Add the Backend directory to Python path so we can import our app modules
backend_dir = Path(__file__).resolve().parent.parent / "Backend"
sys.path.append(str(backend_dir))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database.models import NcertExamples, Base

# Database URLs
LOCAL_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/postgres"
PRODUCTION_DATABASE_URL = "postgresql://postgres:********@shinkansen.proxy.rlwy.net:25660/railway"  # Railway PostgreSQL URL

def create_database_session(database_url: str, db_name: str):
    """Create a database session for the given URL."""
    try:
        engine = create_engine(database_url, echo=False, future=True)
        # Test connection
        with engine.connect() as conn:
            pass
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print(f"✅ Connected to {db_name} database")
        return SessionLocal(), engine
    except Exception as e:
        print(f"❌ Failed to connect to {db_name} database: {e}")
        return None, None

def load_json_data(file_path: str) -> list:
    """Load and parse JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file '{file_path}': {e}")
        sys.exit(1)

def inject_examples(data: list, db: Session, db_name: str) -> int:
    """Insert NCERT examples into the database."""
    count = 0
    
    print(f"\n📝 Processing {len(data)} examples for {db_name}...")
    
    for item in data:
        try:
            # Create new NcertExamples object
            example = NcertExamples(
                example=item.get('example'),
                solution=item.get('solution'),
                topic=item.get('topic'),
                example_number=item.get('example_number'),
                grade=item.get('grade')
            )
            
            # Add to session
            db.add(example)
            count += 1
            
        except Exception as e:
            print(f"Error processing item {count + 1}: {e}")
            print(f"Item data: {item}")
            continue
    
    try:
        # Commit all changes
        db.commit()
        print(f"✅ Successfully inserted {count} NCERT examples into {db_name}")
        return count
    except Exception as e:
        db.rollback()
        print(f"❌ Error committing to {db_name}: {e}")
        return 0

def check_existing_data(db: Session, data: list, db_name: str) -> bool:
    """Check for existing data and ask user for confirmation."""
    if data and 'topic' in data[0] and 'grade' in data[0]:
        topic = data[0]['topic']
        grade = data[0]['grade']
        existing_count = db.query(NcertExamples).filter(
            NcertExamples.topic == topic,
            NcertExamples.grade == grade
        ).count()
        
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing examples for {topic} Grade {grade} in {db_name}")
            return True
    return False

def main():
    """Main function to run the injection script."""
    if len(sys.argv) != 2:
        print("Usage: python inject_ncert_examples.py <json_file_path>")
        print("Example: python inject_ncert_examples.py ../Backend/data/ncert_examples_10_realnumbers.json")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"Error: File '{json_file_path}' does not exist.")
        sys.exit(1)
    
    print(f"🔄 Loading data from: {json_file_path}")
    
    # Load JSON data
    data = load_json_data(json_file_path)
    
    if not data:
        print("No data found in JSON file.")
        sys.exit(1)
    
    print(f"📊 Found {len(data)} examples to insert.")
    
    # Check if production URL is configured
    if PRODUCTION_DATABASE_URL == "REPLACE_WITH_RAILWAY_URL":
        print("⚠️  Production database URL not configured. Update PRODUCTION_DATABASE_URL in the script.")
        use_production = False
    else:
        use_production = True
    
    # Connect to databases
    local_db, local_engine = create_database_session(LOCAL_DATABASE_URL, "LOCAL")
    
    if use_production:
        prod_db, prod_engine = create_database_session(PRODUCTION_DATABASE_URL, "PRODUCTION")
    else:
        prod_db, prod_engine = None, None
    
    # Check if we have at least one working connection
    if not local_db and not prod_db:
        print("❌ Could not connect to any database. Exiting.")
        sys.exit(1)
    
    # Create tables if they don't exist
    if local_engine:
        Base.metadata.create_all(bind=local_engine)
    if prod_engine:
        Base.metadata.create_all(bind=prod_engine)
    
    # Check for existing data and get user confirmation
    has_existing_data = False
    if local_db:
        has_existing_data |= check_existing_data(local_db, data, "LOCAL")
    if prod_db:
        has_existing_data |= check_existing_data(prod_db, data, "PRODUCTION")
    
    if has_existing_data:
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled.")
            return
    
    # Inject data into databases
    total_injected = 0
    
    try:
        if local_db:
            count = inject_examples(data, local_db, "LOCAL")
            total_injected += count
        
        if prod_db:
            count = inject_examples(data, prod_db, "PRODUCTION")
            total_injected += count
        
        print(f"\n🎉 SUMMARY:")
        if local_db:
            print(f"   Local database: Updated")
        if prod_db:
            print(f"   Production database: Updated")
        elif use_production:
            print(f"   Production database: Failed to connect")
        else:
            print(f"   Production database: Not configured")
        print(f"   Total records inserted: {total_injected}")
            
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if local_db:
            local_db.close()
        if prod_db:
            prod_db.close()

if __name__ == "__main__":
    main()
