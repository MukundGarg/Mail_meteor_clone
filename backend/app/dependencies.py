from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import User
from .security import read_session


async def current_user(
    mm_session: str | None = Cookie(default=None), db: AsyncSession = Depends(get_db)
) -> User:
    user_id = read_session(mm_session)
    user = await db.get(User, user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="Connect your Google account to continue")
    return user

