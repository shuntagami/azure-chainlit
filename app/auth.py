import os
import json
import uuid
from authlib.integrations.starlette_client import OAuth
from fastapi import Request, Response, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer

from database import get_db, User

# OAuth setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# Serializer for creating secure tokens
serializer = URLSafeTimedSerializer(os.getenv("SECRET_KEY", "default-secret-key"))

# Authentication functions
def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get the current authenticated user from the session"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    return user

def require_auth(request: Request, db: Session = Depends(get_db)):
    """Middleware to require authentication"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# User management functions
def get_or_create_user(db: Session, email: str, user_info: dict):
    """Get an existing user or create a new one"""
    user = db.query(User).filter(User.identifier == email).first()

    if not user:
        user = User(
            id=uuid.uuid4(),
            identifier=email,
            metadata={
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "email": email,
                "provider": "google"
            }
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user

# Add authentication routes to FastAPI app
def setup_auth_routes(app):
    """Setup authentication routes for the FastAPI app"""
    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SECRET_KEY", "default-secret-key")
    )

    # Login route
    @app.get("/auth/login")
    async def login(request: Request):
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
        return await oauth.google.authorize_redirect(request, redirect_uri)

    # Callback route
    @app.get("/auth/google/callback")
    async def auth_callback(request: Request, db: Session = Depends(get_db)):
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info or not user_info.get("email"):
            return RedirectResponse(url="/auth/login")

        # Get or create user
        email = user_info["email"]
        user = get_or_create_user(db, email, user_info)

        # Set user in session
        request.session["user_id"] = str(user.id)

        # Redirect to home
        return RedirectResponse(url="/")

    # Logout route
    @app.get("/auth/logout")
    async def logout(request: Request):
        request.session.pop("user_id", None)
        return RedirectResponse(url="/")

    # User info route
    @app.get("/api/user")
    async def user_info(request: Request, db: Session = Depends(get_db)):
        user = get_current_user(request, db)
        if not user:
            return {"authenticated": False}

        return {
            "authenticated": True,
            "user": {
                "id": str(user.id),
                "email": user.identifier,
                "name": user.metadata.get("name"),
                "picture": user.metadata.get("picture")
            }
        }
