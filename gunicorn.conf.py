# Gunicorn configuration for PDN Chat

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes - single worker to maintain in-memory session consistency
# (admin_sessions, conversation_history, token_usage are all in-memory dicts)
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5 minutes timeout for long-running requests like 21-day plan
keepalive = 2

# Restart workers to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "pdn-chat"

# Server mechanics
daemon = False
preload_app = True

# Graceful shutdown
graceful_timeout = 30
