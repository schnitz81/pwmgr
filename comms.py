import socket
import config
import process
import base64
import zlib
import bruteforcecheck
import os
import datetime


FAILSTRINGS = [
    "password is wrong",
    "wrong password",
    "wrong session password",
    "credentials wrong",
    "credentials don't match",
    "doesn't exist",
    "Invalid base64"
]


def tcp_listen_and_reply():

    # set the server name and port name from env var if existing, otherwise config file
    port = None
    host = None
    if 'PORT' in os.environ:  # port var
        port = int(os.environ['PORT'])
    else:
        try:
            port = int(config.port)
        except:
            print("Error: Port number needs to be defined in either config file or as PORT env variable.")
            exit(1)
    if 'HOST' in os.environ:  # host var
        host = os.environ['HOST']
    else:
        try:
            host = config.host
        except:
            print("Error: Host address needs to be defined in either config file ('host') or as HOST env variable.")
            exit(1)

    # create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind the socket with server and port number
    s.bind((host, port))

    # allow maximum 1 connection to the socket
    s.listen(1)

    c, addr = s.accept()

    # display client address
    print(datetime.datetime.now(), " -------------------------------------------")
    print("Connection from:", str(addr))

    # check IP ban
    if not bruteforcecheck.is_allowed_to_login(addr[0]):
        returnmsg = "1 Error: Client IP banned."
    else:
        try:
            data = c.recv(16384)
        except ConnectionResetError as conn_error:
            print(f"Connection reset error: {conn_error}")
            # disconnect the server
            c.close()
            return

        # generate response
        returnmsg = process.interpret_and_process(data)

        # add to failed login list if credentials are wrong
        if returnmsg[0] == '1':  # if an error will be returned
            for i in range(len(FAILSTRINGS)):
                if FAILSTRINGS[i] in returnmsg:  # check if error is caused by unauthorized behaviour
                    bruteforcecheck.failed_auth(addr[0])
    log(returnmsg)

    try:
        # encode response
        returnmsg = base64.b64encode(process.b64swap(base64.b64encode(zlib.compress(returnmsg.encode("utf-8"), 1, wbits=zlib.MAX_WBITS | 16))))
    except Exception as returnmsg_e:
        print(returnmsg_e)
        returnmsg = f"1 {returnmsg_e}"
        returnmsg = base64.b64encode(process.b64swap(base64.b64encode(zlib.compress(returnmsg.encode("utf-8"), 1, wbits=zlib.MAX_WBITS | 16))))
    log(f"Parsed returnmsg: {returnmsg}")

    try:
        c.send(returnmsg)
        print("Responded.")
    except Exception as send_e:
        print("Response send error:")
        print(send_e)
    # disconnect the server
    c.close()


def log(msg):
    # set verbose output from env var if existing, otherwise config file
    verbose_output = None
    if 'VERBOSE_OUTPUT' in os.environ:
        if os.environ['VERBOSE_OUTPUT'].casefold() == 'true' or os.environ['VERBOSE_OUTPUT'] == 1 or os.environ['VERBOSE_OUTPUT'].casefold() == 'yes':
            verbose_output = True
    else:
        try:
            if config.verbose_output.casefold() == 'true' or config.verbose_output == 1 or config.verbose_output.casefold() == 'yes':
                verbose_output = True
        except NameError:
            print("Error: verbose_output needs to be defined as true/false in either config file or as VERBOSE_OUTPUT env variable.")
            exit(1)

    if verbose_output:
        print(msg)
