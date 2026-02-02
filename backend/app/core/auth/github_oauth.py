import httpx
from app.config.settings import settings
from app.config.logging import logger


async def exchange_code_for_token(code: str) -> dict:
    url = "https://github.com/login/oauth/access_token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()


async def get_user_info(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    async with httpx.AsyncClient() as client:
        user_response = await client.get("https://api.github.com/user", headers=headers)
        user_response.raise_for_status()
        user_data = user_response.json()

        email_response = await client.get("https://api.github.com/user/emails", headers=headers)
        email_response.raise_for_status()
        emails = email_response.json()
        primary_email = next((e["email"] for e in emails if e["primary"]), None)

        return {
            "github_id": user_data["id"],
            "github_login": user_data["login"],
            "github_avatar_url": user_data.get("avatar_url"),
            "email": primary_email,
            "name": user_data.get("name"),
        }


def get_github_oauth_url(state: str) -> str:
    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": settings.GITHUB_CALLBACK_URL,
        "scope": settings.GITHUB_SCOPES,
        "state": state,
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://github.com/login/oauth/authorize?{query_string}"
