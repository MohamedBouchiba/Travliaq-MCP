from src.mcp_server.server import create_mcp
from mangum import Mangum

mcp = create_mcp()
app = mcp.http_app()
handler = Mangum(app)
