from passlib.context import CryptContext
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from fastapi import  HTTPException
from app.models.user_model import  TokenData
from jose import jwt
import httpx


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 10


def get_secret_from_kong(consumer_id: str) -> str:
    with httpx.Client() as client:
        print(f'consumer_id: {consumer_id}')
        url = f"http://kong:8001/consumers/{consumer_id}/jwt"
        response = client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Failed to fetch secret from Kong")
        kong_data = response.json()
        print(f'Kong Data: {kong_data}')
        if not kong_data['data'][0]["secret"]:
            raise HTTPException(
                status_code=404, detail="No JWT credentials found for the specified consumer")

        secret = kong_data['data'][0]["secret"]
        print(f'Secret: {secret}')
        return secret


def create_jwt_token(data: dict, secret: str):
    to_encode = data.copy()
    expire = datetime.utcnow() + \
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Limit expiration time to 2038-01-19 03:14:07 UTC
    expire = min(expire, datetime(2038, 1, 19, 3, 14, 7))
    to_encode.update({"exp": expire})
    headers = {
        "typ": "JWT",
        "alg": ALGORITHM
    }
    encoded_jwt = jwt.encode(to_encode, secret,
                             algorithm=ALGORITHM, headers=headers)
    return encoded_jwt


