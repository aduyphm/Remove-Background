import socket, json
import zipfile
import os, sys
import time

HOST = 'localhost'  # The server's hostname or IP address
PORT = 10400        # The port used by the server
FORMAT = "utf-8"
SIZE = 1024
zip_name = 'main.zip'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    image_name = 'boy.jpg'

    with zipfile.ZipFile(zip_name, 'w') as f:
        f.write(image_name)
        print(f'[SENDING] Image is being sent.')

    s.send(image_name.encode())
    s.send(zip_name.encode())

    file = open(zip_name, 'rb')
    l = file.read()
    s.sendall(l)

    file.close()
    os.remove(zip_name)

    imgname = s.recv(SIZE).decode()
    filename = s.recv(SIZE).decode()
    print(f"[RECEIVING] Receiving the filename.")
    file = open(filename, "wb")
    l = s.recv(SIZE)
    
    while l:
        file.write(l)
        l = s.recv(SIZE)
    
    file.close()

    with zipfile.ZipFile(filename, 'r') as f:
        print(f"[EXTRACTING] Extracting all file in zip.")
        f.extractall()
    os.remove(filename)

# print('Received', url)
