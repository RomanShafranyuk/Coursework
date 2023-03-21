import socket
import threading
import json
import criptography

# осуществяет подключение клиентов и обмен ключами между ними
def handle_client(sock: socket.socket, addr):
    global users_list, users_list_lock, message_storage

    username = sock.recv(20).decode(encoding='utf-8').strip()
    print(f'[{username}] joined from {addr}!')
    #ожидание приема ключа с клиента и вытягивание хэша с сообщения
    data = sock.recv(2080)
    key = data[:2048]
    hash = data[2048:]
    print(hash)
    #Создание проверочного хэша и отправка его на клиент для проверки
    h1 = criptography.hashing_key(hash).digest()
    sock.send(h1)
    #Ожидание сигнала-результата проверки 
    check = sock.recv(5).decode("utf-8")
    if check == "OK   ":
        #отправка списка онлайн пользователей с ключами клиенту
        users_list_lock.acquire()
        users_list[0].append(username)
        users_list[1].append(sock)
        users_list[2].append(key)
        users_list_lock.release()
    


       # sock.send(json.dumps(users_list[0]).encode(encoding='utf-8'))


    #     h3 = sock.recv(32)
    #     h4 = criptography.hashing_key(h1)
    #     if criptography.is_hash_equal(h3,h4):
    #         sock.send("OK".encode("utf-8"))
    #     else:
    #         sock.send("ERROR".encode("utf-8"))
    #         sock.send(json.dumps({'text': 'conn_close'}).encode(encoding='utf-8'))

    # else:
    #     sock.send(json.dumps({'text': 'conn_close'}).encode(encoding='utf-8'))

    
    
    while True:
        incoming = sock.recv(1024).decode(encoding="utf-8")
        data = json.loads(incoming)
        if data["text"] == 'Online':
            print(f"[INFO] Sent users list: {users_list[0]}")
            sock.send(json.dumps(users_list[0]).encode('utf-8'))
        #Обработка запроса ключа
        elif "Get_key" in data.keys():
            #Находим индекс ключа нужного пользователя
            key_index = users_list.index(data["Get_key"])
            hash_key = criptography.hashing_key(users_list[2][key_index].encode("utf-8")).digest()
            sock.send(json.dumps({'key': users_list[2][key_index] + hash_key}).encode("utf-8")) 
            #Принимаем проверочный хэш с клиента
            h_client = sock.recv(32)
            #Создаем проверочный хэш
            h_check = criptography.hashing_key(hash_key).digest()
            #Проверка и отправка сигнала
            if criptography.is_hash_equal(h_client, h_check):
                sock.send("OK".encode("utf-8"))
            else:
                sock.send("ERROR")
        elif data["text"] == 'conn_close':
            sock.send(json.dumps({'text': 'conn_close'}).encode(encoding='utf-8'))
            break
        else:
            #sock.send(b'Echo: ' + data["text"].encode(encoding="utf-8"))
            print(f"[INFO] Got new message {data}")
            message_storage_lock.acquire()
            message_storage.append(data)
            message_storage_lock.release()

    users_list_lock.acquire()
    user_index = users_list[0].index(username)
    users_list[0].pop(user_index)
    users_list[1].pop(user_index)
    users_list_lock.release()
    sock.close()

# Рассылает сообщение из буфера в отдельном потоке
def send_messages():
    global users_list, users_list_lock, message_storage, message_storage_lock, closing_server_flag
    while True:
        if closing_server_flag:
            break
        message_storage_lock.acquire()
        users_list_lock.acquire()

        #отправка сообщений из буфера message_storage
        for msg in message_storage:
                print(f"[INFO] Sending message {msg}")
                if msg["to"] in users_list[0]:
                    ind = users_list[0].index(msg["to"])
                    receiver_sock = users_list[1][ind]
                    receiver_sock.send(json.dumps(msg).encode(encoding="utf-8"))
                    message_storage.remove(msg)
                    break
        message_storage_lock.release()
        users_list_lock.release()

#список онлайн пользователей
users_list = [[],[], []]
# блокирование логов 
users_list_lock = threading.Lock()
message_storage_lock = threading.Lock()
# буфер сообщений
message_storage = []
# адрес и порт сервера
config = {}
# отключение рассыльщика
closing_server_flag = False


with open('server_config.json') as f:
    config = json.load(f)
# создание сокета для подключений 
server_socket = socket.socket()
server_socket.bind((config['address'], config['port'])) # 127.0.0.1:7001
server_socket.listen(10)
print(f"[INFO] Listening on {config['address']}:{config['port']}")
print("[INFO] Press Ctrl+C to close server")
# создание потока 
msg_thread = threading.Thread(target=send_messages)
msg_thread.start()
# основной цикл
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