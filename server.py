import socket
import threading
import json
import criptography


def handle_client(sock: socket.socket, addr: tuple):
    """
    Осуществяет подключение клиентов и обмен ключами между ними

    Параметры: 

    sock: сокет клиента
    addr: IP адрес и порт клиента

    """
    global online_users_list, online_users_list_lock, message_storage

    # Приём имени при подключении клиента
    username = sock.recv(20).decode(encoding='utf-8').strip()
    print(f'[{username}] joined from {addr}!')

    # ожидание приема ключа с клиента и вытягивание хэша с сообщения
    key_length = int.from_bytes(sock.recv(4))
    data = sock.recv(key_length + 32)
    key = data[:key_length]
    hash = data[key_length:]

    # Создание проверочного хэша и отправка его на клиент для проверки
    h1 = criptography.hashing_key(hash).digest()
    sock.send(h1)

    # Ожидание сигнала-результата проверки
    answer = sock.recv(5).decode("utf-8")
    if answer == "OK   ":

        # добавление пользователя в список онлайн пользователей
        online_users_list_lock.acquire()
        online_users_list[0].append(username)
        online_users_list[1].append(sock)
        online_users_list[2].append(key)
        online_users_list_lock.release()

    # Основной цикл
    while True:

        # Прием сообщения с клиента
        imcoming_message = sock.recv(1024).decode(encoding="utf-8")
        data_of_message = json.loads(imcoming_message)

        # Обработка запроса ключа клиента
        if "Get_key" in data_of_message.keys():

            current_user_index = online_users_list[0].index(
                data_of_message["Get_key"])
            print(online_users_list[current_user_index])
            hash_key = criptography.hashing_key(
                online_users_list[2][current_user_index]).digest()
            sock.send(online_users_list[2][current_user_index] + hash_key)

            # Приём проверочного хэша с клиента
            h3 = sock.recv(32)

            # Создание проверочного хэша
            h4 = hash_key

            # Проверка и отправка сигнала
            if criptography.is_hash_equal(h3, h4):
                sock.send("OK".encode("utf-8"))
            else:
                sock.send("ERROR".encode("utf-8"))
        
        # Обработка запроса списка онлайн-пользователей
        elif data_of_message["text"] == 'Online':
            print(f"[INFO] Sent users list: {online_users_list[0]}")
            sock.send(json.dumps(online_users_list[0]).encode('utf-8'))

         # Обработка запроса отключения клиента
        elif data_of_message["text"] == 'conn_close':
            sock.send(json.dumps({'text': 'conn_close'}
                                 ).encode(encoding='utf-8'))
            break

        # Добавление сообщения в буфер
        else:
            print(f"[INFO] Got new message {data_of_message}")
            message_storage_lock.acquire()
            message_storage.append(data_of_message)
            message_storage_lock.release()

    # Удаление отключенного клиента
    online_users_list_lock.acquire()
    user_index = online_users_list[0].index(username)
    online_users_list[0].pop(user_index)
    online_users_list[1].pop(user_index)
    online_users_list[2].pop(user_index)
    online_users_list_lock.release()
    sock.close()


def send_messages():
    """
    Рассылает сообщение из буфера в отдельном потоке
    """

    global online_users_list, online_users_list_lock, message_storage, message_storage_lock, closing_server_flag

    # Основной цикл отправки сообщений
    while True:
        if closing_server_flag:
            break
        message_storage_lock.acquire()
        online_users_list_lock.acquire()

        # отправка сообщений из буфера message_storage
        for msg in message_storage:
            print(f"[INFO] Sending message {msg}")
            if msg["to"] in online_users_list[0]:
                ind = online_users_list[0].index(msg["to"])
                receiver_sock = online_users_list[1][ind]
                receiver_sock.send(json.dumps(msg).encode(encoding="utf-8"))
                message_storage.remove(msg)
                break
        message_storage_lock.release()
        online_users_list_lock.release()


# список онлайн пользователей
online_users_list = [[], [], []]

# блокирование логов
online_users_list_lock = threading.Lock()
message_storage_lock = threading.Lock()

# буфер сообщений
message_storage = []

# адрес и порт сервера
config = {}

# отключение рассыльщика
closing_server_flag = False

# выгрузка параметров сервера 
with open('server_config.json') as f:
    config = json.load(f)

# создание сокета для подключений
server_socket = socket.socket()
server_socket.bind((config['address'], config['port']))  # 127.0.0.1:7001
server_socket.listen(10)
print(f"[INFO] Listening on {config['address']}:{config['port']}")
print("[INFO] Press Ctrl+C to close server")

# создание потока
msg_thread = threading.Thread(target=send_messages)
msg_thread.start()

# основной цикл
try:
    while True:
        # принимаем клиентов
        client_socket, client_address = server_socket.accept()

        # Вызываем обработчик клиента для каждого клиента
        tmp_thread = threading.Thread(target=handle_client, args=[
                                      client_socket, client_address])
        tmp_thread.start()
except KeyboardInterrupt:
    print('Closing server...')
except Exception:
    print('ERROR')
finally:
    closing_server_flag = True
    msg_thread.join()
    server_socket.close()
