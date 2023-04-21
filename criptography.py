import hashlib
import string
import random
import rsa
def key_generate(N=1024) -> 'tuple[bytes, bytes]':
    """
    Генерирует ключ шифрования для обмена сообщениями.
    Возвращает (приватный ключ, публичный ключ).
    """
    public_key, private_key = rsa.newkeys(N, accurate=True)
    return private_key.save_pkcs1(), public_key.save_pkcs1()

def encrypt_message(msg: bytes, public_key):
    """
    Шифрует сообщение алгоритмом RSA
    """
    return rsa.encrypt(msg, public_key)

def decrypt_message(en_msg: bytes, private_key: rsa.PrivateKey):
    """
    Дешифрует сообщение алгоритмом RSA
    """
    is_decrypted = True
    result = bytes()
    try:
        result = rsa.decrypt(en_msg, private_key)
    except rsa.DecryptionError:
        is_decrypted = False
    return is_decrypted, result

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

if __name__ == "__main__":
    private_key, public_key = key_generate()
    print(len(private_key))
    print(len(public_key))