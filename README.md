# pwmgr
A centralized password manager with distributed encryption.

## Description
The server part listens to connections from a client and verifies the access with session credentials that are predefined through the init command. Multiple clients can be used as long as they are aligned  against the server with the same credentials given with init. 
<br><br>The security functionality is based on a strong encryption of every record that is made client-side before sent to the server. Even if the the server DB is compromised or the communication is eavesdropped, the records themselves will still be safe.

### Server
- Choose folder path for the DB to be stored in the config.py.
- Run the application: 
- ```python3 -u main.py```

There is a Docker image available:
https://hub.docker.com/r/schnitz81/pwmgr-server

Alt. use the Dockerfile to build it. The appropriate port needs to be forwarded and the /db folder mounted for persistence. See comments in Dockerfile for run example.


### Client

#### Installation
Download the client file and make it executable.<br>
Example:<br>
```wget -O /usr/local/bin/pwmgr https://raw.githubusercontent.com/schnitz81/pwmgr/main/client/pwmgr.sh && chmod +x /usr/local/bin/pwmgr```

#### Usage

Run command:<br> 
```pwmgr (parameter)```

Init must be run first to create a session before the other commands can be used. This is the base of the client<->server interaction. 

- init / config<br>
  Create a session. This creates a local session config and attempts to create a remote server db session. If the username db already exists, it's reused. Previous session password must match.<br>
  By entering the same sessionuser/sessionpassword  multiple clients can be used with the same server DB.<br><br>
- init-change / config-change<br>
  Change credentials of an existing session. Old credentials must be given for verification.<br><br> 
- add / encrypt / enc / put / save<br>
  Add a new record.<br>
  Fields stored:<br>
  - Title/Name
  - username
  - password
  - Extra field (optional/may be blank)

  Encryption password selection is prompted. The encryption of the record will be as strong as this password.<br><br> 
- get / decrypt / dec / fetch / show / load<br>
  Fetch a stored record to view. Same encryption password as when the record was stored must be entered.<br><br>  
- list / search<br>
  Search for a record with partial name.<br><br>
- delete / remove / del<br>
  Delete a record.<br><br>
- update / change / edit<br>
  Change a record, e.g. change the password stored.<br>
  If the name of the record already exists, it's not possible to use "add" to overwrite, but this command must be used instead. 
