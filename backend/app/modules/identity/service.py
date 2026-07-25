"""Authenticated identity application service."""

from app.core.security import AuthenticatedIdentity
from app.modules.identity.schemas import MeResponse


def build_me_response(identity: AuthenticatedIdentity) -> MeResponse:
    """Map a verified internal identity to its public response."""
    return MeResponse(
        id=identity.user_id,
        role=identity.role,
    )
