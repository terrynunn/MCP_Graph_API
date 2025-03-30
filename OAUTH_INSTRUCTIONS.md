# Microsoft Graph API OAuth Authentication

This guide explains how to authenticate with Microsoft Graph API using OAuth for delegated permissions.

## Overview

The authentication process works as follows:

1. You run `oauth_auth.py` to start the OAuth flow
2. A browser window opens for you to sign in with your Microsoft account
3. After successful authentication, the token is saved to `graph_api_token.json`
4. The MCP server uses this token for API requests
5. When you start Claude Desktop, you can provide the token when prompted

## Setup Instructions

### 1. Azure Portal Configuration

Before you begin, ensure your Azure AD application is properly configured:

1. Go to the [Azure Portal](https://portal.azure.com) > Azure Active Directory > App Registrations
2. Find your application (ID: d066e517-3692-4df9-836b-bb23a113aa74)
3. Under "Authentication":
   - Add a platform: Web
   - Add redirect URI: `http://localhost:5000/auth/callback`
   - Under "Implicit grant and hybrid flows", check "Access tokens"
   - Set "Allow public client flows" to YES
4. Under "API Permissions":
   - Add the following DELEGATED permissions (not Application):
     - Mail.Read
     - Mail.ReadBasic
     - Mail.ReadWrite
     - Mail.Send
     - User.Read
   - Click "Grant admin consent" for your organization

### 2. Running the Authentication Process

1. Run the batch file or authenticate directly:
   ```
   run_mcp_server.bat
   ```
   or
   ```
   python oauth_auth.py
   ```

2. A browser window will open. Sign in with your Microsoft account.
3. After successful authentication, you'll see a success message, and the token will be saved.

### 3. Starting Claude Desktop

1. After authentication is complete, run:
   ```
   python pass_token_to_claude.py
   ```

2. Copy the displayed token.

3. When Claude Desktop requests authentication for Microsoft Graph API, paste the token.

## Troubleshooting

If you encounter issues:

1. **Token Expired**: Run `oauth_auth.py` again to get a new token.
2. **Authentication Errors**: Check Azure portal settings, especially redirect URI and permissions.
3. **Permission Issues**: Ensure you've granted consent to all required permissions during OAuth flow.
4. **Token Not Found**: Make sure `oauth_auth.py` completed successfully before starting Claude Desktop.

## File Overview

- `oauth_auth.py`: Handles OAuth authentication and saves token to file
- `pass_token_to_claude.py`: Displays token for copying to Claude Desktop
- `graph_api_token.json`: Contains the access token (do not share this file)
- `graph_api.py`: Uses the token for Microsoft Graph API requests

## Security Notes

- The token file contains sensitive information. Do not share it.
- The token is valid for a limited time (usually 1 hour).
- When the token expires, you'll need to run `oauth_auth.py` again. 