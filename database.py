import base64
import sqlite3
from io import StringIO
import file
import hashlib
import config
import logging
from logging import log


def connected_to_db(conn):
    # check uf DB connection is active
    try:
        conn.cursor()
        return True
    except Exception as conn_e:
        return False


def create_connection(sessionuser, sessionpw):
    # create db connection and create new db if both db and backup are missing
    if logging.benchmark_running_counter == 0:
        log("Creating inmem db.", 1)
    conn = None
    try:
        conn = sqlite3.connect(":memory:")
    except Exception as e:
        log(e, 0)
        conn.close()
    # read db file, decrypt and read into inmem sqlite db
    if file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):  # encrypted .encdb file
        try:
            if logging.benchmark_running_counter == 0:
                log(f"{sessionuser}.encdb file exists. Decrypting and reading.", 1)
            memfile = StringIO()
            decrypted_data = file.read_and_decrypt_file(f'{config.db_path}/{sessionuser}.encdb', sessionpw)
            memfile.write(decrypted_data)
            memfile.seek(0)
            conn.cursor().executescript(memfile.read())
            conn.commit()
        except Exception as read_encrypted_db_to_mem_e:
            log(f"DB decryption error: {read_encrypted_db_to_mem_e}", 0)
            conn.close()
    # read unencrypted .db file if it's the only db file with the user name available
    elif file.file_exists(f'{config.db_path}/{sessionuser}.db'):
        try:
            log(f"{sessionuser}.encdb db file not found. but {sessionuser}.db found. Reading as unencrypted db file.", 1)
            unenc_db_conn = sqlite3.connect(f'{config.db_path}/{sessionuser}.db', timeout=12)
            unenc_db_conn.backup(conn)
            conn.commit()
            unenc_db_conn.close()
        except Exception as read_unencrypted_db_to_mem_e:
            log(read_unencrypted_db_to_mem_e, 0)
            conn.close()
    return conn


def create_tables(conn):
    try:
        c = conn.cursor()

        # create both db tables
        c.execute(
            '''
               CREATE TABLE IF NOT EXISTS credentials (
               id INTEGER PRIMARY KEY,
               sessionuser TEXT NOT NULL,
               sessionpw TEXT NOT NULL      
           );'''
        )
        c.execute(
            '''
               CREATE TABLE IF NOT EXISTS transporttokens (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               token TEXT NOT NULL
           );'''
        )
        c.execute(
            '''
               CREATE TABLE IF NOT EXISTS records (
               title TEXT PRIMARY KEY,
               username TEXT,
               pw TEXT,
               extra TEXT,
               verification TEXT
           );'''
        )
    except Exception as creation_e:
        log(creation_e, 0)


def credentials_exist(conn):
    c = conn.cursor()
    with conn:
        c.execute("SELECT * FROM credentials")
        result = c.fetchall()
        if len(result) == 0:
            return False
        else:
            return True


def credentials_match(conn, sessionuser, sessionpw):
    c = conn.cursor()
    with conn:
        c.execute("SELECT sessionuser FROM credentials")
        dbsessionuser = c.fetchone()[0]
        c.execute("SELECT sessionpw FROM credentials")
        try:
            hashed_dbsessionpw = c.fetchone()[0]
            hashed_sessionpw = hashlib.sha3_512(sessionpw.encode()).hexdigest()
        except Exception as hashpw_e:
            log(hashpw_e, 0)
        if dbsessionuser == sessionuser and hashed_dbsessionpw == hashed_sessionpw:
            return True
        else:
            return False


def transporttoken_match(conn, tokensha256):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT token FROM transporttokens;''')
        db_values = c.fetchall()
        strlist = ' | '.join(map(','.join, db_values))
        for token in strlist:
            if hashlib.sha3_512(token.encode()).hexdigest() == tokensha256:
                return True
        return False


def store_credentials(conn, sessionuser, sessionpw):
    c = conn.cursor()
    try:
        hashed_sessionpw = hashlib.sha3_512(sessionpw.encode()).hexdigest()
    except Exception as hashpw_e:
        log(hashpw_e, 0)
    try:
        c.execute(f'''REPLACE INTO credentials (id, sessionuser, sessionpw) VALUES ('1', '{sessionuser}', '{hashed_sessionpw}');''')
        return True
    except Exception as store_e:
        log(store_e, 0)
        return False


def store_transporttoken(conn, token):
    c = conn.cursor()
    with conn:
        try:
            c.execute(f'''INSERT INTO transporttokens (token) VALUES ('{token}');''')
            return True
        except Exception as storetoken_e:
            log(storetoken_e, 0)
            return False


def get_all_transporttokens(conn):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT token FROM transporttokens;''')
        db_values = c.fetchall()
        log(db_values, 2)
        return db_values


def store_record(conn, title, username, pw, extra, verification):
    c = conn.cursor()
    with conn:
        try:
            c.execute(f'''REPLACE INTO records (title, username, pw, extra, verification) VALUES ('{title}', '{username}', '{pw}', '{extra}', '{verification}');''')
            return True
        except Exception as store_e:
            log(f'DB storage error: {store_e}', 0)
            return False


def exact_title_exists(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT title FROM records WHERE title='{title}' COLLATE NOCASE;''')
        if c.fetchall():
            return True
        else:
            return False


def get_title_case_spelling(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT title FROM records WHERE title='{title}' COLLATE NOCASE;''')
        actual_title = c.fetchone()[0]
        if actual_title:
            return actual_title
        else:
            return False


def nbr_of_title_hits(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT COUNT(title) FROM records WHERE title LIKE '%{title}%' COLLATE NOCASE;''')
        nbr_of_hits = c.fetchone()[0]
        return nbr_of_hits


def list_partial_title_records(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT title FROM records WHERE title LIKE '%{title}%' COLLATE NOCASE;''')
        db_values = c.fetchall()
        strlist = ' | '.join(map(','.join, db_values))
        log(strlist, 2)
        return strlist


def list_all_title_records(conn):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT title FROM records;''')
        db_values = c.fetchall()
        strlist = ' | '.join(map(','.join, db_values))
        log(strlist, 2)
        return strlist


def get_record(conn, title):
    c = conn.cursor()
    with conn:
        # fetch exact case spelling of title and base64 encode it separately to handle any spaces in multiword titles
        c.execute(f'''SELECT title FROM records WHERE title='{title}' COLLATE NOCASE;''')
        db_title = ' '.join(c.fetchone())
        b64_db_title = base64.b64encode(db_title.encode('utf-8'))
        c.execute(f'''SELECT username, pw, extra, verification FROM records WHERE title='{title}' COLLATE NOCASE;''')
        strlist = b64_db_title.decode('utf-8') + ' ' + ' '.join(c.fetchone())
        log(strlist, 2)
        return strlist


def delete_record(conn, title):
    c = conn.cursor()
    try:
        c.execute(f'''DELETE FROM records WHERE title='{title}' COLLATE NOCASE;''')
        return True
    except Exception as deleterecord_e:
        log(f"Error: Unable to delete db record {title}: {deleterecord_e}", 0)
        return False


def write_inmem_db_to_file(conn, sessionuser, sessionpw):
    try:
        conn.commit()  # settling db before file writing
        log("Encrypting and saving to file.", 1)
        memfile = StringIO()
        for line in conn.iterdump():
            memfile.write('%s\n' % line)
        memfile.seek(0)
        db_encryption_rtn_code = file.encrypt_and_write_file(memfile.read(), f'{config.db_path}/{sessionuser}.encdb', sessionpw)
        if db_encryption_rtn_code == 0:
            log("Inmem DB written to file.", 2)
            return True
        else:
            return False
    except Exception as e:
        log(e, 0)
        conn.close()
        return False


def write_inmem_db_to_file_unencrypted(conn, sessionuser):
    # write inmem DB to file
    try:
        unenc_db_conn = sqlite3.connect(f'{config.db_path}/{sessionuser}.db', timeout=12)
        conn.backup(unenc_db_conn)
        unenc_db_conn.close()
        return True
    except Exception as read_unencrypted_db_to_mem_e:
        log(read_unencrypted_db_to_mem_e, 0)
        conn.close()
        log(f"Error: Unsuccessful inmem DB to file dump. Unable to write {config.db_path}/{sessionuser}.db", 0)
        return False


def close_connection(conn):
    conn.commit()
    if logging.benchmark_running_counter == 0:
        log("Disconnecting from DB.", 1)
    conn.close()
