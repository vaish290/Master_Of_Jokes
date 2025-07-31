import hmac
from functools import wraps
from flask import current_app

def safe_str_cmp(a, b):
    """Replacement for werkzeug.security.safe_str_cmp using hmac.compare_digest."""
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def log_function_call(func):
    """Decorator to log entry and exit of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_app.logger.debug(f"Entering function: {func.__name__}")
        result = func(*args, **kwargs)
        current_app.logger.debug(f"Exiting function: {func.__name__}, Return Value: {result}")
        return result
    return wrapper