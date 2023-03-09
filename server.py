import socket
import threading
import json


def handle_client(sock: socket.socket, addr):
    global users_list, users_list_lock, message_storage

    username = sock.recv(20).decode(encoding='utf-8')
    print(f'[{username}] joined from {addr}!')
    users_list_lock.acquire()
    users_list[0].append(username)
    users_list[1].append(sock)
    users_list_lock.release()
    
    while True:
        incoming = sock.recv(1024).decode(encoding="utf-8")
        data = json.loads(incoming)
        if data["text"] == 'conn_close':
            sock.send(json.dumps({'text': 'conn_close'}).encode(encoding='utf-8'))
            break
        else:
            #sock.send(b'Echo: ' + data["text"].encode(encoding="utf-8"))
            message_storage_lock.acquire()
            message_storage.append(data)
            message_storage_lock.release()

    users_list_lock.acquire()
    user_index = users_list[0].index(username)
    users_list[0].pop(user_index)
    users_list[1].pop(user_index)
    users_list_lock.release()
    sock.close()


def send_messages():
    global users_list, users_list_lock, message_storage, message_storage_lock, closing_server_flag
    while True:
        if closing_server_flag:
            break
        message_storage_lock.acquire()
        users_list_lock.acquire()
        for msg in message_storage:
                if msg["to"] in users_list[0]:
                    ind = users_list[0].index(msg["to"])
                    receiver_sock = users_list[1][ind]
                    receiver_sock.send(json.dumps(msg).encode(encoding="utf-8"))
                    message_storage.remove(msg)
                    break
        message_storage_lock.release()
        users_list_lock.release()


users_list = [[],[]]
users_list_lock = threading.Lock()
message_storage_lock = threading.Lock()
message_storage = []
config = {}
closing_server_flag = False
with open('server_config.json') as f:
    config = json.load(f)
server_socket = socket.socket()
server_socket.bind((config['address'], config['port'])) # 127.0.0.1:7001
server_socket.listen(10)
print(f"[INFO] Listening on {config['address']}:{config['port']}")
print("[INFO] Press Ctrl+C to close server")
msg_thread = threading.Thread(target=send_messages)
msg_thread.start()
try:
    while True:
        client_socket, client_address = server_socket.accept()
        tmp_thread = threading.Thread(target=handle_client, args=[client_socket, client_address])
        tmp_thread.start()
except KeyboardInterrupt:
    print('Closing server...')
except Exception:
    print('ERROR')
finally:
    closing_server_flag = True
    msg_thread.join()
    server_socket.close()