import subprocess
import pexpect
from flask import flash


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


def init(server, sessionuser, sessionpw):
    try:
        flash('Init handshake...')
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
            if 'Server error' in line:
                flash(line)
                return False
            elif 'Error:' in line:
                flash(line)
                return False
        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Child did not exit gracefully.')
        else:
            print('Child exited gracefully.')
        return True

    except Exception as init_e:
        print(init_e)


def get(title, encryptionpw):
    # initialize return values
    fetched_title = username = pw = extra = ""
    try:
        child = pexpect.spawn(f'pwmgr get {title} --nomask', timeout=50, maxread=1, encoding='utf-8')
        respondalts = child.expect([r':\s*$', pexpect.TIMEOUT])
        if respondalts == 0:
            child.sendline(f'{encryptionpw}')
        flash('Fetching...')
        print('Fetching...')

        child.read_nonblocking()
        output = child.read().split('\n')

        print(f'get: data received from client, sorting fields...')
        for line in output:
            if 'Server error' in line:
                flash(line)
            elif 'can\'t be blank' in line:
                flash('Name seems to be blank')
            elif 'Wrong encryption/decryption password' in line:
                flash('Wrong encryption/decryption password')
            elif 'No matching record found' in line:
                flash('No matching record found.')
            elif 'Specify exact title' in line:
                flash('Partly matched titles found. Use search to list.')
            elif 'title:' in line:
                fetched_title = line.rsplit()[-1]
            elif 'username:' in line:
                username = line.rsplit()[-1]
            elif 'password (hidden):' in line or 'password:' in line:
                pw = line.rsplit()[-1]
            elif 'extra info:' in line:
                extra = line.rsplit()[-1]
                if extra == 'info:':
                    extra = ''

        # title output crop fix
        if fetched_title == '' and 'username:' in output[1]:
            fetched_title = output[0]

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Child did not exit gracefully.')
        else:
            print('Child exited gracefully.')

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
        flash('Fetching...')
        output = child.read().split('\n')
        print(f'search: {output}')
        for line in output:
            if 'Server error' in line:
                flash(line)
            elif 'Records found' in line:
                found_records = True
            if found_records:
                print(line)
                flash(line)

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Child did not exit gracefully.')
        else:
            print('Child exited gracefully.')

    except Exception as search_e:
        print(search_e)

def add(title, username, pw, extra, encryptionpw, overwrite):
    success = False
    try:
        child = pexpect.spawnu('pwmgr add', timeout=5, maxread=1, encoding='utf-8')
        flash('Adding...')
        print('Adding...')
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
        print(f'add: {output}')
        for line in output:
            if 'already exists' in line:
                flash('Title already exists in DB.')
                print('Title already exists in DB.')
                if overwrite:
                    flash('Overwrite selected. Proceeding to update existing record.')
                    print('Overwrite selected. Proceeding to update existing record.')
                    success = update(title, username, pw, extra, encryptionpw)
                    break
                else:
                    flash('Choose overwrite to update existing record.')
            elif 'error'.casefold() in line:
                flash(line)
                success = False
            elif 'successfully' in line:
                success = True

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Child did not exit gracefully.')
        else:
            print('Child exited gracefully.')
        return success

    except Exception as add_e:
        print(add_e)


def update(title, username, pw, extra, encryptionpw):
    success = False
    try:
        child = pexpect.spawnu('pwmgr update', timeout=50, maxread=1, encoding='utf-8')
        flash('Updating...')
        print('Updating...')
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
                flash(line)
                success = False
            elif 'successfully' in line:
                success = True

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Child did not exit gracefully.')
        else:
            print('Child exited gracefully.')
        return success

    except Exception as update_e:
        print(update_e)


def delete(title):
    deleted = False
    try:
        child = pexpect.spawnu('pwmgr delete', timeout=50, maxread=1, encoding='utf-8')
        child.expect(r':\s*$')
        child.sendline(f'{title}')
        flash('Deleting...')
        output = child.read().split('\n')
        print(f'delete: {output}')
        for line in output:
            if 'Server error' in line:
                flash(line)
            elif 'deleted' in line:
                deleted = True

        if child.isalive():
            child.close()
        # Print the final state of the child. Normally isalive() should be FALSE.
        if child.isalive():
            print('Child did not exit gracefully.')
        else:
            print('Child exited gracefully.')
        return deleted

    except Exception as delete_e:
        print(delete_e)