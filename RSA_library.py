import rsa

def generate_key():
    return rsa.newkeys(2048)

def safe_keys_to_file(public_key, private_key):
    with open("public.pem", "wb") as f:
        f.write(public_key.save_pkcs1("PEM"))
    
    with open("private.pem", "wb") as f:
        f.write(private_key.save_pkcs1("PEM"))

def get_key_from_file():
    with open("public.pem") as f:
        public_key = rsa.PublicKey.load_pkcs1(f.read())
    with open("private.pem") as f:
        private_key = rsa.PrivateKey.load_pkcs1(f.read())
    return public_key, private_key

def encrypte_message(msg: str, public_key):
    return rsa.encrypt(msg.encode("utf-8"), public_key)

def decrypte_message(enc_msg, private_key):
    return rsa.decrypt(enc_msg, private_key)    

def get_sign(msg, private_key):
    return rsa.sign(msg.encode(), private_key, "SHA-256")

public_key, private_key = generate_key()
message = "Hello, my friend!"
e = encrypte_message(message, public_key)
public_key, private_key  = get_key_from_file()
d = decrypte_message(e, private_key).decode("utf-8")
print(e)
print(d)

# sign = get_sign(message, private_key)
# print(sign)
# if rsa.verify(message.encode(), sign, public_key) == "SHA-256":
#     print("Проверка пройдена")