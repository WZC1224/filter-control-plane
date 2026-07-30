from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from config import settings


class JWTAuth:
    def create_token(self, user_id: int, username: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        payload = {'user_id': user_id, 'username': username, 'exp': expire}
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    def verify(self, raw_header: str) -> tuple[bool, dict | str]:
        if not raw_header:
            return False, 'missing token'
        token = raw_header
        if token.lower().startswith('bearer '):
            token = token[7:]
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return True, payload
        except JWTError:
            return False, 'invalid or expired token'


jwt_auth = JWTAuth()
