# pwmgr
A centralized password manager with distributed encryption.

## Description
The server part listens to connections from a client and verifies the access with server credentials that are predefined through the init command. Multiple clients can be used as long as they are aligned  against the server with the same server credentials given with init. 
<br><br>The security functionality is based on a strong encryption of every record that is made client-side before sent to the server. Even if the the server DB is compromised or the communication is eavesdropped, the records themselves will still be safe.

### Server
- Choose folder path for the DB to be stored in the config.py.
- Run the application: 
- ```python3 -u main.py```

There is a Docker image available:
https://hub.docker.com/r/schnitz81/pwmgr-server

Alternatively, use the Dockerfile to build it. See comments in Dockerfile for run example.


### Client

#### Installation


#### Usage

Run command:<br> 
```pwmgr (parameter)```

Init must be run first to create a server session before the other commands can be used. This is the base of the client<->server interaction. 

- init / config<br>
  Create a server session<br><br>
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
