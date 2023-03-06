import socket
import threading
import sys

buf = []
def get_input():
    global buf
    while True:
        buf.append(input('>>> '))

port = int(sys.argv[1])
sock = socket.socket()
sock.connect(('localhost', port))
msg = threading.Thread(target=get_input)
msg.start()
while True:
    data = sock.recv(1024)
    if data:
        print(f"Recieve message: {data} ")
    while len(buf) > 0:
        print("Есть что отправить")
        sock.send(buf.pop().encode("utf-8"))
        print("Отправлено")
    


#sock.send(b'hello, world!')

data = sock.recv(1024)
sock.close()

print(data)