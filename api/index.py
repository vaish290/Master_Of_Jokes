from flask import Flask
from werkzeug.wrappers import Request, Response
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Hello from Flask on Vercel (via WSGI)!"

# Vercel expects this WSGI-compatible handler
def handler(environ, start_response):
    return DispatcherMiddleware(app)(environ, start_response)
