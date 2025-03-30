#!/usr/bin/env python3
"""
Minimal test script for MCP server
"""
import sys
import uvicorn
from fastmcp import FastMCP
from fastmcp.resources import TextResource

# Create MCP server
mcp = FastMCP(name="Minimal Test Server")

# Create a simple resource
text_resource = TextResource(
    name="test",
    description="Test resource",
    uri="https://example.com/test",
    text="This is a test resource"
)
mcp.add_resource(text_resource)

# Define a simple tool - remove the resource parameter
@mcp.tool()
async def hello():
    """A simple hello world tool"""
    return {"message": "Hello, MCP!"}

if __name__ == "__main__":
    # Run the MCP server
    print("Starting MCP server on http://127.0.0.1:8000", file=sys.stderr)
    uvicorn.run(mcp.app, host="127.0.0.1", port=8000) 