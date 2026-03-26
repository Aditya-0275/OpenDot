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

def parse_form_body(body):
    params = {}
    if not body:
        return params
    for part in body.split('&'):
        if '=' in part:
            key, value = part.split('=', 1)
            params[urllib.parse.unquote_plus(key)] = urllib.parse.unquote_plus(value)
    return params

def render_layout(content, current_user=None):
    username = current_user['username'] if current_user else None
    
    if username:
        nav = f'''
        <nav>
            <a href="/">Home</a> |
            <a href="/post/new">New Post</a> |
            <a href="/profile/{username}">My Profile</a> |
            <a href="/logout">Log out ({username})</a>
        </nav>
        '''
    else:
        nav = '''
        <nav>
            <a href="/">Home</a> |
            <a href="/login">Log in</a> |
            <a href="/register">Register</a>
        </nav>
        '''

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>RawBlog</title>
        <style>
            body    {{ font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
            nav     {{ margin-bottom: 30px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }}
            nav a   {{ margin-right: 12px; text-decoration: none; color: #333; }}
            nav a:hover {{ text-decoration: underline; }}
            .post   {{ border-bottom: 1px solid #eee; padding: 20px 0; }}
            .post h2 {{ margin: 0 0 6px 0; }}
            .meta   {{ color: #888; font-size: 0.85em; margin-bottom: 10px; }}
            textarea {{ width: 100%; height: 200px; }}
            input[type=text], input[type=password] {{ width: 100%; padding: 6px; margin-top: 4px; }}
            button  {{ margin-top: 10px; padding: 8px 16px; cursor: pointer; }}
        </style>
    </head>
    <body>
        {nav}
        {content}
    </body>
    </html>
    '''