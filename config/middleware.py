"""
Middleware to log full traceback on server errors (when DEBUG is False).
"""
import logging
import traceback

logger = logging.getLogger(__name__)


class Log500Middleware:
    """Log full exception traceback when a 500 response is returned."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.exception(
            "Unhandled exception for %s %s: %s\n%s",
            request.method,
            request.path,
            exception,
            traceback.format_exc(),
        )
        return None
