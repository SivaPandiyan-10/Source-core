from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
from auth_db import create_user, verify_user, store_refresh_token, validate_refresh_token

SECRET_KEY = os.getenv('JWT_SECRET', 'change-me-in-prod')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    return payload


def register_demo_user():
    # create a demo user if not present
    create_user('demo', 'demo')


def validate_refresh(token: str) -> bool:
    return validate_refresh_token(token)
