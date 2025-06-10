"""Role-based access control utilities.

The platform defines several roles with increasing levels of privilege. This
module provides decorators and dependency functions to restrict access to
certain API routes based on a user's role.
"""

from typing import Callable, List

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_active_user
from app.db.models import User


def require_role(*allowed_roles: str) -> Callable[[User], User]:
    """Create a dependency that validates the current user's role.

    Usage:

    ```python
    @router.post("/datasets", dependencies=[Depends(require_role("Owner","Maintainer"))])
    async def create_dataset(...):
        ...
    ```
    """

    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role in {allowed_roles}",
            )
        return current_user

    return dependency