@echo off 1>&2
echo ========== MCP Graph API Server Startup ========== 1>&2

REM Installing required packages
echo Installing required packages... 1>&2
echo ------------------------------- 1>&2
pip install msal requests aiohttp python-dotenv flask 1>&2
echo. 1>&2

REM Setting environment variables for Graph API credentials
echo Setting environment variables... 1>&2
echo -------------------------------- 1>&2

REM --- Graph API Credentials ---
set MICROSOFT_CLIENT_ID=d066e517-3692-4df9-836b-bb23a113aa74
set MICROSOFT_CLIENT_SECRET=g7Q8Q~19w32h6ojVKTqbks9fo3LJCDGsUHCHZbDj
set MICROSOFT_TENANT_ID=e5714482-2e34-4c7f-a8a8-afd742128ada
set MS_GRAPH_USER_EMAIL=terrynunn@unitywl.com
set AUTHORITY=https://login.microsoftonline.com/e5714482-2e34-4c7f-a8a8-afd742128ada
set SCOPE=https://graph.microsoft.com/.default

REM Output environment variables to verify they are set correctly
echo Environment variables set: 1>&2
echo MICROSOFT_CLIENT_ID=%MICROSOFT_CLIENT_ID% 1>&2
echo MICROSOFT_CLIENT_SECRET=[REDACTED] 1>&2
echo MICROSOFT_TENANT_ID=%MICROSOFT_TENANT_ID% 1>&2
echo MS_GRAPH_USER_EMAIL=%MS_GRAPH_USER_EMAIL% 1>&2
echo AUTHORITY=%AUTHORITY% 1>&2
echo SCOPE=%SCOPE% 1>&2
echo. 1>&2

REM Display API URL and permissions needed
echo. 1>&2
echo Graph API URL: https://graph.microsoft.com/v1.0 1>&2
echo. 1>&2

echo Required DELEGATED Permissions: 1>&2
echo ----------------------------- 1>&2
echo 1. Mail.Read - Read user mail 1>&2
echo 2. Mail.ReadBasic - Read basic mail properties 1>&2
echo 3. Mail.ReadWrite - Read and write access to user mail 1>&2
echo 4. Mail.Send - Send mail as a user 1>&2
echo 5. User.Read - Read user profile 1>&2
echo. 1>&2

echo IMPORTANT Azure AD Settings: 1>&2
echo ----------------------------- 1>&2
echo 1. In Azure Portal → App Registrations → Find app with ID %MICROSOFT_CLIENT_ID% 1>&2
echo 2. Under Authentication → Allow public client flows: Set to YES 1>&2
echo 3. Under Authentication → Add Platform → Web → Redirect URI: http://localhost:5000/auth/callback 1>&2
echo 4. Under API Permissions → Add DELEGATED permissions (not Application) 1>&2
echo. 1>&2

echo ========== OAuth Authentication ========== 1>&2
echo First, we need to authenticate with Microsoft Graph API 1>&2
echo A browser window will open for you to sign in. 1>&2
echo. 1>&2

REM Check if token file exists
IF NOT EXIST "graph_api_token.json" (
    echo No token file found, starting OAuth authentication... 1>&2
    python oauth_auth.py
) ELSE (
    echo Token file found! Checking if it's valid... 1>&2
    python -c "import json, time, sys; f=open('graph_api_token.json'); data=json.load(f); f.close(); sys.exit(0 if data.get('expires_at',0) > time.time() else 1)"
    IF %ERRORLEVEL% NEQ 0 (
        echo Token is expired, starting OAuth authentication... 1>&2
        python oauth_auth.py
    ) ELSE (
        echo Token is valid, proceeding with server startup. 1>&2
    )
)

echo. 1>&2
echo ========== Starting MCP Server ========== 1>&2
echo Running main.py with enhanced debugging... 1>&2
echo Server logs will appear below: 1>&2
echo. 1>&2

REM Run the full MCP server with logging
C:\Python311\python.exe C:\Users\nunnt\OneDrive\Desktop\MCP_Graph_API\main.py 