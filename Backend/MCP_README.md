# MCP (Model Context Protocol) Integration for Socratic

This document explains the MCP integration in the Socratic application and how to set it up.

## Overview

The Socratic application now uses the Model Context Protocol (MCP) to enable AI models to directly interact with various services including:

- **Smart Practice Server**: Adaptive question selection and student performance analysis
- **Database Server**: Direct PostgreSQL operations for student data, questions, and analytics
- **Filesystem Server**: Image processing and file management
- **External API Server**: Integration with YouTube, Google Auth, and other external services

## Architecture

```
AI Models (Gemini) → MCP Client → MCP Servers → Resources (DB, Files, APIs)
```

### Key Benefits

- **Direct Database Access**: AI can query student data without API overhead
- **Better Context Management**: Persistent state across AI interactions  
- **Standardized Interface**: Consistent tool calling across all AI models
- **Enhanced Capabilities**: AI can perform complex multi-step operations
- **Better Error Handling**: Protocol-level validation and error management

## Setup Instructions

### 1. Install Dependencies

The required MCP packages are already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Ensure these environment variables are set:

```bash
# Required for all MCP servers
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your_gemini_api_key

# Optional - for external API server
GOOGLE_CLIENT_ID=your_google_client_id
YOUTUBE_API_KEY=your_youtube_api_key

# Optional - for filesystem server
UPLOAD_DIR=./temp_uploads
```

### 3. Validate Setup

Run the validation script to check your setup:

```bash
python validate_mcp_setup.py
```

This will check:
- Environment variables
- Python dependencies
- MCP configuration files
- Database and Redis connections

### 4. Start MCP Servers

You have several options for starting MCP servers:

#### Option A: Automatic startup (Recommended)
The servers will start automatically when the GeminiService initializes them.

#### Option B: Manual startup
```bash
# Start all servers
python start_mcp_servers.py start

# Start specific server
python start_mcp_servers.py start --server smart_practice

# Monitor servers (start + auto-restart)
python start_mcp_servers.py monitor

# Check status
python start_mcp_servers.py status

# Stop servers
python start_mcp_servers.py stop
```

### 5. Run Your Application

Start your FastAPI application as usual:

```bash
uvicorn app.main:app --reload
```

## Configuration

### Server Configuration

MCP servers are configured in `app/mcp/config/server_configs.json`. Each server has:

- **name**: Human-readable name
- **description**: What the server does
- **command**: How to start the server (usually "python")
- **args**: Command line arguments
- **env**: Environment variables specific to this server
- **tools**: List of available tools/functions
- **transport**: Communication method (currently "stdio")

### Adding New Servers

1. Create a new server file in `app/mcp/servers/`
2. Follow the MCP server pattern (see existing servers)
3. Add configuration to `server_configs.json`
4. Update the startup scripts if needed

## Usage in Code

### GeminiService Integration

The `GeminiService` now automatically uses MCP for smart practice features:

```python
from app.services.gemini_service import GeminiService

gemini_service = GeminiService()

# This now uses MCP behind the scenes
result = await gemini_service.select_next_smart_question(
    student_id=123,
    subject="mathematics",
    chapter="Algebra"
)
```

### Direct MCP Usage

You can also use MCP directly:

```python
from app.mcp.client.mcp_client import get_mcp_manager

# Get MCP manager
mcp_manager = await get_mcp_manager()

# Call tools directly
profile = await mcp_manager.call_tool(
    "smart_practice",
    "get_student_profile", 
    {"student_id": 123}
)
```

## Available MCP Tools

### Smart Practice Server
- `get_student_profile`: Get detailed skill profile and performance
- `search_adaptive_questions`: Find questions matching skill requirements
- `calculate_zpd_difficulty`: Calculate optimal difficulty level
- `analyze_learning_patterns`: Analyze learning patterns and suggestions
- `record_smart_practice_attempt`: Record student attempts
- `generate_custom_question`: Generate new questions when needed

### Database Server
- `query_students`: Query student information
- `query_questions`: Query questions from various sources
- `query_grading_sessions`: Query performance history
- `update_knowledge_profile`: Update student profiles
- `create_grading_session`: Create new grading records
- `get_student_analytics`: Get comprehensive analytics

### Filesystem Server
- `save_image`: Save images from base64 data
- `load_image`: Load images as base64
- `process_canvas_image`: Process whiteboard/canvas images
- `cleanup_temp_files`: Clean up temporary files
- `analyze_image_content`: Analyze image content and metadata

### External API Server
- `fetch_youtube_transcript`: Get YouTube video transcripts
- `get_video_metadata`: Get YouTube video information
- `authenticate_google_user`: Validate Google auth tokens
- `fetch_external_content`: Fetch content from external URLs

## Troubleshooting

### Common Issues

1. **"MCP client manager not available"**
   - Check that environment variables are set
   - Ensure MCP servers can start (run validation script)
   - Check logs for server startup errors

2. **"Server not connected"**
   - Verify server configurations in `server_configs.json`
   - Check that the server file exists and is executable
   - Look at server logs for startup issues

3. **Database/Redis connection errors**
   - Verify connection strings in environment variables
   - Ensure services are running and accessible
   - Check network connectivity and permissions

4. **Import errors**
   - Ensure all MCP packages are installed: `pip install mcp mcp-server mcp-types`
   - Check Python path and virtual environment

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check server logs and process status:

```bash
python start_mcp_servers.py status
```

Validate your setup:

```bash
python validate_mcp_setup.py
```

## Migration Notes

The transition from the old "fake MCP" to real MCP includes:

### What Changed
- `SmartPracticeMCPServer` is now a real MCP server using the MCP protocol
- `GeminiService` uses real MCP client instead of manual function calls
- Endpoints in `main.py` simplified to use the new MCP integration
- Added proper MCP infrastructure (client manager, server configs, etc.)

### What Stayed the Same
- API endpoints remain unchanged
- Database models and schemas unchanged
- Frontend integration unchanged
- Core business logic preserved

### Benefits
- Better separation of concerns
- Protocol-level validation and error handling
- Standardized tool calling interface
- Easier to test and maintain
- Future-proof for other MCP-compatible models

## Performance Considerations

- MCP servers run as separate processes, adding some overhead
- Benefits of direct database access often outweigh the process overhead
- Consider caching strategies for frequently accessed data
- Monitor server resource usage in production

## Security

- MCP servers have direct database access - ensure proper validation
- Environment variables contain sensitive data - secure appropriately
- Consider network security if running distributed MCP servers
- Validate all inputs to MCP tools

## Future Enhancements

- Add more specialized MCP servers (e.g., email, calendar, external learning platforms)
- Implement HTTP+SSE transport for distributed deployments
- Add comprehensive logging and monitoring
- Create web UI for MCP server management
- Add automated testing for MCP integrations