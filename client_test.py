import socket
import threading
import sys

def listen_to_server(conn: socket.socket):
    while True:
        data = conn.recv(1024)
        if len(data) > 0:
            print(f'Got message: {data}')
        else:
            break


port = int(sys.argv[1])
sock = socket.socket()
sock.connect(('localhost', port))
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()
while True:
    msg = input('>>> ')
    if msg == '/exit':
        sock.close()
        listener.join(2)
        break
    bs = sock.send(msg.encode(encoding='utf-8'))
    print(f'{bs} bytes sent!')
