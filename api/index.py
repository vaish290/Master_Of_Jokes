# api/index.py

from wsadapter import handle_request
from wsgi import app  
def handler(environ, start_response):
    return handle_request(app, environ, start_response)
