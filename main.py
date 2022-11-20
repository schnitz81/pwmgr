import comms


def main():
    while True:
        comms.tcp_listen_and_reply()


if __name__ == '__main__':
    main()
