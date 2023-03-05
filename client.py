from socket import *
client = socket (AF_INET, SOCK_STREAM)

client.connect(('192.168.1.34', 7000))

data = client.recv(1024)
msg = data.decode('utf-8')

print(f"SERVER MSG: \n\t{msg}")