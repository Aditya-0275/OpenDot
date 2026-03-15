import hashlib
import urllib.parse
import os
from database import get_db

def hash_password(password):
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex()+ ":" + key.hex()

def verify_password(stored_password, provided_password):
    salt_hex, key_hex = stored_password.split(':')
    salt = bytes.fromhex(salt_hex)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode('utf-8'),
        salt,
        100000
    )
    return key.hex() == key_hex

def create_session(user_id):
    token = os.urandom(32).hex()
    conn = get_db()
    conn.execute("INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user_id, token))
    conn.commit()
    conn.close()
    return token

def get_session_user(headers):
    cookie_header = headers.get("Cookie", "")
    if not cookie_header:
        return None
    
    cookies = {}
    for cookie in cookie_header.split(";"):
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            cookies[key.strip()] = value.strip()

    token = cookies.get("session")
    if not token:
        return None

    conn = get_db()
    user = conn.execute(
        "SELECT users.* FROM users JOIN sessions ON users.id = sessions.user_id WHERE sessions.token = ?",
        (token,)
    ).fetchone()
    conn.close()
    return user
