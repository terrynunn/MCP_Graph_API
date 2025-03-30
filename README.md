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

## Features

- Email reading and analysis
- Email composition and sending
- PDF attachment parsing
- Context-aware email interactions 