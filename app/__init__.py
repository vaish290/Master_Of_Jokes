from flask import Flask,request,current_app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
import click
import logging
import uuid
from flask import render_template

db = SQLAlchemy()
SQLALCHEMY_ECHO = True  # Logs all SQL statements executed by SQLAlchemy
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)

    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    configure_logging(app)
    app.logger.info("Master of Jokes program started.")
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database initialized successfully.")
        except Exception as e:
            app.logger.critical(f"Database initialization failed: {e}")
    
    

    @app.before_request
    def log_session():
        session_id = str(uuid.uuid4())
        request.session_id = session_id  # Attach session ID to the request object
        app.logger.debug(f"Session ID: {session_id} - Processing {request.method} {request.path}")

    # Log HTTP status codes after each request
    @app.after_request
    def log_request(response):
        session_id = getattr(request, 'session_id', 'N/A')
        app.logger.info(f"Session ID: {session_id} - Request processed: {request.method} {request.path}, Status Code: {response.status_code}")
    
        if response.status_code != 200:
            app.logger.warning(f"Session ID: {session_id} - Non-200 HTTP response: {response.status_code}")
        return response

    register_cli_commands(app)
    
    @app.errorhandler(500)
    def handle_500_error(e):
        """Log internal server errors."""
        app.logger.error(f"Internal Server Error: {e}")
        return render_template('500.html'), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Log unexpected exceptions."""
        app.logger.error(f"Unexpected error: {e}", exc_info=True)
        return render_template('error.html', error=e), 500


    return app

def register_cli_commands(app):
    """Register custom CLI commands."""
    import click
    from .models import User

    @app.cli.command("init-moderator")
    @click.argument("email")
    @click.argument("nickname")
    @click.argument("password")
    def init_moderator(email, nickname, password):
        """Initialize a moderator account."""
        if User.query.filter_by(role='Moderator').count() > 0:
            print("A moderator already exists.")
            return

        user = User(email=email, nickname=nickname)
        user.set_password(password)
        user.role = 'Moderator'
        db.session.add(user)
        db.session.commit()
        print(f"Moderator {nickname} created.")
        current_app.logger.info(f"Moderator account created: {nickname}")

def configure_logging(app):
    """Configure logging for the application."""
    # Create log format with timestamp and module name
    log_format = '%(asctime)s - %(module)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%dT%H:%M:%S'

    # Set up console handler (WARN level or higher)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARN)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Set up file handler (INFO level or higher)
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Add handlers to Flask's logger
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)

    # Set default logging level to INFO
    app.logger.setLevel(logging.INFO)

    def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            app.logger.critical("Program terminated by user.")
        else:
            app.logger.critical(
                "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
            )
    
    import sys
    sys.excepthook = handle_uncaught_exception