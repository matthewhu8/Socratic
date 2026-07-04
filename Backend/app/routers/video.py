from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_student, get_current_user
from ..database.database import get_db
from ..database.models import YouTubeQuizResults
from ..service_instances import convo_service

router = APIRouter()


@router.post("/api/video/load-transcript")
async def load_video_transcript(
    request: dict,
    current_user = Depends(get_current_user)
):
    """Load and cache transcript when user loads video."""
    video_id = request.get("video_id")
    video_url = request.get("video_url")
    print(f"loading transcript for video {video_id} and url {video_url}")

    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")
    if not video_url:
        raise HTTPException(status_code=400, detail="video_url is required")

    try:
        success = await convo_service.load_and_cache_transcript(video_id, video_url)

        if success:
            return {
                "status": "success",
                "message": f"Transcript cached for video {video_id}",
                "video_id": video_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to load transcript"
            )

    except Exception as e:
        print(f"Error in load_video_transcript endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading transcript: {str(e)}"
        )

@router.post("/api/youtube-video-quiz")
async def youtube_video_quiz(request: dict, current_user = Depends(get_current_user)):
    """Generate a quiz for a YouTube video."""
    try:
        video_id = request.get("video_id")
        video_url = request.get("video_url")
        user_id = current_user.id

        if not video_id or not video_url:
            raise HTTPException(status_code=400, detail="video_id and video_url are required")

        # get session data from redis about this video to find previous messages
        session_data = await convo_service.get_video_session(user_id, video_id)
        previous_messages = session_data.get("messages", [])
        # get entire video transcript from redis
        entire_transcript = convo_service.get_transcript_context(video_id, 0, 1000000)


        # Generate quiz using Gemini
        quiz_response = convo_service.gemini_service.generate_quiz(
            entire_transcript=entire_transcript,
            previous_messages=previous_messages
        )

        return {"quiz": quiz_response}
    except Exception as e:
        print(f"Error in youtube_video_quiz endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quiz")

@router.post("/chat-video")
async def chat_video(request: dict, current_user = Depends(get_current_user)):
    """Handle chat requests about YouTube videos with context awareness and optional image"""
    try:
        print(f"REQUEST RECEIVED: {request}")
        query = request.get("query", "")
        video_id = request.get("video_id", "")
        video_url = request.get("video_url", "")
        timestamp = request.get("timestamp")
        user_id = current_user.id

        if not query or not video_id:
            raise HTTPException(status_code=400, detail="Query and video_id are required")

        # Get or create session history from Redis
        session_data = await convo_service.get_video_session(user_id, video_id)
        print(f"SESSION DATA RECEIVED: {session_data}")
        print(f"ATTEMPTING TO ANSWER: {query}")

        if timestamp:
            print(f"VIDEO TIMESTAMP: {timestamp}")


        # Process the query and update session with timestamp context and image
        response_text = await convo_service.process_video_chat(
            user_id=user_id,
            video_id=video_id,
            video_url=video_url,
            query=query,
            session_data=session_data,
            timestamp=timestamp,
        )

        return {"response": response_text, "video_id": video_id}

    except Exception as e:
        print(f"Error in chat_video endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to process video chat request")

@router.post("/api/store-youtube-quiz-results")
async def store_youtube_quiz_results(request: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Store the results of a YouTube quiz."""
    try:
        video_title = request.get("video_title", "YouTube Video")
        youtube_url = request.get("youtube_url")
        youtube_id = request.get("youtube_id")
        time_spent = request.get("time_spent", 10) # units should be in seconds
        raw_quiz = request.get("raw_quiz") #JSON format identitcal to how the quiz is returned from the youtube_video_quiz endpoint
        student_answers = request.get("student_answers") # JSON format, question number as key, answer and True/false boolean for right or wrong as two values
        score = request.get("score", 0) # score as a percentage

        db_quiz_result = YouTubeQuizResults(
            student_id=current_user.id,
            video_title=video_title,
            youtube_url=youtube_url,
            youtube_id=youtube_id,
            time_spent=time_spent,
            raw_quiz=raw_quiz,
            student_answers=student_answers,
            score=score
        )
        db.add(db_quiz_result)
        db.commit()
        db.refresh()

        return {"status": "success", "message": "Quiz results stored successfully"}

    except Exception as e:
       print(f"Error in store_youtube_quiz_results endpoint: {e}")
       raise HTTPException(status_code=500, detail="At some point during the storage of the quiz results, something went wrong")

@router.get("/api/get-youtube-quiz-results")
async def get_youtube_quiz_results(db: Session = Depends(get_db), current_user = Depends(get_current_student)) -> str:
    pass
