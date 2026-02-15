"""OAuth2 SSO provider configurations — Google, Microsoft, GitHub."""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from app.config import settings

oauth = OAuth()

# ── Google ──
if settings.GOOGLE_CLIENT_ID:
    oauth.register(
        name="google",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# ── Microsoft ──
if settings.MICROSOFT_CLIENT_ID:
    oauth.register(
        name="microsoft",
        client_id=settings.MICROSOFT_CLIENT_ID,
        client_secret=settings.MICROSOFT_CLIENT_SECRET,
        server_metadata_url=f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/v2.0/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

# ── GitHub ──
if settings.GITHUB_CLIENT_ID:
    oauth.register(
        name="github",
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        authorize_url="https://github.com/login/oauth/authorize",
        access_token_url="https://github.com/login/oauth/access_token",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )
