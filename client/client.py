import socket, json
import zipfile
import os, sys
import time

HOST = 'localhost'  # The server's hostname or IP address
PORT = 10500        # The port used by the server
FORMAT = 'utf-8'
SIZE = 1024
DISCONNECT_MESSAGE = '!DISCONNECT'
image_path = 'boy.jpg'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    image_size = os.stat(image_path).st_size
    image_info = f'{image_path}|{image_size}|'
    s.send(image_info.encode(encoding=FORMAT, errors='ignore'))

    f = open(image_path, 'rb')
    has_sent = 0    # records the number of bytes already sent
    while has_sent < image_size:
        file = f.read()
        s.sendall(file)
        has_sent += len(file)
    f.close()
    print('[SEND] Upload successfully.')
    
    data = s.recv(SIZE)
    result_path, result_size, _ = str(data, FORMAT).split('|') 
    result_size = int(result_size)

    f = open(result_path, 'wb')
    has_receive = 0
    remain_receive = result_size
    while has_receive < result_size:
        data = s.recv(remain_receive)
        if not data: break 
        f.write(data)
        has_receive += len(data)
        remain_receive -= len(data)
    f.close()
    print('[RECEIVE] Receive result successfully.')
