"""Authenticated identity application service."""

from app.core.security import AuthenticatedAthlete
from app.modules.identity.schemas import MeResponse


def build_me_response(identity: AuthenticatedAthlete) -> MeResponse:
    """Map a verified internal identity to its public response."""
    return MeResponse(
        athlete_id=identity.athlete_id,
        role=identity.role,
    )
