#!/usr/bin/env python3
import sys
from mcp.server.fastmcp import FastMCP

# Create a simple MCP server
mcp = FastMCP("Simple Test Server")

# Add a simple test tool
@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

# Add a simple resource
@mcp.resource("greeting://hello")
def get_greeting() -> str:
    """Return a simple greeting"""
    return "Welcome to the MCP server!"

if __name__ == "__main__":
    # Run the MCP server
    print("Starting simple MCP server...", file=sys.stderr)
    mcp.run() 