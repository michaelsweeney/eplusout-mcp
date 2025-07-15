
from src.server import mcp


if __name__ == "__main__":
    # Run with stdio transport for MCP
    mcp.run(transport="stdio")
