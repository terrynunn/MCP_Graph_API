#!/usr/bin/env python3
import os
import sys
from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Simple Email Server")

# Define a resource 
@mcp.resource("email://info")
def get_email_info() -> dict:
    """Get information about the email functionality and credentials status"""
    # Check if credentials are available
    has_credentials = all([
        os.environ.get("MICROSOFT_CLIENT_ID"),
        os.environ.get("MICROSOFT_CLIENT_SECRET"),
        os.environ.get("MICROSOFT_TENANT_ID"),
        os.environ.get("AUTHORITY"),
        os.environ.get("SCOPE")
    ])
    
    return {
        "description": "This server provides basic email information through Microsoft Graph API",
        "credentials_available": has_credentials,
        "user_email": os.environ.get("MS_GRAPH_USER_EMAIL", "Not set")
    }

# Define a simple tool that doesn't require external dependencies
@mcp.tool()
def get_email_status() -> dict:
    """Get the status of email service"""
    return {
        "status": "active",
        "service": "Microsoft Graph API",
        "capabilities": [
            "Reading emails",
            "Sending emails",
            "Managing attachments",
            "Parsing PDF content"
        ],
        "connected_account": os.environ.get("MS_GRAPH_USER_EMAIL", "Not set")
    }

@mcp.tool()
def compose_email(to: str, subject: str, body: str) -> dict:
    """Compose an email (simulation only)"""
    return {
        "to": to,
        "subject": subject,
        "body": body,
        "status": "draft",
        "from": os.environ.get("MS_GRAPH_USER_EMAIL", "unknown@example.com")
    }

# Add a prompt for the LLM
@mcp.prompt()
def email_help() -> str:
    email = os.environ.get("MS_GRAPH_USER_EMAIL", "unknown@example.com")
    return f"""
    You have access to basic email capabilities for {email} through Microsoft Graph API.
    
    Available tools:
    1. get_email_status - Check email service status
    2. compose_email - Draft a new email
    
    How can I help you today?
    """

if __name__ == "__main__":
    # Run the MCP server
    print("Starting simple MCP server...", file=sys.stderr)
    mcp.run() 