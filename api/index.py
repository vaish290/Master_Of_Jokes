from flask import Flask

# Create Flask app
app = Flask(__name__)

@app.route("/")
def hello():
    return "✅ Hello from Flask on Vercel!"

# Vercel expects `app` to be the WSGI handler
# So assign `app` as `handler`
handler = app
