"""
Simple HTTP server wrapper for Travliaq MCP Server.

RECOMMENDED: Use 'uvicorn app:app --host 0.0.0.0 --port 8005' instead
for better production deployment (see app.py).

This file is kept for backward compatibility and quick local testing.
"""
import os
from src.mcp_server.server import mcp

if __name__ == "__main__":
    print("⚠️  For production, use: uvicorn app:app --host 0.0.0.0 --port 8005")
    print("   This provides better stability and control.\n")
    
    port = int(os.environ.get("PORT", 8005))
    mcp.run(transport="http", host="0.0.0.0", port=port)
