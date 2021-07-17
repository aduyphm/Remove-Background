from main import *
import socket
import json
import os, sys
import zipfile

HOST = 'localhost'  # Standard loopback interface address (localhost)
PORT = 10500        # Port to listen on (non-privileged ports are > 1023)
SIZE = 1024
FORMAT = "utf-8"
zip_name = "main.zip"

print("[STARTING] Server is starting.")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("[LISTENING] Server is listening.")

    conn, addr = s.accept()
    print(f"[NEW CONNECTION] {addr} connected.")

    imagename = conn.recv(SIZE).decode(FORMAT)
    filename = conn.recv(SIZE).decode(FORMAT)
    print(f"[RECEIVING] Receiving the filename.")
    file = open(filename, "wb")
    l = conn.recv(SIZE)
    
    while l:
        file.write(l)
        l = conn.recv(SIZE)
    
    file.close()

    with zipfile.ZipFile(filename, 'r') as f:
        print(f"[EXTRACTING] Extracting all file in zip.")
        f.extractall()
    os.remove(filename)

    if not os.path.exists(imagename):
        print('Cannot find input path: {0}'.format(imagename))
        exit()

    msg = geturl(imagename)
    data_string = json.dumps(msg)
    with zipfile.ZipFile(zip_name, 'w') as f:
        f.write(msg['url'])
        print(f'[SENDING] Result is being sent.')

    conn.sendall(data_string.encode(FORMAT))
    conn.send(zip_name.encode(FORMAT)) 

    file = open(zip_name, 'rb')
    l = file.read()
    conn.sendall(l)

    file.close()
    os.remove(zip_name)

    conn.close()
