import socket
import threading
import sys
import json
from consolemenu import prompt_utils, ConsoleMenu, SelectionMenu, Screen
from consolemenu.items import FunctionItem

message_buffer = []

def send_message(sock, my_username):
    data = {"from": my_username, "to":"", "text": ""}
    # user_index = SelectionMenu.get_selection(users_online, "Send to...", show_exit_option=False)
    test_prompt = prompt_utils.PromptUtils(Screen())
    data["to"] = test_prompt.input("Send to").input_string
    data["text"] = test_prompt.input("Text").input_string
    bytes_count = sock.send(json.dumps(data).encode(encoding='utf-8'))
    print(f'{bytes_count} bytes sent!')
    test_prompt.enter_to_continue()


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

port, username = int(sys.argv[1]), sys.argv[2]
sock = socket.socket()
sock.connect(('127.0.0.1', port))
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()
sock.send(username.encode(encoding='utf-8'))

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
