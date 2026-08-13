from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, Request, status


@dataclass(frozen=True)
class Principal:
    subject: str
    email: str
    display_name: str
    provider: str = "google"


def current_principal(request: Request) -> Principal:
    """Read an identity that has already been verified by the web auth boundary.

    Development headers keep local work free and testable. Production intentionally
    refuses them; the Google OAuth session adapter will supply a verified principal.
    """

    if request.app.state.auth_mode != "development":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google authentication is not configured for this deployment.",
        )

    subject = request.headers.get("x-ffv-user-id")
    email = request.headers.get("x-ffv-user-email")
    name = request.headers.get("x-ffv-user-name")
    if not subject or not email or not name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in is required.",
        )
    return Principal(subject=subject, email=email.lower(), display_name=name)

