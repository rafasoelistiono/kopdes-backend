from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.database import execute_dashboard_query, execute_write, get_dashboard_connection
from app.core.security import hash_password, verify_password, generate_token, hash_token, token_expires_at

router = APIRouter()
security_scheme = HTTPBearer()


class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    token: str | None = None
    user: dict | None = None
    message: str | None = None


def _ensure_tables():
    with get_dashboard_connection() as conn:
        is_sqlite = conn.dialect.name == "sqlite"
    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
    now_default = "datetime('now')" if is_sqlite else "CURRENT_TIMESTAMP"
    execute_write(f"""
        CREATE TABLE IF NOT EXISTS group9_users (
            id {id_type},
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT ({now_default})
        )
    """)
    execute_write(f"""
        CREATE TABLE IF NOT EXISTS group9_sessions (
            id {id_type},
            user_id INTEGER NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT ({now_default}),
            expires_at TEXT NOT NULL
        )
    """)


def _get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    _ensure_tables()
    raw_token = credentials.credentials
    th = hash_token(raw_token)
    rows = execute_dashboard_query(
        "SELECT u.id, u.username, u.name FROM group9_sessions s "
        "JOIN group9_users u ON u.id = s.user_id "
        "WHERE s.token_hash = :th AND s.expires_at > :now",
        {"th": th, "now": datetime.now(timezone.utc).isoformat()},
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return rows[0]


@router.post("/auth/register")
def register(body: RegisterRequest):
    _ensure_tables()
    existing = execute_dashboard_query(
        "SELECT id FROM group9_users WHERE username = :u", {"u": body.username}
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    pw_hash = hash_password(body.password)
    execute_write(
        "INSERT INTO group9_users (username, password_hash, name) VALUES (:u, :p, :n)",
        {"u": body.username, "p": pw_hash, "n": body.name},
    )
    return {"success": True, "message": "User registered"}


@router.post("/auth/login")
def login(body: LoginRequest):
    _ensure_tables()
    rows = execute_dashboard_query(
        "SELECT id, username, name, password_hash FROM group9_users WHERE username = :u",
        {"u": body.username},
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user = rows[0]
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = generate_token()
    th = hash_token(token)
    expires = token_expires_at()
    execute_write(
        "INSERT INTO group9_sessions (user_id, token_hash, expires_at) VALUES (:uid, :th, :exp)",
        {"uid": user["id"], "th": th, "exp": expires},
    )
    return AuthResponse(
        success=True,
        token=token,
        user={"id": user["id"], "username": user["username"], "name": user["name"]},
    )


@router.post("/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    th = hash_token(credentials.credentials)
    execute_write("DELETE FROM group9_sessions WHERE token_hash = :th", {"th": th})
    return {"success": True, "message": "Logged out"}


@router.get("/auth/me")
def me(current_user: dict = Depends(_get_current_user)):
    return {"success": True, "user": current_user}
