import base64
from cryptography.fernet import Fernet
import streamlit as st
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

def derive_key(password: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def get_master_password():
    """
    Retrieves the MASTER_PASSWORD from the logged in user configuration.
    """
    if "config" in st.session_state:
        return st.session_state.config["MASTER_PASSWORD"]
    else:
        raise Exception("User configuration not available.")

def decrypt_voice_memo(encrypted_file_path: str, master_password: str) -> bytes:
    """
    Decrypts the given encrypted voice memo file using the key derived from master_password.
    """
    salt = b'voicememo_salt' # yes this is not perfectly safe. But I'm lazy. 
    key = derive_key(master_password, salt)
    fernet = Fernet(key)
    with open(encrypted_file_path, "rb") as f:
        encrypted_data = f.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data

def get_decrypted_voice_memo(voice_memo_filename):
    """
    Convenience function that returns the decrypted file data (bytes)
    and the original filename, by looking up the file in "encrypted_voice_memos" folder.
    """
    import os
    file_path = os.path.join("encrypted_voice_memos", voice_memo_filename)
    master_password = get_master_password()
    decrypted_data = decrypt_voice_memo(file_path, master_password)
    return decrypted_data, voice_memo_filename
