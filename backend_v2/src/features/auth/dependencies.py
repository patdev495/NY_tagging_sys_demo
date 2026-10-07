
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from src.core import models
from src.core.database import get_db

from .security import decode_access_token


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db)
) -> models.User:
    """Extracts and verifies the current authenticated user from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thiếu token xác thực hoặc định dạng không đúng (Bearer <token>)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(models.User).filter(models.User.username == payload["sub"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if getattr(user, "is_active", 1) != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khóa",
        )
        
    return user

def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Enforces that the authenticated user has the 'admin' role."""
    if str(current_user.role).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quyền truy cập bị từ chối: Thao tác này chỉ dành cho Quản trị viên (Admin)",
        )
    return current_user
