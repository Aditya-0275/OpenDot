import socket
import os
import sqlite3
from dotenv import load_dotenv
from router import Router

load_dotenv()

def init_db():
    conn = sqlite3.connect('blog.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password  TEXT    NOT NULL,
            bio       TEXT    DEFAULT '',
            created_at TEXT   DEFAULT (datetime('now'))
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            token      TEXT    NOT NULL UNIQUE,
            created_at TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            title      TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id    INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            content    TEXT    NOT NULL,
            created_at TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id    INTEGER NOT NULL,
            user_id    INTEGER NOT NULL,
            type       TEXT    NOT NULL CHECK (type IN ('like', 'dislike')),
            UNIQUE(post_id, user_id),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS follows (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            follower_id INTEGER NOT NULL,
            followee_id INTEGER NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now')),
            UNIQUE(follower_id, followee_id),
            FOREIGN KEY (follower_id) REFERENCES users(id),
            FOREIGN KEY (followee_id) REFERENCES users(id)
        )
    ''')

    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('blog.db')
    conn.row_factory = sqlite3.Row
    return conn

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
    html = '''
    <html>
        <body>
            <h1>Welcome to OpenDot</h1>
            <p>A blogging platform.</p>
            <a href="/about">About</a>
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

IP_ADDR = os.getenv("IP_ADDR", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))

router = Router()
router.register('GET', '/', handle_home)
router.register('GET', '/about', handle_about)

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




