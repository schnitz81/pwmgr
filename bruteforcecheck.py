import socket
import time
from collections import defaultdict


# parameters
BANTIME = 300
MAX_TRIES_WITHIN_INTERVAL = 5
INTERVAL = 120

# globals
bantable = {}
failtable = defaultdict(list)


def is_valid_ipv4(address):
    # check if address is in valid IPv4 format
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False
    return True


def is_allowed_to_login(ip):

    # verify ipv4 format
    try:
        if not is_valid_ipv4(ip):
            raise ValueError("Error: not a valid IP address.")
    except ValueError as e:
        print(e)
        return False

    epochnow = int(time.time())

    if ip in bantable:  # always allow if IP is missing in bantable
        # deny login if ban timestamp is later than now minus ban length
        if bantable[ip] > epochnow - BANTIME:
            return False
        else:
            # delete ip from bantable if ban expired
            del bantable[ip]
    return True


def failed_auth(ip):

    # verify ipv4 format
    try:
        if not is_valid_ipv4(ip):
            raise ValueError("Error: not a valid IP address.")
    except ValueError as e:
        print(e)
        return

    epochnow = int(time.time())

    # add ip and epochnow to list
    failtable[ip].append(epochnow)

    for epoch in failtable[ip]:
        # remove expired
        if epoch > epochnow - INTERVAL:
            break
        else:
            failtable[ip].remove(epoch)

    # ban IP if enough fail records within interval remain
    if len(failtable[ip]) >= MAX_TRIES_WITHIN_INTERVAL:
        bantable[ip] = epochnow
