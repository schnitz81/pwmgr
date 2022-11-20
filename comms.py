import socket
import config
import parsing
import base64

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

    data = c.recv(4096)
    stringdata = data.decode('utf-8')

    # remove newline from input data
    base64stringdata = stringdata.rstrip()
    returnmsg = parsing.interpret_and_process(base64stringdata)

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

