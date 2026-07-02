"""Email/password auth API routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.config import settings
from backend.app.deps.auth import COOKIE_NAME, get_current_user
from backend.app.models.user import LoginRequest, SignupRequest, UserResponse
from backend.app.services import auth_service
from backend.app.services.user_store import create_user, get_user_by_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.jwt_expire_minutes * 60,
        path="/",
    )


def _clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest, response: Response) -> UserResponse:
    if get_user_by_email(body.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        user_id = create_user(body.email, auth_service.hash_password(body.password))
        token = auth_service.create_access_token(user_id, body.email.lower().strip())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    _set_auth_cookie(response, token)
    return UserResponse(id=user_id, email=body.email.lower().strip())


@router.post("/login", response_model=UserResponse)
def login(body: LoginRequest, response: Response) -> UserResponse:
    user = get_user_by_email(body.email)
    if not user or not auth_service.verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    try:
        token = auth_service.create_access_token(user["id"], user["email"])
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    _set_auth_cookie(response, token)
    return UserResponse(id=user["id"], email=user["email"])


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    _clear_auth_cookie(response)


@router.get("/me", response_model=UserResponse)
def me(current_user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user["id"], email=current_user["email"])
