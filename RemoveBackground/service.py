from inference import *
import socket
import json
import os, sys
import zipfile
import time

HOST = 'localhost'  # Standard loopback interface address (localhost)
PORT = 10500        # Port to listen on (non-privileged ports are > 1023)
SIZE = 1024
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = '!DISCONNECT'

print("[STARTING] Server is starting.")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("[LISTENING] Server is listening.")

    conn, addr = s.accept()
    print(f"[NEW CONNECTION] {addr} connected.")

    data = conn.recv(SIZE).decode(FORMAT, errors='ignore')
    splitdata = []
    splitdata = str(data).split('|') 
    image_path = splitdata[0]
    image_size = splitdata[1]
    image_size = int(image_size)

    f = open(image_path, 'wb')
    has_receive = 0
    remain_receive = image_size
    while has_receive < image_size:
        data = conn.recv(remain_receive)
        if not data: break 
        f.write(data)
        has_receive += len(data)
        remain_receive -= len(data)
    f.close()
    print('[RECEIVE] Receive image successfully.')

    if not os.path.exists(image_path):
        print('Cannot find input path: {}'.format(image_path))
        exit()

    msg = geturl(image_path)
    result_path = msg['url']
    result_size = os.stat(result_path).st_size

    result_info = f'{result_path}|{result_size}|'
    conn.send(result_info.encode(FORMAT))

    f = open(result_path, 'rb')
    has_sent = 0
    while has_sent < result_size:
        file = f.read(SIZE)
        conn.sendall(file)
        has_sent += len(file)
    f.close()
    print('[SEND] Send result successfully.')

    os.remove(image_path)
