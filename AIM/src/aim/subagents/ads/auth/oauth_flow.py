"""
OAuth 2.0 Flow Implementation for Ads APIs.

Based on google-ads-python oauth2.py pattern.
Supports both installed app credentials and service account credentials.
"""

import functools
from typing import Any, Callable, Optional, TypeVar, Union

from google.auth import default as ApplicationDefaultCredentials
from google.auth.credentials import Credentials as CredentialsBaseClass
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as InstalledAppCredentials
from google.oauth2.service_account import Credentials as ServiceAccountCreds
from requests import Session

import structlog

logger = structlog.get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

_SERVICE_ACCOUNT_SCOPES: list[str] = [
    "https://www.googleapis.com/auth/adwords"
]
_DEFAULT_TOKEN_URI: str = "https://accounts.google.com/o/oauth2/token"


def _initialize_credentials_decorator(func: F) -> F:
    """
    Decorator to initialize and refresh OAuth credentials.

    Automatically refreshes credentials after creation.
    Supports HTTP proxy for corporate environments.

    Args:
        func: Function that creates credentials

    Returns:
        Initialized and refreshed credentials
    """
    @functools.wraps(func)
    def initialize_credentials_wrapper(*args: Any, **kwargs: Any) -> Any:
        credentials: Union[InstalledAppCredentials, ServiceAccountCreds] = func(
            *args, **kwargs
        )

        # If configs contain http_proxy, refresh through proxy
        proxy: Optional[str] = kwargs.get("http_proxy")

        try:
            if proxy:
                logger.info("refreshing_credentials_via_proxy", proxy=proxy)
                session: Session = Session()
                session.proxies.update({"http": proxy, "https": proxy})
                credentials.refresh(Request(session=session))
            else:
                logger.info("refreshing_credentials")
                credentials.refresh(Request())

            logger.info("credentials_initialized_successfully")
            return credentials

        except Exception as e:
            logger.error(
                "credentials_refresh_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    return initialize_credentials_wrapper


@_initialize_credentials_decorator
def get_installed_app_credentials(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    http_proxy: Optional[str] = None,
    token_uri: str = _DEFAULT_TOKEN_URI,
) -> InstalledAppCredentials:
    """
    Create OAuth2 credentials for installed applications (desktop/mobile).

    This is the most common flow for Google Ads API access.
    Requires OAuth client credentials from Google Cloud Console.

    Args:
        client_id: OAuth 2.0 client ID from Google Cloud Console
        client_secret: OAuth 2.0 client secret
        refresh_token: OAuth 2.0 refresh token (obtained via authorization flow)
        http_proxy: Optional HTTP proxy URL for corporate networks
        token_uri: OAuth token endpoint (default: Google's token URI)

    Returns:
        Initialized and refreshed InstalledAppCredentials

    Raises:
        google.auth.exceptions.RefreshError: If token refresh fails

    Example:
        >>> credentials = get_installed_app_credentials(
        ...     client_id="123456.apps.googleusercontent.com",
        ...     client_secret="secret123",
        ...     refresh_token="1//refresh_token_here"
        ... )
        >>> # Use credentials with Google Ads API client
    """
    logger.info(
        "creating_installed_app_credentials",
        client_id=client_id[:20] + "...",  # Log partial ID for security
        has_refresh_token=bool(refresh_token),
        has_proxy=bool(http_proxy)
    )

    return InstalledAppCredentials(
        None,  # No access token yet (will be refreshed)
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_token,
        token_uri=token_uri,
    )


@_initialize_credentials_decorator
def get_service_account_credentials(
    json_key_file_path: str,
    subject: str,
    http_proxy: Optional[str] = None,
    scopes: list[str] = _SERVICE_ACCOUNT_SCOPES,
) -> ServiceAccountCreds:
    """
    Create OAuth2 credentials for service accounts.

    Service accounts are used for server-to-server authentication.
    Requires service account JSON key file from Google Cloud Console.

    Args:
        json_key_file_path: Path to service account JSON key file
        subject: Email address to impersonate (for domain-wide delegation)
        http_proxy: Optional HTTP proxy URL
        scopes: OAuth scopes to request (default: Google Ads scope)

    Returns:
        Initialized and refreshed ServiceAccountCreds

    Raises:
        google.auth.exceptions.RefreshError: If token refresh fails
        FileNotFoundError: If JSON key file not found

    Example:
        >>> credentials = get_service_account_credentials(
        ...     json_key_file_path="/path/to/service-account.json",
        ...     subject="user@example.com"
        ... )
    """
    logger.info(
        "creating_service_account_credentials",
        json_key_file=json_key_file_path,
        subject=subject,
        scopes=scopes,
        has_proxy=bool(http_proxy)
    )

    credentials = ServiceAccountCreds.from_service_account_file(
        json_key_file_path,
        scopes=scopes
    )

    # Impersonate user if subject provided
    if subject:
        credentials = credentials.with_subject(subject)

    return credentials


def get_application_default_credentials(
    scopes: list[str] = _SERVICE_ACCOUNT_SCOPES,
) -> CredentialsBaseClass:
    """
    Get credentials from application default credentials (ADC).

    ADC automatically finds credentials from:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable
    2. gcloud CLI default credentials
    3. Compute Engine/App Engine/Cloud Run metadata server

    Args:
        scopes: OAuth scopes to request

    Returns:
        Application default credentials

    Raises:
        google.auth.exceptions.DefaultCredentialsError: If no credentials found

    Example:
        >>> # Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
        >>> credentials = get_application_default_credentials()
    """
    logger.info("loading_application_default_credentials", scopes=scopes)

    credentials, project = ApplicationDefaultCredentials(scopes=scopes)

    logger.info(
        "application_default_credentials_loaded",
        project=project,
        credential_type=type(credentials).__name__
    )

    return credentials


def refresh_credentials(
    credentials: Union[InstalledAppCredentials, ServiceAccountCreds],
    http_proxy: Optional[str] = None
) -> None:
    """
    Manually refresh OAuth credentials.

    Useful when credentials expire during long-running operations.

    Args:
        credentials: Credentials to refresh
        http_proxy: Optional HTTP proxy URL

    Raises:
        google.auth.exceptions.RefreshError: If refresh fails
    """
    logger.info("manually_refreshing_credentials")

    try:
        if http_proxy:
            session = Session()
            session.proxies.update({"http": http_proxy, "https": http_proxy})
            credentials.refresh(Request(session=session))
        else:
            credentials.refresh(Request())

        logger.info("credentials_refreshed_successfully")

    except Exception as e:
        logger.error(
            "credentials_refresh_failed",
            error=str(e),
            error_type=type(e).__name__
        )
        raise
