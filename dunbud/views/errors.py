"""
Custom error handlers for the Dungeon Buddy application.
"""

import logging

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


def bad_request(request: HttpRequest, exception: Exception) -> HttpResponse:
    """
    Custom 400 Bad Request handler.

    Args:
        request: The HTTP request.
        exception: The exception that triggered this error.

    Returns:
        HttpResponse: The rendered 400 error page.
    """
    logger.warning("400 Bad Request: %s", exception)
    return render(request, "errors/400.html", status=400)


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:
    """
    Custom 403 Permission Denied handler.

    Args:
        request: The HTTP request.
        exception: The exception that triggered this error.

    Returns:
        HttpResponse: The rendered 403 error page.
    """
    logger.warning("403 Permission Denied: %s", request.path)
    return render(request, "errors/403.html", status=403)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """
    Custom 404 Page Not Found handler.

    Args:
        request: The HTTP request.
        exception: The exception that triggered this error.

    Returns:
        HttpResponse: The rendered 404 error page.
    """
    logger.warning("404 Not Found: %", request.path)
    return render(request, "errors/404.html", status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    """
    Custom 500 Internal Server Error handler.

    Args:
        request: The HTTP request.

    Returns:
        HttpResponse: The rendered 500 error page.
    """
    logger.error("500 Internal Server Error")
    return render(request, "errors/500.html", status=500)


def service_unavailable(
    request: HttpRequest,
    exception: Exception | None = None,
) -> HttpResponse:
    """
    Custom 503 Service Unavailable view.

    Note: Django does not have a default handler for 503. This view can be used
    by custom middleware (e.g., for maintenance mode) or manual triggers.

    Args:
        request: The HTTP request.
        exception: Optional exception details.

    Returns:
        HttpResponse: The rendered 503 error page.
    """
    logger.error("503 Service Unavailable")
    return render(request, "errors/503.html", status=503)
