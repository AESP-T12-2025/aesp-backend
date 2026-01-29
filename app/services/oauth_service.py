"""
OAuth Service
=============
Provides OAuth authentication functionality (Google, etc.)

Features:
- Google OAuth flow
- Token validation
- User creation/linking
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings


# =============================================================================
# CONFIGURATION
# =============================================================================

logger = logging.getLogger(__name__)

# OAuth Configuration
GOOGLE_CLIENT_ID = getattr(settings, 'GOOGLE_CLIENT_ID', None)
GOOGLE_CLIENT_SECRET = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
OAUTH_REDIRECT_URI = getattr(settings, 'OAUTH_REDIRECT_URI', 'http://localhost:8000/auth/google/callback')


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class AuthProvider(str, Enum):
    LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"
    FACEBOOK = "FACEBOOK"
    GITHUB = "GITHUB"


@dataclass
class GoogleUserInfo:
    """User info from Google OAuth."""
    email: str
    name: str
    picture: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    locale: Optional[str] = None
    verified_email: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoogleUserInfo":
        return cls(
            email=data.get("email", ""),
            name=data.get("name", ""),
            picture=data.get("picture"),
            given_name=data.get("given_name"),
            family_name=data.get("family_name"),
            locale=data.get("locale"),
            verified_email=data.get("verified_email", True)
        )


@dataclass
class OAuthToken:
    """OAuth token data."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


# =============================================================================
# SERVICE CLASS
# =============================================================================

class OAuthService:
    """
    OAuth service for social login authentication.
    
    Currently supports:
    - Google OAuth 2.0
    
    Future support:
    - Facebook
    - GitHub
    """
    
    def __init__(self):
        """Initialize OAuth service."""
        self._state_storage: Dict[str, Dict[str, Any]] = {}  # state -> {created_at, user_id}
        self._oauth_links: Dict[int, Dict[str, str]] = {}  # user_id -> {provider: provider_id}
        
        if GOOGLE_CLIENT_ID:
            logger.info("✅ Google OAuth configured")
        else:
            logger.info("📢 Google OAuth running in mock mode (no client ID)")
    
    # =========================================================================
    # STATE MANAGEMENT (CSRF Protection)
    # =========================================================================
    
    def generate_state(self, user_id: Optional[int] = None) -> str:
        """
        Generate a random state parameter for OAuth flow.
        
        Args:
            user_id: Optional user ID for account linking
            
        Returns:
            Random state string
        """
        state = secrets.token_urlsafe(32)
        self._state_storage[state] = {
            "created_at": datetime.now(),
            "user_id": user_id
        }
        return state
    
    def validate_state(self, state: str) -> Optional[Dict[str, Any]]:
        """
        Validate OAuth state parameter.
        
        Args:
            state: State to validate
            
        Returns:
            State data if valid, None otherwise
        """
        if state not in self._state_storage:
            return None
        
        state_data = self._state_storage[state]
        
        # Check expiry (10 minutes)
        if datetime.now() - state_data["created_at"] > timedelta(minutes=10):
            del self._state_storage[state]
            return None
        
        # Remove used state
        del self._state_storage[state]
        return state_data
    
    # =========================================================================
    # GOOGLE OAUTH
    # =========================================================================
    
    def get_google_auth_url(self, state: Optional[str] = None) -> Dict[str, str]:
        """
        Get Google OAuth authorization URL.
        
        Args:
            state: Optional state parameter (generated if not provided)
            
        Returns:
            Dict with auth_url and state
        """
        if not state:
            state = self.generate_state()
        
        if not GOOGLE_CLIENT_ID:
            # Mock mode
            return {
                "auth_url": f"https://mock-oauth.example.com?state={state}",
                "state": state,
                "mock": True
            }
        
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent"
        }
        
        from urllib.parse import urlencode
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    async def exchange_google_code(self, code: str) -> Optional[OAuthToken]:
        """
        Exchange authorization code for tokens.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            OAuthToken if successful
        """
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            # Mock mode - return mock token
            logger.info("📢 [MOCK] Exchanging Google code")
            return OAuthToken(
                access_token="mock_access_token",
                id_token="mock_id_token",
                refresh_token="mock_refresh_token"
            )
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": OAUTH_REDIRECT_URI
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Google token exchange failed: {response.text}")
                    return None
                
                data = response.json()
                return OAuthToken(
                    access_token=data.get("access_token", ""),
                    id_token=data.get("id_token"),
                    refresh_token=data.get("refresh_token"),
                    expires_in=data.get("expires_in", 3600),
                    scope=data.get("scope")
                )
                
        except Exception as e:
            logger.error(f"Google token exchange error: {e}")
            return None
    
    async def get_google_user_info(self, access_token: str) -> Optional[GoogleUserInfo]:
        """
        Get user info from Google using access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            GoogleUserInfo if successful
        """
        if access_token.startswith("mock_"):
            # Mock mode
            logger.info("📢 [MOCK] Getting Google user info")
            return GoogleUserInfo(
                email="mockuser@gmail.com",
                name="Mock User",
                picture="https://example.com/avatar.png",
                given_name="Mock",
                family_name="User"
            )
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Google user info failed: {response.text}")
                    return None
                
                return GoogleUserInfo.from_dict(response.json())
                
        except Exception as e:
            logger.error(f"Google user info error: {e}")
            return None
    
    async def validate_google_id_token(self, id_token: str) -> Optional[GoogleUserInfo]:
        """
        Validate Google ID token and extract user info.
        
        Args:
            id_token: Google ID token
            
        Returns:
            GoogleUserInfo if valid
        """
        if id_token.startswith("mock_"):
            # Mock mode
            return GoogleUserInfo(
                email="mockuser@gmail.com",
                name="Mock User"
            )
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
                )
                
                if response.status_code != 200:
                    logger.error(f"Google ID token validation failed: {response.text}")
                    return None
                
                data = response.json()
                
                # Verify audience
                if GOOGLE_CLIENT_ID and data.get("aud") != GOOGLE_CLIENT_ID:
                    logger.error("Google ID token audience mismatch")
                    return None
                
                return GoogleUserInfo(
                    email=data.get("email", ""),
                    name=data.get("name", data.get("email", "")),
                    picture=data.get("picture"),
                    verified_email=data.get("email_verified", "true") == "true"
                )
                
        except Exception as e:
            logger.error(f"Google ID token validation error: {e}")
            return None
    
    # =========================================================================
    # ACCOUNT LINKING
    # =========================================================================
    
    def link_oauth_account(
        self,
        user_id: int,
        provider: AuthProvider,
        provider_user_id: str
    ) -> Dict[str, Any]:
        """
        Link an OAuth account to an existing user.
        
        Args:
            user_id: Local user ID
            provider: OAuth provider
            provider_user_id: ID from the OAuth provider
            
        Returns:
            Link result
        """
        if user_id not in self._oauth_links:
            self._oauth_links[user_id] = {}
        
        self._oauth_links[user_id][provider.value] = provider_user_id
        
        logger.info(f"🔗 Linked {provider.value} to user {user_id}")
        
        return {
            "success": True,
            "provider": provider.value,
            "message": f"{provider.value} account linked successfully"
        }
    
    def unlink_oauth_account(
        self,
        user_id: int,
        provider: AuthProvider
    ) -> Dict[str, Any]:
        """
        Unlink an OAuth account from a user.
        
        Args:
            user_id: Local user ID
            provider: OAuth provider to unlink
            
        Returns:
            Unlink result
        """
        if user_id in self._oauth_links:
            if provider.value in self._oauth_links[user_id]:
                del self._oauth_links[user_id][provider.value]
                logger.info(f"🔗 Unlinked {provider.value} from user {user_id}")
                return {
                    "success": True,
                    "message": f"{provider.value} account unlinked"
                }
        
        return {
            "success": False,
            "message": f"No {provider.value} account linked"
        }
    
    def get_linked_providers(self, user_id: int) -> Dict[str, bool]:
        """Get linked OAuth providers for a user."""
        links = self._oauth_links.get(user_id, {})
        return {
            "google": "GOOGLE" in links,
            "facebook": "FACEBOOK" in links,
            "github": "GITHUB" in links
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

oauth_service = OAuthService()
