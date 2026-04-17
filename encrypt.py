from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64


def generate_key():
    master_key = get_random_bytes(32)
    master_key_b64 = base64.b64encode(master_key).decode('utf-8')
    with open(".env", "w") as f:
        f.write(f"MASTER_KEY={master_key_b64}\n")


def get_master_key(env_path=".env"):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("MASTER_KEY="):
                key = line.split("=", 1)[1].strip()
                key = key.strip('"').strip("'")
                return key


def encryption_pass(password: str) -> str:
    nonce_random = get_random_bytes(12)
    key_b64 = get_master_key()
    key = base64.b64decode(key_b64)

    crypt = AES.new(key, AES.MODE_GCM, nonce=nonce_random)
    crypt_text, tag = crypt.encrypt_and_digest(password.encode())

    encrypted_pass = nonce_random + crypt_text + tag
    return base64.b64encode(encrypted_pass).decode('utf-8')


def decryprion_pass(encrypted_pass_b64: str) -> str:
    encrypted_pass = base64.b64decode(encrypted_pass_b64)
    sect_nonce = encrypted_pass[:12]
    sect_tag = encrypted_pass[-16:]
    sect_crypt_text = encrypted_pass[12:-16]

    key_b64 = get_master_key()
    key = base64.b64decode(key_b64)

    crypt = AES.new(key, AES.MODE_GCM, nonce = sect_nonce)
    decrypted_pass = crypt.decrypt_and_verify(sect_crypt_text, sect_tag)
    return decrypted_pass.decode('utf-8')


# generate_key()
# print(get_master_key())

my_pass = "Hello, World!"
encr_pass = encryption_pass(my_pass)
decr_pass = decryprion_pass(encr_pass)
print(f"My pass: {my_pass}")
print(f"Encription pass: {encr_pass}")
print(f"Decription pass: {decr_pass}")