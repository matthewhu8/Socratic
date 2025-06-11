from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, UTC
import json
from redis import Redis
import traceback
from .gemini_service import GeminiService
from .youtube_service import YouTubeTranscriptService
import yt_dlp
import redis
import os
from supadata import Supadata

class ConversationService:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        # Existing Redis connection
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Supadata API for transcripts
        api_key = os.getenv("SUPADATA_API_KEY")
        self.supadata_api = Supadata(api_key=api_key)
        
        # Cache settings
        self.transcript_cache_ttl = 24 * 60 * 60  # 24 hours
        self.transcript_prefix = "transcript:"
        
        self.gemini_service = GeminiService()
        self.youtube_service = YouTubeTranscriptService()
    
    def _get_session_key(self, user_id: str, test_id: str, question_id: str) -> str:
        """Generate Redis key for a specific test session."""
        return f"test_session:{user_id}:{test_id}:{question_id}"
    
    def _get_test_key(self, user_id: str, test_id: str) -> str:
        """Generate Redis key for overall test data."""
        return f"test:{user_id}:{test_id}" 
    
    def _ensure_timestamp(self, timestamp_value) -> str:
        """Ensure a timestamp is in ISO format string."""
        if timestamp_value is None:
            return datetime.now(UTC).isoformat()
            
        if isinstance(timestamp_value, str):
            try:
                # Validate it's a proper ISO timestamp
                datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                return timestamp_value
            except ValueError:
                # If not valid, return current time
                print(f"Warning: Invalid timestamp format: {timestamp_value}")
                return datetime.now(UTC).isoformat()
        elif isinstance(timestamp_value, datetime):
            # If it's already a datetime object, just format it
            return timestamp_value.isoformat()
            
        # If it's not a string, datetime, or None, return current time
        print(f"Warning: Invalid timestamp type: {type(timestamp_value)}")
        return datetime.now(UTC).isoformat()
        
    
    async def start_test(self, user_id: int, test_id: int, test_code: str, list_question_ids: List[int], total_questions: int) -> Dict:
        """Initialize a new test session."""
        # Convert parameters to strings for consistent Redis keys
        user_id_str = str(user_id)
        test_id_str = str(test_id)
        
        # Create session key
        session_key = f"test:{user_id_str}:{test_id_str}"
        
        # Convert question IDs to strings since the database stores them as integers
        str_question_ids = [str(qid) for qid in list_question_ids]
            
        # Timestamp for session creation
        start_timestamp = self._ensure_timestamp(datetime.now(UTC).isoformat())
            
        test_data = {
            "user_id": user_id_str,
            "test_id": test_id_str,
            "test_code": test_code,
            "status": "in_progress",
            "start_time": start_timestamp,
            "list_question_ids": str_question_ids,
            "completed_questions": [],
            "total_questions": total_questions,
            "total_time": 0
        }
    
        print(f"Initializing test session for user {user_id_str}, test {test_id_str} with {len(str_question_ids)} questions")
        
        # Initialize session data for each question
        for question_id in str_question_ids:
            session_key_q = self._get_session_key(user_id_str, test_id_str, question_id)
            if not self.redis_client.exists(session_key_q):
                session_data = {
                    "chat_history": [],
                    "start_time": start_timestamp,
                    "end_time": None,
                    "hints_used": 0,
                    "student_answer": None,
                    "is_correct": False,
                    "question_id": question_id,
                    "test_id": test_id_str,
                    "time_spent": 0
                }
                self.redis_client.setex(session_key_q, 2 * 60 * 60, json.dumps(session_data))
        
        # Store test data with 2 hour expiry
        self.redis_client.setex(session_key, 2 * 60 * 60, json.dumps(test_data))
        return test_data
    
    async def process_query(
        self, 
        query: str, 
        user_id: int,
        test_code: str,
        question_id: int,
        public_question: str,
        test_id: int,
        is_practice_exam: bool = False
    ) -> str:
        """Process a user query and return a response."""
        session_key = self._get_session_key(str(user_id), str(test_id), str(question_id))
        test_key = self._get_test_key(str(user_id), str(test_id))
        
        # Get session data
        session_data = self.redis_client.get(session_key)
        test_data = self.redis_client.get(test_key)

        # If no session data exists, try to initialize from overall test data
        if not session_data:
            if not test_data:
                # No test session either, initialize a new session
                print("no session data found, initializing new session")
                session_data = json.dumps({
                    "chat_history": [],
                    "start_time": self._ensure_timestamp(datetime.now(UTC).isoformat()),
                    "hints_used": 0,
                    "student_answer": None,
                    "is_correct": False,
                    "question_id": question_id,
                    "test_id": test_id
                })
            else:
                # Initialize from test data
                test_data_obj = json.loads(test_data)
                if str(question_id) not in test_data_obj.get("list_question_ids", []):
                    test_data_obj["list_question_ids"].append(str(question_id))
                    self.redis_client.setex(test_key, 2 * 60 * 60, json.dumps(test_data_obj))
                
                # Create new session for this question
                session_data = json.dumps({
                    "chat_history": [],
                    "start_time": self._ensure_timestamp(datetime.now(UTC).isoformat()),
                    "hints_used": 0,
                    "student_answer": None,
                    "is_correct": False,
                    "question_id": question_id,
                    "test_id": test_id
                })
        
        session_data = json.loads(session_data)
                
        # Add user message to chat history
        print("adding user message to chat history")
        session_data["chat_history"].append({
            "role": "user",
            "content": query,
            "timestamp": self._ensure_timestamp(datetime.now(UTC).isoformat())
        })
        print("\nchat history:", session_data["chat_history"])
        print()
        
        # Get Gemini response
        print("making request to Gemini service")
        try:
            context = {
                "test_code": test_code,
                "test_id": test_id,
                "question_id": question_id,
                "user_id": user_id,
                "public_question": public_question,
                "isPracticeExam": is_practice_exam
            }
            
            # Get recent chat history for context
            recent_history = (
                session_data["chat_history"][-4:]
                if len(session_data["chat_history"]) > 4
                else session_data["chat_history"]
            )
            
            response_data = await self.gemini_service.generate_response(
                query=query,
                context=context,
                chat_history=recent_history
            )
            
            llm_response = response_data.get("response", "I'm sorry, I couldn't process your request.")
            
        except Exception as e:
            print(f"Error in get_gemini_response: {e}")
            traceback.print_exc()
            llm_response = "I'm sorry, I encountered an error while processing your request. Please try again."
        
        # Add assistant response to chat history
        session_data["chat_history"].append({
            "role": "assistant",
            "content": llm_response,
            "timestamp": self._ensure_timestamp(datetime.now(UTC).isoformat())
        })
        
        # Update session data in Redis
        self.redis_client.setex(session_key, 2 * 60 * 60, json.dumps(session_data))
        
        return llm_response
    
    async def submit_answer(
        self,
        user_id: int,
        test_code: str,
        question_id: int,
        question_index: int,
        answer: str
    ) -> Dict:
        """Submit an answer for a question."""
        session_key = self._get_session_key(str(user_id), str(test_code), str(question_id))
        
        # Get session data
        session_data = self.redis_client.get(session_key)
        if session_data:
            session_data = json.loads(session_data)
            session_data["student_answer"] = answer
            session_data["end_time"] = self._ensure_timestamp(datetime.now(UTC).isoformat())
            
            # Calculate time spent
            start_time = datetime.fromisoformat(session_data["start_time"].replace('Z', '+00:00'))
            end_time = datetime.now(UTC)
            time_spent = int((end_time - start_time).total_seconds())
            session_data["time_spent"] = time_spent
            
            # Update session data in Redis
            self.redis_client.setex(session_key, 2 * 60 * 60, json.dumps(session_data))
        
        return {"status": "success", "message": "Answer submitted successfully"}
    
    async def finish_test(self, user_id: str, test_id: str, request_data: Optional[Dict] = None):
        """Finish a test session."""
        test_key = self._get_test_key(user_id, test_id)
        
        # Get test data
        test_data = self.redis_client.get(test_key)
        if test_data:
            test_data = json.loads(test_data)
            test_data["status"] = "completed"
            test_data["end_time"] = self._ensure_timestamp(datetime.now(UTC).isoformat())
            
            # Update test data in Redis
            self.redis_client.setex(test_key, 2 * 60 * 60, json.dumps(test_data))
        
        return {"status": "success", "message": "Test finished successfully"}
    
    def get_conversation_history(
        self,
        user_id: int,
        test_code: str,
        question_id: int
    ) -> List[Dict]:
        """Get conversation history for a specific question."""
        session_key = self._get_session_key(str(user_id), str(test_code), str(question_id))
        
        session_data = self.redis_client.get(session_key)
        if session_data:
            session_data = json.loads(session_data)
            return session_data.get("chat_history", [])
        
        return []

    async def get_video_session(self, user_id: int, video_id: str) -> Dict:
        """Get or create a video chat session."""
        try:
            session_key = f"video_chat:{user_id}:{video_id}"
            session_data = self.redis_client.get(session_key)
            if session_data:
                return json.loads(session_data)
            
            # Create new session
            new_session = {
                "user_id": user_id,
                "video_id": video_id,
                "messages": [],
                "created_at": datetime.now(UTC).isoformat()
            }
            print("attempting to create new session")
            
            # Store with 24 hour expiration
            self.redis_client.setex(session_key, 24 * 60 * 60, json.dumps(new_session))
            return new_session
        except Exception as e:
            print(f"Error in get_video_session: {e}")
            traceback.print_exc()
            return None
    
    def extract_video_info(self, video_url: str) -> Dict:
        print(f"EXTRACTING VIDEO INFO FOR: {video_url}")
        ydl = yt_dlp.YoutubeDL()
        info = ydl.extract_info(video_url, download=False)
        return {
            "title": info.get("title", ""),
            "author": info.get("uploader", ""),
            "description": info.get("description", "")
        }
            

    async def process_video_chat(self, user_id: int, video_id: str, video_url: str, query: str, session_data: Dict, timestamp: float = None) -> str:
        """Process a video chat query with session persistence and video context."""
        # Add user message to session
        session_data["messages"].append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now(UTC).isoformat(),
            "video_timestamp": timestamp 
        })
        try:
            video_info = self.extract_video_info(video_url)
        except Exception as e:
            print(f"Skipping title and author extraction, Error extracting video info: {e}")
            video_info = None
        transcript = self.get_transcript_context(video_id, timestamp, context_seconds=30)
        
        # Enhanced context for the LLM
        enhanced_context = {
            "video_url": video_url,
            "video_timestamp": timestamp,
            "video_context": video_info,
            "transcript": transcript,
            "message_history": session_data["messages"][-5:] if len(session_data["messages"]) > 5 else session_data["messages"]
        }
        
        response_text = await self.gemini_service.answer_video_question(
            query, 
            session_data, 
            video_context=enhanced_context
        )
        print(f"response_text: {response_text}")
        
        # Add assistant response to session
        session_data["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        # Update session in Redis
        session_key = f"video_chat:{user_id}:{video_id}"
        self.redis_client.setex(session_key, 24 * 60 * 60, json.dumps(session_data))
        
        return response_text 

    async def load_and_cache_transcript(self, video_id: str, video_url: str) -> bool:
        """Load transcript from API and cache it in Redis."""
        try:
            cache_key = f"{self.transcript_prefix}{video_id}"
            
            # Check if already cached
            if self.redis_client.exists(cache_key):
                print(f"Transcript for {video_id} already cached")
                return True
            
            # Fetch from API
            print(f"Fetching transcript for video with id dfdf (video_id): {video_url}")
            transcript = self.supadata_api.youtube.transcript(video_id=video_id, lang="en")
            
            if not transcript.content:
                return False
            
            # Serialize transcript chunks
            transcript_data = [
                {
                    "text": chunk.text,
                    "offset": chunk.offset,
                    "duration": chunk.duration,
                    "lang": chunk.lang
                }
                for chunk in transcript.content
            ]
            print(f"transcript_data RECEIVED: {transcript_data}")
            
            # Cache it
            self.redis_client.setex(
                cache_key,
                self.transcript_cache_ttl,
                json.dumps(transcript_data)
            )
            
            print(f"Cached transcript for {video_id} ({len(transcript_data)} chunks)")
            return True
            
        except Exception as e:
            print(f"Error loading transcript for {video_id}: {e}")
            return False
    
    def get_transcript_context(self, video_id: str, timestamp: float, context_seconds: int = 30) -> str:
        """Get transcript context around timestamp from cache."""
        try:
            cache_key = f"{self.transcript_prefix}{video_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if not cached_data:
                return "Transcript not available. Please load the video first."
            
            transcript_chunks = json.loads(cached_data)
            
            # Find relevant segments (convert timestamp to milliseconds)
            timestamp_ms = timestamp * 1000
            context_ms = context_seconds * 1000
            
            start_time = max(0, timestamp_ms - context_ms)
            end_time = timestamp_ms + context_ms
            
            relevant_segments = []
            for chunk in transcript_chunks:
                chunk_start = chunk['offset']
                chunk_end = chunk['offset'] + chunk['duration']
                
                if chunk_start <= end_time and chunk_end >= start_time:
                    relevant_segments.append({
                        'start': chunk_start / 1000,  # Convert to seconds
                        'text': chunk['text']
                    })
            
            # Format context
            if relevant_segments:
                context_text = f"Video content around {timestamp:.1f}s:\n\n"
                for segment in relevant_segments:
                    context_text += f"[{segment['start']:.1f}s] {segment['text']}\n"
                return context_text
            else:
                return f"No transcript around timestamp {timestamp:.1f}s"
                
        except Exception as e:
            print(f"Error getting transcript context: {e}")
            return "Error retrieving transcript." 