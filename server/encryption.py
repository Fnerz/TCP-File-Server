""" DISCLAIMER!!!!
    This encryption method is NOT secure and is only intended to facilitate the saving process """
import os
try:
    from cryptography.fernet import Fernet
except ImportError:
    os.system("pip install cryptography")

key = b'R-Niy7F12FBuKAWW35CQWQrSgahVwmFZV0jWuMSdGi8='

def generate_key() -> bytes:
    return Fernet.generate_key()

def encrypt_text(message: str, key: bytes) -> str:
    cipher_suite = Fernet(key)
    encrypted_message = cipher_suite.encrypt(message.encode())
    return encrypted_message.decode()  # Change here

def decrypt_text(encrypted_message: str, key: bytes) -> str:
    encrypted_message = encrypted_message.encode()
    cipher_suite = Fernet(key)
    decrypted_message = cipher_suite.decrypt(encrypted_message).decode()
    return decrypted_message

