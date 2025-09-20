# MCP Graph API

A custom MCP server for Microsoft Graph API integration, allowing:
- Reading and understanding emails
- Sending new emails with context
- Accessing and parsing PDF attachments from emails

## Setup

1. Install dependencies:
```bash
uv venv
uv pip install -r requirements.txt
```

2. Configure Microsoft Graph API credentials:
   - Create an Azure AD application
   - Set required permissions for Mail.Read, Mail.Send, etc.
   - Update the `.env` file with your credentials

3. Start the MCP server:
```bash
python main.py
```

### SSE transport (Claude Desktop compatible)

To expose the server over Server-Sent Events (SSE), run:

```bash
python sse_server.py [--host 0.0.0.0] [--port 9000]
```

You can also configure the listener using environment variables:

```bash
export MCP_SSE_HOST=0.0.0.0
export MCP_SSE_PORT=9000
python sse_server.py
```

If no host/port are provided, the server defaults to `127.0.0.1:8000` for
backward compatibility. When running the SSE server remotely, update your
Claude Desktop configuration so the MCP server entry points at the public URL,
and ensure the chosen port is allowed by your firewall or security group.

## Features

- Email reading and analysis
- Email composition and sending
- PDF attachment parsing
- Context-aware email interactions 
