#!/bin/bash

PORT=48222
SESSIONPATH="$HOME/.config/pwmgr/.session"

function init ()
{
	echo ; read -p "Create new session? " configask
	if [ "$configask" != 'y' ] && [ "$configask" != 'Y' ] && [ "$configask" != 'yes' ] && [ "$configask" != 'YES' ]; then
		return
	fi
	echo "Session config."
	echo ; read -p "Server address/IP: " server
	if [ "$server" == '' ]; then
		echo ; echo "Error: server address can't be empty."; exit 1
	fi
	echo ; read -p "Enter session username: " username
	if [ "$username" == '' ]; then
		echo ; echo "Error: session username can't be empty."; exit 1
	fi
	echo ; read -s -p "Enter session password: " sessionpw
	echo ; read -s -p "Repeat session password: " sessionpw2
	if [ "$sessionpw" != "$sessionpw2" ]; then
		echo ; echo "Error: passwords don't match."; exit 1
	elif [ "$sessionpw" == '' ]; then
		echo ; echo "Error: session password can't be empty."; exit 1
	fi

	# create folder for session file
	mkdir -p "$(echo "$SESSIONPATH" | awk 'BEGIN{FS=OFS="/"}{NF--}1')"

	# create local session
	echo "$server" > "$SESSIONPATH"
	echo "$username" | base64 | base64 >> "$SESSIONPATH"
	echo "$sessionpw" | base64 | base64 >> "$SESSIONPATH"
	echo

	# align session with server and create a new user table if non-existent
	echo "Syncing server."
	command="init"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)
	SERVERRESPONSE=$(echo "${command}" "${sessionuser}" "${sessionpw}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo -n "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo "Local session and remote server DB aligned successfully."
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}

function init-change ()
{
	echo ; read -p "Create or overwrite local session and change session credentials server-side? " configask
	if [ "$configask" != 'y' ] && [ "$configask" != 'Y' ] && [ "$configask" != 'yes' ] && [ "$configask" != 'YES' ]; then
		return
	fi
	echo "Session config update."
	echo ; read -p "Server address/IP: " server
	if [ "$server" == '' ]; then
		echo ; echo "Error: server address can't be empty."; exit 1
	fi
	echo ; read -p "Enter CURRENT session username: " sessionuser
	if [ "$sessionuser" == '' ]; then
		echo ; echo "Error: session username can't be empty."; exit 1
	fi
	echo ; read -s -p "Enter CURRENT session password: " sessionpw
	echo ; read -s -p "Repeat CURRENT session password: " sessionpw2
	if [ "$sessionpw" != "$sessionpw2" ]; then
		echo ; echo "Error: passwords don't match."; exit 1
	elif [ "$sessionpw" == '' ]; then
		echo ; echo "Error: session password can't be empty."; exit 1
	fi
	echo ; read -p "Enter NEW session username: " sessionnewuser
	if [ "$sessionnewuser" == '' ]; then
		echo ; echo "Error: session username can't be empty."; exit 1
	fi
	echo ; read -s -p "Enter NEW session password: " sessionnewpw
	echo ; read -s -p "Repeat NEW session password: " sessionnewpw2
	if [ "$sessionnewpw" != "$sessionnewpw2" ]; then
		echo ; echo "Error: passwords don't match."; exit 1
	elif [ "$sessionnewpw" == '' ]; then
		echo ; echo "Error: session password can't be empty."; exit 1
	fi

	# create folder for session file
	mkdir -p "$(echo "$SESSIONPATH" | awk 'BEGIN{FS=OFS="/"}{NF--}1')"

	# encode current credentials
	sessionuser=$(echo -n "$sessionuser" | base64 | base64)
	sessionpw=$(echo -n "$sessionpw" | base64 | base64)

	# create local temp session
	echo "$server" > "$SESSIONPATH.tmp"
	echo "$sessionnewuser" | base64 | base64 >> "$SESSIONPATH.tmp"
	echo "$sessionnewpw" | base64 | base64 >> "$SESSIONPATH.tmp"
	echo

	# get new user and pw encoded
	sessionnewuser=$(head -n 2 "$SESSIONPATH.tmp" | tail -n 1)
	sessionnewpw=$(head -n 3 "$SESSIONPATH.tmp" | tail -n 1)

	# align session with server and create a new user table if non-existent
	echo "Syncing server."
	command="init-change"
	SERVERRESPONSE=$(echo "${command}" "${sessionuser}" "${sessionpw}" "${sessionnewuser}" "${sessionnewpw}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH.tmp")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo -n "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo "Updating local session."
				mv "$SESSIONPATH.tmp" "$SESSIONPATH"
				if [ $? != 0 ]; then
					echo "Error: Local session replacement unsuccessful."
					exit 1
				fi
				echo "Local session and remote server DB aligned successfully."
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}


function sessioncheck ()
{
	if ! [ -f "$SESSIONPATH" ]; then
		echo "No local session found. Please run with init parameter to create one."; exit 1
	fi
}


function status ()
{
	sessioncheck
	echo "Session status check."

	command="status"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo ; echo "Fetching record from server."
	SERVERRESPONSE=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo ; echo "Server response OK:"
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}


function add ()
{
	sessioncheck
	echo "Add new record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo ; echo "Title is \""$title"\""
	else
		echo ; read -p "Name/site/title: " title
	fi
	if [ "$title" == '' ]; then
		echo ; echo "Error: title can't be empty."; exit 1
	fi
	echo ; read -p "Enter username: " username
	if [ "$username" == '' ]; then
		echo ; echo "Error: session username can't be empty."; exit 1
	fi
	echo ; read -s -p "Enter password: " pw
	echo ; read -s -p "Repeat password: " pw2
	if [ "$pw" != "$pw2" ]; then
		echo "Error: passwords don't match."; exit 1
	elif [ "$pw" == '' ]; then
		echo ; echo "Error: session password can't be empty."; exit 1
	fi
	echo ; read -p "Extra field (may be blank): " extra
	while true; do
		echo ; read -s -p "Enter encryption password (or quit):" encryptionpw
		if [ "$encryptionpw" == "q" ] || [ "$encryptionpw" == "Q" ] || [ "$encryptionpw" == "quit" ] || [ "$encryptionpw" == "QUIT" ] || [ "$encryptionpw" == "exit" ] || [ "$encryptionpw" == "EXIT" ]; then
			echo ; exit 1
		fi
		echo ; read -s -p "Repeat encryption password (or quit):" encryptionpw2
		if [ "$encryptionpw2" == "q" ] || [ "$encryptionpw2" == "Q" ] || [ "$encryptionpw2" == "quit" ] || [ "$encryptionpw2" == "QUIT" ] || [ "$encryptionpw2" == "exit" ] || [ "$encryptionpw2" == "EXIT" ]; then
			echo ; exit 1
		fi
		if [ "$encryptionpw" != "$encryptionpw2" ]; then
			echo ; echo ; echo "Error: Encryption passwords don't match."
		elif [ "$encryptionpw" == "$pw" ]; then
			echo ; echo ; echo "Error: Record password and encryption password shouldn't be the same."
		elif [ "$encryptionpw" == '' ]; then
			echo ; echo ; echo "Error: Encryption password can't be empty."
		else
			break
		fi
	done

	# encrypt user and pw
	title=$(echo "$title" | base64 | base64)
	username=$(echo "$username" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")
	pw=$(echo "$pw" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")
	extra=$(echo "$extra" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")
	verification=$(echo "verification" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")

	command="add"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo ; echo "Adding record to server." ; echo
	SERVERRESPONSE=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" "${username}" "${pw}" "${extra}" "${verification}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo "Remember your encryption password."
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}


function get ()
{
	sessioncheck
	echo "Get record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo ; echo "Input title is \""$title"\""
	else
		echo ; read -p "Name/site/title to get: " title
	fi

	if [[ -z "$title" ]]; then
		echo "Name can't be blank."
		exit 1
	fi

	command="get"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo ; echo "Fetching record from server."
	SERVERRESPONSE=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo ; read -s -p "Enter encryption password: " encryptionpw
				if [ "$encryptionpw" == '' ]; then
					echo ; echo "Error: Encryption password can't be empty."; exit 1
				fi
				title=$(echo "$SERVERRESPONSE" | cut -d ' ' -f 2)
				username=$(echo "$SERVERRESPONSE" | cut -d ' ' -f 3 | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw")
				pw=$(echo "$SERVERRESPONSE" | cut -d ' ' -f 4 | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw")
				extra=$(echo "$SERVERRESPONSE" | cut -d ' ' -f 5 | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw")
				verification=$(echo "$SERVERRESPONSE" | cut -d ' ' -f 6 | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw")
				if [ "$verification" != "verification" ]; then
					echo ; echo "Error: Wrong encryption/decryption password given. Unable to decrypt."
					exit 1
				fi
				echo
				echo "title: $title"
				echo "username: $username"
				echo "password: $pw"
				echo "extra info: $extra"
				;;
			3)
				echo ; echo "Partly matched records found:" ; echo
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo ; echo "Specify exact title."
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}


function list ()
{
	sessioncheck
	echo "Get record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo ; echo "Input title is \""$title"\""
	else
		echo ; read -p "Name/site/title to list: " title
	fi
	if [[ -z "$title" ]]; then
		echo "Name can't be blank."
		exit 1
	fi

	command="list"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo ; echo "Fetching record from server."
	SERVERRESPONSE=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo ; echo "Records found:"
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo
				;;
			3)
				echo ; echo "Records found:"
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}


function delete ()
{
	sessioncheck
	echo "Delete record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo ; echo "Input title is \""$title"\""
	else
		echo ; read -p "Name/site/title to delete: " title
	fi
	if [[ -z "$title" ]]; then
		echo "Name can't be blank."
		exit 1
	fi

	command="delete"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo ; echo "Fetching record from server."
	SERVERRESPONSE=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo ; echo "Server record deletion OK:"
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				;;
			3)
				echo ; echo "Records found:" ; echo
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo ; echo "Specify exact record name." ; echo
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}


function update ()
{
	sessioncheck
	echo "Update record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo ; echo "Input title is \""$title"\""
	else
		echo ; read -p "Name/site/title to delete: " title
	fi
	if [[ -z "$title" ]]; then
		echo "Name can't be blank."
		exit 1
	fi
	echo ; read -p "Enter NEW username: " username
	if [ "$username" == '' ]; then
		echo ; echo "Error: session username can't be empty."; exit 1
	fi
	echo ; read -s -p "Enter NEW password: " pw
	echo ; read -s -p "Repeat NEW password: " pw2
	if [ "$pw" != "$pw2" ]; then
		echo "Error: passwords don't match."; exit 1
	elif [ "$pw" == '' ]; then
		echo ; echo "Error: session password can't be empty."; exit 1
	fi
	echo ; read -p "Extra field (may be blank): " extra
	echo ; read -s -p "Enter encryption password: " encryptionpw
	echo ; read -s -p "Repeat encryption password: " encryptionpw2
	if [ "$encryptionpw" != "$encryptionpw2" ]; then
		echo ; echo "Error: Encryption passwords don't match."; exit 1
	elif [ "$encryptionpw" == "$pw" ]; then
		echo ; echo "Error: session password and encryption password shouldn't be the same."; exit 1
	elif [ "$encryptionpw" == '' ]; then
		echo ; echo "Error: Encryption password can't be empty."; exit 1
	fi

	# encrypt user and pw
	title=$(echo "$title" | base64 | base64)
	username=$(echo "$username" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")
	pw=$(echo "$pw" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")
	extra=$(echo "$extra" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")
	verification=$(echo "verification" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 107172 -salt -pass pass:"$encryptionpw" | tr -d "\n")

	command="update"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo ; echo "Adding record to server." ; echo
	SERVERRESPONSE=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" "${username}" "${pw}" "${extra}" "${verification}" | base64 | base64 | nc -w 3 -q 2 "$(head -n 1 "$SESSIONPATH")" $PORT)
	if [ $? != 0 ]; then
		echo -n "Server connect error. "
		echo "$SERVERRESPONSE"
		exit 1
	else
		SERVERRESPONSE=$(echo "$SERVERRESPONSE" | base64 -d | base64 -d)
		case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
			1)
				echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
				;;
			2)
				echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
				echo "Remember your new encryption password."
				;;
			*)
				echo "Unknown error:"
				echo "$SERVERRESPONSE"
				;;
		esac
	fi
}


function helptext ()  # Help text diplayed if no or non-existent input parameter is given.
{
	cat <<'END'
Run command:
$ pwmgr (parameter)

Init must be run first to create a session before the other commands can be
used. This is the base of the client<->server interaction.

	COMMANDS:

- init / config
	Create a session. This creates a local session config and attempts to create
	a remote server	db session. If the username db already exists, it's reused.
	Previous session password must match.
	By entering the same sessionuser/sessionpassword  multiple clients can be
	used with the same server DB.

- init-change / config-change
	Change credentials of an existing session. Old credentials must be given for
	verification.

- status / check
  Check session status against the server.

- add / encrypt / enc / put / save
	Add a new record.
	Fields stored:
	- Title/Name
	- username
	- password
	- Extra field (optional/may be blank)
	Encryption password selection is prompted. The encryption of the record will
	be as strong as this password.

- get / decrypt / dec / fetch / show / load
	Fetch a stored record to view. Same encryption password as when the record
	was stored must be entered.

- list / search
	Search for a record with partial name.

- delete / remove / del
	Delete a record.

- update / change / edit
	Change a record, e.g. change the password stored. If the name of the record
	already exists, it's not possible to use "add" to overwrite, but this command
	must be used instead.

END
}


########################### main #######################################
nbrOfParams=$#

# set title to 2nd input parameter if given
if [[ $nbrOfParams -gt 1 ]]; then
	title=$2
fi

# check if base64 is installed
if [ -z "$(which base64)" ] ; then
	echo "base64 not found."
	exit 1
fi

# check if openssl is installed
if [ -z "$(which openssl)" ] ; then
	echo "openssl not found."
	exit 1
fi

# init parameter input - run init procedure
if [ "$1" == "init" ] || [ "$1" == "config" ]; then
	init

# init-change parameter input - run init-change procedure
elif [ "$1" == "init-change" ] || [ "$1" == "config-change" ] || [ "$1" == "configchange" ]; then
	init-change

# status parameter input - run status procedure
elif [ "$1" == "status" ] || [ "$1" == "check" ] || [ "$1" == "sessioncheck" ]; then
	status

# add parameter input - run add procedure
elif [ "$1" == "add" ] || [ "$1" == "encrypt" ] || [ "$1" == "enc" ] || [ "$1" == "put" ] || [ "$1" == "save" ]; then
	add

# get parameter input - run get procedure
elif [ "$1" == "get" ] || [ "$1" == "decrypt" ] || [ "$1" == "dec" ] || [ "$1" == "fetch" ] || [ "$1" == "show" ] || [ "$1" == "load" ]; then
	get

# list parameter input - run get procedure
elif [ "$1" == "list" ] || [ "$1" == "search" ]; then
	list

# delete parameter input - run get procedure
elif [ "$1" == "delete" ] || [ "$1" == "remove" ] || [ "$1" == "del" ]; then
	delete

# update parameter input - run get procedure
elif [ "$1" == "update" ] || [ "$1" == "change" ] || [ "$1" == "edit" ]; then
	update

else
	helptext
fi
