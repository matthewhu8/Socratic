"""
MCP (Model Context Protocol) integration for Socratic application.
This module provides tools for AI models to interact with various services.
"""

import logging
import asyncio
from typing import Optional
from .client.mcp_client import MCPClientManager, mcp_context

logger = logging.getLogger(__name__)

# Global MCP client manager instance
_mcp_manager: Optional[MCPClientManager] = None

async def initialize_mcp(server_names=None):
    """Initialize MCP client connections"""
    global _mcp_manager
    
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
    
    try:
        await _mcp_manager.initialize(server_names)
        logger.info("MCP client manager initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize MCP: {e}")
        return False

async def get_mcp_manager() -> Optional[MCPClientManager]:
    """Get the global MCP client manager"""
    global _mcp_manager
    
    if _mcp_manager is None:
        success = await initialize_mcp()
        if not success:
            return None
    
    return _mcp_manager

async def shutdown_mcp():
    """Shutdown MCP connections"""
    global _mcp_manager
    
    if _mcp_manager:
        try:
            await _mcp_manager.close()
            logger.info("MCP client manager shutdown successfully")
        except Exception as e:
            logger.error(f"Error during MCP shutdown: {e}")
        finally:
            _mcp_manager = None