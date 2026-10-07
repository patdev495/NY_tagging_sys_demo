import logging

from sqlalchemy.orm import Session

from src.core import models

from .security import hash_password, verify_password

logger = logging.getLogger("AuthService")

DEFAULT_USERS = [
    {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "full_name": "System Administrator",
    },
    {
        "username": "qa",
        "password": "qa123",
        "role": "qa",
        "full_name": "Quality Assurance",
    },
]

def seed_default_users(db: Session):
    """Seeds default admin and qa user accounts if they do not exist."""
    for user_info in DEFAULT_USERS:
        existing = db.query(models.User).filter(models.User.username == user_info["username"]).first()
        if not existing:
            user = models.User(
                username=user_info["username"],
                password_hash=hash_password(user_info["password"]),
                role=user_info["role"],
                full_name=user_info["full_name"],
                is_active=1,
            )
            db.add(user)
            logger.info(f"Seeded default user '{user_info['username']}' with role '{user_info['role']}'.")
    db.commit()

def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
    """Verifies credentials and returns the active User object if valid, else None."""
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    if getattr(user, "is_active", 1) != 1:
        return None
    if not verify_password(password, str(user.password_hash)):
        return None
    return user

def get_user_by_username(db: Session, username: str) -> models.User | None:
    """Finds user by username."""
    return db.query(models.User).filter(models.User.username == username).first()
