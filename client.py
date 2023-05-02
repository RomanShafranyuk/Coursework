import socket
import threading
import argparse
import json
from consolemenu import prompt_utils, ConsoleMenu, SelectionMenu, Screen
from consolemenu.items import FunctionItem
import criptography
from socketmessage import *


def send_message(my_sock: socket.socket, my_username):
    """
    Производит отправку сообщения с клиента на сервер

    Параметры:

    my_sock: сокет отправителя
    my_username: адрес отправителя
    """

    global online_users_list, receiver_key

    # запрос списка онлайн пользователей
    socket_send(my_sock, "online")

    # ожидание списка пользователей
    while len(online_users_list) == 0:
        pass

    # выбор клиента для отправки сообщений, или отмена отправки
    receiver_index = SelectionMenu.get_selection(online_users_list, "Send to...")
    if receiver_index >= len(online_users_list):
        notsend_prompt = prompt_utils.PromptUtils(Screen())
        print("[INFO] No message was sent!")
        notsend_prompt.enter_to_continue()
        return

    # Запрос ключа получателя
    socket_send(my_sock, "getkey", online_users_list[receiver_index].encode('utf-8'))

    # ожидание ключа получателя
    while len(receiver_key) == 0:
        pass

    # Создаем проверочный хэш и отправляем его на сервер
    h3 = criptography.hashing_key(receiver_hash).digest()
    socket_send(my_sock, "h3", h3)

    # Ожидание ответа от сервера
    while len(answer) == 0:
        pass


    if answer == "OK":
        test_prompt = prompt_utils.PromptUtils(Screen())
        # шифрование RSA
        enc_message = criptography.encrypt_message(test_prompt.input("Text").input_string.encode("utf-8"), receiver_key)
        socket_send(my_sock, f"message;{my_username};{online_users_list[receiver_index]}", enc_message)
        print(enc_message)
        test_prompt.enter_to_continue()
    else:
        print("Ошибка! Отключение клиента...")
        socket_send(my_sock, "SHUTDOWN")
        listener.join()
        my_sock.close()


def see_messages():
    """
    Выводит список сообщений на экран
    """

    global message_buffer

    test_prompt = prompt_utils.PromptUtils(Screen())
    print(message_buffer)
    for i in message_buffer:
        print(f"{i['from']}: {i['text']}\n")
    test_prompt.enter_to_continue()


def listen_to_server(my_sock: socket.socket):
    """
    Функция потока прослушки сообщений

    Параметры:

    my_sock: сокет конкретного клиента

    """

    global message_buffer, online_users_list, receiver_key, receiver_hash, answer, private_key

    # Основной цикл
    while True:

        # Прием сообщения
        headers, data = socket_recv(my_sock)
        

        # Выделение хэша и ключа из сообщения
        if headers[0] == "keyhash":
            key_len = int(headers[1])
            receiver_key = data[:key_len]
            receiver_hash = data[key_len:]

        # Обработка ответа о проверки
        elif headers[0] in ["OK", "ERROR"]:
            answer = headers[0]

        # Прием списка онлайн-пользователей
        elif headers[0] == "onlineusers":
            print("[INFO] Got users list!")
            online_users_list = json.loads(data.decode("utf-8"))

        # Прием сообщения об отключении
        elif headers[0] == "SHUTDOWN":
            break

        # Прием обычного сообщения
        elif headers[0] == "message":
            with open("test.bin", "wb") as f:
                f.write(data)
            if headers[1] != "server":
                confirm, data = criptography.decrypt_message(data, private_key)
                
                if not confirm:
                    socket_send(sock, "ping")
                    answer, _ = socket_recv(sock)
                    if answer[0] != "pong":
                        socket_send(sock, "SHUTDOWN")
                    
            message_buffer.append({"from":headers[1], "to": headers[2], "text": data.decode("utf-8")})

        
        
        else:
            break


# буфер сообщений конкретного клиента
message_buffer = []

# список пользователей, которым можно отправить сообщение
online_users_list = []

# принятые ключ и хэш
receiver_key = bytes()
receiver_hash = bytes()

# ответ проверки хэшей
answer = ""

# начало программы
parser = argparse.ArgumentParser(description="Chat client")
parser.add_argument('username')
parser.add_argument('-p', dest='port', type=int, default=7001, required=False)
args = parser.parse_args()

# подключение
username, port = args.username, args.port
print(f"Connecting as '{username}' to '127.0.0.1:{port}'...")
sock = socket.socket()
sock.connect(('127.0.0.1', port))
socket_send(sock, "username", username.encode('utf-8'))

# генерация ключа и отправка его на сервер
private_key, public_key = criptography.key_generate()
pr_len, pu_len = len(private_key), len(public_key)
hash = criptography.hashing_key(public_key).digest()
hash_len = len(hash)
socket_send(sock, f"publickeyhash;{pu_len}", public_key + hash)

# прием хэша с сервера для проверки
_, h1 = socket_recv(sock)

# проверка хэша ключа
if criptography.is_hash_equal(h1, hash):
    socket_send(sock, "OK")
else:
    socket_send(sock, "ERROR")
    print("Возникла ошибка аутентификации! Отключение от сервера...")
    socket_send(sock, "SHUTDOWN")
    sock.close()
    exit(0)

# Создание потока прослушивания сообщений
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()

# Создание консольного меню
menu = ConsoleMenu(f"Secure chat client [{username}]")
item1 = FunctionItem("Send new message", send_message, [sock, username])
item2 = FunctionItem("List incoming messages", see_messages)
menu.append_item(item1)
menu.append_item(item2)
menu.show()

# Отключение
print("Exit routine...")
socket_send(sock, "SHUTDOWN")
listener.join()
sock.close()
# закрыть порт надо именно, не просто закрыть сокет
