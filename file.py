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
        with open(file, 'rb') as f:
            data = f.read()
        proc = subprocess.Popen(
            ['openssl', 'aes-256-cbc', '-d', '-md', 'sha3-512', '-a', '-pbkdf2', '-k', file_encryption_pw],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        decrypted_data, openssl_error = proc.communicate(input=data)
        decrypted_data = decrypted_data.decode('utf-8')

        # check for errors
        if proc.returncode != 0:
            log(f"Error reading DB file: {openssl_error}", 0)
        return decrypted_data
    except Exception as openssl_e:
        log(openssl_e, 0)


def encrypt_and_write_file(memcontent, file, file_encryption_pw):
    try:
        # create openssl write process
        proc = subprocess.Popen(
            ['openssl', 'aes-256-cbc', '-md', 'sha3-512', '-a', '-pbkdf2', '-out', file, '-k', file_encryption_pw],
            stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        # write data
        proc.stdin.write(memcontent.encode('utf-8'))
        proc.stdin.close()

        # wait for openssl write to finish and fetch any errors
        proc_returncode = proc.wait()
        openssl_error = proc.stderr.read()
        proc.stderr.close()

        # check for errors
        if proc_returncode != 0:
            log(f"Error saving encrypted DB file: {openssl_error}", 0)
        return proc_returncode
    except Exception as openssl_e:
        log(openssl_e, 0)