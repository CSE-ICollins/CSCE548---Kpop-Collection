"""
business/exceptions.py
----------------------
Custom exception hierarchy for the K-Pop Collection business layer.
All service-level code should catch these instead of raw DB errors,
keeping the REST layer decoupled from SQLite specifics.
"""


class KpopBusinessError(Exception):
    """Base class for all business-layer errors."""
    pass


class NotFoundError(KpopBusinessError):
    """Raised when a requested resource does not exist."""
    def __init__(self, resource: str, id_value):
        self.resource = resource
        self.id_value = id_value
        super().__init__(f"{resource} with id={id_value} not found.")


class ValidationError(KpopBusinessError):
    """Raised when input data fails a business rule."""
    pass


class ConflictError(KpopBusinessError):
    """Raised when an operation conflicts with existing data (e.g. duplicate)."""
    pass


class DependencyError(KpopBusinessError):
    """Raised when deleting a resource that others depend on."""
    pass
