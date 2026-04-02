"""
business/exceptions.py
-----------------------
Custom exception hierarchy for the K-Pop Collection business layer.

Raised by business classes and caught by the Flask service layer,
which maps them to appropriate HTTP status codes.
"""


class KpopBusinessError(Exception):
    """Base class for all business-layer errors."""


class NotFoundError(KpopBusinessError):
    """Resource does not exist. Maps to HTTP 404."""


class ValidationError(KpopBusinessError):
    """Input fails business-rule validation. Maps to HTTP 400."""


class DependencyError(KpopBusinessError):
    """Delete blocked by child records (FK constraint). Maps to HTTP 409."""