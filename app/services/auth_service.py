"""Business logic related to authentication."""

from __future__ import annotations

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, InvalidCredentialsError, UserAlreadyExistsError
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserCreate, UserLogin


class AuthService:
    """Handle user registration, authentication, and lookup by token subject."""

    def __init__(self, user_repository: UserRepository, settings: Settings) -> None:
        """Initialize the service with its dependencies."""

        self._user_repository = user_repository
        self._settings = settings

    async def register_user(self, payload: UserCreate) -> UserModel:
        """Register a new user after validating uniqueness."""

        existing_user = await self._user_repository.find_by_username(payload.username)
        if existing_user is not None:
            raise UserAlreadyExistsError()

        return await self._user_repository.create_user(
            username=payload.username,
            hashed_password=hash_password(payload.password.get_secret_value()),
        )

    async def authenticate_user(self, payload: UserLogin) -> str:
        """Validate user credentials and issue a JWT access token."""

        user = await self._user_repository.find_by_username(payload.username)
        if user is None:
            raise InvalidCredentialsError()

        password = payload.password.get_secret_value()
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        return create_access_token(subject=user.id, settings=self._settings)

    async def get_user_by_id(self, user_id: str) -> UserModel:
        """Return a user by ID or raise if the user cannot be found."""

        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise AuthenticationError()
        return user

