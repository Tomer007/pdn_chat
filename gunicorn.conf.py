# Gunicorn configuration for PDN Chat
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 300  # 5 minutes timeout for long-running requests like 21-day plan
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "pdn-chat"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
keyfile = None
certfile = None

# Preload app for better performance
preload_app = True

# Worker timeout for graceful shutdown
graceful_timeout = 30

# Maximum time a worker can handle a request
timeout = 300  # 5 minutes for complex AI operations

# Maximum time for graceful worker restart
graceful_timeout = 30

# The maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many seconds, to prevent memory leaks
max_worker_connections = 1000
