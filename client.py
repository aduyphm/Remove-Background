import socket, json

HOST = 'localhost'  # The server's hostname or IP address
PORT = 10500        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    msg = {}
    msg['url'] = 'images/boy.jpg' # image's url
    msg['act'] = 'detect'
    data_string = json.dumps(msg)
    s.sendall(data_string.encode())
    data = s.recv(1024)
    data = json.loads(data.decode())
    url = data.get('url')

print('Received', url)