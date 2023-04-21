import socket
import threading
import json
import criptography
from socketmessage import *
import logging


def handle_client(sock: socket.socket, addr: tuple):
    """
    Осуществяет подключение клиентов и обмен ключами между ними

    Параметры: 

    sock: сокет клиента
    addr: IP адрес и порт клиента

    """
    global online_users_list, online_users_list_lock, message_storage

    # Приём имени при подключении клиента
    _, username_raw = socket_recv(sock)
    username = username_raw.decode('utf-8')
    logging.info(f"({username}) joined from ({addr})!")

    # ожидание приема ключа с клиента и вытягивание хэша с сообщения
    header, data = socket_recv(sock)
    key_length = int(header[1])
    key = data[:key_length]
    hash = data[key_length:]

    # Создание проверочного хэша и отправка его на клиент для проверки
    h1 = criptography.hashing_key(hash).digest()
    socket_send(sock, "hashhash", h1)

    # Ожидание сигнала-результата проверки
    header, _ = socket_recv(sock)
    if header[0] == "OK":
        # добавление пользователя в список онлайн пользователей
        online_users_list_lock.acquire()
        online_users_list[0].append(username)
        online_users_list[1].append(sock)
        online_users_list[2].append(key)
        online_users_list_lock.release()
    elif header[0] == "ERROR":
        logging.error(f'Ошибка аутентификации пользователя ({username})!')
        socket_send(sock, "SHUTDOWN")
        sock.close()
        return

    # Основной цикл
    while True:

        # Прием сообщения с клиента
        header, data = socket_recv(sock)

        # Обработка запроса ключа клиента
        if header[0] == "getkey":
            user_to_find = data.decode('utf-8')
            current_user_index = online_users_list[0].index(user_to_find)
            hash_key = criptography.hashing_key(online_users_list[2][current_user_index]).digest()
            user_key = online_users_list[2][current_user_index]
            # sock.send(online_users_list[2][current_user_index] + hash_key)
            socket_send(sock, f"keyhash;{len(user_key)}", user_key + hash_key)

            # Приём проверочного хэша с клиента
            _, h3 = socket_recv(sock)

            # Создание проверочного хэша
            h4 = hash_key

            # Проверка и отправка сигнала
            if criptography.is_hash_equal(h3, h4):
                socket_send(sock, "OK")
            else:
                socket_send(sock, "ERROR")
                logging.error(f'Ошибка аутентификации пользователя ({username})!')

        
        # Обработка запроса списка онлайн-пользователей
        elif header[0] == "online":
            logging.info(f"Sent users list: {online_users_list[0]}")
            socket_send(sock, "onlineusers", json.dumps(online_users_list[0]).encode('utf-8'))

         # Обработка запроса отключения клиента
        elif header[0] == "SHUTDOWN":
            logging.info(f"Disconnecting ({username})...")
            socket_send(sock, "SHUTDOWN")
            break

        # Добавление сообщения в буфер
        else:
            logging.info(f"New message from ({username})!")
            data_json = json.loads(data.decode('utf-8'))
            message_storage_lock.acquire()
            message_storage.append(data_json)
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
            logging.info(f"Sending message ({msg})!")
            if msg["to"] in online_users_list[0]:
                ind = online_users_list[0].index(msg["to"])
                receiver_sock = online_users_list[1][ind]
                # receiver_sock.send(json.dumps(msg).encode(encoding="utf-8"))
                socket_send(receiver_sock, "message", json.dumps(msg).encode("utf-8"))
                message_storage.remove(msg)
                break
        message_storage_lock.release()
        online_users_list_lock.release()


# список онлайн пользователей
# username, socket, public key
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


# начало программы
# выгрузка параметров сервера 
with open('server_config.json') as f:
    config = json.load(f)

# создание сокета для подключений
server_socket = socket.socket()
server_socket.bind((config['address'], config['port']))  # 127.0.0.1:7001
server_socket.listen(10)
print(f"[INFO] Listening on {config['address']}:{config['port']}")

# создание потока рассыльщика
msg_thread = threading.Thread(target=send_messages)
msg_thread.start()

logging.basicConfig(format='[%(levelname)s] %(funcName)s:%(message)s', level=logging.INFO)
# основной цикл
try:
    while True:
        # принимаем клиентов
        client_socket, client_address = server_socket.accept()

        # Вызываем обработчик клиента для каждого клиента
        tmp_thread = threading.Thread(target=handle_client, args=[client_socket, client_address])
        tmp_thread.start()
except KeyboardInterrupt:
    logging.info('KeyboardInterrupt, closing server...')
except Exception as ex:
    logging.exception(f"Caugth exception: {ex}")
finally:
    logging.info("Finally closing server...")
    closing_server_flag = True
    msg_thread.join()
    server_socket.close()
