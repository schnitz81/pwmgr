# pwmgr
A centralized password manager with distributed encryption.

## Description
The server part listens to connections from a client and verifies the access with session credentials that are predefined through the init command. Multiple clients can be used as long as they are aligned  against the server with the same credentials given with init. 
<br><br>The security functionality is based on a strong encryption of every record that is performed client-side before the data sent to the server. Even if the the server DB is compromised or the communication is eavesdropped, the records themselves will still be safe through the encryption.
<br><br>If keyctl is available in the client environment, it will be used for a temporary user keyring to avoid encryption password user input multiple times within a certain timespan.

## Server
- Choose folder path for the DB to be stored in the config.py.
- Run the application: 
- ```python3 -u main.py```

There is a Docker image available:
https://hub.docker.com/r/schnitz81/pwmgr-server

Alt. use the Dockerfile to build it. The appropriate port needs to be forwarded and the /db folder mounted for persistence. See comments in Dockerfile for run example.


## Client

### Requirements

The client needs netcat-openbsd, openssl and gzip. 

### Installation
Download the client file and make it executable.<br>
Example:<br>
```wget -O /usr/local/bin/pwmgr https://raw.githubusercontent.com/schnitz81/pwmgr/main/client/pwmgr.sh && chmod +x /usr/local/bin/pwmgr```

### Usage

Run command:<br> 
```pwmgr (parameter)```

Init must be run first to create a session before the other commands can be used. This is the base of the client<->server interaction. 

- init / config<br>
  Create a session. This creates a local session config and attempts to create a remote server db session. If the username db already exists, it's reused. Previous session password must match.<br>
  By entering the same sessionuser/sessionpassword  multiple clients can be used with the same server DB.<br><br>
- init-change / config-change / configchange<br>
  Change credentials of an existing session. Old credentials must be given for verification.<br><br>
- status / check / connection / test<br>
  Check session status against the server.<br><br>
- add / encrypt / enc / put / save [(title)]<br>
  Add a new record.<br>
  Fields stored:<br>
  - Title/Name
  - username
  - password
  - Extra field (optional/may be blank)

  Encryption password selection is prompted. The encryption of the record will be as strong as this password.<br><br> 
- get / decrypt / dec / fetch / show / load [(title)]<br>
  Fetch a stored record to view. Same encryption password as when the record was stored must be entered.<br><br>  
- list / search [(title)]/[all]<br>
  Search for a record with partial name.<br><br>
- delete / remove / del [(title)]<br>
  Delete a record.<br><br>
- update / change / edit<br>
  Change a record, e.g. change the password stored.<br>
  If the name of the record already exists, it's not possible to use "add" to overwrite, but this command must be used instead. 

## Web-app

![screenshot](webapp/images/screenshot.png)

The web-app is an alternative way of using the client. It also makes it easier to use pwmgr on mobile devices where terminals are rarely used.
Since it only interacts with the terminal based client, it only needs the client part and can be run separately from the pwmgr server. 

### Requirements

- The Python3 dependencies are listed in the requirements file.
- The pwmgr client executable needs to be present in one of the PATH locations (and named "pwmgr"), with the dependencies listed above.

### Usage

- See comments in Dockerfile for build and run example as container. Or:<br>
- Use pip to install the requirements and install the client manually with the dependencies as above.
- Run with: ```python -u main.py```<br>
