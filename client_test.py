import socket
import threading
import sys

def listen_to_server(conn: socket.socket):
    while True:
        data = conn.recv(1024).decode(encoding='utf-8')
        if data == 'conn_close':
            break
        elif len(data) > 0:
            print(f'Got message: {data}')
        else:
            break

username = 'dimadivan'
port = 7001
sock = socket.socket()
sock.connect(('localhost', port))
listener = threading.Thread(target=listen_to_server, args=[sock])
listener.start()
sock.send(username.encode(encoding='utf-8'))
while True:
    msg = input('>>> ')
    if msg == '/exit':
        print('Closing program...')
        sock.send(b'conn_close')
        listener.join()
        sock.close()
        break
    bytes_count = sock.send(msg.encode(encoding='utf-8'))
    print(f'{bytes_count} bytes sent!')
