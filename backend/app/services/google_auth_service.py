"""
Ecolyy Google Authentication Service

Verifies Google Sign-In ID tokens and returns a trusted payload.

Supports:
- Google OAuth / Google Identity Services
- Client ID / audience verification
- Issuer verification
- Verified email requirement
- Small clock-skew tolerance for local development
"""

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings


# Small tolerance for minor differences between the local machine clock
# and Google's token timestamp.
GOOGLE_CLOCK_SKEW_SECONDS = 10


def verify_google_token(token: str) -> dict:
    """
    Verify a Google ID token and return trusted user information.

    Raises:
        ValueError: If the token is invalid, expired, has the wrong
                    audience/issuer, or the Google email is unverified.
    """

    if not token or not isinstance(token, str):
        raise ValueError("Google ID token is missing or invalid")

    try:
        payload = google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=GOOGLE_CLOCK_SKEW_SECONDS,
        )

    except Exception as exc:
        raise ValueError(
            f"Invalid Google token: {exc}"
        ) from exc

    # Google issuer validation
    issuer = payload.get("iss")

    if issuer not in (
        "accounts.google.com",
        "https://accounts.google.com",
    ):
        raise ValueError("Invalid token issuer")

    # Google must confirm the email address
    if not payload.get("email_verified", False):
        raise ValueError("Google email is not verified")

    # Required Google claims
    google_id = payload.get("sub")
    email = payload.get("email")

    if not google_id:
        raise ValueError("Google token does not contain a user ID")

    if not email:
        raise ValueError("Google token does not contain an email")

    email = email.lower().strip()

    name = payload.get("name") or email.split("@")[0]

    return {
        "google_id": google_id,
        "email": email,
        "name": name,
        "picture": payload.get("picture"),
    }

