import base64
import config
import sqlite3
from io import StringIO
import file
import hashlib
import comms


def create_connection(sessionuser, sessionpw):
    # create db connection and create new db if both db and backup are missing
    print(f"Creating inmem db.")
    conn = None
    try:
        conn = sqlite3.connect(":memory:")
    except Exception as e:
        print(e)
        conn.close()
    # read db file, decrypt and read into inmem sqlite db
    if file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):  # encrypted .encdb file
        try:
            print(f"{sessionuser}.encdb file exists. Decrypting and reading.")
            memfile = StringIO()
            decrypted_data = file.read_and_decrypt_file(f'{config.db_path}/{sessionuser}.encdb', sessionpw)
            memfile.write(decrypted_data)
            memfile.seek(0)
            conn.cursor().executescript(memfile.read())
            conn.commit()
        except Exception as read_encrypted_db_to_mem_e:
            print(f"DB decryption error: {read_encrypted_db_to_mem_e}")
            conn.close()
    # read unencrypted .db file if it's the only db file with the user name available
    elif file.file_exists(f'{config.db_path}/{sessionuser}.db'):
        try:
            print(f"{sessionuser}.encdb db file not found. but {sessionuser}.db found. Reading as unencrypted db file.")
            unenc_db_conn = sqlite3.connect(f'{config.db_path}/{sessionuser}.db', timeout=12)
            unenc_db_conn.backup(conn)
            conn.commit()
            unenc_db_conn.close()
        except Exception as read_unencrypted_db_to_mem_e:
            print(read_unencrypted_db_to_mem_e)
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
               CREATE TABLE IF NOT EXISTS records (
               title TEXT PRIMARY KEY,
               username TEXT,
               pw TEXT,
               extra TEXT,
               verification TEXT
           );'''
        )
    except Exception as creation_e:
        print(creation_e)


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
            print(hashpw_e)
        if dbsessionuser == sessionuser and hashed_dbsessionpw == hashed_sessionpw:
            return True
        else:
            return False


def store_credentials(conn, sessionuser, sessionpw):
    c = conn.cursor()
    try:
        hashed_sessionpw = hashlib.sha3_512(sessionpw.encode()).hexdigest()
    except Exception as hashpw_e:
        print(hashpw_e)
    try:
        c.execute(f'''REPLACE INTO credentials (id, sessionuser, sessionpw) VALUES ('1', '{sessionuser}', '{hashed_sessionpw}');''')
        return True
    except Exception as store_e:
        print(store_e)
        return False


def store_record(conn, title, username, pw, extra, verification):
    c = conn.cursor()
    try:
        c.execute(f'''REPLACE INTO records (title, username, pw, extra, verification) VALUES ('{title}', '{username}', '{pw}', '{extra}', '{verification}');''')
        return True
    except Exception as store_e:
        print(f'DB storage error: {store_e}')
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
        comms.log(strlist)
        return strlist


def list_all_title_records(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT title FROM records;''')
        db_values = c.fetchall()
        strlist = ' | '.join(map(','.join, db_values))
        comms.log(strlist)
        return strlist


def get_record(conn, title):
    c = conn.cursor()
    with conn:
        # fetch exact case spelling of title and base64 encode it separately to handle potential spaces
        c.execute(f'''SELECT title FROM records WHERE title='{title}' COLLATE NOCASE;''')
        db_title = ' '.join(c.fetchone())
        b64_db_title = base64.b64encode(base64.b64encode(db_title.encode('utf-8')))
        c.execute(f'''SELECT username, pw, extra, verification FROM records WHERE title='{title}' COLLATE NOCASE;''')
        strlist = b64_db_title.decode('utf-8') + ' ' + ' '.join(c.fetchone())
        comms.log(strlist)
        return strlist


def delete_record(conn, title):
    c = conn.cursor()
    try:
        c.execute(f'''DELETE FROM records WHERE title='{title}' COLLATE NOCASE;''')
        return True
    except Exception as deleterecord_e:
        print(f"Error: Unable to delete db record {title}: {deleterecord_e}")
        return False


def write_inmem_db_to_file(conn, sessionuser, sessionpw):
    try:
        conn.commit()  # settling db before file writing
        print("Encrypting and saving to file.")
        memfile = StringIO()
        for line in conn.iterdump():
            memfile.write('%s\n' % line)
        memfile.seek(0)
        db_encryption_rtn_code = file.encrypt_and_write_file(memfile.read(), f'{config.db_path}/{sessionuser}.encdb', sessionpw)
        if db_encryption_rtn_code == 0:
            return True
        else:
            return False
    except Exception as e:
        print(e)
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
        print(read_unencrypted_db_to_mem_e)
        conn.close()
        return False


def close_connection(conn):
    conn.commit()
    print("Disconnecting from db.")
    conn.close()

