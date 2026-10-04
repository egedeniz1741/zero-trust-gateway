import datetime
import uuid
from app.config import ALGORITHM, JWT_SECRET
from app.database import redis_client
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

security_scheme = HTTPBearer()


def create_jwt_token(username: str, role: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=15),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
):
    token = credentials.credentials
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        jti = decoded.get("jti")

        
        if jti and redis_client.get(f"blacklist:{jti}"):
            raise HTTPException(
                status_code=401, detail="Token has been revoked (Logged out)"
            )

        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or tampered token")


def require_role(required_role: str):
    def role_checker(user_data: dict = Depends(verify_token)):
        if user_data.get("role") != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Requires '{required_role}' role",
            )
        return user_data

    return role_checker