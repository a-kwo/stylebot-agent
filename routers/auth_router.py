import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db
from auth import hash_password, verify_password, create_access_token
from models import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db=Depends(get_db)):
    if len(req.username.strip()) < 3:
        raise HTTPException(400, "Username must be at least 3 characters")
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (req.username.strip(), hash_password(req.password)),
        )
        db.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Username already taken")

    db.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
    db.commit()

    return TokenResponse(access_token=create_access_token(user_id))


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db=Depends(get_db)):
    row = db.execute(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (req.username.strip(),),
    ).fetchone()

    if row is None or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    return TokenResponse(access_token=create_access_token(row["id"]))
