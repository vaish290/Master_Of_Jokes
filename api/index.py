# api/index.py

from wsgi_adapter import handle_request
from wsgi import app  
def handler(environ, start_response):
    return handle_request(app, environ, start_response)
