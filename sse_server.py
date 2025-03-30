#!/usr/bin/env python3
"""
SSE Server for MCP - Run this to start the MCP server in SSE mode
This server provides email functionality through Microsoft Graph API
"""
import os
import sys
from fastmcp import FastMCP
from fastmcp.resources import TextResource
from dotenv import load_dotenv
from graph_api import GraphAPIClient
from pdf_handler import PDFHandler

# Load environment variables
load_dotenv()

# Initialize clients
graph_client = GraphAPIClient()
pdf_handler = PDFHandler()

# Create MCP server
mcp = FastMCP(name="Graph API Server")

# Create a TextResource directly
email_resource = TextResource(
    name="email",
    description="Access and manage emails through Microsoft Graph API",
    uri="https://example.com/email",
    text="Email management through Microsoft Graph API"
)
mcp.add_resource(email_resource)

# Define tools for email operations
@mcp.tool()
async def list_emails(limit: int = 10, filter_query: str = None):
    """List recent emails from the inbox.
    
    Args:
        limit: Maximum number of emails to retrieve (default: 10)
        filter_query: Optional OData filter query for filtering emails
        
    Returns:
        List of email objects with basic information
    """
    return await graph_client.list_emails(limit, filter_query)

@mcp.tool()
async def get_email(email_id: str):
    """Retrieve a specific email by ID with full details.
    
    Args:
        email_id: The unique identifier of the email
        
    Returns:
        Complete email details including body, sender, recipients, etc.
    """
    return await graph_client.get_email(email_id)

@mcp.tool()
async def send_email(recipients: list, subject: str, body: str, attachments: list = None):
    """Send a new email.
    
    Args:
        recipients: List of email addresses to send to
        subject: Email subject line
        body: Email body content (HTML supported)
        attachments: Optional list of attachment paths or data
        
    Returns:
        Status of the email send operation
    """
    return await graph_client.send_email(recipients, subject, body, attachments)

@mcp.tool()
async def get_attachments(email_id: str):
    """Get all attachments from a specific email.
    
    Args:
        email_id: The unique identifier of the email
        
    Returns:
        List of attachment metadata
    """
    return await graph_client.get_attachments(email_id)

@mcp.tool()
async def download_attachment(email_id: str, attachment_id: str, save_path: str = None):
    """Download a specific email attachment.
    
    Args:
        email_id: The unique identifier of the email
        attachment_id: The unique identifier of the attachment
        save_path: Optional path to save the attachment to
        
    Returns:
        Path to the saved attachment or raw attachment data
    """
    return await graph_client.download_attachment(email_id, attachment_id, save_path)

@mcp.tool()
async def parse_pdf_attachment(email_id: str, attachment_id: str):
    """Parse a PDF attachment from an email.
    
    Args:
        email_id: The unique identifier of the email
        attachment_id: The unique identifier of the attachment
        
    Returns:
        Extracted text content from the PDF
    """
    attachment_data = await graph_client.download_attachment(email_id, attachment_id)
    return pdf_handler.parse_pdf(attachment_data)

if __name__ == "__main__":
    # Run the MCP server in SSE mode
    print("Starting MCP server in SSE mode...", file=sys.stderr)
    print("Connect Claude Desktop to this server to manage emails through Graph API", file=sys.stderr)
    mcp.run(transport="sse") 