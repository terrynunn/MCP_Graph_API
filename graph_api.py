import os
import base64
import json
import tempfile
from pathlib import Path
import httpx
import msal
from dotenv import load_dotenv
import sys
import time

class GraphAPIClient:
    """Client for interacting with Microsoft Graph API."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get credentials from environment variables
        self.client_id = os.getenv("MICROSOFT_CLIENT_ID")
        self.client_secret = os.getenv("MICROSOFT_CLIENT_SECRET")
        self.tenant_id = os.getenv("MICROSOFT_TENANT_ID")
        self.authority = os.getenv("AUTHORITY", f"https://login.microsoftonline.com/{self.tenant_id}")
        
        # Handle space-separated scopes
        scope = os.getenv("SCOPE", "https://graph.microsoft.com/.default")
        self.scope = scope.split() if ' ' in scope else [scope]
        self.user_email = os.getenv("MS_GRAPH_USER_EMAIL")
        
        # Token file path - use absolute path to avoid path issues
        token_filename = "graph_api_token.json"
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.token_file = os.path.join(current_dir, token_filename)
        print(f"Token file path: {self.token_file}", file=sys.stderr)
        
        # Set base URL for Graph API
        self.base_url = "https://graph.microsoft.com/v1.0"
        
        # Track token status
        self._token = None
        self._token_expiry = 0
        
        # Log environment variable status
        print(f"MS_GRAPH_USER_EMAIL: {'Set' if self.user_email else 'Not set'}", file=sys.stderr)
        print(f"TENANT_ID: {'Set' if self.tenant_id else 'Not set'}", file=sys.stderr)
        print(f"CLIENT_ID: {'Set' if self.client_id else 'Not set'}", file=sys.stderr)
        print(f"CLIENT_SECRET: {'Set (value hidden)' if self.client_secret else 'Not set'}", file=sys.stderr)
        print(f"SCOPE: {self.scope}", file=sys.stderr)
        
        # Initialize MSAL app
        try:
            self.app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,
                client_credential=self.client_secret
            )
            print("MSAL app initialized successfully", file=sys.stderr)
            
            # Try to load token from file on startup
            self._load_token_from_file()
        except Exception as e:
            print(f"Error initializing MSAL app: {e}", file=sys.stderr)
            self.app = None
    
    def _load_token_from_file(self):
        """Load OAuth token from file if available"""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, "r") as f:
                    token_data = json.load(f)
                
                # Check if token is valid
                if "expires_at" in token_data and token_data["expires_at"] > time.time():
                    self._token = token_data["access_token"]
                    self._token_expiry = token_data["expires_at"]
                    print(f"Token loaded from file, valid until {time.ctime(self._token_expiry)}", file=sys.stderr)
                    return True
                else:
                    print("Token in file is expired", file=sys.stderr)
            else:
                print(f"Token file {self.token_file} not found", file=sys.stderr)
        except Exception as e:
            print(f"Error loading token from file: {e}", file=sys.stderr)
        
        return False
            
    async def _get_token(self):
        """
        Acquire an access token for the Graph API using delegated permissions.
        For delegated flow, we use OAuth token stored in file.
        """
        # Return cached token if still valid
        if self._token and self._token_expiry > time.time():
            print("Using cached token", file=sys.stderr)
            return self._token

        # Try to load token from file (in case it was refreshed externally)
        if self._load_token_from_file():
            return self._token
            
        # If we still don't have a valid token, we need to ask user to run the OAuth flow
        print("No valid token found. Please run oauth_auth.py to get a new token.", file=sys.stderr)
        print("Command: python oauth_auth.py", file=sys.stderr)
        
        # Check token file every 2 seconds for 60 seconds (30 attempts)
        for attempt in range(30):
            print(f"Waiting for token... attempt {attempt+1}/30", file=sys.stderr)
            time.sleep(2)
            
            if self._load_token_from_file():
                return self._token
        
        print("Timed out waiting for token. Please run oauth_auth.py and try again.", file=sys.stderr)
        return None
    
    async def _make_request(self, method, endpoint, params=None, data=None, headers=None):
        """Make a request to the Graph API."""
        try:
            token = await self._get_token()
            if not token:
                return {"error": "No valid token available. Please run oauth_auth.py to authenticate.", "status": "failed"}
                
            url = f"{self.base_url}/{endpoint}"
            
            headers = headers or {}
            headers.update({
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            })
            
            print(f"Making {method} request to {url}", file=sys.stderr)
            print(f"Request params: {params}", file=sys.stderr)
            
            async with httpx.AsyncClient() as client:
                if method.lower() == "get":
                    response = await client.get(url, params=params, headers=headers)
                elif method.lower() == "post":
                    response = await client.post(url, params=params, json=data, headers=headers)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                if response.status_code >= 400:
                    error_detail = f"Status: {response.status_code}, Response: {response.text}"
                    print(f"Error in Graph API request: {error_detail}", file=sys.stderr)
                    return {"error": error_detail, "status": "failed", "status_code": response.status_code}
                
                try:
                    return response.json()
                except:
                    # If not JSON, return text
                    return {"content": response.text, "status": "success"}
        except Exception as e:
            print(f"Error making request: {e}", file=sys.stderr)
            raise
    
    async def test_permissions(self):
        """Test the API permissions to verify what actions are allowed."""
        results = {
            "token_acquisition": "not_tested",
            "permissions_tested": [],
            "available_endpoints": [],
            "auth_type": "delegated"  # Using delegated permissions now
        }
        
        # Test token acquisition first
        try:
            print("Testing token acquisition...", file=sys.stderr)
            
            # Check if token file exists
            if not os.path.exists(self.token_file):
                results["token_acquisition"] = "failed: Token file not found"
                results["recommended_fix"] = "Run oauth_auth.py to authenticate using OAuth"
                return results
                
            # Try to load token from file
            with open(self.token_file, "r") as f:
                token_data = json.load(f)
                
            # Check if token is expired
            if "expires_at" in token_data and token_data["expires_at"] < time.time():
                results["token_acquisition"] = "failed: Token is expired"
                results["recommended_fix"] = "Run oauth_auth.py to get a new token"
                return results  # If we can't get a token, no point testing further
                
            # If we get here, we should have a valid token
            token = await self._get_token()
            if token:
                results["token_acquisition"] = "success"
            else:
                results["token_acquisition"] = "failed: Could not acquire token"
                results["recommended_fix"] = "Run oauth_auth.py to authenticate"
                return results  # If we can't get a token, no point testing further
        except Exception as e:
            results["token_acquisition"] = f"error: {str(e)}"
            results["recommended_fix"] = "Check the error and run oauth_auth.py to authenticate"
            return results  # If we can't get a token, no point testing further
            
        # Test API permissions specifically for mail access with delegated permissions
        try:
            # For delegated permissions, we'll use both /me and specific user endpoints
            endpoints_to_test = []
            
            # /me endpoints should work with delegated permissions
            endpoints_to_test.extend([
                {
                    "endpoint": "me",
                    "description": "Current user profile access",
                    "required_for": "basic user information",
                    "required_permission": "User.Read"
                },
                {
                    "endpoint": "me/messages?$top=1",
                    "description": "Current user messages access",
                    "required_for": "reading emails",
                    "required_permission": "Mail.Read"
                },
                {
                    "endpoint": "me/mailFolders/inbox/messages?$top=1",
                    "description": "Current user mailbox folders access",
                    "required_for": "accessing mail folders",
                    "required_permission": "Mail.ReadBasic"
                }
            ])
            
            # If we have a specific user email, test those endpoints too
            if self.user_email:
                results["user_email"] = self.user_email
                
                # Add user-specific endpoints
                endpoints_to_test.extend([
                    {
                        "endpoint": f"users/{self.user_email}",
                        "description": "Specific user profile access",
                        "required_for": "basic user information",
                        "required_permission": "User.Read.All"
                    },
                    {
                        "endpoint": f"users/{self.user_email}/messages?$top=1",
                        "description": "Specific user messages access",
                        "required_for": "reading specific user emails",
                        "required_permission": "Mail.Read.All"
                    },
                    {
                        "endpoint": f"users/{self.user_email}/mailFolders/inbox/messages?$top=1",
                        "description": "Specific user mailbox folders access",
                        "required_for": "accessing specific user mail folders",
                        "required_permission": "Mail.ReadBasic.All"
                    }
                ])
            else:
                results["user_email"] = "not set (but not required for /me endpoints)"
            
            for endpoint_test in endpoints_to_test:
                endpoint = endpoint_test["endpoint"]
                print(f"Testing access to: {endpoint}", file=sys.stderr)
                
                response = await self._make_request("GET", endpoint)
                
                endpoint_result = {
                    "endpoint": endpoint,
                    "description": endpoint_test["description"],
                    "required_for": endpoint_test["required_for"],
                    "required_permission": endpoint_test["required_permission"],
                    "status": "success" if "error" not in response else "failed"
                }
                
                if "error" in response:
                    endpoint_result["error"] = response["error"]
                    print(f"Access denied to {endpoint}: {response['error']}", file=sys.stderr)
                else:
                    print(f"Successfully accessed {endpoint}", file=sys.stderr)
                    
                results["permissions_tested"].append(endpoint_result)
                
                if endpoint_result["status"] == "success":
                    results["available_endpoints"].append(endpoint)
            
            # Provide recommendations based on test results
            if not any(r["status"] == "success" for r in results["permissions_tested"]):
                results["overall_status"] = "failed"
                results["recommended_fix"] = """
                1. Run oauth_auth.py to authenticate with all required permissions
                2. Ensure you've consented to all required permissions during OAuth flow
                3. Check that your Azure AD app is configured with proper redirect URI
                """
            else:
                success_count = sum(1 for r in results["permissions_tested"] if r["status"] == "success")
                total_count = len(results["permissions_tested"])
                
                if success_count == total_count:
                    results["overall_status"] = "success"
                elif success_count > 0:
                    results["overall_status"] = "partial"
                    results["recommended_fix"] = """
                    Some permissions are working, but not all. You can:
                    1. Use only the endpoints that work (/me endpoints)
                    2. Run oauth_auth.py again and ensure you consent to all permissions
                    """
                
        except Exception as e:
            results["error"] = str(e)
            print(f"Error testing permissions: {e}", file=sys.stderr)
            
        return results
    
    async def list_emails(self, limit=10, filter_query=None):
        """List recent emails from the inbox."""
        try:
            # Try multiple approaches to fetch emails with focus on user-specific endpoints
            methods_to_try = []
            
            # Method 1: Use specific user endpoint if available (preferred approach)
            if self.user_email:
                methods_to_try.append({
                    "endpoint": f"users/{self.user_email}/messages",
                    "description": f"Specific user endpoint: {self.user_email}"
                })
                
                # Also try the mailbox approach for the specific user
                methods_to_try.append({
                    "endpoint": f"users/{self.user_email}/mailFolders/inbox/messages",
                    "description": f"User mailbox inbox folder: {self.user_email}"
                })
            
            # Only try /me endpoints as a last resort since they require different permissions
            methods_to_try.append({
                "endpoint": "me/messages",
                "description": "Standard /me/messages endpoint"
            })
            
            methods_to_try.append({
                "endpoint": "me/mailFolders/inbox/messages",
                "description": "Mailbox inbox folder"
            })
            
            for method in methods_to_try:
                endpoint = method["endpoint"]
                print(f"Trying to list emails with method: {method['description']}", file=sys.stderr)
                
                params = {
                    "$top": limit,
                    "$orderby": "receivedDateTime DESC",
                    "$select": "id,subject,receivedDateTime,from,bodyPreview"
                }
                
                if filter_query:
                    # Convert the user-friendly filter to Microsoft Graph API format
                    # Example: 'subject:contains "test"' becomes 'contains(subject, "test")'
                    filter_parts = []
                    
                    # Split by OR/AND, preserving the operators
                    parts = filter_query.split(" OR ")
                    for part in parts:
                        subparts = part.split(" AND ")
                        processed_subparts = []
                        
                        for subpart in subparts:
                            if "subject:contains" in subpart:
                                # Extract the search term
                                search_term = subpart.split('"')[1]
                                processed_subparts.append(f"contains(subject, '{search_term}')")
                            elif "received:gt" in subpart:
                                # Handle date filtering
                                date = subpart.split("received:gt ")[1].strip()
                                processed_subparts.append(f"receivedDateTime gt {date}")
                            else:
                                # Pass through other filters as-is
                                processed_subparts.append(subpart)
                        
                        filter_parts.append("(" + " and ".join(processed_subparts) + ")")
                    
                    # Join all parts with OR
                    params["$filter"] = " or ".join(filter_parts)
                    print(f"Converted filter query: {params['$filter']}", file=sys.stderr)
                    
                response = await self._make_request("GET", endpoint, params=params)
                
                # Check if this method worked
                if "error" not in response:
                    print(f"Successfully listed emails with method: {method['description']}", file=sys.stderr)
                    return response.get("value", [])
                else:
                    print(f"Failed to list emails with method: {method['description']} - {response.get('error')}", file=sys.stderr)
            
            # If we got here, all methods failed
            return {
                "error": "All methods to list emails failed. Check API permissions and credentials.",
                "status": "failed",
                "methods_tried": [m["description"] for m in methods_to_try]
            }
        except Exception as e:
            print(f"Error listing emails: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def get_email(self, email_id):
        """Get a specific email by ID."""
        try:
            # Use specific user endpoint when available
            if self.user_email:
                endpoint = f"users/{self.user_email}/messages/{email_id}"
            else:
                endpoint = f"me/messages/{email_id}"
                
            params = {
                "$select": "id,subject,receivedDateTime,from,toRecipients,ccRecipients,body,hasAttachments"
            }
            
            return await self._make_request("GET", endpoint, params=params)
        except Exception as e:
            print(f"Error getting email: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def get_attachments(self, email_id):
        """Get attachments for a specific email."""
        try:
            # Use specific user endpoint when available
            if self.user_email:
                endpoint = f"users/{self.user_email}/messages/{email_id}/attachments"
            else:
                endpoint = f"me/messages/{email_id}/attachments"
                
            params = {
                "$select": "id,name,contentType,size"
            }
            
            response = await self._make_request("GET", endpoint, params=params)
            return response.get("value", [])
        except Exception as e:
            print(f"Error getting attachments: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def download_attachment(self, email_id, attachment_id, save_path=None):
        """Download a specific attachment."""
        try:
            # Use specific user endpoint when available
            if self.user_email:
                endpoint = f"users/{self.user_email}/messages/{email_id}/attachments/{attachment_id}"
            else:
                endpoint = f"me/messages/{email_id}/attachments/{attachment_id}"
                
            response = await self._make_request("GET", endpoint)
            
            if "error" in response:
                return response
                
            # Extract content from response
            content_bytes = base64.b64decode(response.get("contentBytes", ""))
            
            if save_path:
                # Save to specified path
                path = Path(save_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content_bytes)
                return str(path)
            else:
                # Return content directly
                return content_bytes
        except Exception as e:
            print(f"Error downloading attachment: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def send_email(self, recipients, subject, body, attachments=None):
        """Send an email."""
        try:
            # Use specific user endpoint when available
            if self.user_email:
                endpoint = f"users/{self.user_email}/sendMail"
            else:
                endpoint = "me/sendMail"
            
            # Prepare message data
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML",
                        "content": body
                    },
                    "toRecipients": [{"emailAddress": {"address": email}} for email in recipients]
                }
            }
            
            # Add attachments if provided
            if attachments:
                message["message"]["attachments"] = []
                for attachment in attachments:
                    # Handle file paths or binary data
                    if isinstance(attachment, str) and Path(attachment).exists():
                        path = Path(attachment)
                        content = base64.b64encode(path.read_bytes()).decode()
                        attachment_item = {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": path.name,
                            "contentBytes": content
                        }
                        message["message"]["attachments"].append(attachment_item)
                    elif isinstance(attachment, dict) and "name" in attachment and "content" in attachment:
                        content = base64.b64encode(attachment["content"]).decode() if isinstance(attachment["content"], bytes) else attachment["content"]
                        attachment_item = {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": attachment["name"],
                            "contentBytes": content
                        }
                        message["message"]["attachments"].append(attachment_item)
            
            # Send the email
            response = await self._make_request("POST", endpoint, data=message)
            if "error" in response:
                return response
            return {"status": "sent", "recipients": recipients, "subject": subject}
        except Exception as e:
            print(f"Error sending email: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def list_folders(self):
        """List available mail folders."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders"
            else:
                endpoint = "me/mailFolders"
            
            params = {
                "$select": "id,displayName,childFolderCount,totalItemCount",
                "$top": 100
            }
            
            response = await self._make_request("GET", endpoint, params=params)
            return response.get("value", [])
        except Exception as e:
            print(f"Error listing folders: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
        
    async def create_folder(self, folder_name, parent_folder_id=None):
        """Create a new mail folder."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders"
                if parent_folder_id:
                    endpoint = f"users/{self.user_email}/mailFolders/{parent_folder_id}/childFolders"
            else:
                endpoint = "me/mailFolders"
                if parent_folder_id:
                    endpoint = f"me/mailFolders/{parent_folder_id}/childFolders"
            
            data = {
                "displayName": folder_name
            }
            
            response = await self._make_request("POST", endpoint, data=data)
            return response
        except Exception as e:
            print(f"Error creating folder: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
        
    async def move_email(self, email_id, destination_folder_id):
        """Move an email to another folder."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/messages/{email_id}/move"
            else:
                endpoint = f"me/messages/{email_id}/move"
            
            data = {
                "destinationId": destination_folder_id
            }
            
            response = await self._make_request("POST", endpoint, data=data)
            return response
        except Exception as e:
            print(f"Error moving email: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
        
    async def delete_folder(self, folder_id):
        """Delete a mail folder."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders/{folder_id}"
            else:
                endpoint = f"me/mailFolders/{folder_id}"
            
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient() as client:
                response = await client.delete(f"{self.base_url}/{endpoint}", 
                                             headers={"Authorization": f"Bearer {await self._get_token()}", **headers})
                
                if response.status_code >= 400:
                    return {"error": f"Status: {response.status_code}, Response: {response.text}", 
                            "status": "failed", "status_code": response.status_code}
                
                return {"status": "success", "message": "Folder deleted successfully"}
        except Exception as e:
            print(f"Error deleting folder: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
        
    async def rename_folder(self, folder_id, new_name):
        """Rename a mail folder."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders/{folder_id}"
            else:
                endpoint = f"me/mailFolders/{folder_id}"
            
            data = {
                "displayName": new_name
            }
            
            # PATCH request
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient() as client:
                response = await client.patch(f"{self.base_url}/{endpoint}", 
                                           json=data,
                                           headers={"Authorization": f"Bearer {await self._get_token()}", **headers})
                
                if response.status_code >= 400:
                    return {"error": f"Status: {response.status_code}, Response: {response.text}", 
                            "status": "failed", "status_code": response.status_code}
                
                return response.json()
        except Exception as e:
            print(f"Error renaming folder: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def list_categories(self):
        """List available email categories."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/outlook/masterCategories"
            else:
                endpoint = "me/outlook/masterCategories"
            
            response = await self._make_request("GET", endpoint)
            return response.get("value", [])
        except Exception as e:
            print(f"Error listing categories: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def create_category(self, display_name, color="preset0"):
        """Create a new email category.
        
        Available colors: none, preset0, preset1, preset2, ... preset24
        """
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/outlook/masterCategories"
            else:
                endpoint = "me/outlook/masterCategories"
            
            data = {
                "displayName": display_name,
                "color": color
            }
            
            response = await self._make_request("POST", endpoint, data=data)
            return response
        except Exception as e:
            print(f"Error creating category: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def delete_category(self, category_id):
        """Delete an email category."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/outlook/masterCategories/{category_id}"
            else:
                endpoint = f"me/outlook/masterCategories/{category_id}"
            
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/{endpoint}",
                    headers={"Authorization": f"Bearer {await self._get_token()}", **headers}
                )
                
                if response.status_code >= 400:
                    return {
                        "error": f"Status: {response.status_code}, Response: {response.text}", 
                        "status": "failed", 
                        "status_code": response.status_code
                    }
                
                return {"status": "success", "message": "Category deleted successfully"}
        except Exception as e:
            print(f"Error deleting category: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def assign_category(self, email_id, category_names):
        """Assign one or more categories to an email."""
        try:
            if not isinstance(category_names, list):
                category_names = [category_names]
            
            if self.user_email:
                endpoint = f"users/{self.user_email}/messages/{email_id}"
            else:
                endpoint = f"me/messages/{email_id}"
            
            data = {
                "categories": category_names
            }
            
            # Use PATCH to update only the categories field
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/{endpoint}",
                    json=data,
                    headers={"Authorization": f"Bearer {await self._get_token()}", **headers}
                )
                
                if response.status_code >= 400:
                    return {
                        "error": f"Status: {response.status_code}, Response: {response.text}", 
                        "status": "failed", 
                        "status_code": response.status_code
                    }
                
                return response.json()
        except Exception as e:
            print(f"Error assigning category: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def remove_category(self, email_id, category_name):
        """Remove a category from an email."""
        try:
            # First get current categories
            if self.user_email:
                endpoint = f"users/{self.user_email}/messages/{email_id}"
            else:
                endpoint = f"me/messages/{email_id}"
            
            params = {"$select": "id,categories"}
            
            message = await self._make_request("GET", endpoint, params=params)
            if "error" in message:
                return message
            
            current_categories = message.get("categories", [])
            new_categories = [cat for cat in current_categories if cat != category_name]
            
            # Update with new category list
            data = {
                "categories": new_categories
            }
            
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/{endpoint}",
                    json=data,
                    headers={"Authorization": f"Bearer {await self._get_token()}", **headers}
                )
                
                if response.status_code >= 400:
                    return {
                        "error": f"Status: {response.status_code}, Response: {response.text}", 
                        "status": "failed", 
                        "status_code": response.status_code
                    }
                
                return response.json()
        except Exception as e:
            print(f"Error removing category: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def archive_email(self, email_id):
        """Move an email to the Archive folder.
        
        This method first finds the Archive folder ID and then moves the email there.
        """
        try:
            # First find the Archive folder
            if self.user_email:
                folders_endpoint = f"users/{self.user_email}/mailFolders"
            else:
                folders_endpoint = "me/mailFolders"
            
            folders = await self._make_request("GET", folders_endpoint)
            if "error" in folders:
                return folders
            
            archive_folder = None
            for folder in folders.get("value", []):
                if folder.get("displayName") == "Archive":
                    archive_folder = folder
                    break
            
            # If Archive folder doesn't exist, create it
            if not archive_folder:
                if self.user_email:
                    create_endpoint = f"users/{self.user_email}/mailFolders"
                else:
                    create_endpoint = "me/mailFolders"
                
                data = {"displayName": "Archive"}
                archive_folder = await self._make_request("POST", create_endpoint, data=data)
                if "error" in archive_folder:
                    return archive_folder
            
            # Now move the email to the Archive folder
            return await self.move_email(email_id, archive_folder["id"])
        except Exception as e:
            print(f"Error archiving email: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def list_rules(self):
        """List inbox rules."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders/inbox/messageRules"
            else:
                endpoint = "me/mailFolders/inbox/messageRules"
            
            response = await self._make_request("GET", endpoint)
            return response.get("value", [])
        except Exception as e:
            print(f"Error listing rules: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def create_rule(self, display_name, conditions, actions, sequence=None, is_enabled=True):
        """Create a new inbox rule.
        
        Args:
            display_name: Name of the rule
            conditions: Dictionary of conditions (see Microsoft Graph API docs)
            actions: Dictionary of actions (see Microsoft Graph API docs)
            sequence: Order in which the rule should run (lower numbers run first)
            is_enabled: Whether the rule should be active
        """
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders/inbox/messageRules"
            else:
                endpoint = "me/mailFolders/inbox/messageRules"
            
            data = {
                "displayName": display_name,
                "conditions": conditions,
                "actions": actions,
                "isEnabled": is_enabled
            }
            
            if sequence is not None:
                data["sequence"] = sequence
            
            response = await self._make_request("POST", endpoint, data=data)
            return response
        except Exception as e:
            print(f"Error creating rule: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def delete_rule(self, rule_id):
        """Delete an inbox rule."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders/inbox/messageRules/{rule_id}"
            else:
                endpoint = f"me/mailFolders/inbox/messageRules/{rule_id}"
            
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/{endpoint}",
                    headers={"Authorization": f"Bearer {await self._get_token()}", **headers}
                )
                
                if response.status_code >= 400:
                    return {
                        "error": f"Status: {response.status_code}, Response: {response.text}", 
                        "status": "failed", 
                        "status_code": response.status_code
                    }
                
                return {"status": "success", "message": "Rule deleted successfully"}
        except Exception as e:
            print(f"Error deleting rule: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"}
    
    async def update_rule(self, rule_id, update_data):
        """Update an existing inbox rule."""
        try:
            if self.user_email:
                endpoint = f"users/{self.user_email}/mailFolders/inbox/messageRules/{rule_id}"
            else:
                endpoint = f"me/mailFolders/inbox/messageRules/{rule_id}"
            
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/{endpoint}",
                    json=update_data,
                    headers={"Authorization": f"Bearer {await self._get_token()}", **headers}
                )
                
                if response.status_code >= 400:
                    return {
                        "error": f"Status: {response.status_code}, Response: {response.text}", 
                        "status": "failed", 
                        "status_code": response.status_code
                    }
                
                return response.json()
        except Exception as e:
            print(f"Error updating rule: {e}", file=sys.stderr)
            return {"error": str(e), "status": "failed"} 