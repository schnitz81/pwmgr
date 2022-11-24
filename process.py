import base64
import database
import file
import config


def interpret_and_process(base64stringdata):
    # decode base64
    try:
        debaseddata1 = base64.b64decode(base64stringdata)
        debaseddata2 = base64.b64decode(debaseddata1).rstrip()
    except Exception as b64decodeerror:
        print(f"Error: Unable to decode base64 data: {b64decodeerror}")
        returnmsg = "1 Invalid base64 data to decode."
        return returnmsg

    print(debaseddata2)

    debaseddata2 = debaseddata2.decode('utf8')

    # interpret received command
    command = debaseddata2.split(' ')[0]


    ### init ############################################################################################
    if command == 'init':
        try:
            sessionuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        except Exception as b64decodeerror:
            print(f"Error: Unable to decode base64 data: {b64decodeerror}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # Create DB if non-existent
        print(f"Connecting to {sessionuser} db.")
        conn = database.create_connection(sessionuser)

        # create tables if non-existent
        database.create_tables(conn)

        # check if credentials exist
        if database.credentials_exist(conn):
            # check if received credentials match db
            if database.credentials_match(conn, sessionuser, sessionpw):
                returnmsg = "2 Credentials match previous record. No change needed in server."
            # received credentials don't match
            else:
                returnmsg = "1 Error: User exists in server and provided password is wrong."

        # credentials don't exist since before
        else:
            credentials_stored = database.store_credentials(conn, sessionuser, sessionpw)
            if credentials_stored:
                returnmsg = "2 No previous credentials for user in DB. Saving."
            else:
                returnmsg = "1 Error: Credentials storing unsuccessful."
        print(returnmsg)
        database.close_connection(conn)
        return returnmsg

    ### init-change ############################################################################################
    elif command == 'init-change':
        try:
            sessionuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
            sessionnewuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[3])).decode('utf8').rstrip()
            sessionnewpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[4])).decode('utf8').rstrip()
        except Exception as b64decodeerror:
            print(f"Error: Unable to decode base64 data: {b64decodeerror}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Unable to change previous session. Create a new session and DB with init."
            print(returnmsg)
            return returnmsg
        else:
            print("DB exists.")

        print(f"Connecting to {sessionuser} db.")
        conn = database.create_connection(sessionuser)

        # create tables if non-existent
        database.create_tables(conn)

        # check if credentials exist
        if database.credentials_exist(conn):

            # check if received credentials match db
            if not database.credentials_match(conn, sessionuser, sessionpw):
                returnmsg = "1 Entered session credentials wrong. Current session user and password must be verified to change them."
                print(returnmsg)
                database.close_connection(conn)
                return returnmsg

            # received credentials match, overwrite
            else:
                dbfile_renamed = False

                # overwrite old credentials with new in DB
                credentials_stored = database.store_credentials(conn, sessionnewuser, sessionnewpw)
                database.close_connection(conn)

                # rename database file to new username
                if credentials_stored:
                    dbfile_renamed = file.rename_file(f'{config.db_path}/{sessionuser}.db', f'{config.db_path}/{sessionnewuser}.db')

                if credentials_stored and dbfile_renamed:
                    returnmsg = "2 Old credentials overwritten and db file renamed successfully."
                elif credentials_stored and not dbfile_renamed:
                    returnmsg = "1 Error: Credentials stored but unable to rename DB file. Login will probably not work unless DB file is renamed."
                elif not credentials_stored:
                    returnmsg = "1 Error: Credentials storing unsuccessful."
                print(returnmsg)
                return returnmsg

        # credentials don't exist since before
        else:
            returnmsg = "1. No previous credentials found. Unable to change."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg


    ### status ##########################################################################################
    elif command == 'status':
        try:
            sessionuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        except Exception as b64decodeerror:
            print(f"Error: Unable to decode base64 data: {b64decodeerror}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server session not aligned."
            print(returnmsg)
            return returnmsg
        else:
            print("DB exists.")

        print(f"Connecting to {sessionuser} db.")
        conn = database.create_connection(sessionuser)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
        else:
            returnmsg = "2 Session credentials received match server DB."
        database.close_connection(conn)
        print(returnmsg)
        return returnmsg

    ### add | update #####################################################################################
    elif command == 'add' or command == 'update':
        try:
            sessionuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
            title = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[3])).decode('utf8').rstrip()
        except Exception as b64decodeerror:
            print(f"Error: Unable to decode base64 data: {b64decodeerror}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg
        username = debaseddata2.split(' ')[4]
        pw = debaseddata2.split(' ')[5]
        extra = debaseddata2.split(' ')[6]
        verification = debaseddata2.split(' ')[7]

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server session not aligned."
            print(returnmsg)
            return returnmsg
        else:
            print("DB exists.")

        print(f"Connecting to {sessionuser} db.")
        conn = database.create_connection(sessionuser)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # avoid overwrite when add command is used
        if database.exact_title_exists(conn, title) and command != 'update':
            returnmsg = "1 Error: Record already exists. Use update to overwrite/change record."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        # don't create new record with update command
        elif not database.exact_title_exists(conn, title) and command == 'update':
            returnmsg = "1 Error: Record not found. Unable to update. Specify exact name to update."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg

        # store record
        record_stored = database.store_record(conn, title, username, pw, extra, verification)
        if record_stored:
            if command == 'add':  # return message depending on command used
                returnmsg = "2 Record stored in DB successfully."
            else:  # update command used
                returnmsg = "2 Record updated in DB successfully."
        else:
            returnmsg = "1 Error: Record storing unsuccessful."
        print(returnmsg)
        database.close_connection(conn)
        return returnmsg


    ### get ############################################################################################
    elif command == 'get':
        try:
            sessionuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        except Exception as b64decodeerror:
            print(f"Error: Unable to decode base64 data: {b64decodeerror}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg
        title = debaseddata2.split(' ')[3]

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server session not aligned."
            print(returnmsg)
            return returnmsg
        else:
            print("DB exists.")

        print(f"Connecting to {sessionuser} db.")
        conn = database.create_connection(sessionuser)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # get record, exact match or multimatch suggestions
        if database.exact_title_exists(conn, title):
            record = database.get_record(conn, title)
            returnmsg = f"2 {record}"
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            returnmsg = f"3 {records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = f"1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        print(returnmsg)
        return returnmsg


    ### list ############################################################################################
    elif command == 'list':
        try:
            sessionuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        except Exception as b64decodeerror:
            print(f"Error: Unable to decode base64 data: {b64decodeerror}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg
        title = debaseddata2.split(' ')[3]

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server session not aligned."
            print(returnmsg)
            return returnmsg
        else:
            print("DB exists.")

        print(f"Connecting to {sessionuser} db.")
        conn = database.create_connection(sessionuser)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # always get multimatch suggestions
        if database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            returnmsg = f"3 {records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = f"1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        print(returnmsg)
        return returnmsg


    ### delete ############################################################################################
    elif command == 'delete':
        try:
            sessionuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
            sessionpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        except Exception as b64decodeerror:
            print(f"Error: Unable to decode base64 data: {b64decodeerror}")
            returnmsg = "1 Invalid base64 data to decode."
            return returnmsg
        title = debaseddata2.split(' ')[3]

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{sessionuser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server session not aligned."
            print(returnmsg)
            return returnmsg
        else:
            print("DB exists.")

        print(f"Connecting to {sessionuser} db.")
        conn = database.create_connection(sessionuser)

        # verify session credentials
        if not database.credentials_match(conn, sessionuser, sessionpw):
            returnmsg = "1 Session credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Session credentials received match server DB.")

        # delete exact match
        if database.exact_title_exists(conn, title):
            record_deleted = database.delete_record(conn, title)
            if record_deleted:
                returnmsg = f"2 Record deleted."
                print(returnmsg)
            else:
                returnmsg = f"1 Error when deleting record from DB."
                print(returnmsg)

        # always get multimatch suggestions
        elif database.nbr_of_title_hits(conn, title) >= 1:
            records = database.list_partial_title_records(conn, title)
            returnmsg = f"3 {records}"
        elif database.nbr_of_title_hits(conn, title) < 1:
            returnmsg = f"1 No matching record found."
        else:
            returnmsg = "1 Unknown server error."
        database.close_connection(conn)
        print(returnmsg)
        return returnmsg

    ### no command matches ###############################################################################
    else:
        returnmsg = f"1 Unknown command."
        print(returnmsg)
        return returnmsg