import socket
import os
from database import init_db, get_db
from dotenv import load_dotenv
from router import Router
from utils import *

load_dotenv()

def parse_request(request_data):
    '''
    This function is used to parse the request data and return the method, path, version, headers, and body
    '''
    lines = request_data.split("\r\n")

    request_line = lines[0]
    parts = request_line.split(" ")
    if len(parts) < 3:
        return None, None, None, {}, ""
    method = parts[0]
    path = parts[1]
    version = parts[2]

    headers = {}
    i = 1
    while i < len(lines) and lines[i] != "":
        line = lines[i]
        colon_index = line.index(":")
        key   = line[:colon_index].strip()
        value = line[colon_index + 1:].strip()
        headers[key] = value
        i += 1

    body = "/r/n".join(lines[i + 1:])

    return method, path, version, headers, body

def make_response(status_code, status_text, body, content_type='text/html; charset=utf-8'):
    response = (
        f'HTTP/1.1 {status_code} {status_text}\r\n'
        f'Content-Type: {content_type}\r\n'
        f'Content-Length: {len(body.encode("utf-8"))}\r\n'
        '\r\n'
        f'{body}'
    )
    return response.encode('utf-8')

def handle_home(method, path, headers, body):
    user = get_session_user(headers)

    if user:
        html = f'''
        <html>
        <body>
            <h1>Welcome back, {user["username"]}!</h1>
            <p><a href="/logout">Log out</a></p>
        </body>
        </html>
        '''
    else:
        html = '''
        <html>
        <body>
            <h1>Welcome to RawBlog</h1>
            <p><a href="/login">Log in</a> or <a href="/register">Register</a></p>
        </body>
        </html>
        '''
    return make_response(200, 'OK', html)

def handle_about(method, path, headers, body):
    html = '''
    <html>
        <body>
            <h1>About OpenDot</h1>
            <p>You can post blogs, read others blogs and like/comment on them.</p>
            <a href="/">Home</a>
        </body>
    </html>
    '''
    return make_response(200, 'OK', html)

def handle_not_found(method, path, headers, body):
    html = '''
    <html>
        <body>
            <h1>404 — Page Not Found</h1>
            <p>The path you requested does not exist.</p>
            <a href="/">Go Home</a>
        </body>
    </html>
    '''
    return make_response(404, 'Not Found', html)

def handle_register(method, path, headers, body):
    if method == 'GET':
        html = '''
        <html>
        <body>
            <h1>Create an Account</h1>
            <form method="POST" action="/register">
                <label>Username:<br>
                    <input type="text" name="username" required>
                </label><br><br>
                <label>Password:<br>
                    <input type="password" name="password" required>
                </label><br><br>
                <button type="submit">Register</button>
            </form>
            <p>Already have an account? <a href="/login">Log in</a></p>
        </body>
        </html>
        '''
        return make_response(200, 'OK', html)

    if method == 'POST':
        params   = parse_form_body(body)
        username = params.get('username', '').strip()
        password = params.get('password', '').strip()

        if not username or not password:
            return make_response(400, 'Bad Request', '<h1>Username and password are required.</h1>')

        hashed = hash_password(password)
        try:
            conn = get_db()
            conn.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, hashed)
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return make_response(400, 'Bad Request', '<h1>Username already taken.</h1>')

        response_body = '<h1>Account created! <a href="/login">Log in</a></h1>'
        return make_response(200, 'OK', response_body)

def handle_login(method, path, headers, body):
    if method == 'GET':
        html = '''
        <html>
        <body>
            <h1>Log In</h1>
            <form method="POST" action="/login">
                <label>Username:<br>
                    <input type="text" name="username" required>
                </label><br><br>
                <label>Password:<br>
                    <input type="password" name="password" required>
                </label><br><br>
                <button type="submit">Log In</button>
            </form>
            <p>No account? <a href="/register">Register</a></p>
        </body>
        </html>
        '''
        return make_response(200, 'OK', html)

    if method == 'POST':
        params   = parse_form_body(body)
        username = params.get('username', '').strip()
        password = params.get('password', '').strip()

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()

        if not user or not verify_password(user['password'], password):
            return make_response(401, 'Unauthorized', '<h1>Invalid username or password.</h1>')

        token = create_session(user['id'])

        response_body = f'<h1>Welcome, {user["username"]}! <a href="/">Go home</a></h1>'
        response = (
            f'HTTP/1.1 302 Found\r\n'
            f'Location: /\r\n'
            f'Set-Cookie: session={token}; HttpOnly; Path=/\r\n'
            f'Content-Length: 0\r\n'
            '\r\n'
        )
        return response.encode('utf-8')

def handle_logout(method, path, headers, body):
    cookie_header = headers.get('Cookie', '')
    token = ''
    for part in cookie_header.split(';'):
        part = part.strip()
        if part.startswith('session='):
            token = part[len('session='):]

    if token:
        conn = get_db()
        conn.execute('DELETE FROM sessions WHERE token = ?', (token,))
        conn.commit()
        conn.close()

    response = (
        'HTTP/1.1 302 Found\r\n'
        'Location: /login\r\n'
        'Set-Cookie: session=; HttpOnly; Path=/; Max-Age=0\r\n'
        'Content-Length: 0\r\n'
        '\r\n'
    )
    return response.encode('utf-8')

IP_ADDR = os.getenv("IP_ADDR", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))

router = Router()
router.register('GET',  '/',         handle_home)
router.register('GET',  '/about',    handle_about)
router.register('GET',  '/register', handle_register)
router.register('POST', '/register', handle_register)
router.register('GET',  '/login',    handle_login)
router.register('POST', '/login',    handle_login)
router.register('GET',  '/logout',   handle_logout)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP_ADDR, PORT))
server_socket.listen(5)

init_db()

print(f"Server is listening on {IP_ADDR}:{PORT}")

while True:
    client_socket, client_address = server_socket.accept()

    request_data = client_socket.recv(4096)
    raw_request  = request_data.decode('utf-8')

    print(raw_request)

    method, path, version, headers, body = parse_request(raw_request)

    print(method, path, version, headers, body)

    if method is None:
        client_socket.close()
        continue

    handler = router.resolve(method, path)

    if handler:
        response = handler(method, path, headers, body)
    else:
        response = handle_not_found(method, path, headers, body)

    client_socket.sendall(response)
    client_socket.close()




