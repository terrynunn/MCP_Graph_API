#!/usr/bin/env python3
import os
import json
import asyncio
import sys
import platform
import socket
from graph_api import GraphAPIClient
from pdf_handler import PDFHandler
from mcp.server.fastmcp import FastMCP, Context

try:
    from dotenv import load_dotenv
    # Try to load environment variables from .env file, but don't fail if it doesn't exist
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, using environment variables directly", file=sys.stderr)

# Print environment variables (redacted for security)
print("Environment variables:", file=sys.stderr)
print(f"CLIENT_ID: {'Present' if os.environ.get('MICROSOFT_CLIENT_ID') else 'Missing'}", file=sys.stderr)
print(f"CLIENT_SECRET: {'Present' if os.environ.get('MICROSOFT_CLIENT_SECRET') else 'Missing'}", file=sys.stderr)
print(f"TENANT_ID: {'Present' if os.environ.get('MICROSOFT_TENANT_ID') else 'Missing'}", file=sys.stderr)
print(f"AUTHORITY: {'Present' if os.environ.get('AUTHORITY') else 'Missing'}", file=sys.stderr)
print(f"SCOPE: {os.environ.get('SCOPE')}", file=sys.stderr)
print(f"MS_GRAPH_USER_EMAIL: {os.environ.get('MS_GRAPH_USER_EMAIL')}", file=sys.stderr)

# Initialize clients
try:
    print("Initializing Graph API client...", file=sys.stderr)
    graph_client = GraphAPIClient()
    pdf_handler = PDFHandler()
except Exception as e:
    print(f"Error initializing clients: {e}", file=sys.stderr)
    # Continue anyway, as we want to at least start the server

# Create MCP server
mcp = FastMCP("Graph API Server")

# Define a resource for email info
@mcp.resource("email://info")
def get_email_info() -> str:
    """Get information about the email functionality"""
    credentials_status = "configured" if all([
        os.environ.get("MICROSOFT_CLIENT_ID"),
        os.environ.get("MICROSOFT_CLIENT_SECRET"),
        os.environ.get("MICROSOFT_TENANT_ID"),
        os.environ.get("AUTHORITY")
    ]) else "missing"
    
    return f"This server provides access to email functionality through Microsoft Graph API. Credentials are {credentials_status}."

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
    try:
        print(f"Listing {limit} emails with filter '{filter_query}'", file=sys.stderr)
        result = await graph_client.list_emails(limit, filter_query)
        if isinstance(result, dict) and "error" in result:
            print(f"Error in list_emails: {result['error']}", file=sys.stderr)
        return result
    except Exception as e:
        print(f"Exception in list_emails: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def get_email(email_id: str):
    """Retrieve a specific email by ID with full details.
    
    Args:
        email_id: The unique identifier of the email
        
    Returns:
        Complete email details including body, sender, recipients, etc.
    """
    try:
        print(f"Getting email with ID: {email_id}", file=sys.stderr)
        return await graph_client.get_email(email_id)
    except Exception as e:
        print(f"Exception in get_email: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

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
    try:
        print(f"Sending email to {recipients} with subject '{subject}'", file=sys.stderr)
        return await graph_client.send_email(recipients, subject, body, attachments)
    except Exception as e:
        print(f"Exception in send_email: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def get_attachments(email_id: str):
    """Get all attachments from a specific email.
    
    Args:
        email_id: The unique identifier of the email
        
    Returns:
        List of attachment metadata
    """
    try:
        print(f"Getting attachments for email: {email_id}", file=sys.stderr)
        return await graph_client.get_attachments(email_id)
    except Exception as e:
        print(f"Exception in get_attachments: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

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
    try:
        print(f"Downloading attachment {attachment_id} from email {email_id}", file=sys.stderr)
        attachment_data = await graph_client.download_attachment(email_id, attachment_id, save_path)
        if isinstance(attachment_data, dict) and "error" in attachment_data:
            return attachment_data
        return {"status": "success", "size": len(attachment_data) if not save_path else f"Saved to {save_path}"}
    except Exception as e:
        print(f"Exception in download_attachment: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def parse_pdf_attachment(email_id: str, attachment_id: str):
    """Parse a PDF attachment from an email.
    
    Args:
        email_id: The unique identifier of the email
        attachment_id: The unique identifier of the attachment
        
    Returns:
        Extracted text content from the PDF
    """
    try:
        print(f"Parsing PDF attachment {attachment_id} from email {email_id}", file=sys.stderr)
        attachment_data = await graph_client.download_attachment(email_id, attachment_id)
        if isinstance(attachment_data, dict) and "error" in attachment_data:
            return attachment_data
        return pdf_handler.parse_pdf(attachment_data)
    except Exception as e:
        print(f"Exception in parse_pdf_attachment: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def test_api_permissions():
    """Test API permissions to diagnose access issues."""
    try:
        print("Testing API permissions...", file=sys.stderr)
        results = await graph_client.test_permissions()
        print(f"API permission test results: {results}", file=sys.stderr)
        return results
    except Exception as e:
        print(f"Error testing API permissions: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def test_connection():
    """Test if the server is properly configured and connected."""
    try:
        print("Running test_connection tool", file=sys.stderr)
        credentials_status = all([
            os.environ.get("MICROSOFT_CLIENT_ID"),
            os.environ.get("MICROSOFT_CLIENT_SECRET"),
            os.environ.get("MICROSOFT_TENANT_ID"),
            os.environ.get("AUTHORITY")
        ])
        
        return {
            "server": "running",
            "credentials": "present" if credentials_status else "missing",
            "client_id_present": bool(os.environ.get("MICROSOFT_CLIENT_ID")),
            "client_secret_present": bool(os.environ.get("MICROSOFT_CLIENT_SECRET")),
            "tenant_id_present": bool(os.environ.get("MICROSOFT_TENANT_ID")),
            "authority_present": bool(os.environ.get("AUTHORITY")),
            "scope": os.environ.get("SCOPE", "Not set"),
            "user_email": os.environ.get("MS_GRAPH_USER_EMAIL", "Not set")
        }
    except Exception as e:
        print(f"Error in test_connection: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def debug_system():
    """Provide detailed debugging information about the system and configuration."""
    try:
        print("Running debug_system tool", file=sys.stderr)
        # System info
        system_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "hostname": socket.gethostname()
        }
        
        # Environment variables (redacted)
        env_vars = {
            "CLIENT_ID": bool(os.environ.get("MICROSOFT_CLIENT_ID")),
            "CLIENT_SECRET": bool(os.environ.get("MICROSOFT_CLIENT_SECRET")),
            "TENANT_ID": bool(os.environ.get("MICROSOFT_TENANT_ID")),
            "AUTHORITY": os.environ.get("AUTHORITY"),
            "SCOPE": os.environ.get("SCOPE"),
            "MS_GRAPH_USER_EMAIL": os.environ.get("MS_GRAPH_USER_EMAIL")
        }
        
        # Test token acquisition (safely)
        token_test = "Not tested"
        try:
            token = await graph_client._get_token()
            token_test = "Success - Token acquired" if token else "Failed - No token returned"
        except Exception as e:
            token_test = f"Error: {str(e)}"
        
        # List registered tools
        tools = [
            "list_emails", "get_email", "send_email", "get_attachments", 
            "download_attachment", "parse_pdf_attachment", "test_connection", 
            "debug_system", "test_api_permissions"
        ]
        
        return {
            "system_info": system_info,
            "environment_variables": env_vars,
            "token_test": token_test,
            "tools_registered": tools
        }
    except Exception as e:
        print(f"Error in debug_system: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def list_mail_folders():
    """List all mail folders in the user's mailbox.
    
    Returns:
        List of mail folders with their IDs and names
    """
    try:
        print("Listing mail folders", file=sys.stderr)
        return await graph_client.list_folders()
    except Exception as e:
        print(f"Exception in list_mail_folders: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def create_mail_folder(folder_name: str, parent_folder_id: str = None):
    """Create a new mail folder.
    
    Args:
        folder_name: Name of the folder to create
        parent_folder_id: Optional ID of parent folder to create this folder in
        
    Returns:
        Information about the created folder
    """
    try:
        print(f"Creating mail folder '{folder_name}'", file=sys.stderr)
        result = await graph_client.create_folder(folder_name, parent_folder_id)
        return result
    except Exception as e:
        print(f"Exception in create_mail_folder: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def move_email_to_folder(email_id: str, folder_id: str):
    """Move an email to a different folder.
    
    Args:
        email_id: ID of the email to move
        folder_id: ID of the destination folder
        
    Returns:
        Status of the move operation
    """
    try:
        print(f"Moving email {email_id} to folder {folder_id}", file=sys.stderr)
        result = await graph_client.move_email(email_id, folder_id)
        return result
    except Exception as e:
        print(f"Exception in move_email_to_folder: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def delete_mail_folder(folder_id: str):
    """Delete a mail folder.
    
    Args:
        folder_id: ID of the folder to delete
        
    Returns:
        Status of the delete operation
    """
    try:
        print(f"Deleting folder {folder_id}", file=sys.stderr)
        result = await graph_client.delete_folder(folder_id)
        return result
    except Exception as e:
        print(f"Exception in delete_mail_folder: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def rename_mail_folder(folder_id: str, new_name: str):
    """Rename a mail folder.
    
    Args:
        folder_id: ID of the folder to rename
        new_name: New name for the folder
        
    Returns:
        Updated folder information
    """
    try:
        print(f"Renaming folder {folder_id} to '{new_name}'", file=sys.stderr)
        result = await graph_client.rename_folder(folder_id, new_name)
        return result
    except Exception as e:
        print(f"Exception in rename_mail_folder: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

# Add a prompt to help the LLM understand how to use the email tools
@mcp.prompt()
def email_help() -> str:
    return """
    You have access to the following email capabilities:
    
    1. list_emails - Get a list of recent emails
    2. get_email - Get details of a specific email
    3. send_email - Send a new email
    4. get_attachments - List attachments for an email
    5. download_attachment - Download a specific attachment
    6. parse_pdf_attachment - Extract text from a PDF attachment
    7. test_connection - Test if the server is properly configured
    8. debug_system - Get detailed diagnostics about the system
    9. test_api_permissions - Test Microsoft Graph API permissions
    
    Mail Folder Management:
    10. list_mail_folders - List all available mail folders
    11. create_mail_folder - Create a new mail folder
    12. move_email_to_folder - Move an email to a different folder
    13. delete_mail_folder - Delete a mail folder
    14. rename_mail_folder - Rename a mail folder
    
    If you encounter issues, try running test_connection, debug_system, or test_api_permissions first to diagnose the problem.
    
    How can I help you with your emails today?
    """

# MCP server setup function to ensure proper tool registration
def register_all_tools():
    """Manually register all tools to ensure they're available."""
    tool_functions = [
        list_emails, get_email, send_email, get_attachments, 
        download_attachment, parse_pdf_attachment, test_connection, 
        debug_system, test_api_permissions,
        list_mail_folders, create_mail_folder, move_email_to_folder,
        delete_mail_folder, rename_mail_folder,
        list_email_categories, create_email_category, delete_email_category,
        assign_email_category, remove_email_category,
        archive_email,
        list_email_rules, create_email_rule, delete_email_rule, update_email_rule
    ]
    
    # Force-register all tools
    for func in tool_functions:
        name = func.__name__
        print(f"Ensuring {name} is registered", file=sys.stderr)
        if not hasattr(mcp, name):
            print(f"Manual registration for {name}", file=sys.stderr)
            mcp.tool()(func)

# Category management tools
@mcp.tool()
async def list_email_categories():
    """List all available email categories.
    
    Returns:
        List of email categories with their IDs, names, and colors
    """
    try:
        print("Listing email categories", file=sys.stderr)
        return await graph_client.list_categories()
    except Exception as e:
        print(f"Exception in list_email_categories: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def create_email_category(display_name: str, color: str = "preset0"):
    """Create a new email category.
    
    Args:
        display_name: Name of the category to create
        color: Color for the category (preset0 through preset24, or none)
        
    Returns:
        Information about the created category
    """
    try:
        print(f"Creating email category '{display_name}' with color '{color}'", file=sys.stderr)
        return await graph_client.create_category(display_name, color)
    except Exception as e:
        print(f"Exception in create_email_category: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def delete_email_category(category_id: str):
    """Delete an email category.
    
    Args:
        category_id: ID of the category to delete
        
    Returns:
        Status of the delete operation
    """
    try:
        print(f"Deleting email category {category_id}", file=sys.stderr)
        return await graph_client.delete_category(category_id)
    except Exception as e:
        print(f"Exception in delete_email_category: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def assign_email_category(email_id: str, category_names: list):
    """Assign one or more categories to an email.
    
    Args:
        email_id: ID of the email
        category_names: List of category names to assign
        
    Returns:
        Updated email information
    """
    try:
        print(f"Assigning categories {category_names} to email {email_id}", file=sys.stderr)
        return await graph_client.assign_category(email_id, category_names)
    except Exception as e:
        print(f"Exception in assign_email_category: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def remove_email_category(email_id: str, category_name: str):
    """Remove a category from an email.
    
    Args:
        email_id: ID of the email
        category_name: Name of the category to remove
        
    Returns:
        Updated email information
    """
    try:
        print(f"Removing category {category_name} from email {email_id}", file=sys.stderr)
        return await graph_client.remove_category(email_id, category_name)
    except Exception as e:
        print(f"Exception in remove_email_category: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

# Email archiving tool
@mcp.tool()
async def archive_email(email_id: str):
    """Archive an email by moving it to the Archive folder.
    
    Args:
        email_id: ID of the email to archive
        
    Returns:
        Status of the archive operation
    """
    try:
        print(f"Archiving email {email_id}", file=sys.stderr)
        return await graph_client.archive_email(email_id)
    except Exception as e:
        print(f"Exception in archive_email: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

# Rule management tools
@mcp.tool()
async def list_email_rules():
    """List all inbox rules.
    
    Returns:
        List of inbox rules with their conditions and actions
    """
    try:
        print("Listing email rules", file=sys.stderr)
        return await graph_client.list_rules()
    except Exception as e:
        print(f"Exception in list_email_rules: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def create_email_rule(display_name: str, conditions: dict, actions: dict, sequence: int = None, is_enabled: bool = True):
    """Create a new inbox rule.
    
    Args:
        display_name: Name of the rule
        conditions: Dictionary of conditions (subject contains, from contains, etc.)
        actions: Dictionary of actions (move to folder, mark as read, etc.)
        sequence: Order in which the rule should run (lower numbers run first)
        is_enabled: Whether the rule should be active
        
    Returns:
        Information about the created rule
    """
    try:
        print(f"Creating email rule '{display_name}'", file=sys.stderr)
        return await graph_client.create_rule(display_name, conditions, actions, sequence, is_enabled)
    except Exception as e:
        print(f"Exception in create_email_rule: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def delete_email_rule(rule_id: str):
    """Delete an inbox rule.
    
    Args:
        rule_id: ID of the rule to delete
        
    Returns:
        Status of the delete operation
    """
    try:
        print(f"Deleting email rule {rule_id}", file=sys.stderr)
        return await graph_client.delete_rule(rule_id)
    except Exception as e:
        print(f"Exception in delete_email_rule: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

@mcp.tool()
async def update_email_rule(rule_id: str, update_data: dict):
    """Update an existing inbox rule.
    
    Args:
        rule_id: ID of the rule to update
        update_data: Dictionary of properties to update
        
    Returns:
        Updated rule information
    """
    try:
        print(f"Updating email rule {rule_id}", file=sys.stderr)
        return await graph_client.update_rule(rule_id, update_data)
    except Exception as e:
        print(f"Exception in update_email_rule: {e}", file=sys.stderr)
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    # Ensure all tools are registered
    register_all_tools()
    
    # Run the MCP server using the built-in method
    print("Starting MCP server with the following tools:", file=sys.stderr)
    for tool_name in dir(mcp):
        if not tool_name.startswith('_'):
            print(f" - {tool_name}", file=sys.stderr)
            
    print("\nStarting server...", file=sys.stderr)
    mcp.run() 