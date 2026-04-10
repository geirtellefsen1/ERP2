import httpx
import os
from datetime import datetime, timedelta, timezone


class Auth0Client:
    def __init__(self):
        self.domain = os.getenv("AUTH0_DOMAIN", "")
        self.client_id = os.getenv("AUTH0_CLIENT_ID", "")
        self.client_secret = os.getenv("AUTH0_CLIENT_SECRET", "")
        self.api_audience = os.getenv("AUTH0_API_AUDIENCE", "")
        self._access_token = None
        self._token_expiry = None

    def get_access_token(self) -> str:
        """Get M2M access token from Auth0."""
        if self._access_token and self._token_expiry and self._token_expiry > datetime.now(timezone.utc):
            return self._access_token

        url = f"https://{self.domain}/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "audience": self.api_audience,
            "grant_type": "client_credentials",
        }

        response = httpx.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 60)

        return self._access_token

    def get_user_by_email(self, email: str):
        """Get user details from Auth0 Management API."""
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        url = f"https://{self.domain}/api/v2/users-by-email?email={email}"
        response = httpx.get(url, headers=headers)

        if response.status_code == 200:
            users = response.json()
            return users[0] if users else None
        return None

    def create_user(self, email: str, password: str, user_metadata: dict = None):
        """Create user in Auth0."""
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "email": email,
            "password": password,
            "connection": "Username-Password-Authentication",
            "user_metadata": user_metadata or {},
            "email_verified": False,
        }

        url = f"https://{self.domain}/api/v2/users"
        response = httpx.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
