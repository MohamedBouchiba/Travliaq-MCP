"""
ASGI application for Travliaq MCP Server.

This follows FastMCP best practices for production deployment.
Run with: uvicorn app:app --host 0.0.0.0 --port 8005

The MCP endpoint will be available at: http://localhost:8005/mcp
"""
from src.mcp_server.server import mcp

# Create ASGI app - uvicorn will use this
app = mcp.http_app()
