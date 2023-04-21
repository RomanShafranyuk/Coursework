# Simple message protocol for sockets.
import socket


def socket_send(sock: socket.socket, header: str, content: bytes = 'empty'.encode('utf-8')):
    # send header
    header_data = header.encode('utf-8')
    header_len = len(header_data)
    sock.send(header_len.to_bytes(4, 'little'))
    sock.send(header_data)
    # send content
    content_len = len(content)
    sock.send(content_len.to_bytes(4, 'little'))
    sock.send(content)


def socket_recv(sock: socket.socket):
    """
    Возвращает список заголовков, и контент в виде `bytes`
    """
    # recv header
    header_len = int.from_bytes(sock.recv(4), 'little')
    header = sock.recv(header_len).decode('utf-8')
    # recv content
    content_len = int.from_bytes(sock.recv(4), 'little')
    content = sock.recv(content_len)
    return header.split(';'), content
