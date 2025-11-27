import os
from src.mcp_server.server import create_mcp

if __name__ == "__main__":
    mcp = create_mcp()
    # Use SSE transport for compatibility with MCP Python client (sse_client)
    # The SSE endpoint will be available at the root path "/"
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
