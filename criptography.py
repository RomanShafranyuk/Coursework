import hashlib
import string
import random
def key_generate(chars = string.ascii_uppercase + string.digits, N=2048): 
    return ''.join(random.choice(chars) for _ in range(N))

def hashing_key(msg:bytes):
    return hashlib.sha256(msg)


def is_hash_equal(incomming_hash, msg_check):
    return hashlib.sha256(msg_check).digest() == incomming_hash