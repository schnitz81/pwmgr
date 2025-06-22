import os
import subprocess
from logging import log


def file_exists(filepath):
    if os.path.exists(filepath):
        return True
    else:
        return False


def rename_file(old_filepath, new_filepath):
    try:
        os.rename(old_filepath, new_filepath)
        return True
    except Exception as rename_e:
        log("Error: Unable to rename file:", 0)
        log(rename_e, 0)
        return False


def read_and_decrypt_file(file, file_encryption_pw):
    try:
        openssl_output = subprocess.run(f'''
                cat "{file}" | openssl aes-256-cbc -d -md sha3-512 -a -pbkdf2 -k '{file_encryption_pw}'
            ''',
            shell=True, check=True,
            executable='/bin/sh',
            capture_output=True,
            text=True
        )
        return openssl_output.stdout
    except Exception as openssl_e:
        log(openssl_e, 0)


def encrypt_and_write_file(memcontent, file, file_encryption_pw):
    try:
        openssl_output = subprocess.run(f'''
                echo "{memcontent}" | openssl aes-256-cbc -md sha3-512 -a -pbkdf2 -out '{file}' -k '{file_encryption_pw}'
            ''',
            shell=True, check=True,
            executable='/bin/sh',
            capture_output=True,
            text=True
        )
        return openssl_output.returncode
    except Exception as openssl_e:
        log(openssl_e, 0)