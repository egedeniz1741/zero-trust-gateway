import datetime
import os
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from passlib.context import CryptContext
import psycopg2
from pydantic import BaseModel

app = FastAPI(title="Zero-Trust Gateway API")

JWT_SECRET = os.getenv("JWT_SECRET", "dev_fallback_secret")
DATABASE_URL = os.getenv("DATABASE_URL")
ALGORITHM = "HS256"
ADMIN_USER = os.getenv("INITIAL_ADMIN_USER")
ADMIN_PASSWORD = os.getenv("INITIAL_ADMIN_PASSWORD")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer()


def init_db():
    if not DATABASE_URL or not ADMIN_USER or not ADMIN_PASSWORD:
        return
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(50) PRIMARY KEY,
            hashed_password TEXT NOT NULL,
            role VARCHAR(20) NOT NULL
        );
    """)
    hashed_pw = pwd_context.hash(ADMIN_PASSWORD)
    cur.execute(
        """
        INSERT INTO users (username, hashed_password, role)
        VALUES (%s, %s, %s)
        ON CONFLICT (username) DO NOTHING;
    """,
        (ADMIN_USER, hashed_pw, "admin"),
    )
    conn.commit()
    cur.close()
    conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/login")
def login(request: LoginRequest):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        "SELECT username, hashed_password, role FROM users WHERE username = %s",
        (request.username,),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not pwd_context.verify(request.password, user[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "sub": user[0],
        "role": user[2],
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=15),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    token = credentials.credentials
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or tampered token")


@app.get("/vault-data")
def get_secret_vault(user_data: dict = Depends(verify_token)):
    return {
        "message": "Welcome to the Zero-Trust PostgreSQL Vault!",
        "authenticated_user": user_data["sub"],
        "role": user_data["role"],
        "secret_records": [
            "DB_Engine: PostgreSQL 15",
            "Password_Storage: Bcrypt Hashed",
        ],
    }