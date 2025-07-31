"""
Filesystem MCP Server for Socratic application.
Provides file and image processing operations for AI models.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Any
import json
import base64
import tempfile
import shutil
from pathlib import Path

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
    from PIL import Image
    import io
except ImportError:
    # Fallback if PIL not available
    Image = None
    io = None

logger = logging.getLogger(__name__)

class FilesystemMCPServer:
    """MCP Server for file and image processing operations"""
    
    def __init__(self):
        self.server = Server("filesystem-server", "1.0.0")
        self.upload_dir = Path(os.getenv("UPLOAD_DIR", "./temp_uploads"))
        self.upload_dir.mkdir(exist_ok=True)
        self._register_tools()
    
    def _register_tools(self):
        """Register MCP tools"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="save_image",
                    description="Save an image from base64 data to filesystem",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_data": {"type": "string", "description": "Base64 encoded image data"},
                            "filename": {"type": "string", "description": "Desired filename (optional)"},
                            "format": {"type": "string", "enum": ["png", "jpg", "jpeg", "webp"], "default": "png"},
                            "session_id": {"type": "string", "description": "Session ID for organization"}
                        },
                        "required": ["image_data"]
                    }
                ),
                Tool(
                    name="load_image",
                    description="Load an image file and return as base64",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to image file"},
                            "max_size": {"type": "integer", "default": 1024, "description": "Maximum dimension in pixels"}
                        },
                        "required": ["file_path"]
                    }
                ),
                Tool(
                    name="process_canvas_image",
                    description="Process canvas image data for AI analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "canvas_data": {"type": "string", "description": "Base64 encoded canvas image"},
                            "previous_canvas": {"type": "string", "description": "Previous canvas state for comparison"},
                            "operation": {
                                "type": "string",
                                "enum": ["analyze", "compare", "extract_annotations"],
                                "default": "analyze"
                            }
                        },
                        "required": ["canvas_data"]
                    }
                ),
                Tool(
                    name="cleanup_temp_files",
                    description="Clean up temporary files and directories",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {"type": "string", "description": "Session ID to clean up"},
                            "older_than_hours": {"type": "integer", "default": 24, "description": "Delete files older than N hours"},
                            "file_pattern": {"type": "string", "description": "File pattern to match (glob style)"}
                        }
                    }
                ),
                Tool(
                    name="analyze_image_content",
                    description="Analyze image content and extract metadata",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "image_path": {"type": "string", "description": "Path to image file"},
                            "analysis_type": {
                                "type": "string",
                                "enum": ["basic", "detailed", "handwriting"],
                                "default": "basic"
                            }
                        },
                        "required": ["image_path"]
                    }
                )
            ]
        
        @self.server.call_tool() 
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "save_image":
                    result = await self._save_image(**arguments)
                elif name == "load_image":
                    result = await self._load_image(**arguments)
                elif name == "process_canvas_image":
                    result = await self._process_canvas_image(**arguments)
                elif name == "cleanup_temp_files":
                    result = await self._cleanup_temp_files(**arguments)
                elif name == "analyze_image_content":
                    result = await self._analyze_image_content(**arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return CallToolResult(content=[TextContent(text=json.dumps(result))])
                
            except Exception as e:
                logger.error(f"Tool call error for {name}: {e}")
                error_result = {"error": str(e)}
                return CallToolResult(content=[TextContent(text=json.dumps(error_result))])
    
    # Tool implementation methods
    async def _save_image(self,
                         image_data: str,
                         filename: Optional[str] = None,
                         format: str = "png",
                         session_id: Optional[str] = None) -> Dict:
        """Save an image from base64 data to filesystem"""
        try:
            # Clean image data (remove data URL prefix if present)
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            # Decode base64
            try:
                decoded_data = base64.b64decode(image_data)
            except Exception as e:
                return {"error": f"Invalid base64 data: {str(e)}"}
            
            # Generate filename if not provided
            if not filename:
                import uuid
                timestamp = int(os.time())
                filename = f"image_{timestamp}_{uuid.uuid4().hex[:8]}.{format}"
            
            # Create session directory if provided
            if session_id:
                session_dir = self.upload_dir / session_id
                session_dir.mkdir(exist_ok=True)
                file_path = session_dir / filename
            else:
                file_path = self.upload_dir / filename
            
            # Save image
            if Image and format.lower() in ['png', 'jpg', 'jpeg', 'webp']:
                # Use PIL for better image handling
                try:
                    pil_image = Image.open(io.BytesIO(decoded_data))
                    
                    # Convert to RGB if saving as JPEG
                    if format.lower() in ['jpg', 'jpeg'] and pil_image.mode in ('RGBA', 'LA', 'P'):
                        # Create white background
                        rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                        if pil_image.mode == 'P':
                            pil_image = pil_image.convert('RGBA')
                        rgb_image.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
                        pil_image = rgb_image
                    
                    pil_image.save(file_path, format=format.upper())
                    
                    # Get image info
                    width, height = pil_image.size
                    file_size = file_path.stat().st_size
                    
                    return {
                        "status": "success",
                        "file_path": str(file_path),
                        "filename": filename,
                        "size_bytes": file_size,
                        "dimensions": {"width": width, "height": height},
                        "format": format
                    }
                    
                except Exception as e:
                    logger.warning(f"PIL processing failed, falling back to raw save: {e}")
            
            # Fallback: save raw data
            with open(file_path, 'wb') as f:
                f.write(decoded_data)
            
            file_size = file_path.stat().st_size
            
            return {
                "status": "success",
                "file_path": str(file_path),
                "filename": filename,
                "size_bytes": file_size,
                "format": format
            }
            
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return {"error": f"Save failed: {str(e)}"}
    
    async def _load_image(self,
                         file_path: str,
                         max_size: int = 1024) -> Dict:
        """Load an image file and return as base64"""
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {"error": "File not found"}
            
            if not path.is_file():
                return {"error": "Path is not a file"}
            
            # Check file size (limit to 10MB)
            if path.stat().st_size > 10 * 1024 * 1024:
                return {"error": "File too large (max 10MB)"}
            
            if Image:
                try:
                    # Use PIL for better image handling
                    with Image.open(path) as pil_image:
                        # Resize if too large
                        if pil_image.width > max_size or pil_image.height > max_size:
                            pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                        
                        # Convert to RGB if necessary
                        if pil_image.mode in ('RGBA', 'LA', 'P'):
                            rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                            if pil_image.mode == 'P':
                                pil_image = pil_image.convert('RGBA')
                            rgb_image.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == 'RGBA' else None)
                            pil_image = rgb_image
                        
                        # Convert to base64
                        buffer = io.BytesIO()
                        pil_image.save(buffer, format='PNG')
                        image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        
                        return {
                            "status": "success",
                            "image_data": image_data,
                            "original_dimensions": {"width": pil_image.width, "height": pil_image.height},
                            "file_size": path.stat().st_size,
                            "format": "png"
                        }
                        
                except Exception as e:
                    logger.warning(f"PIL loading failed, falling back to raw load: {e}")
            
            # Fallback: load raw data
            with open(path, 'rb') as f:
                raw_data = f.read()
                image_data = base64.b64encode(raw_data).decode('utf-8')
                
                return {
                    "status": "success",
                    "image_data": image_data,
                    "file_size": len(raw_data),
                    "format": "raw"
                }
            
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return {"error": f"Load failed: {str(e)}"}
    
    async def _process_canvas_image(self,
                                  canvas_data: str,
                                  previous_canvas: Optional[str] = None,
                                  operation: str = "analyze") -> Dict:
        """Process canvas image data for AI analysis"""
        try:
            if operation == "analyze":
                # Basic analysis of canvas content
                result = {
                    "operation": "analyze",
                    "has_content": len(canvas_data) > 0,
                    "estimated_size": len(canvas_data),
                    "analysis": "Canvas contains drawing data"
                }
                
                if Image:
                    try:
                        # Try to analyze the actual image
                        if canvas_data.startswith('data:image'):
                            canvas_data = canvas_data.split(',')[1]
                        
                        decoded_data = base64.b64decode(canvas_data)
                        pil_image = Image.open(io.BytesIO(decoded_data))
                        
                        # Basic image analysis
                        width, height = pil_image.size
                        mode = pil_image.mode
                        
                        # Check if image has significant non-white content
                        if mode in ('RGB', 'RGBA'):
                            # Convert to grayscale and check variance
                            grayscale = pil_image.convert('L')
                            pixels = list(grayscale.getdata())
                            non_white_pixels = sum(1 for p in pixels if p < 240)  # Not pure white
                            content_ratio = non_white_pixels / len(pixels)
                            
                            result.update({
                                "dimensions": {"width": width, "height": height},
                                "mode": mode,
                                "content_ratio": round(content_ratio, 3),
                                "has_drawing": content_ratio > 0.01  # More than 1% non-white
                            })
                            
                    except Exception as e:
                        logger.warning(f"Image analysis failed: {e}")
                        result["analysis_error"] = str(e)
                
                return result
                
            elif operation == "compare" and previous_canvas:
                # Compare two canvas states
                result = {
                    "operation": "compare",
                    "current_size": len(canvas_data),
                    "previous_size": len(previous_canvas),
                    "size_difference": len(canvas_data) - len(previous_canvas)
                }
                
                if Image:
                    try:
                        # Load both images and compare
                        if canvas_data.startswith('data:image'):
                            canvas_data = canvas_data.split(',')[1]
                        if previous_canvas.startswith('data:image'):
                            previous_canvas = previous_canvas.split(',')[1]
                        
                        current_img = Image.open(io.BytesIO(base64.b64decode(canvas_data)))
                        previous_img = Image.open(io.BytesIO(base64.b64decode(previous_canvas)))
                        
                        if current_img.size == previous_img.size:
                            # Pixel-level comparison (simplified)
                            current_pixels = list(current_img.convert('RGB').getdata())
                            previous_pixels = list(previous_img.convert('RGB').getdata())
                            
                            different_pixels = sum(1 for i, (c, p) in enumerate(zip(current_pixels, previous_pixels)) if c != p)
                            difference_ratio = different_pixels / len(current_pixels)
                            
                            result.update({
                                "pixel_differences": different_pixels,
                                "difference_ratio": round(difference_ratio, 3),
                                "has_changes": difference_ratio > 0.001
                            })
                        else:
                            result["size_mismatch"] = True
                            
                    except Exception as e:
                        logger.warning(f"Image comparison failed: {e}")
                        result["comparison_error"] = str(e)
                
                return result
                
            elif operation == "extract_annotations":
                # Extract annotation data from canvas
                return {
                    "operation": "extract_annotations",
                    "annotations": "Annotation extraction not implemented in this version",
                    "note": "This would identify different types of markings, text, shapes, etc."
                }
            
            else:
                return {"error": f"Unknown operation: {operation}"}
            
        except Exception as e:
            logger.error(f"Error processing canvas image: {e}")
            return {"error": f"Processing failed: {str(e)}"}
    
    async def _cleanup_temp_files(self,
                                session_id: Optional[str] = None,
                                older_than_hours: int = 24,
                                file_pattern: Optional[str] = None) -> Dict:
        """Clean up temporary files and directories"""
        try:
            import glob
            import time
            
            deleted_files = 0
            deleted_size = 0
            current_time = time.time()
            age_threshold = older_than_hours * 3600  # Convert to seconds
            
            if session_id:
                # Clean specific session directory
                session_dir = self.upload_dir / session_id
                if session_dir.exists():
                    for file_path in session_dir.rglob("*"):
                        if file_path.is_file():
                            file_age = current_time - file_path.stat().st_mtime
                            if file_age > age_threshold:
                                file_size = file_path.stat().st_size
                                file_path.unlink()
                                deleted_files += 1
                                deleted_size += file_size
                    
                    # Remove empty directory
                    try:
                        session_dir.rmdir()
                    except OSError:
                        pass  # Directory not empty
            else:
                # Clean all files matching criteria
                search_pattern = file_pattern or "*"
                for file_path in self.upload_dir.rglob(search_pattern):
                    if file_path.is_file():
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > age_threshold:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            deleted_files += 1
                            deleted_size += file_size
            
            return {
                "status": "success",
                "deleted_files": deleted_files,
                "deleted_size_bytes": deleted_size,
                "deleted_size_mb": round(deleted_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
            return {"error": f"Cleanup failed: {str(e)}"}
    
    async def _analyze_image_content(self,
                                   image_path: str,
                                   analysis_type: str = "basic") -> Dict:
        """Analyze image content and extract metadata"""
        try:
            path = Path(image_path)
            
            if not path.exists():
                return {"error": "Image file not found"}
            
            if not Image:
                return {"error": "PIL not available for image analysis"}
            
            with Image.open(path) as pil_image:
                basic_info = {
                    "file_path": str(path),
                    "file_size": path.stat().st_size,
                    "dimensions": {"width": pil_image.width, "height": pil_image.height},
                    "mode": pil_image.mode,
                    "format": pil_image.format
                }
                
                if analysis_type == "basic":
                    return {
                        "analysis_type": "basic",
                        **basic_info
                    }
                
                elif analysis_type == "detailed":
                    # More detailed analysis
                    # Check if image has transparency
                    has_transparency = pil_image.mode in ('RGBA', 'LA') or 'transparency' in pil_image.info
                    
                    # Basic color analysis
                    if pil_image.mode in ('RGB', 'RGBA'):
                        colors = pil_image.getcolors(maxcolors=256*256*256)
                        if colors:
                            dominant_color = max(colors, key=lambda x: x[0])[1]
                            num_unique_colors = len(colors)
                        else:
                            dominant_color = None
                            num_unique_colors = "many"
                    else:
                        dominant_color = None
                        num_unique_colors = "unknown"
                    
                    return {
                        "analysis_type": "detailed",
                        **basic_info,
                        "has_transparency": has_transparency,
                        "dominant_color": dominant_color,
                        "unique_colors": num_unique_colors
                    }
                
                elif analysis_type == "handwriting":
                    # Specific analysis for handwriting detection
                    grayscale = pil_image.convert('L')
                    pixels = list(grayscale.getdata())
                    
                    # Simple heuristics for handwriting detection
                    dark_pixels = sum(1 for p in pixels if p < 128)
                    total_pixels = len(pixels)
                    ink_ratio = dark_pixels / total_pixels
                    
                    # Check for stroke patterns (simplified)
                    has_strokes = ink_ratio > 0.01 and ink_ratio < 0.8
                    
                    return {
                        "analysis_type": "handwriting",
                        **basic_info,
                        "ink_ratio": round(ink_ratio, 3),
                        "likely_has_handwriting": has_strokes,
                        "confidence": "low",  # This is a very basic analysis
                        "note": "Advanced handwriting detection would require ML models"
                    }
                
                else:
                    return {"error": f"Unknown analysis type: {analysis_type}"}
            
        except Exception as e:
            logger.error(f"Error analyzing image content: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

# Main entry point for MCP server
async def main():
    """Main entry point for the MCP server"""
    try:
        # Initialize the server
        server_instance = FilesystemMCPServer()
        
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