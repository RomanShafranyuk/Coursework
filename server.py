from socket import *

server = socket(AF_INET, SOCK_STREAM)

server.bind(('192.168.1.34', 7000))

server.listen(2)

user, address = server.accept()
print(f"CONNECTED:\n{user}\n{address}")

user.send ("You are connected!".encode('utf-8'))
#while True:
