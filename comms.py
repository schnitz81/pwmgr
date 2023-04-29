import socket
import config
import process
import base64
import bruteforcecheck


FAILSTRINGS = [
    "password is wrong",
    "credentials wrong",
    "credentials don't match",
    "DB doesn't exist"
]


def tcp_listen_and_reply():

    # take the server name and port name
    host = config.host
    port = config.port

    # create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind the socket with server and port number
    s.bind((host, port))

    # allow maximum 1 connection to the socket
    s.listen(1)

    c, addr = s.accept()

    # display client address
    print("------------------------------------")
    print("connection from:", str(addr))

    # check IP ban
    if not bruteforcecheck.is_allowed_to_login(addr[0]):
        returnmsg = "1 Error: Client IP banned."
    else:
        data = c.recv(4096)
        stringdata = data.decode('utf-8')

        # remove newline from input data
        base64stringdata = stringdata.rstrip()
        returnmsg = process.interpret_and_process(base64stringdata)

        # add to failed login list if credentials are wrong
        for i in range(len(FAILSTRINGS)):
            if FAILSTRINGS[i] in returnmsg:
                bruteforcecheck.failed_auth(addr[0])

    try:
        returnmsg = base64.b64encode(base64.b64encode(returnmsg.encode("utf-8")))
    except Exception as returnmsg_e:
        print(returnmsg_e)
        returnmsg = f"1 {returnmsg_e}"
        returnmsg = base64.b64encode(base64.b64encode(returnmsg.encode("utf-8")))

    print(f"Parsed returnmsg: {returnmsg}")
    try:
        c.send(returnmsg)
        print("Responded.")
    except Exception as send_e:
        print("Response send error:")
        print(send_e)

    # disconnect the server
    c.close()

