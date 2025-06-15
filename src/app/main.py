from fastapi import FastAPI

import app.gmail_mcp_server as gmail_mcp_server
import app.oauth as oauth

app = FastAPI(
    lifespan=lambda app: gmail_mcp_server.mcp.session_manager.run()
)

app.mount("/oauth2", oauth.oauth2Api)
app.mount("/mcp/gmail", app=gmail_mcp_server.mcp.streamable_http_app(), name="Gmail MCP")
