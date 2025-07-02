import socket
import config
import process
import datacrunch
import bruteforcecheck
import os
import datetime
from _thread import *
import logging
from logging import log

FAILSTRINGS = [
    "password is wrong",
    "wrong password",
    "wrong session password",
    "credentials wrong",
    "credentials don't match",
    "doesn't exist",
    "invalid base64",
    "no matching transport encryption token"
]


def threaded(connsock, addr):

    # check IP ban
    if not bruteforcecheck.is_allowed_to_login(addr[0]):
        returnmsg = "1 Error: Client IP banned."
    else:
        try:
            data = connsock.recv(16384)
        except ConnectionResetError as conn_error:
            log(f"Connection reset error: {conn_error}", 0)
            # disconnect the server
            connsock.close()
            return

        # generate response
        returnmsg = process.interpret_and_process(data)

        # add to failed login list if credentials are wrong
        if returnmsg[0] == '1':  # if an error will be returned
            for i in range(len(FAILSTRINGS)):
                if FAILSTRINGS[i].casefold() in returnmsg.casefold():  # check if error is caused by unauthorized behaviour
                    bruteforcecheck.failed_auth(addr[0])
    log(f"returnmsg to parse: {returnmsg}", 2)

    # encode response
    returnmsg = datacrunch.transport_encode(returnmsg)

    try:
        connsock.send(returnmsg.encode('utf-8'))
        if logging.benchmark_running_counter < 2:
            log("Responded.", 1)
            if logging.benchmark_running_counter == 1:
                log("Benchmark started. Suppressing output for following benchmark connections.", 1)
    except Exception as send_e:
        log("Response send error:", 0)
        log(send_e, 0)
    # disconnect the server
    connsock.close()


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
            log("Error: Port number needs to be defined in either config file or as PORT env variable.", 0)
            exit(1)
    if 'HOST' in os.environ:  # host var
        host = os.environ['HOST']
    else:
        try:
            host = config.host
        except:
            log("Error: Host address needs to be defined in either config file ('host') or as HOST env variable.", 0)
            exit(1)

    # create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind the socket with server and port number
    s.bind((host, port))

    # maximum connections allowed to the socket
    s.listen(5)

    while True:
        connsock, addr = s.accept()

        # display client address
        if logging.benchmark_running_counter == 0:
            log(f"{datetime.datetime.now()} -------------------------------------------", 1)
            log(f"Connection from: {str(addr)}", 1)

        # create thread to handle connection
        start_new_thread(threaded, (connsock, addr))
