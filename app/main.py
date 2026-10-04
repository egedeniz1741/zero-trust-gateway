from app.database import get_db_connection, init_db, pwd_context, redis_client
from app.security import create_jwt_token, require_role, verify_token
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Zero-Trust Gateway API")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup_event():
    init_db()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/")
def serve_dashboard():
    return FileResponse("static/index.html")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/login")
def login(request: LoginRequest):
    conn = get_db_connection()
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

    token = create_jwt_token(username=user[0], role=user[2])
    return {"access_token": token, "token_type": "bearer"}


@app.post("/logout")
def logout(user_data: dict = Depends(verify_token)):
    jti = user_data.get("jti")
    redis_client.setex(f"blacklist:{jti}", 900, "revoked")
    return {"message": "Successfully logged out and token revoked in Redis"}


@app.get("/vault-data")
def get_secret_vault(user_data: dict = Depends(verify_token)):
    return {
        "message": "Welcome to the Zero-Trust PostgreSQL Vault!",
        "authenticated_user": user_data["sub"],
        "role": user_data["role"],
        "records": ["DB_Engine: PostgreSQL 15", "Session_Store: Redis 7"],
    }


@app.delete("/admin/purge-logs")
def purge_security_logs(user_data: dict = Depends(require_role("admin"))):
    return {
        "status": "CRITICAL: Security logs purged successfully",
        "executed_by": user_data["sub"],
    }