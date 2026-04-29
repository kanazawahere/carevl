import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from app.core.config import settings

def pad(data: bytes) -> bytes:
    """PKCS#7 padding"""
    block_size = 16
    padding_len = block_size - (len(data) % block_size)
    return data + bytes([padding_len] * padding_len)


def unpad(data: bytes) -> bytes:
    if not data:
        raise ValueError("Empty ciphertext")
    padding_len = data[-1]
    if padding_len < 1 or padding_len > 16:
        raise ValueError("Invalid PKCS#7 padding")
    return data[:-padding_len]

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


def decrypt_file(input_file_path: str, output_file_path: str, key: bytes | None = None) -> None:
    """
    Decrypt AES-256-CBC file (IV prepended). If key is None, uses settings.ENCRYPTION_KEY UTF-8 (32 bytes).
    """
    k = key if key is not None else settings.ENCRYPTION_KEY.encode("utf-8")
    if len(k) != 32:
        raise ValueError("Decryption key must be exactly 32 bytes for AES-256.")

    with open(input_file_path, "rb") as f_in:
        iv = f_in.read(16)
        ciphertext = f_in.read()

    cipher = Cipher(algorithms.AES(k), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    plain = unpad(padded)

    os.makedirs(os.path.dirname(output_file_path) or ".", exist_ok=True)
    with open(output_file_path, "wb") as f_out:
        f_out.write(plain)


def aes_key_from_invite_field(raw: str) -> bytes:
    """32-byte AES key: UTF-8 string of length 32, or base64 decoding to 32 bytes."""
    b = raw.encode("utf-8")
    if len(b) == 32:
        return b
    try:
        dec = base64.b64decode(raw)
        if len(dec) == 32:
            return dec
    except Exception:
        pass
    raise ValueError(
        "encryption_key must be 32 UTF-8 bytes or base64 decoding to 32 bytes (same as snapshot key)."
    )


def compute_file_sha256(filepath: str) -> str:
    """
    Computes the SHA-256 hash of a file.
    """
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
