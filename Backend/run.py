#!/usr/bin/env python3
"""
Script to run the monolithic Socratic backend application.
"""
import uvicorn
import os
import subprocess
import sys
from pathlib import Path
from app.database.models import Base
from app.database.database import engine

def run_migrations():
    """Run database migrations using Alembic."""
    try:
        print("Running database migrations...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], check=True, capture_output=True, text=True)
        print("Migrations completed successfully")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e}")
        print(f"Error output: {e.stderr}")
        # Fallback to create_all for development
        print("Falling back to create_all...")
        Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Get configuration from environment
    database_url = os.getenv("DATABASE_URL", "SQLite database")
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Determine if we're in production
    is_production = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("VERCEL")
    
    print(f"Starting Socratic backend on {host}:{port}")
    print(f"Database: {database_url}")
    print(f"Environment: {'Production' if is_production else 'Development'}")
    
    # Run migrations
    run_migrations()
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=not is_production  # Only reload in development
    ) 