import requests
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Dict, Optional
from supadata import Supadata, SupadataError
import os
import yt_dlp
import ffmpeg
import base64
import tempfile
import logging
import subprocess
from io import BytesIO
from PIL import Image

class YouTubeTranscriptService:
    def __init__(self):
        api_key = os.getenv("SUPADATA_API_KEY")
        self.supadata_api = Supadata(api_key=api_key)
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'best[height<=720]/best',  # Get best quality up to 720p
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'audioformat': 'mp3',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        }
    
    def get_video_frame(self, video_url_input: str, timestamp: float) -> Optional[str]:
        """
        Get the video frame at the given timestamp.
        
        Args:
            video_id: YouTube video ID
            timestamp: Time in seconds to extract frame from
            
        Returns:
            Base64 encoded image string, or None if extraction fails
        """
        print(f"Getting video frame for {video_url_input} at {timestamp}s")
        try:
            # Get video streaming URL using yt-dlp
            youtube_url = video_url_input
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract video info without downloading
                info = ydl.extract_info(youtube_url, download=False)
                
                # Get the best video format URL
                video_url = None
                if 'url' in info:
                    video_url = info['url']
                elif 'formats' in info:
                    # Find the best video format
                    for fmt in info['formats']:
                        if fmt.get('vcodec') != 'none' and fmt.get('url'):
                            video_url = fmt['url']
                            break
                
                if not video_url:
                    logging.error(f"Could not extract video URL for {video_url_input}")
                    return None
                
                # Use ffmpeg to extract frame at specific timestamp
                return self._extract_frame_with_ffmpeg(video_url, timestamp)
                
        except Exception as e:
            print(f"Error extracting video frame for {video_url_input} at {timestamp}s: {str(e)}")
            logging.error(f"Error extracting video frame for {video_url_input} at {timestamp}s: {str(e)}")
            return None
    
    def _extract_frame_with_ffmpeg(self, video_url: str, timestamp: float) -> Optional[str]:
        """
        Extract a single frame from video at specified timestamp using ffmpeg.
        
        Args:
            video_url: Direct video stream URL
            timestamp: Time in seconds to extract frame from
            
        Returns:
            Base64 encoded JPEG image, or None if extraction fails
        """
        print(f"Extracting video frame for {video_url} at {timestamp}s")
        try:
            # Create a temporary file for the output frame
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                # Use ffmpeg to extract frame at specific timestamp
                process = (
                    ffmpeg
                    .input(video_url, ss=timestamp)  # Seek to timestamp
                    .output(
                        temp_path,
                        vframes=1,  # Extract only 1 frame
                        format='image2',
                        vcodec='mjpeg',
                        **{'q:v': 2}  # High quality JPEG
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )
                
                # Check if the file was actually created and has content
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    logging.error(f"FFmpeg did not create output file or file is empty")
                    return None
                
                # Read the extracted frame and convert to base64
                with open(temp_path, 'rb') as img_file:
                    img_data = img_file.read()
                
                # Convert to base64
                base64_image = base64.b64encode(img_data).decode('utf-8')
                
                # Return in format suitable for Gemini API
                return f"data:image/jpeg;base64,{base64_image}"
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except subprocess.CalledProcessError as e:
            # Handle ffmpeg execution errors
            stderr_output = ""
            if hasattr(e, 'stderr') and e.stderr:
                stderr_output = e.stderr.decode('utf-8', errors='ignore')
            logging.error(f"FFmpeg command failed (return code {e.returncode}): {stderr_output}")
            return None
        except FileNotFoundError as e:
            # Handle case where ffmpeg binary is not found
            logging.error(f"FFmpeg binary not found: {str(e)}")
            return None
        except PermissionError as e:
            # Handle permission issues
            logging.error(f"Permission error accessing temporary file: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error in frame extraction: {str(e)}")
            return None

if __name__ == "__main__":
    # for local testing
    youtube_service = YouTubeTranscriptService()
    youtube_service.get_video_frame("https://www.youtube.com/watch?v=5iTOphGnCtg&t=548s", 10)

    