from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database.database import engine
from .database.models import Base
from .routers import auth, feedback, grading, practice, questions, tutor, video

load_dotenv()

# Create all tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Socratic Monolithic Backend")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

# CORS middleware - Updated for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend in local development
        "http://localhost:3100",  # React frontend (fallback port when 3000 is taken)
        "http://localhost:80",    # Frontend in containerized environment
        "http://localhost",       # Frontend in containerized environment (default port 80)
        "http://0.0.0.0:3000",
        "0.0.0.0:3000",
        "http://0.0.0.0:8000",
        "http://10.147.120.71:3000",
        "http://10.147.120.71:8000",
        "http://Matthews-MacBook-Pro.local:3000",
        "http://Matthews-MacBook-Pro.local:8000",
        # Add your production domains here
        "https://*.up.railway.app",  # All Railway subdomains
        "https://*.vercel.app",   # In case you use Vercel for frontend
        "https://socratic.up.railway.app"      # Replace with your custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(video.router)
app.include_router(questions.router)
app.include_router(grading.router)
app.include_router(tutor.router)
app.include_router(feedback.router)
app.include_router(practice.router)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
