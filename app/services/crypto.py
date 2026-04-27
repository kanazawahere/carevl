import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from app.core.config import settings

def pad(data: bytes) -> bytes:
    """PKCS#7 padding"""
    block_size = 16
    padding_len = block_size - (len(data) % block_size)
    return data + bytes([padding_len] * padding_len)

def encrypt_file(input_file_path: str, output_file_path: str) -> None:
    """
    Encrypts a file using AES-256-CBC.
    The encryption key is loaded from the environment/config.
    """
    key = settings.ENCRYPTION_KEY.encode('utf-8')
    if len(key) != 32:
        raise ValueError("Encryption key must be exactly 32 bytes for AES-256.")

    # Generate a random 16-byte IV
    iv = os.urandom(16)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    with open(input_file_path, 'rb') as f_in:
        file_data = f_in.read()

    padded_data = pad(file_data)
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    with open(output_file_path, 'wb') as f_out:
        # Prepend the IV to the output file for decryption later
        f_out.write(iv)
        f_out.write(ciphertext)

    print(f"Successfully encrypted {input_file_path} to {output_file_path}")
