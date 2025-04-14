import subprocess
import pexpect
from flask import flash
import re


def test():
    try:
        value = subprocess.run(f'''
                pwmgr status
            ''',
            shell=True, check=True,
            executable='/bin/bash',
            capture_output=True,
            text=True)
        return value.stdout
    except Exception as test_e:
        print(test_e)


def init(server, sessionuser, sessionpw, new):
    try:
        log('Init handshake...')
        if not new:
            child = pexpect.spawnu('pwmgr init --nonew', timeout=5, maxread=1, encoding='utf-8')
        else:
            child = pexpect.spawnu('pwmgr init', timeout=5, maxread=1, encoding='utf-8')
        child.expect(r'\?\s*$')
        child.sendline('Y')
        child.expect(r':\s*$')
        child.sendline(f'{server}')
        child.expect(r':\s*$')
        child.sendline(f'{sessionuser}')
        child.expect(r':\s*$')
        child.sendline(f'{sessionpw}')
        child.expect(r':\s*$')
        child.sendline(f'{sessionpw}')
        child.read_nonblocking()
        output = child.read().split('\n')
        print(f'init: {output}')
        for line in output:
            if 'nonew selected' in line:
                log('Entered user not found. Check username or create a new user by adding a new record.')
                return False
            elif 'Server error' in line:
                log(line)
                return False
            elif 'Error:' in line:
                log(line)
                return False
            elif 'No previous credentials' in line:
                log('Session user not found. Created new user with entered session credentials.')
        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Subprocess did not exit gracefully.')
        else:
            print('Subprocess exited gracefully.')
        return True

    except Exception as init_e:
        print(init_e)


def get(title, encryptionpw):
    # initialize return values
    fetched_title = username = pw = extra = ""
    try:
        child = pexpect.spawn(f'pwmgr get "{title}" --nomask', timeout=50, maxread=1, encoding='utf-8')
        respondalts = child.expect([r':\s*$', pexpect.TIMEOUT])
        if respondalts == 0:
            child.sendline(f'{encryptionpw}')
        log('Fetching...')

        child.read_nonblocking()
        output = child.read().split('\n')

        print(f'get: data received from client, sorting fields...')
        for line in output:
            if 'Server error' in line:
                log(line)
            elif 'name can\'t be blank' in line:
                log('Name seems to be blank')
            elif 'Wrong encryption password' in line:
                log('Wrong encryption password')
            elif 'No matching record found' in line:
                log('No matching record found.')
            elif 'Specify exact title' in line:
                log('Partly matched titles found. Use search to list.')
            elif 'title:' in line:
                pattern = r'title:\s(.*?)\r'
                fetched_title = re.search(pattern, line).group(1).strip()
            elif 'username:' in line:
                pattern = r'username:\s(.*?)\r'
                username = re.search(pattern, line).group(1).strip()
            elif 'password (hidden):' in line or 'password:' in line:
                pw = line.rsplit()[-1]
            elif 'extra info:' in line:
                pattern = r'extra\sinfo:\s(.*?)\r'
                extra = re.search(pattern, line).group(1).strip()

        # title output crop fix
        if fetched_title == '' and 'username:' in output[1]:
            fetched_title = output[0]
        elif fetched_title == '' and 'username:' in output[2]:
            fetched_title = output[0]

        print(f"fetched title: {fetched_title}")

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Subprocess did not exit gracefully.')
        else:
            print('Subprocess exited gracefully.')

    except Exception as get_e:
        print(get_e)

    return fetched_title, username, pw, extra


def delete_session():
    try:
        value = subprocess.run(f'''
                PWMGR_CLIENT_PATH=$(which pwmgr)
                SESSIONPATH=$(grep -m 1 'SESSIONPATH' $PWMGR_CLIENT_PATH | cut -f 2 -d '"')
                eval rm -f $SESSIONPATH
            ''',
            shell=True, check=True,
            executable='/bin/bash',
            capture_output=True,
            text=True)
        return value.stdout
    except Exception as test_e:
        print(test_e)


def search(title):
    found_records = False
    try:
        child = pexpect.spawnu('pwmgr search', timeout=50, maxread=1, encoding='utf-8')
        child.expect(r':\s*$')
        child.sendline(f'{title}')
        log('Fetching...')
        output = child.read().split('\n')
        print(f'search: {output}')
        for line in output:
            if 'Server error' in line:
                log(line)
            elif 'Records found' in line:
                found_records = True
            if found_records:
                log(line)

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Subprocess did not exit gracefully.')
        else:
            print('Subprocess exited gracefully.')

    except Exception as search_e:
        print(search_e)

def add(title, username, pw, extra, encryptionpw, overwrite):
    success = False
    try:
        child = pexpect.spawnu('pwmgr add', timeout=5, maxread=1, encoding='utf-8')
        log('Adding...')
        child.expect(r':\s*$')
        child.sendline(f'{title}')
        child.expect(r':\s*$')
        child.sendline(f'{username}')
        child.expect(r':\s*$')
        child.sendline(f'{pw}')
        child.expect(r':\s*$')
        child.sendline(f'{pw}')
        child.expect(r':\s*$')
        child.sendline(f'{extra}')
        child.expect(r':\s*$')
        child.sendline(f'{encryptionpw}')
        child.expect(r':\s*$')
        child.sendline(f'{encryptionpw}')

        # Output pw similarity message before buffer read because exception will make later conditions miss it.
        if pw == encryptionpw:
            log('Record password and encryption password can\'t be the same.')

        output = child.read().split('\n')
        print(f'add: {output}')
        for line in output:
            if 'already exists' in line:
                log('Title already exists in DB.')
                if overwrite:
                    log('Overwrite selected. Proceeding to update existing record.')
                    success = update(title, username, pw, extra, encryptionpw)
                    break
                else:
                    log('Choose overwrite to update existing record.')
            elif 'error'.casefold() in line:
                log(line)
                success = False
            elif 'successfully' in line:
                success = True

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Subprocess did not exit gracefully.')
        else:
            print('Subprocess exited gracefully.')
        return success

    except Exception as add_e:
        print(add_e)


def update(title, username, pw, extra, encryptionpw):
    success = False
    try:
        child = pexpect.spawnu('pwmgr update', timeout=50, maxread=1, encoding='utf-8')
        log('Updating...')
        child.expect(r':\s*$')
        child.sendline(f'{title}')
        child.expect(r':\s*$')
        child.sendline(f'{username}')
        child.expect(r':\s*$')
        child.sendline(f'{pw}')
        child.expect(r':\s*$')
        child.sendline(f'{pw}')
        child.expect(r':\s*$')
        child.sendline(f'{extra}')
        child.expect(r':\s*$')
        child.sendline(f'{encryptionpw}')
        child.expect(r':\s*$')
        child.sendline(f'{encryptionpw}')
        output = child.read().split('\n')
        print(f'update: {output}')
        for line in output:
            if 'error'.casefold() in line:
                log(line)
                success = False
            elif 'successfully' in line:
                success = True

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Subprocess did not exit gracefully.')
        else:
            print('Subprocess exited gracefully.')
        return success

    except Exception as update_e:
        print(update_e)


def delete(title):
    deleted = False
    try:
        child = pexpect.spawnu('pwmgr delete', timeout=50, maxread=1, encoding='utf-8')
        child.expect(r':\s*$')
        child.sendline(f'{title}')
        log('Deleting...')
        output = child.read().split('\n')
        print(f'delete: {output}')
        for line in output:
            if 'Server error' in line:
                log(line)
            elif 'deleted' in line:
                deleted = True

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Subprocess did not exit gracefully.')
        else:
            print('Subprocess exited gracefully.')
        return deleted

    except Exception as delete_e:
        print(delete_e)


def log(msg):
    flash(msg)
    print(msg)
