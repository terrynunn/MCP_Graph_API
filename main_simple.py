#!/usr/bin/env python3
print("Testing Python execution...")

try:
    import fastmcp
    print("Successfully imported fastmcp")
except ImportError as e:
    print(f"Failed to import fastmcp: {e}")

try:
    from fastmcp import FastMCP
    from fastmcp.resources import TextResource
    print("Successfully imported FastMCP and TextResource")
except ImportError as e:
    print(f"Failed to import FastMCP or TextResource: {e}")

# Try other imports
try:
    import uvicorn
    print("Successfully imported uvicorn")
except ImportError as e:
    print(f"Failed to import uvicorn: {e}")

try:
    import dotenv
    print("Successfully imported python-dotenv")
except ImportError as e:
    print(f"Failed to import python-dotenv: {e}")

# Try creating a simple MCP server
try:
    mcp = FastMCP(name="Test Server")
    print("Successfully created FastMCP instance")
    
    # Try with a simpler approach - Just add a dictionary with the resource
    @mcp.resource
    def test_resource():
        return {
            "name": "test",
            "description": "Test resource"
        }
    
    print("Successfully created test resource")
    
    # Define a tool
    @mcp.tool(resource="test")
    async def test_tool():
        """Test tool"""
        return {"status": "ok"}
    
    print("Successfully created test tool")
    
    # Try to start the server (don't actually start it)
    print("Server would start with uvicorn.run(mcp.app, host='127.0.0.1', port=8000)")
    
except Exception as e:
    print(f"Error creating MCP server: {e}")

print("Python script completed successfully") 