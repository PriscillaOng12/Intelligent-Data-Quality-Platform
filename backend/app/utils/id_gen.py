"""ID generation utilities."""

import uuid


def generate_id() -> str:
    """Generate a short unique identifier."""

    return uuid.uuid4().hex