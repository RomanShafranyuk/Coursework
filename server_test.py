import socket
import threading
import json


def handle_client(sock: socket.socket, addr):
    global users_list, users_list_lock

    username = sock.recv(20).decode(encoding='utf-8')
    print(f'[{username}] joined from {addr}!')
    users_list_lock.acquire()
    users_list.append([username, sock])
    users_list_lock.release()

    while True:
        data = sock.recv(1024)
        if data.decode(encoding='utf-8') == 'conn_close':
            break
        else:
            sock.send(b'Echo: ' + data)
    
    users_list_lock.acquire()
    for i in range(len(users_list)):
        if users_list[i][0] == username:
            users_list.pop(i)
            break
    users_list_lock.release()
    sock.close()


users_list = []
users_list_lock = threading.Lock()

config = {}
with open('server_config.json') as f:
    config = json.load(f)
server_socket = socket.socket()
server_socket.bind((config['address'], config['port'])) # 127.0.0.1:7001
server_socket.listen(10)
print(f"[INFO] Listening on {config['address']}:{config['port']}")
while True:
    client_socket, client_address = server_socket.accept()
    tmp_thread = threading.Thread(target=handle_client, args=[client_socket, client_address])
    tmp_thread.start()
    # tmp_thread.join()
    # break
server_socket.close()