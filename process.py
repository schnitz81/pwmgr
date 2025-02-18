import base64
import database
import file
import config
import zlib
import comms


def connected_to_db(conn):
    # check uf DB connection is active
    try:
        conn.cursor()
        return True
    except Exception as conn_e:
        return False


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


def interpret_and_process(base64_stringdata):
    # decode base64
    try:
        unswapped_b64 = base64.b64decode(base64_stringdata)
        swapped_b64 = b64swap(unswapped_b64)
        debased_data = base64.b64decode(swapped_b64)
    except Exception as b64decode_error:
        print(f"Error: Unable to decode base64 data: {b64decode_error}")
        returnmsg = "1 Invalid base64 data to decode."
        return returnmsg

    # decompress and convert to string
    try:
        decompressed_data = zlib.decompress(debased_data, wbits=zlib.MAX_WBITS | 16)
        decompressed_data = decompressed_data.decode('utf-8')
    except Exception as decompress_error:
        print(f"Error: Unable to decompress debase64:d data: {decompress_error}")
        returnmsg = "1 Decompress error."
        return returnmsg

    comms.log(decompressed_data)

    # interpret received command
    command = decompressed_data.split(' ')[0]
    print(f'Command: {command}')


    ### init ############################################################################################
    if command == 'init':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
            nonew = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[3])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # only create new DB if nonew isn't set
        if nonew and not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            print(f"Error: nonew selected and user DB ({config.db_path}/{sessionuser}.encdb) doesn't exist.")
            returnmsg = f"1 nonew selected and user DB ({config.db_path}/{sessionuser}.encdb) doesn't exist."
            return returnmsg

        # Connect to and create DB if non-existent
        conn = database.create_connection(sessionuser, sessionpw)

        # create tables if non-existent
        database.create_tables(conn)

        # verify connection
        if not connected_to_db(conn):
            returnmsg = f"1 Unable to decrypt and connect to existing server DB ({config.db_path}/{sessionuser}.encdb). Possibly wrong password."
            return returnmsg

        # check if credentials exist
        if database.credentials_exist(conn):
            # check if received credentials match db
            if database.credentials_match(conn, sessionuser, sessionpw):
                print("Init matched existing credentials in DB.")
                returnmsg = f"2 Credentials match previous record in DB. Reusing server DB for '{sessionuser}'."
            # received credentials don't match
            else:
                returnmsg = f"1 User DB for '{sessionuser}' exists in server but provided password is wrong."

        # credentials don't exist since before
        else:
            credentials_stored = database.store_credentials(conn, sessionuser, sessionpw)
            db_written = database.write_inmem_db_to_file(conn, sessionuser, sessionpw)  # write encrypted db file
            if not db_written:
                returnmsg = f"1 Unable to write server DB to disk ({config.db_path}/{sessionuser}.encdb)."
            elif credentials_stored:
                print("Stored new credentials.")
                returnmsg = f"2 No previous credentials for user '{sessionuser}' in DB. Saving."
            else:
                returnmsg = "1 Credentials storing unsuccessful."
        database.close_connection(conn)
        return returnmsg


    ### init-change ############################################################################################
    elif command == 'init-change':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
            sessionnewuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[3])).decode('utf8').rstrip()
            sessionnewpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[4])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            print("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # create tables if non-existent
        database.create_tables(conn)

        # verify connection and session credentials
        if not connected_to_db(conn):
            returnmsg = f"1 Unable to decrypt and connect to existing DB ({config.db_path}/{sessionuser}.encdb). Possibly wrong password. Current session user and password must be verified to change them."
            return returnmsg
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Entered session credentials don't match DB records. Current session user and password must be verified to change them."
            database.close_connection(conn)
            return returnmsg
        else:
            dbfile_renamed = False

            # overwrite old credentials with new in DB
            credentials_stored = database.store_credentials(conn, sessionnewuser, sessionnewpw)

            # write encrypted db file with OLD username and NEW password since it's not renamed yet
            db_written = database.write_inmem_db_to_file(conn, sessionuser, sessionnewpw)

            database.close_connection(conn)

            # rename database file to new username
            if credentials_stored:
                dbfile_renamed = file.rename_file(f'{config.db_path}/{sessionuser}.encdb', f'{config.db_path}/{sessionnewuser}.encdb')

            # return rename and credentials change result
            if credentials_stored and dbfile_renamed and db_written:
                print("Credentials overwritten and DB file renamed.")
                returnmsg = f"2 Old credentials overwritten and DB file renamed successfully ({sessionuser} -> {sessionnewuser})."
            elif not credentials_stored:
                returnmsg = "1 Credentials storing unsuccessful."
            elif credentials_stored and not dbfile_renamed:
                returnmsg = "1 Credentials stored but unable to rename DB file. Login will probably not work unless DB file is renamed."
            elif not db_written:
                returnmsg = "1 Unable to write changed DB to disk."
            return returnmsg

    ### status ##########################################################################################
    elif command == 'status':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            print("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # verify connection and session credentials
        if not connected_to_db(conn):
            returnmsg = f"1 Unable to decrypt and connect to existing server DB ({config.db_path}/{sessionuser}.encdb). Possibly wrong password."
            return returnmsg
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = f"1 Session credentials don't match server DB file ({config.db_path}/{sessionuser}.encdb)."
        else:
            print("Session check valid.")
            returnmsg = f"2 Success: Session check successful against server DB ({config.db_path}/{sessionuser}.encdb)."
        database.close_connection(conn)
        return returnmsg


    ### add | update #####################################################################################
    elif command == 'add' or command == 'update':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
            title = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[3])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg
        username = decompressed_data.split(' ')[4]
        pw = decompressed_data.split(' ')[5]
        extra = decompressed_data.split(' ')[6]
        verification = decompressed_data.split(' ')[7]

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            print("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # verify connection and session credentials
        if not connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong password."
            return returnmsg
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # "all" is reserved.
        elif title.casefold() == "all":
            returnmsg = "1 Invalid title name. \"ALL\" is reserved."

        # avoid overwrite when add command is used
        elif database.exact_title_exists(conn, title) and command != 'update':
            returnmsg = "1 Record already exists. Use update to overwrite/change record."

        # don't create new record with update command if record is missing
        elif not database.exact_title_exists(conn, title) and command == 'update':
            returnmsg = "1 Record not found. Unable to update. Specify exact name to update."

        else:
            # get exact title case spelling when using update
            if database.exact_title_exists(conn, title) and command == 'update':
                title = database.get_title_case_spelling(conn, title)

            if not title:  # not able to check title case spelling
                returnmsg = "1 Record storing unsuccessful. Unable to get title case spelling."

            # store record
            else:
                record_stored = database.store_record(conn, title, username, pw, extra, verification)
                if record_stored:
                    db_written = database.write_inmem_db_to_file(conn, sessionuser, sessionpw)  # write encrypted db file
                    if not db_written:
                        returnmsg = "1 Unable to write changed DB to disk."
                    elif command == 'add':  # return message depending on command used
                        print("Record added to DB.")
                        returnmsg = "2 Record stored in DB successfully."
                    else:  # update command used
                        print("Record updated in DB.")
                        returnmsg = "2 Record updated in DB successfully."
                else:
                    returnmsg = "1 Record storing unsuccessful."
        database.close_connection(conn)
        return returnmsg


    ### get ############################################################################################
    elif command == 'get':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
            title = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[3])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            print("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # verify connection and session credentials
        if not connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong password."
            return returnmsg
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # get record, exact match or multimatch suggestions
        elif database.exact_title_exists(conn, title):
            record = database.get_record(conn, title)
            print("Record queried from DB.")
            returnmsg = f"2 {record}"
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            print("Partial match(es) only. List of partial matches queried from DB.")
            returnmsg = f"3 {records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = "1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        return returnmsg


    ### list ############################################################################################
    elif command == 'list':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
            title = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[3])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            print("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # verify connection and session credentials
        if not connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong password."
            return returnmsg
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # if list all is requested
        elif title.casefold() == 'all'.casefold():
            records = database.list_all_title_records(conn, title)
            print("List of all record titles queried from DB.")
            returnmsg = f"3 {records}"

        # always get multimatch suggestions
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            print("List of partial matches queried from DB.")
            returnmsg = f"3 {records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = "1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        return returnmsg


    ### delete ############################################################################################
    elif command == 'delete':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
            title = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[3])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            print("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # verify connection and session credentials
        if not connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong password."
            return returnmsg
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # delete exact match
        elif database.exact_title_exists(conn, title):
            record_deleted = database.delete_record(conn, title)
            db_written = database.write_inmem_db_to_file(conn, sessionuser, sessionpw)  # write encrypted db file
            if not db_written:
                returnmsg = "1 Unable to write changed DB to disk."
            elif record_deleted:
                print("Record deleted from DB.")
                returnmsg = "2 Record deleted from DB."
            else:
                returnmsg = "1 Error when deleting record from DB."

        # always get multimatch suggestions
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            print("Partial match(es) only. List of partial matches queried from DB instead of deleting.")
            returnmsg = f"3 {records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = "1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        return returnmsg


    ### backup ##########################################################################################
    elif command == 'backup':
        try:
            sessionuser = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(decompressed_data.split(' ')[2])).decode('utf8').rstrip()
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 Encrypted DB file ({config.db_path}/{sessionuser}.encdb) not found in server. Unable to dump DB into backup file."
            return returnmsg
        else:
            print("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # verify connection and session credentials
        if not connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong password."
            return returnmsg
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
        else:
            # dump DB into unencrypted file
            if database.write_inmem_db_to_file_unencrypted(conn, sessionuser):
                print(f"Decrypted DB file saved to {config.db_path}/{sessionuser}.db")
                returnmsg = f"2 Database successfully backed up to {config.db_path}/{sessionuser}.db in server."
            else:
                returnmsg = f"1 Unable to backup database as unencrypted to {config.db_path}/{sessionuser}.db in server."

        database.close_connection(conn)
        return returnmsg


    ### no command matches ###############################################################################
    else:
        returnmsg = "1 Unknown command."
        return returnmsg