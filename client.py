import socket
import threading
import sys
import json
from consolemenu import prompt_utils, ConsoleMenu, SelectionMenu, Screen
from consolemenu.items import FunctionItem
import criptography


def socket_send(sock: socket.socket, type: str, content):
    data = {"type": type, "content": content}
    raw_data = json.dumps(data, ensure_ascii=False).encode("utf-8")
    raw_data_length = len(raw_data)
    sock.send(raw_data_length.to_bytes(4))
    sock.send(raw_data)


def socket_recv(sock: socket.socket) -> dict:
    raw_data_length = int.from_bytes(sock.recv(4))
    raw_data = sock.recv(raw_data_length)
    data = json.loads(raw_data.decode("utf-8"))
    return data


def send_message(my_sock: socket.socket, my_username):
    """
    Производит отправку сообщения с клиента на сервер

    Параметры:

    my_sock: сокет отправителя
    my_username: адрес отправителя
    """

    global online_users_list

    # запрос список юзеров
    my_sock.send(json.dumps({"text": 'Online'}).encode(encoding='utf-8'))

    # ожидание списка пользователей
    while len(online_users_list) == 0:
        pass

    # выбор клиента для отправки сообщений
    receiver_index = SelectionMenu.get_selection(
        online_users_list, "Send to...")
    if receiver_index >= len(online_users_list):
        notsend_prompt = prompt_utils.PromptUtils(Screen())
        print("[INFO] No message was sent!")
        notsend_prompt.enter_to_continue()
        return

    # Запрос ключа получателя
    my_sock.send(json.dumps({"Get_key": online_users_list[receiver_index]}).encode("utf-8"))

    # ожидание ключа
    while len(receiver_key) == 0:
        pass
    # Создаем проверочный хэш и отправляем его на сервер
    h3 = criptography.hashing_key(receiver_hash).digest()
    my_sock.send(h3)

    # Ожидание ответа от сервера
    while len(answer) == 0:
        pass
    # Формирование структуры отправки сообщений
    data = {"from": my_username,
            "to": online_users_list[receiver_index], "text": ""}

    if answer == "OK":
        data = {"from": my_username, "to": "", "text": ""}
        test_prompt = prompt_utils.PromptUtils(Screen())
        data["to"] = online_users_list[receiver_index]
        data["text"] = test_prompt.input("Text").input_string
        bytes_count = my_sock.send(json.dumps(data).encode(encoding='utf-8'))
        print(f'{bytes_count} bytes sent!')
        test_prompt.enter_to_continue()
    else:
        print("Ошибка! Клиент будет отключен")
        my_sock.send(json.dumps({"text": 'conn_close'}
                                ).encode(encoding='utf-8'))
        listener.join()
        my_sock.close()


def see_messages():
    """
    Выводит список сообщений на экран
    """

    global message_buffer

    test_prompt = prompt_utils.PromptUtils(Screen())
    for i in message_buffer:
        print(f"{i['from']}: {i['text']}\n")
    test_prompt.enter_to_continue()

# Поток прослушки сообщений


def listen_to_server(my_sock: socket.socket):
    """
    Функция потока прослушки сообщений

    Параметры:

    my_sock: сокет конкретного клиента

    """

    global message_buffer, online_users_list, receiver_key, receiver_hash, answer

    # Основной цикл
    while True:

        # Прием сообщения
        incoming = my_sock.recv(2080)

        # Выделение хэша и ключа из сообщения
        if len(incoming) == 2080:
            receiver_key = incoming[:2048]
            receiver_hash = incoming[2048:]

        # Обработка ответа о проверки
        elif incoming.decode(encoding="utf-8") in ["OK", "ERROR"]:
            answer = incoming.decode(encoding="utf-8")

        # Прием списка онлайн-пользователей
        elif isinstance(json.loads(incoming.decode(encoding="utf-8")), list):
            print("[INFO] Got users list!")
            online_users_list = json.loads(
                incoming.decode(encoding="utf-8")).copy()

        # Прием сообщения об отключении
        elif json.loads(incoming.decode(encoding="utf-8"))['text'] == 'conn_close':
            break

        # Прием обычного сообщения
        elif len(incoming) > 0:
            message_buffer.append(json.loads(
                incoming.decode(encoding="utf-8")))
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


# подключение
port, username = int(sys.argv[1]), sys.argv[2]
sock = socket.socket()
sock.connect(('127.0.0.1', port))
username_to_send = username.rjust(20, " ")
sock.send(username_to_send.encode(encoding='utf-8'))

# генерация ключа и отправка его на сервер
private_key, public_key = criptography.key_generate()
public_key_length = len(public_key)
sock.send(public_key_length.to_bytes(4))
hash = criptography.hashing_key(public_key).digest()
sock.send(public_key + hash)

# прием хэша с сервера для проверки
h1 = sock.recv(32)

# проверка хэша ключа
if criptography.is_hash_equal(h1, hash):
    sock.send("OK   ".encode("utf-8"))
else:
    sock.send("ERROR".encode("utf-8"))
    print("Возникла ошибка аутентификации! Пользователь отключен...")
    sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
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
sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
listener.join()
sock.close()
