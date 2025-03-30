#!/usr/bin/env python3
"""
Helper script to pass OAuth token to Claude Desktop.
This script loads the token from the specified file and displays it for easy copying.
"""

import os
import json
import time
import sys

# Use absolute path for token file to avoid path issues
token_filename = "graph_api_token.json"
current_dir = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(current_dir, token_filename)

def main():
    """Main function to check and display the token."""
    if not os.path.exists(TOKEN_FILE):
        print("Error: Token file not found.")
        print("Please run oauth_auth.py first to authenticate.")
        sys.exit(1)

    try:
        with open(TOKEN_FILE, "r") as f:
            token_data = json.load(f)
            
        # Check if token is valid
        if "expires_at" not in token_data or token_data["expires_at"] < time.time():
            print("Error: Token is expired.")
            print("Please run oauth_auth.py to get a new token.")
            sys.exit(1)
            
        # Display token for copying
        print("\n=== TOKEN INFORMATION ===")
        print(f"Valid until: {time.ctime(token_data['expires_at'])}")
        print("\n=== COPY THE TOKEN BELOW TO CLAUDE DESKTOP ===")
        print("\n" + token_data["access_token"] + "\n")
        print("=== END OF TOKEN ===\n")
        
        print("Instructions:")
        print("1. Copy the entire token above")
        print("2. In Claude Desktop, when asked for authentication, paste this token")
        print("3. This will allow Claude to access your emails through Microsoft Graph API")
        
    except Exception as e:
        print(f"Error reading token: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 