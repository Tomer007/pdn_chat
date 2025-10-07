# LangSmith Configuration

This application supports LangSmith tracing for monitoring and debugging LangChain operations.

## Environment Variables

Set the following environment variables to enable LangSmith tracing:

```bash
# Required
LANGSMITH_API_KEY=your_langsmith_api_key_here

# Optional (with defaults)
LANGSMITH_PROJECT=pdn-chat
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_TRACING_V2=true
```

## Render Deployment

In your `render.yaml`, set the environment variables:

```yaml
envVars:
  - key: LANGSMITH_API_KEY
    value: your_actual_langsmith_api_key
  - key: LANGSMITH_PROJECT
    value: pdn-chat
  - key: LANGSMITH_TRACING_V2
    value: "true"
```

## Local Development

Create a `.env` file in the project root:

```bash
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=pdn-chat
LANGSMITH_TRACING_V2=true
```

## Features

- **Automatic Tracing**: All LangChain LLM calls are automatically traced
- **Optional**: Application works without LangSmith (graceful fallback)
- **Centralized Config**: Single configuration point in `app/utils/langsmith_config.py`
- **Memory Integration**: Works with existing memory monitoring

## Getting LangSmith API Key

1. Visit [https://smith.langchain.com](https://smith.langchain.com)
2. Sign up or log in
3. Go to Settings → API Keys
4. Create a new API key
5. Copy the key and set it as `LANGSMITH_API_KEY`

## Monitoring

Once configured, you can monitor your traces at:
- **Dashboard**: [https://smith.langchain.com](https://smith.langchain.com)
- **Project**: Use the project name set in `LANGSMITH_PROJECT`

## Troubleshooting

- **No traces appearing**: Check that `LANGSMITH_API_KEY` is set correctly
- **403 Forbidden**: Verify the API key is valid and has proper permissions
- **Connection errors**: Check network connectivity and endpoint URL
