import socket
import threading
import argparse
import json
from consolemenu import prompt_utils, ConsoleMenu, SelectionMenu, Screen
from consolemenu.items import FunctionItem
import criptography
from socketmessage import *
from datetime import datetime

from time import sleep
import subprocess
import playsound


def close_port():
    command = f"netsh interface set interface \"Беспроводная сеть\" disable"
    subprocess.call(command, shell=True)


def open_port():
    command = f"netsh interface set interface \"Беспроводная сеть\" enable"
    subprocess.call(command, shell=True)


def check_timetable(server_address, username):
    global sock, listener, timetable_shutdown, exit_flag

    # загрузить расписание
    with open(f"timetable_{username}.json") as f:
        tt_data = json.load(f)
    
    pause_len = tt_data['pause_len']
    table = tt_data['data']

    # цикл проверки
    while True:
        if exit_flag:
            break

        # проверка времени
        current_time = datetime.now()
        for time in table:
            if current_time.hour == time[0] and current_time.minute == time[1]:
                timetable_shutdown = True
        
        if timetable_shutdown:
            print(f"\nЗапланированное отключение от сервера на {pause_len} минут...")
            socket_send(sock, "ping")
            listener.join()
            sock.close()
            close_port()

            sleep(pause_len * 60)
            open_port()
            sleep(5)
            print("Подключаемся обратно к серверу...")
            sock = socket.socket()
            connect_to_server(username, server_address[0], server_address[1])
            listener = threading.Thread(target=listen_to_server, args=[sock])
            listener.start()
            timetable_shutdown = False
            print("Для продолжения работы нажмите клавишу [Enter]...")


# def send_message(my_sock: socket.socket, my_username):
def send_message(my_username):
    """
    Производит отправку сообщения с клиента на сервер

    Параметры:

    my_sock: сокет отправителя
    my_username: адрес отправителя
    """

    global online_users_list, receiver_key, sock

    print("запрос списка онлайн пользователей")
    # запрос списка онлайн пользователей
    socket_send(sock, "online")

    # ожидание списка пользователей
    while len(online_users_list) == 0:
        pass

    # выбор клиента для отправки сообщений, или отмена отправки
    while True:
        try:
            receiver_index = SelectionMenu.get_selection(online_users_list, "Send to...")
            break
        except KeyboardInterrupt:
            test_prompt = prompt_utils.PromptUtils(Screen())
            print("Не нажимайте сочетание клавиш [Ctrl+C]!")
            playsound.playsound("sound_ctrlc.mp3", True)
            test_prompt.enter_to_continue()

    if receiver_index >= len(online_users_list):
        notsend_prompt = prompt_utils.PromptUtils(Screen())
        print("[INFO] No message was sent!")
        notsend_prompt.enter_to_continue()
        return

    # Запрос ключа получателя
    socket_send(sock, "getkey", online_users_list[receiver_index].encode('utf-8'))

    # ожидание ключа получателя
    while len(receiver_key) == 0:
        pass

    # Создаем проверочный хэш и отправляем его на сервер
    h3 = criptography.hashing_key(receiver_hash).digest()
    socket_send(sock, "h3", h3)

    # Ожидание ответа от сервера
    while len(answer) == 0:
        pass


    if answer == "OK":
        test_prompt = prompt_utils.PromptUtils(Screen())
        while True:
            try:
                message_input = test_prompt.input("Text").input_string
                break
            except KeyboardInterrupt:
                test_prompt = prompt_utils.PromptUtils(Screen())
                print("Не нажимайте сочетание клавиш [Ctrl+C]!")
                playsound.playsound("sound_ctrlc.mp3", True)
                test_prompt.enter_to_continue()
        # шифрование RSA
        enc_message = criptography.encrypt_message(message_input.encode("utf-8"), receiver_key)
        socket_send(sock, f"message;{my_username};{online_users_list[receiver_index]}", enc_message)
        # print(enc_message)
        test_prompt.enter_to_continue()
    else:
        print("Ошибка! Отключение клиента...")
        socket_send(sock, "SHUTDOWN")
        listener.join()
        sock.close()


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

    global message_buffer, online_users_list, receiver_key, receiver_hash, answer, private_key, timetable_shutdown

    # Основной цикл
    while True:

        # Прием сообщения
        headers, data = socket_recv(my_sock)

        if timetable_shutdown:
            break
        
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
            # print("[INFO] Got users list!")
            online_users_list = json.loads(data.decode("utf-8"))

        elif headers[0] == "ping":
            socket_send(sock, "pong")

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


def connect_to_server(username, address, port):
    global sock, private_key, public_key

    sock.connect((address, port))
    socket_send(sock, "username", username.encode('utf-8'))

    # генерация ключа и отправка его на сервер
    private_key, public_key = criptography.key_generate()
    pr_len, pu_len = len(private_key), len(public_key)
    hash = criptography.hashing_key(public_key).digest()
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


timetable_shutdown = False
exit_flag = False

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
parser.add_argument('-a', dest='address', type=str, default="127.0.0.1", required=False)
args = parser.parse_args()

# подключение
username, address, port = args.username, args.address, args.port
sock = socket.socket()
print("Подключение к серверу...")
connect_to_server(username, address, port)
# Создание потока прослушивания сообщений
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()

timetable_monitor = threading.Thread(target=check_timetable, args=[(address, port), username])
timetable_monitor.start()

print(f"Добро пожаловать, '{username}'!")
playsound.playsound("sound_login.mp3", True)
# Создание консольного меню
menu = ConsoleMenu(f"Secure chat client [{username}]")
item1 = FunctionItem("Send new message", send_message, [username])
item2 = FunctionItem("List incoming messages", see_messages)
menu.append_item(item1)
menu.append_item(item2)
while True:
    try:
        menu.show()
        break
    except KeyboardInterrupt:
        test_prompt = prompt_utils.PromptUtils(Screen())
        print("Не нажимайте сочетание клавиш [Ctrl+C]!")
        playsound.playsound("sound_ctrlc.mp3", True)
        test_prompt.enter_to_continue()

# Отключение
print("Exit routine...")
playsound.playsound("sound_logoff.mp3", True)
exit_flag = True
socket_send(sock, "SHUTDOWN")
listener.join()
timetable_monitor.join()
sock.close()
