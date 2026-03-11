import socket
import os
from dotenv import load_dotenv

load_dotenv()

"""
At the very start the server is just a program that listens for incoming network connections.
"""

def parse_request(request_data):
    '''
    This function is used to parse the request data and return the method, path, version, headers, and body
    '''
    lines = request_data.split("\r\n")

    # Request line
    request_line = lines[0]
    parts = request_line.split(" ")
    method = parts[0]
    path = parts[1]
    version = parts[2]

    # Headers
    headers = {}
    i = 1
    while i < len(lines) and lines[i] != "":
        line = lines[i]
        colon_index = line.index(":")
        key   = line[:colon_index].strip()
        value = line[colon_index + 1:].strip()
        headers[key] = value
        i += 1

    # Body
    body = "/r/n".join(lines[i + 1:])

    return method, path, version, headers, body

IP_ADDR = os.getenv("IP_ADDR", "0.0.0.0")
PORT = int(os.getenv("PORT", 8080))

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((IP_ADDR, PORT))
server_socket.listen(5)

print(f"Server is listening on {IP_ADDR}:{PORT}")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Connection from {client_address}")
    
    request_data = client_socket.recv(4096)
    raw_request = request_data.decode("utf-8")

    method, path, version, headers, body = parse_request(raw_request)

    print(f"Method: {method}")
    print(f"Path: {path}")
    print(f"Version: {version}")
    print(f"Headers: {headers}")
    print(f"Body: {body}")
    print("-----")

    response_body = "<h1>Hello from raw TCP server</h1><p>No framework used, just bytes.</p>"

    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        f"Content-Length: {len(response_body.encode('utf-8'))}\r\n"
        "\r\n"
        f"{response_body}"
    )

    client_socket.sendall(response.encode("utf-8"))
    client_socket.close()

"""
The server needs to handle connections **forever** — not just once. 
This infinite loop means: 
After handling one connection, go back and wait for the next one. 
Every real server runs a loop like this at its core.
"""


