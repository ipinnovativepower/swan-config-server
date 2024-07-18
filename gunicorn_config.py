# gunicorn_config.py

bind = '0.0.0.0:8000'
workers = 1  # You can adjust this based on your testing needs
timeout = 60  # Keep-alive timeout (seconds)
keepalive = 60  # Connection keep-alive duration (seconds)
max_requests = 50  # Max client requests per connection

# logging
accesslog = '-'  # log to stdout
errorlog = '-'  # log to stdout

