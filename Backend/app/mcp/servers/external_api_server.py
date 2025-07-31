"""
External API MCP Server for Socratic application.
Provides integration with external services (YouTube, Google, etc.) for AI models.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from mcp.server import Server
    from mcp.types import (
        Tool, 
        TextContent, 
        CallToolResult
    )
    from mcp.server.stdio import stdio_server
except ImportError:
    # Fallback for development
    class Server:
        def __init__(self, name: str, version: str):
            self.name = name
            self.version = version
        
        def list_tools(self):
            def decorator(func):
                return func
            return decorator
        
        def call_tool(self):
            def decorator(func):
                return func
            return decorator
    
    def stdio_server():
        def decorator(func):
            return func
        return decorator
    
    class Tool:
        def __init__(self, name: str, description: str, inputSchema: dict):
            self.name = name
            self.description = description
            self.inputSchema = inputSchema
    
    class TextContent:
        def __init__(self, text: str):
            self.text = text
    
    class CallToolResult:
        def __init__(self, content: List):
            self.content = content

try:
    import requests
    from youtube_transcript_api import YouTubeTranscriptApi
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token
except ImportError:
    # Fallback imports
    requests = None
    YouTubeTranscriptApi = None
    google_requests = None
    id_token = None

logger = logging.getLogger(__name__)

class ExternalAPIMCPServer:
    """MCP Server for external API integrations"""
    
    def __init__(self):
        self.server = Server("external-api-server", "1.0.0")
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="fetch_youtube_transcript",
                    description="Fetch transcript from a YouTube video",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {"type": "string", "description": "YouTube video ID"},
                            "video_url": {"type": "string", "description": "Full YouTube URL (alternative to video_id)"},
                            "language": {"type": "string", "default": "en", "description": "Preferred language code"},
                            "include_timestamps": {"type": "boolean", "default": True, "description": "Include timestamp information"}
                        }
                    }
                ),
                Tool(
                    name="get_video_metadata",
                    description="Get metadata for a YouTube video",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {"type": "string", "description": "YouTube video ID"},
                            "video_url": {"type": "string", "description": "Full YouTube URL (alternative to video_id)"},
                            "include_statistics": {"type": "boolean", "default": False, "description": "Include view count, likes, etc."}
                        }
                    }
                ),
                Tool(
                    name="authenticate_google_user",
                    description="Authenticate and validate Google user tokens",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "id_token": {"type": "string", "description": "Google ID token"},
                            "client_id": {"type": "string", "description": "Google Client ID (optional, uses env var if not provided)"}
                        },
                        "required": ["id_token"]
                    }
                ),
                Tool(
                    name="fetch_external_content",
                    description="Fetch content from external URLs with safety checks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "format": "uri", "description": "URL to fetch"},
                            "method": {"type": "string", "enum": ["GET", "POST"], "default": "GET"},
                            "headers": {"type": "object", "description": "Additional headers"},
                            "timeout": {"type": "integer", "default": 30, "description": "Request timeout in seconds"},
                            "max_size": {"type": "integer", "default": 10485760, "description": "Maximum response size in bytes (10MB default)"}
                        },
                        "required": ["url"]
                    }
                )
            ]
        
        @self.server.call_tool() 
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "fetch_youtube_transcript":
                    result = await self._fetch_youtube_transcript(**arguments)
                elif name == "get_video_metadata":
                    result = await self._get_video_metadata(**arguments)
                elif name == "authenticate_google_user":
                    result = await self._authenticate_google_user(**arguments)
                elif name == "fetch_external_content":
                    result = await self._fetch_external_content(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(content=[TextContent(text=json.dumps(result))])
                
            except Exception as e:
                logger.error(f"Tool call error for {name}: {e}")
                error_result = {"error": str(e)}
                return CallToolResult(content=[TextContent(text=json.dumps(error_result))])
    
    # Tool implementation methods
    async def _fetch_youtube_transcript(self,
                                      video_id: Optional[str] = None,
                                      video_url: Optional[str] = None,
                                      language: str = "en",
                                      include_timestamps: bool = True) -> Dict:
        """Fetch transcript from a YouTube video"""
        try:
            if not YouTubeTranscriptApi:
                return {"error": "YouTube transcript API not available"}
            
            # Extract video ID from URL if provided
            if video_url and not video_id:
                video_id = self._extract_video_id(video_url)
            
            if not video_id:
                return {"error": "No video ID provided"}
            
            # Fetch transcript
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # Try to get transcript in preferred language
                try:
                    transcript = transcript_list.find_transcript([language])
                except:
                    # Fall back to any available transcript
                    try:
                        transcript = transcript_list.find_manually_created_transcript(['en'])
                    except:
                        transcript = transcript_list.find_generated_transcript(['en'])
                
                # Fetch the actual transcript data
                transcript_data = transcript.fetch()
                
                if include_timestamps:
                    formatted_transcript = []
                    for item in transcript_data:
                        formatted_transcript.append({
                            "text": item['text'],
                            "start": item['start'],
                            "duration": item['duration']
                        })
                    
                    # Also create a simple text version
                    text_only = " ".join([item['text'] for item in transcript_data])
                    
                    return {
                        "status": "success",
                        "video_id": video_id,
                        "language": transcript.language_code,
                        "is_generated": transcript.is_generated,
                        "transcript_with_timestamps": formatted_transcript,
                        "text_only": text_only,
                        "total_duration": max([item['start'] + item['duration'] for item in transcript_data])
                    }
                else:
                    text_only = " ".join([item['text'] for item in transcript_data])
                    return {
                        "status": "success",
                        "video_id": video_id,
                        "language": transcript.language_code,
                        "is_generated": transcript.is_generated,
                        "transcript": text_only
                    }
                    
            except Exception as e:
                return {"error": f"Failed to fetch transcript: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error fetching YouTube transcript: {e}")
            return {"error": f"Transcript fetch failed: {str(e)}"}
    
    async def _get_video_metadata(self,
                                video_id: Optional[str] = None,
                                video_url: Optional[str] = None,
                                include_statistics: bool = False) -> Dict:
        """Get metadata for a YouTube video"""
        try:
            if not requests:
                return {"error": "Requests library not available"}
            
            # Extract video ID from URL if provided
            if video_url and not video_id:
                video_id = self._extract_video_id(video_url)
            
            if not video_id:
                return {"error": "No video ID provided"}
            
            if self.youtube_api_key:
                # Use YouTube Data API if available
                base_url = "https://www.googleapis.com/youtube/v3/videos"
                parts = ["snippet"]
                if include_statistics:
                    parts.append("statistics")
                
                params = {
                    "id": video_id,
                    "part": ",".join(parts),
                    "key": self.youtube_api_key
                }
                
                response = requests.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                if not data.get("items"):
                    return {"error": "Video not found"}
                
                video_data = data["items"][0]
                snippet = video_data["snippet"]
                
                result = {
                    "status": "success",
                    "video_id": video_id,
                    "title": snippet.get("title"),
                    "description": snippet.get("description"),
                    "channel_title": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                    "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                    "duration": video_data.get("contentDetails", {}).get("duration"),
                    "category_id": snippet.get("categoryId")
                }
                
                if include_statistics and "statistics" in video_data:
                    stats = video_data["statistics"]
                    result["statistics"] = {
                        "view_count": stats.get("viewCount"),
                        "like_count": stats.get("likeCount"),
                        "comment_count": stats.get("commentCount")
                    }
                
                return result
            else:
                # Fallback: try to get basic info without API key
                # This is limited and may not always work
                try:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Very basic scraping - this is fragile and limited
                    html = response.text
                    
                    # Try to extract title
                    title_start = html.find('<title>')
                    title_end = html.find('</title>')
                    if title_start != -1 and title_end != -1:
                        title = html[title_start + 7:title_end].replace(' - YouTube', '')
                    else:
                        title = "Unknown"
                    
                    return {
                        "status": "limited_success",
                        "video_id": video_id,
                        "title": title,
                        "note": "Limited metadata without YouTube API key"
                    }
                    
                except Exception as e:
                    return {"error": f"Failed to get metadata without API: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error getting video metadata: {e}")
            return {"error": f"Metadata fetch failed: {str(e)}"}
    
    async def _authenticate_google_user(self,
                                      id_token_str: str,
                                      client_id: Optional[str] = None) -> Dict:
        """Authenticate and validate Google user tokens"""
        try:
            if not id_token or not google_requests:
                return {"error": "Google authentication libraries not available"}
            
            # Use provided client_id or fall back to environment variable
            google_client_id = client_id or self.google_client_id
            if not google_client_id:
                return {"error": "Google Client ID not configured"}
            
            try:
                # Verify the ID token with Google
                id_info = id_token.verify_oauth2_token(
                    id_token_str, 
                    google_requests.Request(), 
                    google_client_id
                )
                
                # Extract user information
                user_email = id_info.get("email")
                user_name = id_info.get("name")
                google_user_id = id_info.get("sub")
                email_verified = id_info.get("email_verified", False)
                
                return {
                    "status": "success",
                    "user_email": user_email,
                    "user_name": user_name,
                    "google_user_id": google_user_id,
                    "email_verified": email_verified,
                    "issued_at": id_info.get("iat"),
                    "expires_at": id_info.get("exp")
                }
                
            except ValueError as e:
                return {"error": f"Token verification failed: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error authenticating Google user: {e}")
            return {"error": f"Authentication failed: {str(e)}"}
    
    async def _fetch_external_content(self,
                                    url: str,
                                    method: str = "GET",
                                    headers: Optional[Dict] = None,
                                    timeout: int = 30,
                                    max_size: int = 10485760) -> Dict:
        """Fetch content from external URLs with safety checks"""
        try:
            if not requests:
                return {"error": "Requests library not available"}
            
            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                return {"error": "Invalid URL scheme. Only HTTP and HTTPS are allowed"}
            
            # Prepare headers
            request_headers = {
                "User-Agent": "Socratic-AI-Bot/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            if headers:
                request_headers.update(headers)
            
            # Make request
            if method == "GET":
                response = requests.get(
                    url, 
                    headers=request_headers, 
                    timeout=timeout,
                    stream=True  # For size checking
                )
            elif method == "POST":
                response = requests.post(
                    url, 
                    headers=request_headers, 
                    timeout=timeout
                )
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            
            response.raise_for_status()
            
            # Check content size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > max_size:
                return {"error": f"Content too large: {content_length} bytes (max: {max_size})"}
            
            # Read content with size limit
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > max_size:
                    return {"error": f"Content exceeded size limit during download"}
            
            # Try to decode as text
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('latin1')
                except UnicodeDecodeError:
                    text_content = content.decode('utf-8', errors='ignore')
            
            return {
                "status": "success",
                "url": url,
                "status_code": response.status_code,
                "content_type": response.headers.get('content-type'),
                "content_length": len(content),
                "content": text_content,
                "headers": dict(response.headers),
                "encoding": response.encoding
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {url}: {e}")
            return {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Error fetching external content: {e}")
            return {"error": f"Fetch failed: {str(e)}"}
    
    # Helper methods
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        try:
            # Handle various YouTube URL formats
            if "youtube.com/watch?v=" in url:
                return url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                return url.split("youtu.be/")[1].split("?")[0]
            elif "youtube.com/embed/" in url:
                return url.split("embed/")[1].split("?")[0]
            else:
                return None
        except (IndexError, AttributeError):
            return None

# Main entry point for MCP server
async def main():
    """Main entry point for the MCP server"""
    try:
        # Initialize the server
        server_instance = ExternalAPIMCPServer()
        
        # Run the server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            await server_instance.server.run(
                read_stream,
                write_stream,
                server_instance.server.create_initialization_options()
            )
            
    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the server
    asyncio.run(main())