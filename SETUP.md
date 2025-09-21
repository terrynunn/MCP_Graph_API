# Setting Up MCP Graph API

This guide provides detailed instructions for setting up the MCP Graph API server to work with Microsoft Graph API and Claude.

## Prerequisites

1. Python 3.9 or higher
2. uv package manager
3. Microsoft Azure account with admin privileges
4. Claude Desktop with MCP support

## Step 1: Azure App Registration

1. Sign in to the [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations" > "New registration"
3. Name your application (e.g., "MCP Graph API")
4. Set the redirect URI to `http://localhost:5000/auth/callback` (for local development)
5. Click "Register"

### Configure API Permissions

1. In your registered app, go to "API permissions"
2. Click "Add a permission" > "Microsoft Graph" > "Application permissions"
3. Add the following permissions:
   - Mail.Read
   - Mail.ReadBasic
   - Mail.ReadBasic.All
   - Mail.ReadWrite
   - Mail.Send
   - User.Read
   - User.ReadBasic.All
4. Click "Grant admin consent for [your tenant]"

### Create a Client Secret

1. Go to "Certificates & secrets" > "New client secret"
2. Add a description and set an expiration
3. Copy the generated secret value (you'll only see it once)

## Step 2: Project Setup

1. Clone this repository:
```bash
git clone https://github.com/yourusername/mcp-graph-api.git
cd mcp-graph-api
```

2. Set up Python environment with uv:
```bash
uv venv
# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Create a `.env` file based on the template:
```bash
cp .env.example .env
```

5. Edit the `.env` file with your Azure app details:
```
CLIENT_ID=your_client_id_from_azure
CLIENT_SECRET=your_client_secret_from_azure
TENANT_ID=your_tenant_id
AUTHORITY=https://login.microsoftonline.com/your_tenant_id
SCOPE=https://graph.microsoft.com/.default
```

## Step 3: Running the MCP Server

1. Start the server:
```bash
python main.py
```

2. You should see output like:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Step 4: Connecting to Claude

1. Start Claude Desktop
2. Open the Claude settings and navigate to Claude Developer
3. Add a new MCP Server with:
   - Name: MCP Graph API
   - URL: http://localhost:8000
   - Description: Microsoft Graph API integration for email management
4. Save the settings and restart Claude
5. In a new conversation, you can now use prompts like the example in `example.py`

## Testing

1. Run the example file to see MCP call formats:
```bash
python example.py
```

2. Test each endpoint manually:
   - List emails
   - Get email details
   - Check attachments
   - Parse PDF attachments
   - Send test emails

## Troubleshooting

### Authentication Issues

- Verify your Client ID and Secret in the `.env` file
- Check that API permissions are granted correctly
- Ensure admin consent is granted for the necessary permissions

### Email Access Issues

- Confirm the user account has mailboxes accessible via Graph API
- Verify permission scopes include Mail.Read and Mail.Send

### PDF Parsing Issues

- Ensure PyPDF2 is installed correctly
- Test with a simple PDF file
- Check for encoding or corruption issues in the PDF 