from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    id: str
    email: str
    role: str = "user"

class AuthProvider:
    """
    Abstract Auth Provider to allow switching between Supabase, Keycloak, etc.
    Current implementation is a stub.
    """
    
    async def get_user(self, token: str) -> Optional[User]:
        # Mock validation
        if token == "valid-token":
            return User(id="123", email="user@example.com")
        return None

    async def login(self, email: str, password: str) -> Optional[str]:
        # Mock login
        if email == "user@example.com" and password == "password":
            return "valid-token"
        return None

auth_provider = AuthProvider()
