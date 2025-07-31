from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify(message="Hello from Flask on Vercel!")

# Required for Vercel
def handler(environ, start_response):
    from werkzeug.middleware.dispatcher import DispatcherMiddleware
    from werkzeug.wrappers import Request, Response
    return DispatcherMiddleware(lambda e, s: Response("Not Found", status=404), {
        '/': app
    })(environ, start_response)
