import requests
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Optional

class YouTubeTranscriptService:
    def __init__(self):
        self.transcript_api = YouTubeTranscriptApi()
        pass
    
    def get_transcript_around_timestamp(self, video_id: str, timestamp: float, context_seconds: int = 30) -> str:
        """
        Get transcript content around a specific timestamp.
        
        Args:
            video_id: YouTube video ID
            timestamp: Current video timestamp in seconds
            context_seconds: Seconds of context before/after timestamp
        
        Returns:
            Formatted transcript text around the timestamp
        """
        try:
            # Get transcript
            print(f"GETTING TRANSCRIPT FOR ____ VIDEO: {video_id}")
            transcript_list = self.transcript_api.get_transcript(video_id=video_id)
            print(f"TRANSCRIPT wallahi: {transcript_list}") 

            # Find relevant segments around the timestamp
            relevant_segments = []
            start_time = max(0, timestamp - context_seconds)
            end_time = timestamp + context_seconds
            
            for entry in transcript_list:
                entry_start = entry['start']
                entry_end = entry['start'] + entry['duration']
                
                # Include if segment overlaps with our time window
                if (entry_start <= end_time and entry_end >= start_time):
                    relevant_segments.append({
                        'start': entry_start,
                        'text': entry['text']
                    })
            
            # Format the context
            if relevant_segments:
                context_text = f"Video content around timestamp {timestamp:.1f}s:\n\n"
                for segment in relevant_segments:
                    context_text += f"[{segment['start']:.1f}s] {segment['text']}\n"
                return context_text
            else:
                return f"No transcript available around timestamp {timestamp:.1f}s"
                
        except Exception as e:
            print(f"error getting transcript: {e}")
            return "Transcript not available for this video."
    
    def get_full_transcript(self, video_id: str) -> Optional[List[Dict]]:
        """Get the full transcript for a video."""
        try:
            return YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            print(f"Error getting full transcript for video {video_id}: {e}")
            return None 