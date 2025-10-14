from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "CHANGE_THIS_TO_A_STRONG_SECRET"  # ⚠️ Đổi trước khi đưa lên production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Token có hạn 1 ngày

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    """Kiểm tra mật khẩu người dùng nhập với mật khẩu đã hash."""
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    """Tạo mật khẩu được hash để
