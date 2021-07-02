import socket
import json
import os
from InstanceSegmentation import run
from RemoveBackground import inference

HOST = 'localhost'  # Standard loopback interface address (localhost)
PORT = 10500        # Port to listen on (non-privileged ports are > 1023)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("I'm listening")
    conn, addr = s.accept()
    print('Connected by', addr)
    while True:
        data = conn.recv(1024)
        if not data:
            break
        data = json.loads(data.decode())
        url = data.get('url')
        act = data.get('act')
        if not os.path.exists(url):
            print('Cannot find input path: {0}'.format(url))
            exit()
        if act == 'detect':
            # Gọi function instance segmentation
            msg = run.geturl(url)
        elif act == 'remove-bg':
            # Gọi function remove background
            msg = inference.geturl(url)
        else: 
            # Thông báo lỗi
            print('No suitable action')
            exit()

        data_string = json.dumps(msg)
        conn.sendall(data_string.encode())