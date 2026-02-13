"""Authentication module using Supabase."""

from datetime import datetime, timedelta
from typing import Optional
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from supabase import create_client, Client
from pydantic import BaseModel

from .config import get_settings
from .database import create_user, create_portfolio, get_user_portfolio, get_user_by_email

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

settings = get_settings()
security = HTTPBearer()

# Supabase client (optional for temp deployments)
supabase: Optional[Client] = None
if not settings.supabase_url.startswith("https://placeholder"):
    supabase = create_client(settings.supabase_url, settings.supabase_key)


# Models
class UserSignup(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


class TokenData(BaseModel):
    user_id: str
    email: str


# Password helper functions
def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# Authentication functions
async def signup_user(email: str, password: str) -> Token:
    """
    Sign up new user with email confirmation.

    Args:
        email: User email
        password: User password

    Returns:
        Token with access credentials
    """
    # Use Supabase if configured
    if supabase is not None:
        try:
            # Sign up with Supabase (sends confirmation email)
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create user"
                )

            user_id = response.user.id

            # Create user record in our database
            await create_user(user_id, email)

            # Create initial portfolio
            await create_portfolio(user_id, settings.default_starting_balance)

            # Create access token
            access_token = create_access_token(
                data={"sub": user_id, "email": email}
            )

            return Token(
                access_token=access_token,
                user_id=user_id,
                email=email
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signup failed: {str(e)}"
            )

    # Fallback to local database auth
    else:
        try:
            # Check if user already exists
            existing_user = await get_user_by_email(email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )

            # Generate user ID
            user_id = str(uuid.uuid4())

            # Hash password
            password_hash = hash_password(password)

            # Create user record in database
            await create_user(user_id, email, password_hash)

            # Create initial portfolio
            await create_portfolio(user_id, settings.default_starting_balance)

            # Create access token
            access_token = create_access_token(
                data={"sub": user_id, "email": email}
            )

            return Token(
                access_token=access_token,
                user_id=user_id,
                email=email
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signup failed: {str(e)}"
            )


async def login_user(email: str, password: str) -> Token:
    """
    Login user.

    Args:
        email: User email
        password: User password

    Returns:
        Token with access credentials
    """
    # Use Supabase if configured
    if supabase is not None:
        try:
            # Login with Supabase
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            user_id = response.user.id

            # Ensure portfolio exists
            portfolio = await get_user_portfolio(user_id)
            if not portfolio:
                await create_portfolio(user_id, settings.default_starting_balance)

            # Create access token
            access_token = create_access_token(
                data={"sub": user_id, "email": email}
            )

            return Token(
                access_token=access_token,
                user_id=user_id,
                email=email
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(e)}"
            )

    # Fallback to local database auth
    else:
        try:
            # Get user from database
            user = await get_user_by_email(email)
            if not user or not user.password_hash:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            # Verify password
            if not verify_password(password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid credentials"
                )

            user_id = user.id

            # Ensure portfolio exists
            portfolio = await get_user_portfolio(user_id)
            if not portfolio:
                await create_portfolio(user_id, settings.default_starting_balance)

            # Create access token
            access_token = create_access_token(
                data={"sub": user_id, "email": email}
            )

            return Token(
                access_token=access_token,
                user_id=user_id,
                email=email
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Login failed: {str(e)}"
            )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token

    Returns:
        TokenData with user information
    """
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")

        if user_id is None or email is None:
            raise credentials_exception

        return TokenData(user_id=user_id, email=email)

    except JWTError:
        raise credentials_exception


async def verify_email_token(token: str) -> bool:
    """
    Verify email confirmation token.

    Args:
        token: Email verification token

    Returns:
        True if verified successfully
    """
    if supabase is None:
        return False

    try:
        response = supabase.auth.verify_otp({
            "token": token,
            "type": "email"
        })
        return response.user is not None
    except Exception:
        return False
