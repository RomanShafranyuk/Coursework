import socket

sock = socket.socket()
sock.bind(('', 9090))
sock.listen(1)
conn, addr = sock.accept()
print('connected:', conn, addr)
conn1, addr1 = sock.accept()
print('connected:', conn1, addr1)

conn.close()
conn1.close()