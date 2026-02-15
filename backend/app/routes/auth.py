"""Auth routes — login, register, SSO, and token refresh."""

from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import RedirectResponse

from app.auth.oauth_providers import oauth
from app.auth.service import AuthService
from app.config import settings
from app.models.schemas import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])
_auth_service = AuthService()


# ── Email / Password ──

@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest):
    return await _auth_service.register(body.email, body.name, body.password)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    return await _auth_service.login(body.email, body.password)


# ── Google SSO ──

@router.get("/sso/google")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/sso/google/callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo") or await oauth.google.userinfo(token=token)
    result = await _auth_service.sso_login(
        provider="google",
        provider_user_id=str(user_info["sub"]),
        email=user_info["email"],
        name=user_info.get("name", user_info["email"]),
        avatar_url=user_info.get("picture"),
    )
    # Redirect to frontend with token in query params
    return RedirectResponse(
        url=f"http://localhost:3000/auth/callback?token={result['access_token']}&refresh={result['refresh_token']}"
    )


# ── Microsoft SSO ──

@router.get("/sso/microsoft")
async def microsoft_login(request: Request):
    redirect_uri = settings.MICROSOFT_REDIRECT_URI
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)


@router.get("/sso/microsoft/callback")
async def microsoft_callback(request: Request):
    token = await oauth.microsoft.authorize_access_token(request)
    user_info = token.get("userinfo") or await oauth.microsoft.userinfo(token=token)
    result = await _auth_service.sso_login(
        provider="microsoft",
        provider_user_id=str(user_info.get("sub", user_info.get("oid"))),
        email=user_info["email"],
        name=user_info.get("name", user_info["email"]),
    )
    return RedirectResponse(
        url=f"http://localhost:3000/auth/callback?token={result['access_token']}&refresh={result['refresh_token']}"
    )


# ── GitHub SSO ──

@router.get("/sso/github")
async def github_login(request: Request):
    redirect_uri = settings.GITHUB_REDIRECT_URI
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/sso/github/callback")
async def github_callback(request: Request):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)
    user_info = resp.json()
    # GitHub may not expose email publicly
    email = user_info.get("email")
    if not email:
        emails_resp = await oauth.github.get("user/emails", token=token)
        emails = emails_resp.json()
        primary = next((e for e in emails if e.get("primary")), emails[0])
        email = primary["email"]

    result = await _auth_service.sso_login(
        provider="github",
        provider_user_id=str(user_info["id"]),
        email=email,
        name=user_info.get("name") or user_info.get("login", email),
        avatar_url=user_info.get("avatar_url"),
    )
    return RedirectResponse(
        url=f"http://localhost:3000/auth/callback?token={result['access_token']}&refresh={result['refresh_token']}"
    )
