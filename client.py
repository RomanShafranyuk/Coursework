import socket
import threading
import sys
import json
from consolemenu import prompt_utils, ConsoleMenu, SelectionMenu, Screen
from consolemenu.items import FunctionItem
import criptography

message_buffer = []


def send_message(sock: socket.socket, my_username):
    sock.send(json.dumps({"text": 'Online'}).encode(encoding='utf-8'))
    users_list = json.loads(sock.recv(1024).decode("utf-8"))
    user_index = SelectionMenu.get_selection(users_list, "Send to...", show_exit_option=False)
    #Запрос ключа получателя
    sock.send(json.dumps({"Get_key": users_list[user_index]}))
    #Принимаем ключ и хэш ключа
    sock.recv(2080)
    key = data[:2048]
    hash = data[2048:]
    #Создаем проверочный хэш и отправляем его на сервер
    h_check = criptography.hashing_key(hash)
    sock.send(h_check)
    #ожидание сигнала
    answer = sock.recv(10).decode("utf-8")
    if answer == "OK":
        data = {"from": my_username, "to":"", "text": ""}
        test_prompt = prompt_utils.PromptUtils(Screen())
        data["to"] = users_list[user_index]
        data["text"] = test_prompt.input("Text").input_string
        bytes_count = sock.send(json.dumps(data).encode(encoding='utf-8'))
        print(f'{bytes_count} bytes sent!')
        test_prompt.enter_to_continue()
    else:
        print("Ошибка! Клиент будет отключен")
        sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
        listener.join()
        sock.close()

def see_messages():
    global message_buffer
    test_prompt = prompt_utils.PromptUtils(Screen())
    for i in message_buffer:
        print(f"{i['from']}: {i['text']}\n")
    test_prompt.enter_to_continue()


def listen_to_server(conn: socket.socket):
    global message_buffer
    while True:
        incoming = conn.recv(1024).decode(encoding='utf-8')
        data = json.loads(incoming)
        if data['text'] == 'conn_close':
            break
        elif len(data) > 0:
            message_buffer.append(data)
        else:
            break

#подключение
port, username = int(sys.argv[1]), sys.argv[2]
sock = socket.socket()
sock.connect(('127.0.0.1', port))
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()
sock.send(username.encode(encoding='utf-8'))
#генерация ключа и отправка его на сервер
public_key = criptography.key_generate()
hash = criptography.hashing_key(public_key)
sock.send(public_key.encode("utf-8") + hash)
#прием хэша с сервера для проверки 
h1 = sock.recv(32)
#проверка хэша ключа
h2 = criptography.hashing_key(h1)
if criptography.is_hash_equal(h1,h2):
    sock.send("OK".encode("utf-8"))
else:
    sock.send("ERROR".encode("utf-8"))
    print("Возникла ошибка аутентификации! Пользователь отключен...")
    sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
    listener.join()
    sock.close()
    exit(0)
menu = ConsoleMenu(f"Secure chat client [{username}]")
item1 = FunctionItem("Send new message", send_message, [sock, username])
item2 = FunctionItem("List incoming messages", see_messages)
menu.append_item(item1)
menu.append_item(item2)
menu.show()

print("Exit routine...")
sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
listener.join()
sock.close()

# while True:
#     data = {"from" : "", "to" : "", "text" : ""}
#     data["from"] = username
#     data["to"] = input("Send to: ")
#     data["text"] = input('>>> ')
    
#     if data["text"] == '/exit':
#         print('Closing program...')
#         sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
#         listener.join()
#         sock.close()
#         break
#     bytes_count = sock.send(json.dumps(data).encode(encoding='utf-8'))
#     print(f'{bytes_count} bytes sent!')
