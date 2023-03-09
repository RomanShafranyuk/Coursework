import socket
import threading
import sys
import json
def listen_to_server(conn: socket.socket):
    while True:
        incoming = conn.recv(1024).decode(encoding='utf-8')
        data = json.loads(incoming)
        if data['text'] == 'conn_close':
            break
        elif len(data) > 0:
            print(f'{data["from"]}: {data["text"]}')
        else:
            break

port, username = int(sys.argv[1]), sys.argv[2]
sock = socket.socket()
sock.connect(('192.168.212.71', port))
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()
sock.send(username.encode(encoding='utf-8'))
while True:
    data = {"from" : "", "to" : "", "text" : ""}
    data["from"] = username
    data["to"] = input("Send to: ")
    data["text"] = input('>>> ')
    
    if data["text"] == '/exit':
        print('Closing program...')
        sock.send(json.dumps({"text": 'conn_close'}).encode(encoding='utf-8'))
        listener.join()
        sock.close()
        break
    bytes_count = sock.send(json.dumps(data).encode(encoding='utf-8'))
    print(f'{bytes_count} bytes sent!')
