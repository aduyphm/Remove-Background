import socket, json
import zipfile
import os, sys

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
    answer = s.recv(SIZE).decode(FORMAT)

    if answer == "GOT SIZE":
        with open(image_path, 'rb') as f:
            l = f.read()
            s.send(l)
        print('[SEND] Upload successfully.')
    else:
        s.close()
    
    data = s.recv(SIZE).decode(FORMAT)
    splitdata = []
    splitdata = str(data).split('|')
    result_path = splitdata[0]
    result_size = splitdata[1]
    result_size = int(result_size)

    s.send("GOT SIZE".encode(FORMAT))

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
