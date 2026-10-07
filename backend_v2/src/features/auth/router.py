from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db

from . import dependencies, schemas, security, service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=schemas.LoginResponse)
def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Đăng nhập hệ thống, trả về Token và vai trò (Admin / QA)."""
    user = service.authenticate_user(db, request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không chính xác",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = {
        "sub": str(user.username),
        "user_id": int(user.id),
        "role": str(user.role),
    }
    # Token valid for 24 hours
    token = security.create_access_token(token_data, expires_delta_seconds=86400)
    
    return schemas.LoginResponse(
        access_token=token,
        token_type="bearer",
        user=schemas.UserResponse.model_validate(user),
    )

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user_profile(current_user: models.User = Depends(dependencies.get_current_user)):
    """Lấy thông tin tài khoản và vai trò của người dùng hiện tại."""
    return schemas.UserResponse.model_validate(current_user)
