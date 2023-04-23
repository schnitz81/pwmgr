import config
import sqlite3


def create_connection(sessionuser):
    # create db connection and create new db if both db and backup are missing
    conn = None
    try:
        conn = sqlite3.connect(f'{config.db_path}/{sessionuser}.db', timeout=12)
        return conn
    except Exception as e:
        print(e)
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
        dbsessionpw = c.fetchone()[0]
        if dbsessionuser == sessionuser and dbsessionpw == sessionpw:
            return True
        else:
            return False


def store_credentials(conn, sessionuser, sessionpw):
    c = conn.cursor()
    try:
        c.execute(f'''REPLACE INTO credentials (id, sessionuser, sessionpw) VALUES ('1', '{sessionuser}', '{sessionpw}');''')
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
        actualTitle = c.fetchone()[0]
        if actualTitle:
            return actualTitle
        else:
            return False


def nbr_of_title_hits(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT COUNT(title) FROM records WHERE title LIKE '%{title}%' COLLATE NOCASE;''')
        nbrOfhits = c.fetchone()[0]
        return nbrOfhits


def list_partial_title_records(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT title FROM records WHERE title LIKE '%{title}%' COLLATE NOCASE;''')
        dbvals = c.fetchall()
        strlist = ' '.join(map(','.join, dbvals))
        print(strlist)
        return strlist


def get_record(conn, title):
    c = conn.cursor()
    with conn:
        c.execute(f'''SELECT * FROM records WHERE title='{title}' COLLATE NOCASE;''')
        strlist = ' '.join(c.fetchone())
        print(strlist)
        return strlist


def delete_record(conn, title):
    c = conn.cursor()
    try:
        c.execute(f'''DELETE FROM records WHERE title='{title}' COLLATE NOCASE;''')
        return True
    except Exception as deleterecord_e:
        print(f"Error: Unable to delete db record {title}")
        return False


def close_connection(conn):
    conn.commit()
    print("Disconnecting from db.")
    conn.close()

