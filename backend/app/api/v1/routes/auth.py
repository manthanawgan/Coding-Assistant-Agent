import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import User
from app.core.auth.github_oauth import exchange_code_for_token, get_user_info, get_github_oauth_url
from app.core.auth.jwt import create_access_token, get_current_user
from app.api.v1.schemas.auth import TokenResponse, UserResponse, GitHubAuthUrlResponse

router = APIRouter()


@router.get("/login")
async def login():
    state = secrets.token_urlsafe(32)
    auth_url = get_github_oauth_url(state)
    return GitHubAuthUrlResponse(auth_url=auth_url, state=state)


@router.get("/callback")
async def callback(code: str, state: str, db: AsyncSession = Depends(get_db)):
    try:
        token_data = await exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")

        user_info = await get_user_info(access_token)

        result = await db.execute(
            select(User).where(User.github_id == user_info["github_id"])
        )
        user = result.scalar_one_or_none()

        if user:
            user.github_access_token = access_token
            await db.commit()
        else:
            user = User(
                github_id=user_info["github_id"],
                github_login=user_info["github_login"],
                github_avatar_url=user_info.get("github_avatar_url"),
                github_access_token=access_token,
                email=user_info.get("email"),
                name=user_info.get("name"),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        jwt_token = create_access_token(str(user.id))
        return TokenResponse(access_token=jwt_token, user=UserResponse.model_validate(user))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}
