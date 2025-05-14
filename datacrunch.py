import subprocess
import base64
import zlib
import string
import secrets
import comms
import database
import hashlib


def generate_token(length):
    characters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    token = ''.join(secrets.choice(characters) for i in range(length))
    return token


def b64swap(b64):
    if len(b64) > 4:
        b64str = b64.decode('utf-8')
        byteoffset = 2
        swapped_b64 = b64str
        while byteoffset < len(b64str) - 2:
            # byteswap
            swapped_b64 = swapped_b64[:byteoffset - 1] + swapped_b64[byteoffset] + swapped_b64[byteoffset - 1] + swapped_b64[byteoffset + 1:]
            byteoffset = byteoffset + 2
        swapped_b64 = swapped_b64.encode('utf-8')
        return swapped_b64
    else:
        print("Error: b64 string received for swapping is too short.")


def scramble(data):
    # compress and convert to string
    try:
        uncompressed_data = data.encode("utf-8")
        compressed_data = zlib.compress(uncompressed_data, 1, wbits=zlib.MAX_WBITS | 16)
    except Exception as compress_error:
        print(f"Error: Unable to compress base64:d data: {compress_error}")
        returnmsg = "1 Compress error."
        return returnmsg
    try:
        unswapped_b64 = base64.b64encode(compressed_data)
        swapped_b64 = b64swap(unswapped_b64)
        based_data = base64.b64encode(swapped_b64)
        based_data = based_data.decode('utf8').rstrip()
        return based_data
    except Exception as b64encode_error:
        print(f"Error: Unable to encode base64 data: {b64encode_error}")
        returnmsg = "1 base64 encoding error."
        return returnmsg


def descramble(data):
    try:
        swapped_b64 = base64.b64decode(data)
        unswapped_b64 = b64swap(swapped_b64)
        debased_data = base64.b64decode(unswapped_b64)
    except Exception as b64decode_error:
        print(f"Error: Unable to decode base64 data: {b64decode_error}")
        returnmsg = "1 Invalid base64 data to decode."
        return returnmsg
    # decompress and convert to string
    try:
        decompressed_data = zlib.decompress(debased_data, wbits=zlib.MAX_WBITS | 16)
        decompressed_data = decompressed_data.decode('utf-8')
        return decompressed_data
    except Exception as decompress_error:
        print(f"Error: Unable to decompress debase64:d data: {decompress_error}")
        returnmsg = "1 Decompress error."
        return returnmsg


def fetch_token_from_hash(conn, tokenmd5):
    transporttokens = database.get_all_transporttokens(conn)
    # compare hashsums from end of the DB list
    for token in reversed(transporttokens):
        comms.log(f"comparing {hashlib.md5(token[0].encode()).hexdigest()}")
        if hashlib.md5(token[0].encode()).hexdigest() == tokenmd5:
            comms.log(f"Found matching token for hash: {tokenmd5} ({token})")
            return token[0]
    comms.log("Error: No matching token found.")
    return False


def transport_decrypt(data, transporttoken):
    try:
        # decrypt data with generated encryptionpw
        openssl_output = subprocess.run(f'''
                echo "{data}" | base64 -d | openssl aes-256-cbc -d -md sha3-512 -pbkdf2 -k "{transporttoken}"
            ''',
            shell=True, check=True,
            executable='/bin/sh',
            capture_output=True,
            text=True
        )
        return openssl_output.stdout
    except Exception as openssl_e:
        print(openssl_e)


def transport_encrypt(data, transporttoken):
    try:
        # encrypt data with generated encryptionpw
        openssl_output = subprocess.run(f'''
                echo "{data}" | openssl aes-256-cbc -md sha3-512 -a -pbkdf2 -k "{transporttoken}" | tr -d "\n"
            ''',
            shell=True, check=True,
            executable='/bin/sh',
            capture_output=True,
            text=True
        )
        return openssl_output.stdout
    except Exception as openssl_e:
        print(openssl_e)
