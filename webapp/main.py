from flask import Flask
from flask import request
from flask import render_template
from flask import flash
from flask import session
from flask import redirect
import commands
import secrets
import uuid


app = Flask(__name__)
secret = secrets.token_urlsafe(32)
app.secret_key = secret
websession_userid = ''
entity = ''
overwrite = False

server = sessionuser = sessionpw = encryptionpw = encryptionpw2 = title = fetched_title = username = pw = extra = ""

def reset_vars():
    global server, sessionuser, sessionpw, encryptionpw, encryptionpw2, title, fetched_title, username, pw, extra
    server = sessionuser = sessionpw = encryptionpw = encryptionpw2 = title = fetched_title = username = pw = extra = ""


# websession handling
@app.before_request
def create_websession():
    global websession_userid
    if 'websession_userid' not in session:
        log('New session connected. Generating new session and resetting.')
        websession_userid = session['websession_userid'] = str(uuid.uuid4())
        reset_vars()

# add page
@app.route("/add", methods=['GET', 'POST'])
def add():
    global sessionuser, title, username, pw, extra, encryptionpw, encryptionpw2, overwrite, entity
    overwrite = False

    # ADD BUTTON
    if request.method == 'POST' and (request.form['btn'] == 'Add' or request.form['btn'] == 'Overwrite'):
        title = '\n'.join(map(str, request.form.getlist('title'))).strip()
        username = '\n'.join(map(str, request.form.getlist('username'))).strip()
        pw = '\n'.join(map(str, request.form.getlist('pw'))).strip()
        extra = '\n'.join(map(str, request.form.getlist('extra'))).strip()
        encryptionpw = '\n'.join(map(str, request.form.getlist('encryptionpw'))).strip()
        encryptionpw2 = '\n'.join(map(str, request.form.getlist('encryptionpw2'))).strip()

        if username == "":
            log("Username can't be empty.")
        elif pw == "":
            log("Password can't be empty.")
        elif encryptionpw == "":
            log("Encryption password can't be empty.")
        elif encryptionpw2 == "":
            log("Encryption password confirmation can't be empty.")
        elif encryptionpw != encryptionpw2:
            log("Encryption password confirmation is different.")

        if request.form['btn'] == 'Overwrite':
            overwrite = True

        return redirect("/")

    # CANCEL BUTTON
    elif request.method == 'POST' and request.form['btn'] == 'Cancel':
        return redirect("/")

    return (
        render_template("add.html", sessionuser=sessionuser, title=title, username=username, pw=pw, extra=extra, encryptionpw=encryptionpw, encryptionpw2=encryptionpw2)
    )


@app.route("/", methods=['GET', 'POST'])
def index():

    global server, sessionuser, sessionpw, encryptionpw, encryptionpw2, title, fetched_title, username, pw, extra
    global websession_userid
    global entity
    global overwrite

    if request.method == 'POST' and (request.form['btn'] == 'Get' or request.form['btn'] == 'Search' or request.form['btn'] == 'Add' or request.form['btn'] == 'Delete'):
        server = '\n'.join(map(str, request.form.getlist('server'))).strip()
        sessionuser = '\n'.join(map(str, request.form.getlist('sessionuser'))).strip()
        sessionpw = '\n'.join(map(str, request.form.getlist('sessionpw'))).strip()
        encryptionpw = '\n'.join(map(str, request.form.getlist('encryptionpw'))).strip()
        title = '\n'.join(map(str, request.form.getlist('title'))).strip()
        entity = request.remote_addr + '-' + request.user_agent.string
        new = False

        # field checks
        if not request.form['btn'] == 'Add' and (server == "" or sessionuser == "" or sessionpw == "" or title == ""):
            log("Server, user, session password and title need to be filled.")
        elif request.form['btn'] == 'Add' and (server == "" or sessionuser == "" or sessionpw == ""):
            log("Server, user and session password need to be filled when adding new record.")
        elif encryptionpw == "" and request.form['btn'] == 'Get':
            log("Encryption password can't be empty when using 'get'.")

        else:
            # run commands
            log('Creating session.')

            # only allow creation of new user DB if "add" function is selected.
            if request.form['btn'] == 'Add':
                new = True
            if not commands.init(server, sessionuser, sessionpw, new):
                log("Error: Init failed.")
            else:

                # GET BUTTON
                if request.form['btn'] == 'Get':
                    try:
                        fetched_title, username, pw, extra = commands.get(title, encryptionpw)

                        if fetched_title:
                            log(f'Fetch successful.')
                        else:
                            log(f'Warning: fetch not fully successful.')
                    except TypeError:
                        log("Error: Values not fetched")

                # SEARCH BUTTON
                elif request.form['btn'] == 'Search':
                    commands.search(title)

                #ADD BUTTON
                elif request.form['btn'] == 'Add':
                    return redirect("/add")

                # DELETE BUTTON
                elif request.form['btn'] == 'Delete':
                    if commands.delete(title):
                        log(f'{title} deleted.')
                    else:
                        log('Deletion error.')

                log('Deleting session.')
                commands.delete_session()

    # CLEAR BUTTON
    elif request.method == 'POST' and request.form['btn'] == 'Clear':
        reset_vars()
        session.pop('websession_userid', None)

    # add record
    elif encryptionpw2 != '':
        if encryptionpw != encryptionpw2:
            log("Error: Confirmation encryption password doesn't match.")
        else:
            if commands.add(title, username, pw, extra, encryptionpw, overwrite):
                log('Record stored in DB successfully.')
            else:
                log('Error: Record add failed.')
        encryptionpw2 = ''

    # REQUEST ID CHECK ####
    current_entity = request.remote_addr + '-' + request.user_agent.string
    print(f'Previous entity: {entity}')
    print(f'Current entity: {current_entity}')

    # check session before returning values
    if current_entity != entity:
        reset_vars()
        log('Page blank due to new browser access.')
    ########################

    return (
        render_template("home.html", server=server, sessionuser=sessionuser, sessionpw=sessionpw, encryptionpw=encryptionpw, title=title, fetched_title=fetched_title, username=username, pw=pw, extra=extra)
    )


def log(msg):
    flash(msg)
    print(msg)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8888, debug=True)