from src.mcp_server.server import create_mcp
mcp = create_mcp()
app = mcp.http_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
