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
        print(f"Error: Unable to decode json data: {b64decodeerror}")

    print(debaseddata2)

    debaseddata2 = debaseddata2.decode('utf8')

    # interpret received command
    command = debaseddata2.split(' ')[0]


    ### init ############################################################################################
    if command == 'init':
        serveruser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
        serverpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        print(f"Connecting to {serveruser} db.")
        conn = database.create_connection(serveruser)

        # create tables if non-existent
        database.create_tables(conn)

        # check if credentials exist
        if database.credentials_exist(conn):

            # check if received credentials match db
            if database.credentials_match(conn, serveruser, serverpw):
                returnmsg = "2 Credentials match previous record. No change needed in server."
                print(returnmsg)
                database.close_connection(conn)
                return returnmsg

            # received credentials don't match
            else:
                returnmsg = "1 Error: User exists in server and provided password is wrong."
                print(returnmsg)
                database.close_connection(conn)
                return returnmsg

        # credentials don't exist since before
        else:
            credentials_stored = database.store_credentials(conn, serveruser, serverpw)
            if credentials_stored:
                returnmsg = "2 No previous credentials for user in DB. Saving."
            else:
                returnmsg = "1 Error: Credentials storing unsuccessful."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg

    ### init-change ############################################################################################
    elif command == 'init-change':
        serveruser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
        serverpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        servernewuser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[3])).decode('utf8').rstrip()
        servernewpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[4])).decode('utf8').rstrip()
        print(f"Connecting to {serveruser} db.")
        conn = database.create_connection(serveruser)

        # create tables if non-existent
        database.create_tables(conn)

        # check if credentials exist
        if database.credentials_exist(conn):

            # check if received credentials match db
            if not database.credentials_match(conn, serveruser, serverpw):
                returnmsg = "1 Current credentials wrong. Current user and password must be verified to change serveruser and serverpassword."
                print(returnmsg)
                database.close_connection(conn)
                return returnmsg

            # received credentials match, overwrite
            else:
                dbfile_renamed = False

                # overwrite old credentials with new in DB
                credentials_stored = database.store_credentials(conn, servernewuser, servernewpw)
                database.close_connection(conn)

                # rename database file to new username
                if credentials_stored:
                    dbfile_renamed = file.rename_file(f'{config.db_path}/{serveruser}.db', f'{config.db_path}/{servernewuser}.db')

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


    ### add | update #####################################################################################
    elif command == 'add' or command == 'update':
        serveruser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
        serverpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        title = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[3])).decode('utf8').rstrip()
        username = debaseddata2.split(' ')[4]
        pw = debaseddata2.split(' ')[5]
        extra = debaseddata2.split(' ')[6]
        verification = debaseddata2.split(' ')[7]
        print(f"Connecting to {serveruser} db.")
        conn = database.create_connection(serveruser)


        # verify db existence
        if not file.file_exists(f'{config.db_path}/{serveruser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server init not aligned."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("DB exists.")

        # connect db
        conn = database.create_connection(serveruser)

        # verify server credentials
        if not database.credentials_match(conn, serveruser, serverpw):
            returnmsg = "1 Server credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Server credentials match.")

        # avoid overwrite when add command is used
        if database.exact_title_exists(conn, title) and command != 'update':
            returnmsg = "1 Error: Record already exists. Use update to overwrite/change password."
            print(returnmsg)
            return returnmsg

        # don't create new record with update command
        elif not database.exact_title_exists(conn, title) and command == 'update':
            returnmsg = "1 Error: Record not found. Unable to update. Specify exact name to update."
            print(returnmsg)
            return returnmsg

        # store record
        record_stored = database.store_record(conn, title, username, pw, extra, verification)
        if record_stored:
            if command == 'add':  # return message depending on command used
                returnmsg = "2 Record stored in DB successfully."
            else:
                returnmsg = "2 Record updated in DB successfully."
        else:
            returnmsg = "1 Error: Record storing unsuccessful."
        print(returnmsg)
        database.close_connection(conn)
        return returnmsg


    ### get ############################################################################################
    elif command == 'get':
        serveruser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
        serverpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        title = debaseddata2.split(' ')[3]
        print(f"Connecting to {serveruser} db.")
        conn = database.create_connection(serveruser)

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{serveruser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server init not aligned."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("DB exists.")

        # connect db
        conn = database.create_connection(serveruser)

        # verify server credentials
        if not database.credentials_match(conn, serveruser, serverpw):
            returnmsg = "1 Server credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Server credentials match.")

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
        serveruser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
        serverpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        title = debaseddata2.split(' ')[3]
        print(f"Connecting to {serveruser} db.")
        conn = database.create_connection(serveruser)

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{serveruser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server init not aligned."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("DB exists.")

        # connect db
        conn = database.create_connection(serveruser)

        # verify server credentials
        if not database.credentials_match(conn, serveruser, serverpw):
            returnmsg = "1 Server credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Server credentials match.")

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
        serveruser = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[1])).decode('utf8').rstrip()
        serverpw = base64.b64decode(base64.b64decode(debaseddata2.split(' ')[2])).decode('utf8').rstrip()
        title = debaseddata2.split(' ')[3]
        print(f"Connecting to {serveruser} db.")
        conn = database.create_connection(serveruser)

        # verify db existence
        if not file.file_exists(f'{config.db_path}/{serveruser}.db'):
            returnmsg = "1 Error: DB doesn't exist. Client and server init not aligned."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("DB exists.")

        # connect db
        conn = database.create_connection(serveruser)

        # verify server credentials
        if not database.credentials_match(conn, serveruser, serverpw):
            returnmsg = "1 Server credentials don't match DB."
            print(returnmsg)
            database.close_connection(conn)
            return returnmsg
        else:
            print("Server credentials match.")

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
            print(returnmsg)
        else:
            returnmsg = "1 Unknown server error."
            print(returnmsg)
        database.close_connection(conn)
        return returnmsg

    else:
        returnmsg = f"1 Unknown command."
        print(returnmsg)
        return returnmsg