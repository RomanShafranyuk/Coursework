import socket
import threading
import sys
import json
from consolemenu import prompt_utils, ConsoleMenu, SelectionMenu, Screen
from consolemenu.items import FunctionItem
import criptography

message_buffer = []
users_list = []
user_key = bytes()
user_hash = bytes()
check_result = ""

def send_message(sock: socket.socket, my_username):
    global users_list
    # запрашиваем список юзеров
    sock.send(json.dumps({"text": 'Online'}).encode(encoding='utf-8'))
    # ждем
    while len(users_list) == 0:
        pass
    # users_list = json.loads(sock.recv(1024).decode("utf-8"))
    user_index = SelectionMenu.get_selection(users_list, "Send to...")
    if user_index >= len(users_list):
        notsend_prompt = prompt_utils.PromptUtils(Screen())
        print("[INFO] No message was sent!")
        notsend_prompt.enter_to_continue()
        return
    #Запрос ключа получателя
    sock.send(json.dumps({"Get_key": users_list[user_index]}))
    # ждем ключа
    while len(user_key) == 0:
        pass
    #Создаем проверочный хэш и отправляем его на сервер
    h_check = criptography.hashing_key(hash).digest()
    sock.send(h_check)
    while len(check_result) == 0:
        pass

    data = {"from": my_username, "to": users_list[user_index], "text": ""}
    if check_result == "OK":
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
    global message_buffer, users_list, user_key, user_hash, check_result
    while True:
        incoming = conn.recv(2080)
        # data = json.loads(incoming)
        if len(incoming) == 2080:
            user_key = incoming[:2048]
            user_hash = incoming[2048:]
        elif incoming.decode(encoding="utf-8") in ["OK", "ERROR"]:
            check_result = incoming.decode(encoding="utf-8")
        elif isinstance(json.loads(incoming.decode(encoding="utf-8")), list):
            print("[INFO] Got users list!")
            users_list = json.loads(incoming.decode(encoding="utf-8")).copy()
        elif json.loads(incoming.decode(encoding="utf-8"))['text'] == 'conn_close':
            break
        elif len(incoming) > 0:
            message_buffer.append(json.loads(incoming.decode(encoding="utf-8")))
        else:
            break
#подключение
port, username = int(sys.argv[1]), sys.argv[2]
sock = socket.socket()
sock.connect(('127.0.0.1', port))
username_to_send = username.rjust(20, " ")
sock.send(username_to_send.encode(encoding='utf-8'))




#генерация ключа и отправка его на сервер
public_key = criptography.key_generate()
hash = criptography.hashing_key(public_key.encode("utf-8")).digest()
print(hash)
sock.send(public_key.encode("utf-8") + hash)



#прием хэша с сервера для проверки 
h1 = sock.recv(32)
#проверка хэша ключа
if criptography.is_hash_equal(h1,hash):
    sock.send("OK   ".encode("utf-8"))
else:
    sock.send("ERROR".encode("utf-8"))
    print("Возникла ошибка аутентификации! Пользователь отключен...")
    sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
    sock.close()
    exit(0)
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()

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
