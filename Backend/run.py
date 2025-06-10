#!/usr/bin/env python3
"""
Script to run the monolithic Socratic backend application.
"""
import uvicorn
import os
from pathlib import Path
from app.database.models import Base
from app.database.database import engine

# Create all tables in the database
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
    
    uvicorn.run(
        "app.main:app", 
        host=host, 
        port=port, 
        reload=not is_production  # Only reload in development
    ) 