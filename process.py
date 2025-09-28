import database
import file
import datacrunch
import config
import logging
from logging import log


def interpret_and_process(received_data):

    # decode received data
    transportdecoded_data = datacrunch.transport_decode(received_data)
    # catch error
    if '1 invalid base64' in transportdecoded_data.casefold() or '1 decompress error' in transportdecoded_data.casefold() or "1 Decrypt error" in transportdecoded_data.casefold():
        returnmsg = transportdecoded_data
        return returnmsg

    log(transportdecoded_data, 2)

    # interpret received command
    command = transportdecoded_data.split(' ')[0]

    # reset benchmark counter at any other command except 'benchmark'
    if command != 'benchmark':
        logging.benchmark_running_counter = 0

    if logging.benchmark_running_counter == 0:
        log(f'Command: {command}', 1)

    ### init ############################################################################################
    if command == 'init':
        try:
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            nonew = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # only create new DB if nonew isn't set
        if bool(int(nonew)) and not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            log(f"Error: nonew selected and user DB ({config.db_path}/{sessionuser}.encdb) doesn't exist.", 0)
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
                log(f"Credentials match previous record in DB. Reusing server DB for '{sessionuser}'.", 1)
                credentials_ok = True
            # received credentials don't match
            else:
                returnmsg = f"1 User DB for '{sessionuser}' exists in server but provided password is wrong."

        # credentials don't exist since before
        else:
            if database.store_credentials(conn, sessionuser, sessionpw):
                log(f"No previous credentials for user '{sessionuser}' in DB. Saving.", 1)
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
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            sessionnewuser = str(transportdecoded_data.split(' ')[3]).rstrip()
            sessionnewpw = str(transportdecoded_data.split(' ')[4]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            log("DB exists.", 1)

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
                # create transporttoken and save to db before renaming db file
                transporttoken = datacrunch.generate_token(50)
                database.store_transporttoken(conn, transporttoken)

                # write encrypted db file with OLD username and NEW password since it's not renamed to new username yet
                db_written = database.write_inmem_db_to_file(conn, sessionuser, sessionnewpw)

                # renae encrypted db file to new username
                dbfile_renamed = file.rename_file(f'{config.db_path}/{sessionuser}.encdb', f'{config.db_path}/{sessionnewuser}.encdb')

            # return rename and credentials change result
            if credentials_stored and dbfile_renamed and db_written:
                log(f"Old credentials overwritten and DB file renamed successfully ({sessionuser} -> {sessionnewuser}).", 1)
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
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            tokenmd5 = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            log("DB exists.", 1)

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
            log("Credentials match, but no matching transport encryption token found in DB that matches the client.", 2)
            returnmsg = "1 No matching transport encryption token found in DB."
        else:
            log("Session check valid.", 1)
            msg_to_encrypt = f"Success: Session check successful against server DB ({config.db_path}/{sessionuser}.encdb)."
            log(f"returnmsg to encrypt: {msg_to_encrypt}", 2)
            returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
            log(f"encrypted returnmsg: {returnmsg}", 2)
            returnmsg = f"2 {returnmsg}"
        database.close_connection(conn)
        return returnmsg


    ### add | update #####################################################################################
    elif command == 'add' or command == 'update':
        try:
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            tokenmd5 = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            log("DB exists.", 1)

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
            log("Credentials match, but no matching transport encryption token found in DB that matches the client.", 2)
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            log("Session credentials received match server DB.", 1)

        log(transportdecoded_data.split(' ')[4], 2)

        # transport decryption
        title = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[4], transporttoken).rstrip()
        username = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[5], transporttoken).rstrip()
        pw = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[6], transporttoken).rstrip()
        extra = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[7], transporttoken).rstrip()
        verification = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[8], transporttoken).rstrip()

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
                        log("Record added to DB.", 1)
                        msg_to_encrypt = "Record stored in DB successfully."
                        log(f"returnmsg to encrypt: {msg_to_encrypt}", 2)
                        returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                        log(f"encrypted returnmsg: {returnmsg}", 2)
                        returnmsg = f"2 {returnmsg}"
                    else:  # update command used
                        log("Record updated in DB.", 1)
                        msg_to_encrypt = "Record updated in DB successfully."
                        log(f"returnmsg to encrypt: {msg_to_encrypt}", 2)
                        returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                        log(f"encrypted returnmsg: {returnmsg}", 2)
                        returnmsg = f"2 {returnmsg}"
                else:
                    returnmsg = "1 Record storing unsuccessful."
        database.close_connection(conn)
        return returnmsg


    ### get ############################################################################################
    elif command == 'get':
        try:
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            tokenmd5 = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            log("DB exists.", 1)

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
            log("Credentials match, but no matching transport encryption token found in DB that matches the client.", 2)
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            log("Session credentials received match server DB.", 1)

        # transport decryption
        title = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[4], transporttoken).rstrip()
        log(f"Getting title: {title}", 2)
        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # get record, exact match or multimatch suggestions
        elif database.exact_title_exists(conn, title):
            record = database.get_record(conn, title)
            log("Record queried from DB.", 1)
            log(f"record to encrypt: {record}", 2)
            encrypted_record = datacrunch.transport_encrypt(record, transporttoken)
            log(f"encrypted returnmsg: {encrypted_record}", 2)
            returnmsg = f"2 {encrypted_record}"
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            log("Partial match(es) only. List of partial matches queried from DB.", 1)
            log(f"records to encrypt: {records}", 2)
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            log(f"encrypted returnmsg: {encrypted_records}", 2)
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
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            tokenmd5 = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as b64decode_error:
            log(f"Error: Unable to decode base64 data: {b64decode_error}", 0)
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            log("DB exists.", 1)

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
            log("Credentials match, but no matching transport encryption token found in DB that matches the client.", 2)
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            log("Session credentials received match server DB.", 1)

        # transport decryption
        title = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[4], transporttoken).rstrip()

        # if letter is missing in title
        if not any(c.isalpha() for c in title):
            returnmsg = "1 Invalid title name. At least one letter is required."

        # if list all is requested
        elif title.casefold() == 'all'.casefold():
            records = database.list_all_title_records(conn)
            log("List of all record titles queried from DB.", 1)
            log(f"records to encrypt: {records}", 2)
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            log(f"encrypted returnmsg: {encrypted_records}", 2)
            returnmsg = f"3 {encrypted_records}"
        # always get multimatch suggestions
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            log("List of partial matches queried from DB.", 1)
            log(f"records to encrypt: {records}", 2)
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            log(f"encrypted returnmsg: {encrypted_records}", 2)
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
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            tokenmd5 = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            log("DB exists.", 1)

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
            log("Credentials match, but no matching transport encryption token found in DB that matches the client.", 2)
            returnmsg = "1 No matching transport encryption token found in DB."
            return returnmsg
        else:
            log("Session credentials received match server DB.", 1)

        # transport decryption
        title = datacrunch.transport_decrypt(transportdecoded_data.split(' ')[4], transporttoken).rstrip()

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
                log("Record deleted from DB.", 1)
                msg_to_encrypt = "Record deleted from DB."
                log(f"returnmsg to encrypt: {msg_to_encrypt}", 2)
                returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                log(f"encrypted returnmsg: {returnmsg}", 2)
                returnmsg = f"2 {returnmsg}"
            else:
                returnmsg = "1 Error when deleting record from DB."

        # always get multimatch suggestions
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            log("Partial match(es) only. List of partial matches queried from DB instead of deleting.", 1)
            log(f"records to encrypt: {records}", 2)
            encrypted_records = datacrunch.transport_encrypt(records, transporttoken)
            log(f"encrypted returnmsg: {encrypted_records}", 2)
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
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            tokenmd5 = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 Encrypted DB file ({config.db_path}/{sessionuser}.encdb) not found in server. Unable to dump DB into backup file."
            return returnmsg
        else:
            log("DB exists.", 1)

        # create old backup if backup already exists
        if file.file_exists(f'{config.db_path}/{sessionuser}.db'):
            log(f"{config.db_path}/{sessionuser}.db already exists. Renaming to .old", 2)
            file.rename_file(f'{config.db_path}/{sessionuser}.db', f'{config.db_path}/{sessionuser}.db.old')

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
                log(f"Decrypted DB file saved to {config.db_path}/{sessionuser}.db", 1)
                msg_to_encrypt = f"Database successfully backed up to {config.db_path}/{sessionuser}.db in server."
                log(f"returnmsg to encrypt: {msg_to_encrypt}", 2)
                returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
                log(f"encrypted returnmsg: {returnmsg}", 2)
                returnmsg = f"2 {returnmsg}"
            else:
                returnmsg = f"1 Unable to backup database as unencrypted to {config.db_path}/{sessionuser}.db in server."

        database.close_connection(conn)
        return returnmsg


    ### benchmark ##########################################################################################
    elif command == 'benchmark':
        try:
            sessionuser = str(transportdecoded_data.split(' ')[1]).rstrip()
            sessionpw = str(transportdecoded_data.split(' ')[2]).rstrip()
            tokenmd5 = str(transportdecoded_data.split(' ')[3]).rstrip()
        except Exception as transportdecoded_data_err:
            log(f"Error: Unable to interpret decoded transport data: {transportdecoded_data_err}", 0)
            returnmsg = "1 Unable to fetch valid input parameters from received data."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.encdb'):
            returnmsg = f"1 DB file ({config.db_path}/{sessionuser}.encdb) doesn't exist in server. Client and server session not aligned."
            return returnmsg
        else:
            log("DB exists.", 2)

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
            log("Credentials match, but no matching transport encryption token found in DB that matches the client.", 2)
            returnmsg = "1 No matching transport encryption token found in DB."
        else:
            log("Session check valid.", 2)
            msg_to_encrypt = "benchverify"
            returnmsg = datacrunch.transport_encrypt(msg_to_encrypt, transporttoken)
            log(f"encrypted returnmsg: {returnmsg}", 2)
            returnmsg = f"2 {returnmsg}"

            # increase benchmark counter for logging suppression at non-verbose logging
            logging.benchmark_running_counter += 1

        database.close_connection(conn)
        return returnmsg


    ### no command matches ###############################################################################
    else:
        returnmsg = "1 Unknown command."
        return returnmsg