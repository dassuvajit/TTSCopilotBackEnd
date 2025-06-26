import os
import supabase
from jose import jwt, JWTError
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_supabase():
    return supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=ALGORITHM)

def decode_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])

def get_user_by_username(client, username):
    res = client.table("users").select("*").eq("username", username).single().execute()
    return res.data if res.data else None

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        client = get_supabase()
        user = get_user_by_username(client, username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Token decode failed")

def get_user_version(client):
    res = client.table("app_versions").select("*").order("id", desc=True).limit(1).execute()
    return res.data[0] if res.data else None


def generate_signed_url(client, file_path, bucket="exe-files", expiry_seconds=5):
    res = client.storage.from_(bucket).create_signed_url(file_path, expiry_seconds)

    if res and "signedURL" in res:
        return res["signedURL"]
    else:
        raise HTTPException(status_code=500, detail=f"Failed to generate signed URL: {res}")

from cryptography.fernet import Fernet
import os

FERNET_KEY = os.getenv("FERNET_KEY")  # Put this in .env file securely
fernet = Fernet(FERNET_KEY)

def encrypt_url(url: str) -> str:
    return fernet.encrypt(url.encode()).decode()

