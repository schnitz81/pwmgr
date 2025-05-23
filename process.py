import base64
import database
import file
import datacrunch
import config
import comms


def interpret_and_process(received_data):
    # decode received data
    descrambled_data = datacrunch.descramble(received_data)
    # catch error
    if '1 invalid base64' in descrambled_data.casefold() or '1 decompress error' in descrambled_data.casefold():
        returnmsg = descrambled_data
        return returnmsg

    comms.log(descrambled_data)

    # interpret received command
    command = descrambled_data.split(' ')[0]
    print(f'Command: {command}')


    ### init ############################################################################################
    if command == 'init':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            nonew = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[3])).decode('utf8').rstrip()
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
        if not database.connected_to_db(conn):
            returnmsg = f"1 Unable to decrypt and connect to existing server DB ({config.db_path}/{sessionuser}.encdb). Possibly wrong session password."
            return returnmsg

        # check if credentials exist
        credentials_ok = False
        created_new_db = False
        if database.credentials_exist(conn):
            # check if received credentials match db
            if database.credentials_match(conn, sessionuser, sessionpw):
                print(f"Credentials match previous record in DB. Reusing server DB for '{sessionuser}'.")
                credentials_ok = True
            # received credentials don't match
            else:
                returnmsg = f"1 User DB for '{sessionuser}' exists in server but provided password is wrong."

        # credentials don't exist since before
        else:
            if database.store_credentials(conn, sessionuser, sessionpw):
                print(f"No previous credentials for user '{sessionuser}' in DB. Saving.")
                credentials_ok = True
                created_new_db = True
            else:
                returnmsg = "1 Credentials storing unsuccessful."

        if credentials_ok:
            #create transporttoken
            transporttoken = datacrunch.generate_token(50)
            database.store_transporttoken(conn, transporttoken)
            if created_new_db:
                returnmsg = f"2 {transporttoken}"
            else:  # reused old db file, different response code
                returnmsg = f"3 {transporttoken}"
            db_written = database.write_inmem_db_to_file(conn, sessionuser, sessionpw)  # write encrypted db file
            if not db_written:
                returnmsg = f"1 Unable to write server DB to disk ({config.db_path}/{sessionuser}.encdb)."

        database.close_connection(conn)
        return returnmsg


    ### init-change ############################################################################################
    elif command == 'init-change':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            sessionnewuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[3])).decode('utf8').rstrip()
            sessionnewpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[4])).decode('utf8').rstrip()
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
        if not database.connected_to_db(conn):
            returnmsg = f"1 Unable to decrypt and connect to existing DB ({config.db_path}/{sessionuser}.encdb). Possibly wrong session password. Current session user and password must be verified to change them."
        elif not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Entered session credentials don't match DB records. Current user and session password must be verified to change them."
        else:
            dbfile_renamed = False

            # overwrite old credentials with new in DB
            credentials_stored = database.store_credentials(conn, sessionnewuser, sessionnewpw)

            # rename database file to new username
            if credentials_stored:
                # create transporttoken and save to db before renaming it
                transporttoken = datacrunch.generate_token(50)
                database.store_transporttoken(conn, transporttoken)

                # write encrypted db file with OLD username and NEW password since it's not renamed to new username yet
                db_written = database.write_inmem_db_to_file(conn, sessionuser, sessionnewpw)

                # renae encrypted db file to new username
                dbfile_renamed = file.rename_file(f'{config.db_path}/{sessionuser}.encdb', f'{config.db_path}/{sessionnewuser}.encdb')

            # return rename and credentials change result
            if credentials_stored and dbfile_renamed and db_written:
                print(f"Old credentials overwritten and DB file renamed successfully ({sessionuser} -> {sessionnewuser}).")
                returnmsg = f"2 {transporttoken}"
            elif not credentials_stored:
                returnmsg = "1 Credentials storing unsuccessful."
            elif credentials_stored and not dbfile_renamed:
                returnmsg = "1 Credentials stored but unable to rename DB file. Login will probably not work unless DB file is renamed."
            elif not db_written:
                returnmsg = "1 Unable to write changed DB to disk."

        database.close_connection(conn)
        return returnmsg


    ### status ##########################################################################################
    elif command == 'status':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            tokenmd5 = descrambled_data.split(' ')[3]
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

        # verify db connection
        if not database.connected_to_db(conn):
            returnmsg = f"1 Unable to decrypt and connect to existing server DB ({config.db_path}/{sessionuser}.encdb). Possibly wrong session password."
            return returnmsg

        # check and fetch transporttoken
        transporttoken = datacrunch.fetch_token_from_hash(conn, tokenmd5)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = f"1 Session credentials don't match server DB file ({config.db_path}/{sessionuser}.encdb)."
        elif not transporttoken:
            comms.log("Credentials match, but no matching transport encryption token found in DB that matches the client.")
            returnmsg = "1 No matching transport encryption token found in DB."
        else:
            print("Session check valid.")
            msg_to_encrypt = f"Success: Session check successful against server DB ({config.db_path}/{sessionuser}.encdb)."
            comms.log(f"returnmsg to encrypt: {msg_to_encrypt}")
            returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
            comms.log(f"encrypted returnmsg: {returnmsg}")
            returnmsg = f"2 {returnmsg}"
        database.close_connection(conn)
        return returnmsg


    ### add | update #####################################################################################
    elif command == 'add' or command == 'update':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            tokenmd5 = descrambled_data.split(' ')[3]
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

        # verify db connection
        if not database.connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong session password."
            return returnmsg

        # check and fetch transporttoken
        transporttoken = datacrunch.fetch_token_from_hash(conn, tokenmd5)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        elif not transporttoken:
            comms.log("Credentials match, but no matching transport encryption token found in DB that matches the client.")
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        print(descrambled_data.split(' ')[4])

        # transport decryption
        title = datacrunch.transport_decrypt(descrambled_data.split(' ')[4], transporttoken).rstrip()
        username = datacrunch.transport_decrypt(descrambled_data.split(' ')[5], transporttoken).rstrip()
        pw = datacrunch.transport_decrypt(descrambled_data.split(' ')[6], transporttoken).rstrip()
        extra = datacrunch.transport_decrypt(descrambled_data.split(' ')[7], transporttoken).rstrip()
        verification = datacrunch.transport_decrypt(descrambled_data.split(' ')[8], transporttoken).rstrip()

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
                        msg_to_encrypt = "Record stored in DB successfully."
                        comms.log(f"returnmsg to encrypt: {msg_to_encrypt}")
                        returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                        comms.log(f"encrypted returnmsg: {returnmsg}")
                        returnmsg = f"2 {returnmsg}"
                    else:  # update command used
                        print("Record updated in DB.")
                        msg_to_encrypt = "Record updated in DB successfully."
                        comms.log(f"returnmsg to encrypt: {msg_to_encrypt}")
                        returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                        comms.log(f"encrypted returnmsg: {returnmsg}")
                        returnmsg = f"2 {returnmsg}"
                else:
                    returnmsg = "1 Record storing unsuccessful."
        database.close_connection(conn)
        return returnmsg


    ### get ############################################################################################
    elif command == 'get':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            tokenmd5 = descrambled_data.split(' ')[3]
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

        # verify DB connection
        if not database.connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong session password."
            return returnmsg

        # check and fetch transporttoken
        transporttoken = datacrunch.fetch_token_from_hash(conn, tokenmd5)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        elif not transporttoken:
            comms.log("Credentials match, but no matching transport encryption token found in DB that matches the client.")
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # transport decryption
        title = datacrunch.transport_decrypt(descrambled_data.split(' ')[4], transporttoken).rstrip()
        comms.log(f"Getting title: {title}")
        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # get record, exact match or multimatch suggestions
        elif database.exact_title_exists(conn, title):
            record = database.get_record(conn, title)
            print("Record queried from DB.")
            comms.log(f"record to encrypt: {record}")
            encrypted_record = datacrunch.transport_encrypt(record, transporttoken)
            comms.log(f"encrypted returnmsg: {encrypted_record}")
            returnmsg = f"2 {encrypted_record}"
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            print("Partial match(es) only. List of partial matches queried from DB.")
            comms.log(f"records to encrypt: {records}")
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            comms.log(f"encrypted returnmsg: {encrypted_records}")
            returnmsg = f"3 {encrypted_records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = "1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        return returnmsg


    ### list ############################################################################################
    elif command == 'list':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            tokenmd5 = descrambled_data.split(' ')[3]
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

        # verify DB connection
        if not database.connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong session password."
            return returnmsg

        # check and fetch transporttoken
        transporttoken = datacrunch.fetch_token_from_hash(conn, tokenmd5)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        elif not transporttoken:
            comms.log("Credentials match, but no matching transport encryption token found in DB that matches the client.")
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # transport decryption
        title = datacrunch.transport_decrypt(descrambled_data.split(' ')[4], transporttoken).rstrip()

        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # if list all is requested
        elif title.casefold() == 'all'.casefold():
            records = database.list_all_title_records(conn)
            print("List of all record titles queried from DB.")
            comms.log(f"records to encrypt: {records}")
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            comms.log(f"encrypted returnmsg: {encrypted_records}")
            returnmsg = f"3 {encrypted_records}"
        # always get multimatch suggestions
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            print("List of partial matches queried from DB.")
            comms.log(f"records to encrypt: {records}")
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            comms.log(f"encrypted returnmsg: {encrypted_records}")
            returnmsg = f"3 {encrypted_records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = "1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        return returnmsg


    ### delete ############################################################################################
    elif command == 'delete':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            tokenmd5 = descrambled_data.split(' ')[3]
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

        # verify DB connection
        if not database.connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong session password."
            return returnmsg

        # check and fetch transporttoken
        transporttoken = datacrunch.fetch_token_from_hash(conn, tokenmd5)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        elif not transporttoken:
            comms.log("Credentials match, but no matching transport encryption token found in DB that matches the client.")
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # transport decryption
        title = datacrunch.transport_decrypt(descrambled_data.split(' ')[4], transporttoken).rstrip()

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
                msg_to_encrypt = "Record deleted from DB."
                comms.log(f"returnmsg to encrypt: {msg_to_encrypt}")
                returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                comms.log(f"encrypted returnmsg: {returnmsg}")
                returnmsg = f"2 {returnmsg}"
            else:
                returnmsg = "1 Error when deleting record from DB."

        # always get multimatch suggestions
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            print("Partial match(es) only. List of partial matches queried from DB instead of deleting.")
            comms.log(f"records to encrypt: {records}")
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            comms.log(f"encrypted returnmsg: {encrypted_records}")
            returnmsg = f"3 {encrypted_records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = "1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        return returnmsg


    ### backup ##########################################################################################
    elif command == 'backup':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            tokenmd5 = descrambled_data.split(' ')[3]
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

        # verify DB connection
        if not database.connected_to_db(conn):
            returnmsg = "1 Unable to decrypt and connect to existing DB. Possibly wrong session password."
            return returnmsg

        # check and fetch transporttoken
        transporttoken = datacrunch.fetch_token_from_hash(conn, tokenmd5)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            database.close_connection(conn)
            return returnmsg
        else:
            # dump DB into unencrypted file
            if database.write_inmem_db_to_file_unencrypted(conn, sessionuser):
                print(f"Decrypted DB file saved to {config.db_path}/{sessionuser}.db")
                msg_to_encrypt = f"Database successfully backed up to {config.db_path}/{sessionuser}.db in server."
                comms.log(f"returnmsg to encrypt: {msg_to_encrypt}")
                returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                comms.log(f"encrypted returnmsg: {returnmsg}")
                returnmsg = f"2 {returnmsg}"
            else:
                returnmsg = f"1 Unable to backup database as unencrypted to {config.db_path}/{sessionuser}.db in server."

        database.close_connection(conn)
        return returnmsg

    ### benchmark ##########################################################################################
    elif command == 'benchmark':
        try:
            sessionuser = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(descrambled_data.split(' ')[2])).decode('utf8').rstrip()
            tokenmd5 = descrambled_data.split(' ')[3]
        except Exception as b64decode_error:
            print(f"Error: Unable to decode base64 data: {b64decode_error}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            comms.log("DB exists.")

        # connect to db
        conn = database.create_connection(sessionuser, sessionpw)

        # verify db connection
        if not database.connected_to_db(conn):
            returnmsg = f"1 Unable to decrypt and connect to existing server DB ({config.db_path}/{sessionuser}.encdb). Possibly wrong session password."
            return returnmsg

        # check and fetch transporttoken
        transporttoken = datacrunch.fetch_token_from_hash(conn, tokenmd5)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = f"1 Session credentials don't match server DB file ({config.db_path}/{sessionuser}.encdb)."
        elif not transporttoken:
            comms.log("Credentials match, but no matching transport encryption token found in DB that matches the client.")
            returnmsg = "1 No matching transport encryption token found in DB."
        else:
            comms.log("Session check valid.")
            msg_to_encrypt = "benchverify"
            returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
            comms.log(f"encrypted returnmsg: {returnmsg}")
            returnmsg = f"2 {returnmsg}"
        database.close_connection(conn)
        return returnmsg


    ### no command matches ###############################################################################
    else:
        returnmsg = "1 Unknown command."
        return returnmsg