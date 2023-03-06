import socket
import threading

def connect(address, port):
    sock = socket.socket()
    sock.bind((address, port))
    sock.listen(1)
    conn, addr = sock.accept()
    print('connected:', conn, addr)
    while True:
        data = conn.recv(1024)
        if len(data) > 0:
            print(f"Receiving message: {data}")
    #conn.close()


client1 = threading.Thread(target=connect, args=('localhost', 7002))
client2 = threading.Thread(target=connect, args=('localhost', 7003))
client1.start()
client2.start()
while True:
    pass
