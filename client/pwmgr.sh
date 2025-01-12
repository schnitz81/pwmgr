#!/bin/bash

PORT=48222
SESSIONPATH="$HOME/.config/pwmgr/.session"
KEY_SESSION_SECONDS=$((60*90))


function response_valid() {
	local nc_err=$1
	local response=$2
	if [[ $nc_err -ne 0 ]]; then
		echo -e "Error: Connection error. No server response.\n"; exit 1
	elif [ -z "$response" ]; then
		echo -e "Error: Server response empty.\n"; exit 1
	elif [ "${#response}" -lt 5 ]; then
		echo -e "Error: Server response data too short: $response\n"; exit 1
	elif [[ "$(echo -n "$response" | base64 -d 2>&1)" =~ "invalid" ]]; then
		echo -e "Error: Server response is not valid base64 encoding: $response\n"; exit 1
	fi
}


function b64swap() {
	# byteswap b64
	local str=$1
	if [ "${#str}" -lt 4 ]; then
		echo -e "Error: b64 string too short to swap.\n"; exit 1
	fi
	local byteoffset=2
	local looplimit=$((${#str}-2))
	while [[ $byteoffset -lt $looplimit ]]; do
		local beginstr="${str:0:$((byteoffset-1))}"
		local c2="${str:$((byteoffset-1)):1}"
		local c3="${str:$byteoffset:1}"
		local endstr="${str:$((byteoffset+1))}"
		str="${beginstr}${c3}${c2}${endstr}"
		byteoffset=$((byteoffset+2))
	done
	echo -n "$str"
}


function decode_response() {
	local response=$1
	local unswapped_serverresponse=$(echo "$response" | base64 -d)
	local swapped_serverresponse=$(b64swap "$unswapped_serverresponse")
	local uncompressed_response=$(echo "$swapped_serverresponse" | base64 -d | gunzip -f)
	echo "$uncompressed_response"
}


function add_key_to_key_session() {
	if [ -n "$(which keyctl 2>/dev/null)" ] ; then
		keyctl link @u @s 1>/dev/null 2>&1  # link user and session keyring
		if $(keyctl list @u | grep -v 'expired' | grep -q 'pwmgr'); then  # revoke old key session if existing
			keyctl revoke $(keyctl search @u user pwmgr)
		fi
		local encpw=$1
		local b64sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1 | base64 -d)  # get sessionpw from session file
		if [ "$(echo $b64sessionpw | wc -m)" -gt 3 ]; then
			local encpw_encrypted=$(encrypt "$encpw" "$b64sessionpw")
			local b64_encpw_unswapped=$(echo -n "$encpw_encrypted" | base64 -w0)
			local b64_encpw_swapped=$(b64swap "$b64_encpw_unswapped")
			if [ $? -eq 0 ]; then  # write to session and set timeout if it was successfully created
				local id=$(keyctl add user pwmgr "$b64_encpw_swapped" @u)
				keyctl timeout "$id" "$KEY_SESSION_SECONDS"
			fi
		fi
	fi
}


function get_key_from_key_session() {
	if [ -n "$(which keyctl 2>/dev/null)" ] ; then
		keyctl link @u @s 1>/dev/null 2>&1  # link user and session keyring
		if $(keyctl list @u | grep -v 'expired' | grep -q 'pwmgr'); then  # only fetch key if the key session exists
			# check for error when using key
			keyctl pipe $(keyctl search @u user pwmgr) 1>/dev/null  # test key fetching to detect any error
			if [ $? -ne 1 ]; then
				local b64sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1 | base64 -d)
				local b64_encpw_unswapped=$(keyctl pipe $(keyctl search @u user pwmgr))
				local b64_encpw_swapped=$(b64swap "$b64_encpw_unswapped")
				local encpw_encrypted=$(echo "$b64_encpw_swapped" | base64 -d)
				local encpw=$(decrypt "$encpw_encrypted" "$b64sessionpw")
				echo -n "$encpw"
			fi
		fi
	fi
}


function encrypt() {
	local unencrypted_data="$1"
	local encryptionpw="$2"
	echo "$unencrypted_data" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter 577372 -salt -pass pass:"$encryptionpw" | tr -d "\n"
}


function decrypt() {
	local encrypted_data="$1"
	local encryptionpw="$2"
	echo "$encrypted_data" | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter 577372 -salt -pass pass:"$encryptionpw" | tr -d "\0"
}


function init () {
	echo ; read -p "Create new session? " configask
	if [ "$configask" != 'y' ] && [ "$configask" != 'Y' ] && [ "$configask" != 'yes' ] && [ "$configask" != 'YES' ]; then
		return
	fi
	echo "Session config."
	echo ; read -p "Server address/IP: " server
	if [ "$server" == '' ]; then
		echo -e "\nError: server address can't be empty.\n"; exit 1
	fi
	echo ; read -p "Enter session username: " username
	if [ "$username" == '' ]; then
		echo -e "\nError: session username can't be empty.\n"; exit 1
	fi
	echo ; read -s -p "Enter session password: " sessionpw
	echo ; read -s -p "Repeat session password: " sessionpw2
	if [ "$sessionpw" != "$sessionpw2" ]; then
		echo -e "\nError: passwords don't match.\n"; exit 1
	elif [ "$sessionpw" == '' ]; then
		echo -e "\nError: session password can't be empty.\n"; exit 1
	fi

	# create folder for session file
	mkdir -p -m 0700 "$(echo "$SESSIONPATH" | awk 'BEGIN{FS=OFS="/"}{NF--}1')"

	# create obligatory local session with user only permissions
	touch "$SESSIONPATH" && chmod 0600 "$SESSIONPATH" || (res=$?; echo -e "\nError: Failed to create session."; (exit $res))
	echo "$server" > "$SESSIONPATH"
	echo -n "$username" | base64 -w0 | base64 -w0 >> "$SESSIONPATH"
	echo >> "$SESSIONPATH"  # add newline
	echo -n "$sessionpw" | base64 -w0 | base64 -w0 >> "$SESSIONPATH"
	echo >> "$SESSIONPATH"  # add newline
	echo

	# align session with server and create a new user table if non-existent
	echo "Syncing server."
	command="init"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)
	nonew=$(echo -n "$nonew" | base64 -w0 | base64 -w0)
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${nonew}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo "Local session and remote server DB aligned successfully."
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function init-change () {
	echo ; read -p "Create or overwrite local session and change session credentials server-side? " configask
	if [ "$configask" != 'y' ] && [ "$configask" != 'Y' ] && [ "$configask" != 'yes' ] && [ "$configask" != 'YES' ]; then
		return
	fi
	echo "Session config update."
	echo ; read -p "Server address/IP: " server
	if [ "$server" == '' ]; then
		echo -e "\nError: server address can't be empty.\n"; exit 1
	fi
	echo ; read -p "Enter CURRENT session username: " sessionuser
	if [ "$sessionuser" == '' ]; then
		echo -e "\nError: session username can't be empty.\n"; exit 1
	fi
	echo ; read -s -p "Enter CURRENT session password: " sessionpw
	echo ; read -s -p "Repeat CURRENT session password: " sessionpw2
	if [ "$sessionpw" != "$sessionpw2" ]; then
		echo -e "\nError: passwords don't match.\n"; exit 1
	elif [ "$sessionpw" == '' ]; then
		echo -e "\nError: session password can't be empty.\n"; exit 1
	fi
	echo ; read -p "Enter NEW session username: " sessionnewuser
	if [ "$sessionnewuser" == '' ]; then
		echo -e "\nError: session username can't be empty.\n"; exit 1
	fi
	echo ; read -s -p "Enter NEW session password: " sessionnewpw
	echo ; read -s -p "Repeat NEW session password: " sessionnewpw2
	if [ "$sessionnewpw" != "$sessionnewpw2" ]; then
		echo -e "\nError: passwords don't match.\n"; exit 1
	elif [ "$sessionnewpw" == '' ]; then
		echo -e "\nError: session password can't be empty.\n"; exit 1
	fi

	# create folder for session file
	mkdir -p "$(echo "$SESSIONPATH" | awk 'BEGIN{FS=OFS="/"}{NF--}1')"

	# encode current credentials
	sessionuser=$(echo -n "$sessionuser" | base64 -w0 | base64 -w0)
	sessionpw=$(echo -n "$sessionpw" | base64 -w0 | base64 -w0)

	# create local temp session
	touch "$SESSIONPATH.tmp" && chmod 0600 "$SESSIONPATH.tmp" || (res=$?; echo -e "\nError: Failed to create temp session."; (exit $res))
	echo "$server" > "$SESSIONPATH.tmp"
	echo -n "$sessionnewuser" | base64 -w0 | base64 -w0 >> "$SESSIONPATH.tmp"
	echo >> "$SESSIONPATH.tmp"  # add newline
	echo -n "$sessionnewpw" | base64 -w0 | base64 -w0 >> "$SESSIONPATH.tmp"
	echo >> "$SESSIONPATH.tmp"  # add newline
	echo

	# get new user and pw encoded
	sessionnewuser=$(head -n 2 "$SESSIONPATH.tmp" | tail -n 1)
	sessionnewpw=$(head -n 3 "$SESSIONPATH.tmp" | tail -n 1)

	# align session with server and create a new user table if non-existent
	echo "Syncing server."
	command="init-change"
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${sessionnewuser}" "${sessionnewpw}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH.tmp")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo "Updating local session."
			mv "$SESSIONPATH.tmp" "$SESSIONPATH"
			if [ $? != 0 ]; then
				echo -e "Error: Local session replacement unsuccessful.\n"
				exit 1
			fi
			echo "Local session and remote server DB aligned successfully."
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function sessioncheck () {
	if ! [ -f "$SESSIONPATH" ]; then
		echo -e "No local session found. Please run with init parameter to create one.\n"
		exit 1
	elif [[ $(cat $SESSIONPATH | wc -l) -lt 3 ]]; then
		echo -e "Local session exists but is invalid.\n"
		exit 1
	fi
}


function status () {
	sessioncheck
	echo "Session status check."

	command="status"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo -e "\nChecking status..."
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			echo -e "\nServer response OK:"
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function add () {
	sessioncheck
	echo "Add new record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo -e "\nTitle is \"$title\""
	else
		echo ; read -p "Name/site/title: " title
	fi
	if [ "$title" == '' ]; then
		echo -e "\nError: title can't be empty.\n"; exit 1
	fi
	echo ; read -p "Enter username: " username
	if [ "$username" == '' ]; then
		echo -e "\nError: session username can't be empty.\n"; exit 1
	fi
	echo ; read -s -p "Enter password: " pw
	echo ; read -s -p "Repeat password: " pw2
	if [ "$pw" != "$pw2" ]; then
		echo -e "\nError: passwords don't match.\n"; exit 1
	elif [ "$pw" == '' ]; then
		echo -e "\nError: session password can't be empty.\n"; exit 1
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
			echo -e "\n\nError: Encryption passwords don't match."
		elif [ "$encryptionpw" == "$pw" ]; then
			echo -e "\n\nError: Record password and encryption password shouldn't be the same."
		elif [ "$encryptionpw" == '' ]; then
			echo -e "\n\nError: Encryption password can't be empty."
		else
			break
		fi
	done

	# encrypt user and pw
	echo -e "\nEncrypting..."
	title=$(echo "$title" | base64 -w0 | base64 -w0)
	username=$(encrypt "$username" "$encryptionpw")
	pw=$(encrypt "$pw" "$encryptionpw")
	extra=$(encrypt "$extra" "$encryptionpw")
	verification=$(encrypt "verification" "$encryptionpw")

	command="add"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo -e "\nAdding record...\n"
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" "${username}" "${pw}" "${extra}" "${verification}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo "Remember your encryption password."
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function get () {
	sessioncheck
	echo "Get record."
	if [[ -n "$title" ]]; then
		echo -e "\nInput title is \"$title\""
	else
		echo ; read -p "Name/site/title to get: " title
	fi

	if [[ -z "$title" ]]; then  # if title is not entered as parameter or prompt
		echo -e "Record name can't be blank.\n"
		exit 1
	fi

	command="get"
	title=$(echo "$title" | base64 -w0 | base64 -w0)
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo -e "\nFetching record..."
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			# try key session if available
			encryptionpw=$(get_key_from_key_session)
			if [ -n "$encryptionpw" ]; then
				echo -e "\nTesting key session password..."
				verification=$(decrypt $(echo "$SERVERRESPONSE" | cut -d ' ' -f 6) "$encryptionpw")
			fi

			# no valid encpw from key session, enter manually
			if [ "$verification" != "verification" ]; then
				echo ; read -s -p "Enter encryption password: " encryptionpw
				if [ "$encryptionpw" == '' ]; then
					echo -e "\nError: Encryption password can't be empty.\n"; exit 1
				fi

				# decrypt and verify verification string when entered manually
				echo -e "\nTesting password..."
				verification=$(decrypt $(echo "$SERVERRESPONSE" | cut -d ' ' -f 6) "$encryptionpw")
				if [ "$verification" != "verification" ]; then
					echo -e "\nError: Wrong encryption/decryption password given. Unable to decrypt.\n"
					exit 1
				fi
			fi

			echo -e "\nDecrypting..."
			title=$(echo "$SERVERRESPONSE" | cut -d ' ' -f 2)
			username=$(decrypt $(echo "$SERVERRESPONSE" | cut -d ' ' -f 3) "$encryptionpw")
			pw=$(decrypt $(echo "$SERVERRESPONSE" | cut -d ' ' -f 4) "$encryptionpw")
			extra=$(decrypt $(echo "$SERVERRESPONSE" | cut -d ' ' -f 5) "$encryptionpw")

			echo
			echo "title: $title"
			echo "username: $username"

			if (( $nomask )); then  # output password depending on nomask input parameter
				echo "password: $pw"
			else
				echo -n "password (hidden): "
				tput setaf 0 ; tput setb 0 ; tput setab 0  # hide password
				echo -n "$pw"
				tput sgr0  # reset terminal back to normal colors
			fi

			echo  # new line after terminal color reset
			echo "extra info: $extra"
			echo

			# add encryption pw to key session
			add_key_to_key_session "$encryptionpw"

			# copy to X clipboard
			if (( $copytoclipboard )); then
				# check if xclip is installed
				if [ -z "$(which xclip 2>/dev/null)" ]; then
					echo -e "\nxclip not found. Password not copied.\n"
				else
					# send password to xclip
					echo -n "$pw" | xclip -selection c -r
					# check xclip response
					if [[ $? -eq 0 ]]; then
						echo -e "\nPassword copied to clipboard.\n"
					fi
				fi
			fi
			;;
		3)
			echo -e "\nPartly matched records found:\n"
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo -e "\nSpecify exact title."
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function list () {
	sessioncheck
	echo "List records."
	if [ "$title" == 'all' ] || [ "$title" == 'ALL' ]; then
		echo -e "\nList all titles."
	elif [[ $nbrOfParams -gt 1 ]]; then
		echo -e "\nInput title to list is \"$title\""
	else
		echo ; read -p "Name/site/title to list: " title
	fi
	if [[ -z "$title" ]]; then
		echo -e "Name can't be blank.\n"
		exit 1
	fi

	command="list"
	title=$(echo "$title" | base64 -w0 | base64 -w0)
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo -e "\nFetching records..."
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			echo -e "\nRecords found:\n"
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo
			;;
		3)
			echo -e "\nRecords found:\n"
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function delete () {
	sessioncheck
	echo "Delete record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo -e "\nInput title is \"$title\""
	else
		echo ; read -p "Name/site/title to delete: " title
	fi
	if [[ -z "$title" ]]; then
		echo -e "Name can't be blank.\n"
		exit 1
	fi

	command="delete"
	title=$(echo "$title" | base64 -w0 | base64 -w0)
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo -e "\nDeleting record..."
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			echo -e "\nServer record deletion OK:"
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo
			;;
		3)
			echo -e "\nRecords found:\n"
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo -e "\nSpecify exact record name."
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function update () {
	sessioncheck
	echo "Update record."
	if [[ $nbrOfParams -gt 1 ]] ; then
		echo -e "\nInput title is \"$title\""
	else
		echo ; read -p "Name/site/title to update: " title
	fi
	if [[ -z "$title" ]]; then
		echo -e "Name can't be blank.\n"
		exit 1
	fi
	echo ; read -p "Enter NEW username: " username
	if [ "$username" == '' ]; then
		echo -e "\nError: session username can't be empty.\n"; exit 1
	fi
	echo ; read -s -p "Enter NEW password: " pw
	echo ; read -s -p "Repeat NEW password: " pw2
	if [ "$pw" != "$pw2" ]; then
		echo -e "\nError: passwords don't match.\n"; exit 1
	elif [ "$pw" == '' ]; then
		echo -e "\nError: session password can't be empty.\n"; exit 1
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
			echo -e "\n\nError: Encryption passwords don't match."
		elif [ "$encryptionpw" == "$pw" ]; then
			echo -e "\n\nError: Record password and encryption password shouldn't be the same."
		elif [ "$encryptionpw" == '' ]; then
			echo -e "\n\nError: Encryption password can't be empty."
		else
			break
		fi
	done

	# encrypt user and pw
	echo -e "\nEncrypting..."
	title=$(echo "$title" | base64 -w0 | base64 -w0)
	username=$(encrypt "$username" "$encryptionpw")
	pw=$(encrypt "$pw" "$encryptionpw")
	extra=$(encrypt "$extra" "$encryptionpw")
	verification=$(encrypt "verification" "$encryptionpw")

	command="update"
	sessionuser=$(head -n 2 "$SESSIONPATH" | tail -n 1)
	sessionpw=$(head -n 3 "$SESSIONPATH" | tail -n 1)

	echo -e "\nUpdating record...\n"
	unswapped_b64=$(echo -n "${command}" "${sessionuser}" "${sessionpw}" "${title}" "${username}" "${pw}" "${extra}" "${verification}" | gzip -1f | base64 -w0)
	swapped_b64=$(b64swap "$unswapped_b64")
	SERVERRESPONSE=$(echo -n "$swapped_b64" | base64 -w0 | nc -N -w 5 "$(head -n 1 "$SESSIONPATH")" $PORT)
	response_valid $? $SERVERRESPONSE
	SERVERRESPONSE=$(decode_response $SERVERRESPONSE)

	case $(echo "$SERVERRESPONSE" | cut -d ' ' -f 1) in
		1)
			echo "Server error: $(echo "$SERVERRESPONSE" | cut -d ' ' -f 2-)"
			echo
			;;
		2)
			echo "$SERVERRESPONSE" | cut -d ' ' -f 2-
			echo "Remember your new encryption password."
			echo
			;;
		*)
			echo "Unknown error:"
			echo "$SERVERRESPONSE"
			echo
			;;
	esac
}


function helptext () {  # Help text diplayed if no or non-existent input parameter is given.
	cat <<'END'
Run command:
$ pwmgr (parameter) [(title)]

Init must be run first to create a session before the other commands can be
used. This is the base of the client<->server interaction.

COMMANDS:

- init / config
	Create a session. This creates a local session config and attempts to create
	a remote server	db session. If the username db already exists, it's reused.
	Previous session password must match.
	By entering the same sessionuser/sessionpassword multiple clients can be
	used with the same server DB.
	Optional:
	--nonew  : Expect an already existing user DB in the server. Exit without
	action if it's not found.

- init-change / config-change
	Change credentials of an existing session. Old credentials must be given for
	verification.

- status / check / connection / test
	Check session status against the server.

- add / encrypt / enc / put / save [(title)]
	Add a new record.
	Fields stored:
	- Title/Name
	- username
	- password
	- Extra field (optional/may be blank)
	Encryption password selection is prompted. The encryption of the record will
	be as strong as this password.

- get / decrypt / dec / fetch / show / load [(title)]
	Fetch a stored record to view. Same encryption password as when the record
	was stored must be entered.
	Optional:
	-c / --copy  : Attempt to automatically copy password to the X clipboard
	using xclip.
	--nomask  : Don't mask the password in the output.

- list / search [(title)]/[all]
	Search for a record with partial name. Searching for "all" will list all
	records in DB.

- delete / remove / del [(title)]
	Delete a record.

- update / change / edit
	Change a record, e.g. change the password stored. If the name of the record
	already exists, it's not possible to use "add" to overwrite, so this command
	must be used instead.

END
}


########################### main #######################################
nbrOfParams=$#

# set title to 2nd input parameter if given
if [[ $nbrOfParams -gt 1 ]]; then
	# possible parameters that shouldn't be interpreted as a record title
	if [ "$2" != "-c" ] && [ "$2" != "--copy" ] && [ "$2" != "--nomask" ]; then
		title=$2
	fi
fi

# check if netcat is installed
if [ -z "$(which nc 2>/dev/null)" ]; then
	echo "netcat not found. netcat-openbsd version of netcat needed."
	exit 1
fi

# check if base64 is installed
if [ -z "$(which base64 2>/dev/null)" ]; then
	echo "base64 not found."
	exit 1
fi

# check if openssl is installed
if [ -z "$(which openssl 2>/dev/null)" ]; then
	echo "openssl not found."
	exit 1
fi

# check if gzip is installed
if [ -z "$(which gzip 2>/dev/null)" ]; then
	echo "gzip not found."
	exit 1
fi

# init parameter input - run init procedure
if [ "$1" == "init" ] || [ "$1" == "config" ]; then
	# new session creation block option
	if [[ $nbrOfParams -gt 1 ]] && [ "$2" == "--nonew" ]; then
		nonew=1
	fi
	init

# init-change parameter input - run init-change procedure
elif [ "$1" == "init-change" ] || [ "$1" == "config-change" ] || [ "$1" == "configchange" ]; then
	init-change

# status parameter input - run status procedure
elif [ "$1" == "status" ] || [ "$1" == "check" ] || [ "$1" == "connection" ] || [ "$1" == "test" ]; then
	status

# add parameter input - run add procedure
elif [ "$1" == "add" ] || [ "$1" == "encrypt" ] || [ "$1" == "enc" ] || [ "$1" == "put" ] || [ "$1" == "save" ]; then
	add

# get parameter input - run get procedure
elif [ "$1" == "get" ] || [ "$1" == "decrypt" ] || [ "$1" == "dec" ] || [ "$1" == "fetch" ] || [ "$1" == "show" ] || [ "$1" == "load" ]; then
	# copy to clipboard
	if [ "$2" == "-c" ] || [ "$3" == "-c" ] || [ "$4" == "-c" ] || [ "$2" == "--copy" ] || [ "$3" == "--copy" ] || [ "$4" == "--copy" ]; then
		copytoclipboard=1
	fi
	# password mask override
	if [ "$2" == "--nomask" ] || [ "$3" == "--nomask" ] || [ "$4" == "--nomask" ]; then
		nomask=1
	fi
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
