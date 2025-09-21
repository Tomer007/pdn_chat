# Render MCP Server Setup Guide

This guide explains how to set up the Render MCP (Model Context Protocol) server for deployment management.

## Prerequisites

1. A Render account with active services
2. Cursor IDE with MCP support
3. Render API key

## Step 1: Get Your Render API Key

1. Log in to your [Render Dashboard](https://dashboard.render.com)
2. Navigate to **Account Settings** → **API Keys**
3. Click **Create API Key**
4. Give it a descriptive name (e.g., "PDN Chat MCP")
5. Copy the generated API key

## Step 2: Configure Environment Variables

Add your Render API key to your environment:

```bash
# Add to your .env file or export in your shell
export RENDER_API_KEY=your-render-api-key-here
```

## Step 3: MCP Configuration

The Render MCP server has been added to your Cursor configuration at `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/Users/tomer.gur/dev-tools/pdn_chat"],
      "env": {}
    },
    "python-linter": {
      "command": "python3",
      "args": ["/Users/tomer.gur/dev-tools/pdn_chat/mcp-python-server.py"],
      "env": {}
    },
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer ${RENDER_API_KEY}"
      }
    }
  }
}
```

## Step 4: Restart Cursor

After adding the MCP server configuration, restart Cursor to load the new MCP server.

## Step 5: Set Your Render Workspace

In Cursor, you can now use natural language commands to manage your Render services:

```
Set my Render workspace to [WORKSPACE_NAME]
```

Replace `[WORKSPACE_NAME]` with your actual Render workspace name.

## Available Commands

With the Render MCP server, you can now:

- **Deploy services**: "Deploy the latest changes to production"
- **Check service status**: "What's the status of my pdn-chat service?"
- **View logs**: "Show me the logs for the pdn-chat service"
- **Manage environment variables**: "Update the OPENAI_API_KEY environment variable"
- **Scale services**: "Scale up my pdn-chat service to 2 instances"
- **View service details**: "Show me details about my pdn-chat service"

## Troubleshooting

### MCP Server Not Loading
1. Ensure your `RENDER_API_KEY` environment variable is set
2. Check that the MCP configuration file is valid JSON
3. Restart Cursor completely

### API Key Issues
1. Verify your API key is correct in Render dashboard
2. Ensure the API key has the necessary permissions
3. Check that the key hasn't expired

### Connection Issues
1. Verify your internet connection
2. Check if Render's MCP service is operational
3. Try regenerating your API key

## Security Notes

- Keep your Render API key secure and never commit it to version control
- Use environment variables to store sensitive information
- Regularly rotate your API keys for security

## Next Steps

Once configured, you can use the Render MCP server to:
1. Monitor your PDN Chat deployment
2. Deploy updates with natural language commands
3. Manage environment variables and configuration
4. Scale services based on demand
5. Debug issues by viewing logs and service status

For more information, refer to the [Render MCP Server Documentation](https://render.com/docs/mcp-server).
