#!/usr/bin/env python3
import os
import sys
import time
import json
import webbrowser
import msal
from flask import Flask, request, redirect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment variables
CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
AUTHORITY = os.getenv("AUTHORITY", f"https://login.microsoftonline.com/{TENANT_ID}")
REDIRECT_URI = "http://localhost:5000/auth/callback"

# Update scope to include all necessary permissions including rule management
SCOPE = [
    "Mail.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "MailboxSettings.Read",
    "MailboxSettings.ReadWrite",
    "User.Read"
]

# Comment out the .default scope
# SCOPE = [
#     "https://graph.microsoft.com/.default"
# ]

# Token file path - use absolute path to avoid path issues
token_filename = "graph_api_token.json"
current_dir = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(current_dir, token_filename)
print(f"Token will be saved to: {TOKEN_FILE}")

# Create Flask app for OAuth callback
app = Flask(__name__)

# Create MSAL app
msal_app = msal.ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)

def save_token(token_data):
    """Save token data to file"""
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)
    print(f"Token saved to {TOKEN_FILE}")
    return token_data

def load_token():
    """Load token data from file if available"""
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading token: {e}")
    return None

def is_token_valid(token_data):
    """Check if token is valid and not expired"""
    if not token_data:
        return False
    
    # Check if the token has an expiration time
    if "expires_at" not in token_data:
        return False
    
    # Check if the token is expired (with 5-minute buffer)
    if token_data["expires_at"] < time.time() + 300:
        return False
    
    return True

@app.route("/")
def login():
    """Initiate OAuth flow"""
    auth_url = msal_app.get_authorization_request_url(
        SCOPE,
        redirect_uri=REDIRECT_URI,
        state="12345"  # Use a random state value in production
    )
    return redirect(auth_url)

@app.route("/auth/callback")
def auth_callback():
    """Handle OAuth callback"""
    # Get authorization code from query parameters
    code = request.args.get("code")
    
    if not code:
        return "Error: No authorization code received", 400
    
    # Acquire token with authorization code
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )
    
    if "error" in result:
        return f"Error: {result.get('error')}: {result.get('error_description')}", 400
    
    # Add expiration time
    result["expires_at"] = time.time() + result.get("expires_in", 3600)
    
    # Save token
    save_token(result)
    
    return """
    <html>
        <body>
            <h1>Authentication Successful</h1>
            <p>You can now close this window and return to Claude Desktop.</p>
            <script>
                setTimeout(function() { window.close(); }, 3000);
            </script>
        </body>
    </html>
    """

def get_token_interactive():
    """Get token through interactive authentication"""
    # Check if we have a valid cached token
    token_data = load_token()
    
    if is_token_valid(token_data):
        print("Using cached token")
        return token_data
    
    # Start Flask server for OAuth callback
    print("Starting OAuth authentication flow...")
    print("Please log in with your Microsoft account in the browser window.")
    
    # Open browser to authentication URL
    webbrowser.open(f"http://localhost:5000/")
    
    # Run Flask app
    app.run(host="localhost", port=5000)
    
    # After authentication, load the token
    return load_token()

if __name__ == "__main__":
    # Get token
    token = get_token_interactive()
    
    if token:
        print("Authentication successful!")
        print(f"Token saved to {TOKEN_FILE}")
        print(f"Access token: {token.get('access_token')[:10]}...")
    else:
        print("Authentication failed!")
        sys.exit(1) 