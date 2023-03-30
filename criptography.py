import hashlib
import string
import random
def key_generate(chars = string.ascii_uppercase + string.digits, N=2048) -> string: 
    """
    Генерирует ключ шифрования для обмена сообщениями
    """
    return ''.join(random.choice(chars) for _ in range(N))

def hashing_key(msg:bytes):
    """
    Хэширует сообщение алгоритмом SHA256

    Параметры:

    msg: сообщение, которое будет захэшировано
    """
    return hashlib.sha256(msg)


def is_hash_equal(incomming_hash, msg_check):
    """
    Проверяет хэши на эквивалентность

    Параметры:

    incoming_hash: приходящий с сервера/клиента хэш
    ms
    """
    return hashlib.sha256(msg_check).digest() == incomming_hash