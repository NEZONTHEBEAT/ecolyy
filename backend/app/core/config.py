"""
Ecolyy Application Configuration

All production-sensitive values are loaded from environment variables
or backend/.env during local development.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.

    Local development:
        backend/.env

    Production:
        Render Environment Variables
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # =========================================================
    # APPLICATION
    # =========================================================

    APP_NAME: str = "Ecolyy API"
    ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # =========================================================
    # SECURITY / JWT
    # =========================================================

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # =========================================================
    # MONGODB
    # =========================================================

    # Supports the existing MONGODB_URI variable from .env.
    MONGO_URI: str = ""
    MONGO_DB_NAME: str = "ecolyy"

    # =========================================================
    # CORS
    # =========================================================

    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000,"
        "http://localhost:5500,"
        "http://127.0.0.1:5500,"
        "http://localhost:8000,"
        "http://127.0.0.1:8000"
    )

    # =========================================================
    # GOOGLE SIGN-IN
    # =========================================================

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # =========================================================
    # ROLE / EMAIL CONFIGURATION
    # =========================================================

    SUPER_ADMIN_EMAIL: str = ""

    PARTNER_EMAILS: str = ""

    INSTITUTE_EMAILS: str = ""

    # =========================================================
    # DEFAULT PASSWORDS
    # =========================================================
    #
    # Kept for backward compatibility with existing project code.
    # These MUST be configured through environment variables if used.
    #

    DEFAULT_PARTNER_PASSWORD: str = ""
    DEFAULT_INSTITUTE_PASSWORD: str = ""
    DEFAULT_USER_PASSWORD: str = ""
    DEFAULT_ADMIN_PASSWORD: str = ""

    # =========================================================
    # DASHBOARD REDIRECTS
    # =========================================================

    REDIRECT_ADMIN: str = "/admin/dashboard.html"
    REDIRECT_PARTNER: str = "/partner/dashboard.html"
    REDIRECT_INSTITUTE: str = "/institution/dashboard.html"
    REDIRECT_USER: str = "/user/dashboard.html"

    # =========================================================
    # DISPLAY ROLE NAMES
    # =========================================================

    DISPLAY_ADMIN: str = "Super Admin"
    DISPLAY_PARTNER: str = "Collection Partner"
    DISPLAY_INSTITUTE: str = "Institute"
    DISPLAY_USER: str = "User"

    # =========================================================
    # OTP
    # =========================================================

    OTP_EXPIRE_MINUTES: int = 5

    # =========================================================
    # SMTP / EMAIL
    # =========================================================

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@ecolyy.app"

    # =========================================================
    # CORS PROPERTY
    # =========================================================

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS origins into a list."""

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    # =========================================================
    # EMAIL LIST PROPERTIES
    # =========================================================

    @property
    def partner_emails_list(self) -> List[str]:
        """Return normalized partner email addresses."""

        return [
            email.strip().lower()
            for email in self.PARTNER_EMAILS.split(",")
            if email.strip()
        ]

    @property
    def institute_emails_list(self) -> List[str]:
        """Return normalized institution email addresses."""

        return [
            email.strip().lower()
            for email in self.INSTITUTE_EMAILS.split(",")
            if email.strip()
        ]

    # =========================================================
    # ROLE DETECTION
    # =========================================================

    def detect_role_from_email(self, email: str) -> str:
        """
        Determine the user's role from their email address.

        Admin:
            SUPER_ADMIN_EMAIL

        Partner:
            PARTNER_EMAILS

        Institution:
            INSTITUTE_EMAILS

        Everything else:
            user
        """

        email = email.strip().lower()

        if email == self.SUPER_ADMIN_EMAIL.lower():
            return "admin"

        if email in self.partner_emails_list:
            return "partner"

        if email in self.institute_emails_list:
            return "institution"

        return "user"

    # =========================================================
    # ROLE CHECK HELPERS
    # =========================================================

    def is_admin_email(self, email: str) -> bool:
        """Check whether an email belongs to the super admin."""

        return email.strip().lower() == self.SUPER_ADMIN_EMAIL.lower()

    def is_partner_email(self, email: str) -> bool:
        """Check whether an email belongs to a configured partner."""

        return email.strip().lower() in self.partner_emails_list

    def is_institute_email(self, email: str) -> bool:
        """Check whether an email belongs to a configured institution."""

        return email.strip().lower() in self.institute_emails_list

    # =========================================================
    # DEFAULT PASSWORD
    # =========================================================

    def get_default_password_for_role(self, role: str) -> str:
        """
        Return configured default password for a role.

        These values are intentionally empty by default and should
        only be configured when legacy/demo functionality requires them.
        """

        passwords = {
            "admin": self.DEFAULT_ADMIN_PASSWORD,
            "partner": self.DEFAULT_PARTNER_PASSWORD,
            "institution": self.DEFAULT_INSTITUTE_PASSWORD,
            "user": self.DEFAULT_USER_PASSWORD,
        }

        return passwords.get(role, self.DEFAULT_USER_PASSWORD)

    # =========================================================
    # DASHBOARD REDIRECT
    # =========================================================

    def get_redirect_url_for_role(self, role: str) -> str:
        """Return dashboard URL for the detected role."""

        redirects = {
            "admin": self.REDIRECT_ADMIN,
            "partner": self.REDIRECT_PARTNER,
            "institution": self.REDIRECT_INSTITUTE,
            "user": self.REDIRECT_USER,
        }

        return redirects.get(role, self.REDIRECT_USER)

    # =========================================================
    # DISPLAY ROLE
    # =========================================================

    def get_display_role(self, role: str) -> str:
        """Return human-readable role name."""

        display_names = {
            "admin": self.DISPLAY_ADMIN,
            "partner": self.DISPLAY_PARTNER,
            "institution": self.DISPLAY_INSTITUTE,
            "user": self.DISPLAY_USER,
        }

        return display_names.get(role, self.DISPLAY_USER)

    # =========================================================
    # ROLE VALIDATION
    # =========================================================

    def validate_role_for_email(
        self,
        email: str,
        role: str,
    ) -> bool:
        """
        Validate whether a role matches the authoritative role
        detected from the email address.
        """

        detected_role = self.detect_role_from_email(email)

        return detected_role == role

    # =========================================================
    # ALL ROLES
    # =========================================================

    def get_all_roles(self) -> List[str]:
        """Return all supported roles."""

        return [
            "admin",
            "partner",
            "institution",
            "user",
        ]

    # =========================================================
    # ALLOWED EMAILS FOR ROLE
    # =========================================================

    def get_allowed_emails_for_role(
        self,
        role: str,
    ) -> List[str]:
        """Return explicitly configured emails for a role."""

        if role == "admin":
            return [self.SUPER_ADMIN_EMAIL.lower()]

        if role == "partner":
            return self.partner_emails_list

        if role == "institution":
            return self.institute_emails_list

        return []


# =============================================================
# SETTINGS SINGLETON
# =============================================================

@lru_cache
def get_settings() -> Settings:
    """Create and cache the application settings instance."""

    return Settings()


settings = get_settings()
