#!/usr/bin/env python3
"""
Example usage of the MCP Graph API server.
This file demonstrates how to use the API from a Claude MCP client.
"""

import json

# Example MCP call for listing recent emails
list_emails_call = {
    "name": "list_emails",
    "parameters": {
        "limit": 5
    }
}

# Example MCP call for getting email details
get_email_call = {
    "name": "get_email",
    "parameters": {
        "email_id": "AAMkADg0NDNjNzM3LWZiMTAtNGIzYS1iZDYwLTZiMjE3MzA2MTI5MgBGAAAAAAD7E_PeBSxpR5_cJ5UMJ27sBwB-0iGgM9JeRZ9Aml2tM8UGAAAAANOQAAB-0iGgM9JeRZ9Aml2tM8UGAAAAAPKQAAA="
    }
}

# Example MCP call for sending an email
send_email_call = {
    "name": "send_email",
    "parameters": {
        "recipients": ["recipient@example.com"],
        "subject": "Test Email from MCP Graph API",
        "body": "<h1>Hello from MCP Graph API</h1><p>This is a test email sent via Microsoft Graph API.</p>"
    }
}

# Example MCP call for listing attachments
get_attachments_call = {
    "name": "get_attachments",
    "parameters": {
        "email_id": "AAMkADg0NDNjNzM3LWZiMTAtNGIzYS1iZDYwLTZiMjE3MzA2MTI5MgBGAAAAAAD7E_PeBSxpR5_cJ5UMJ27sBwB-0iGgM9JeRZ9Aml2tM8UGAAAAANOQAAB-0iGgM9JeRZ9Aml2tM8UGAAAAAPKQAAA="
    }
}

# Example MCP call for parsing a PDF attachment
parse_pdf_attachment_call = {
    "name": "parse_pdf_attachment",
    "parameters": {
        "email_id": "AAMkADg0NDNjNzM3LWZiMTAtNGIzYS1iZDYwLTZiMjE3MzA2MTI5MgBGAAAAAAD7E_PeBSxpR5_cJ5UMJ27sBwB-0iGgM9JeRZ9Aml2tM8UGAAAAANOQAAB-0iGgM9JeRZ9Aml2tM8UGAAAAAPKQAAA=",
        "attachment_id": "AAMkADg0NDNjNzM3LWZiMTAtNGIzYS1iZDYwLTZiMjE3MzA2MTI5MgBGAAAAAAD7E_PeBSxpR5_cJ5UMJ27sBwB-0iGgM9JeRZ9Aml2tM8UGAAAAANOQAAB-0iGgM9JeRZ9Aml2tM8UGAAAAAPKQAAABEIAAAA="
    }
}

# Example Claude prompt for using the MCP
claude_prompt = """
You have access to Microsoft Graph API through MCP tools to help me manage my emails.

Please check my recent emails and summarize any important messages I've received in the past day.
If there are any emails with PDF attachments, please analyze the content of those PDFs and provide a brief summary.

After that, help me draft a response to the most important email.
"""

print("Example MCP calls for Claude:")
print(json.dumps(list_emails_call, indent=2))
print(json.dumps(get_email_call, indent=2))
print(json.dumps(send_email_call, indent=2))
print(json.dumps(get_attachments_call, indent=2))
print(json.dumps(parse_pdf_attachment_call, indent=2))
print("\nExample Claude prompt:")
print(claude_prompt) 