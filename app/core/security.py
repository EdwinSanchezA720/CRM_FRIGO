"""
Utilidades de seguridad: hash de contraseñas y JWT (JSON Web Tokens).

Java equivalent: PasswordEncoder + JwtUtil (Spring Security)

¿Qué es un JWT?
    Es una cadena de texto firmada que el servidor entrega al hacer login.
    El cliente la guarda y la envía en cada request como:
        Authorization: Bearer eyJhbGci...

    El servidor puede leer el JWT y saber quién es el usuario SIN consultar la BD,
    porque la firma garantiza que el token es auténtico y no fue modificado.

    Estructura del JWT: header.payload.signature
    El payload contiene: user_id, email, rol, tenant_id, exp (expiración)
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings


def hash_password(plain_password: str) -> str:
    """
    Convierte una contraseña en texto plano a un hash seguro con bcrypt.
    Ejemplo: "Admin123!" → "$2b$12$XaB3kL...hash..."

    El hash NO es reversible — no se puede recuperar la contraseña original.
    gensalt() genera un salt aleatorio — por eso cada llamada produce un hash distinto.
    bcrypt es lento a propósito para dificultar ataques de fuerza bruta.
    """
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compara la contraseña ingresada contra el hash guardado en la BD.
    Retorna True si coinciden, False si no.
    """
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict) -> str:
    """
    Crea un JWT firmado con los datos del usuario.
    Java equivalent: jwtUtil.generateToken(userDetails)

    El token expira en ACCESS_TOKEN_EXPIRE_MINUTES minutos (ver config.py).
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Lee y verifica un JWT. Retorna el payload (datos del usuario) si es válido.
    Retorna None si el token es inválido, fue modificado, o ya expiró.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
