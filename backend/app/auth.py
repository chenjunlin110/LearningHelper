from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import settings

ALGORITHM = "HS256"
security = HTTPBearer()


class TokenPayload(dict):
    sub: str
    exp: int


def create_access_token(subject: str, expires_minutes: Optional[int] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes or settings.jwt_expire_min)
    to_encode = {"sub": subject, "exp": int(expire.timestamp())}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=ALGORITHM)


async def get_current_subject(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    try:
        payload: TokenPayload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])  # type: ignore
        return payload["sub"]
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
