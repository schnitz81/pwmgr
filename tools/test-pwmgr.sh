#!/bin/bash

#
# Script for running an automated test of pwmgr, both server and client, to
# verify functionality during development.
#


TESTUSER="pwmgr_test_tool_user"
TESTPASSWORD="testpassword"
LOGFILE="/tmp/pwmgr_test_tool.log"
SESSIONPATH="$HOME/.config/pwmgr/.session"
PORT=48222


function log () {
	local logmsg=$1
	local expect_return_code=$2
	local errormsg=""
	if [ "$expect_return_code" -eq 0 ]; then
		errormsg="SUCCESS"
	else
		errormsg="FAIL"
	fi
	echo "$(date +"%Y%m%d %H:%M:%S") : $logmsg : $errormsg" >> $LOGFILE
}


function init () {
	echo "Testing init..."
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client init
		log_user 1

		expect {
			"session? " {
				send -- "y\r"
				exp_continue
			}
			"IP: " {
				send -- "$server\r"
				exp_continue
			}
			"username: " {
				send -- "$TESTUSER\r"
				exp_continue
			}
			"password: " {
				send -- "$TESTPASSWORD\r"
				exp_continue
			}
			"password: " {
				send -- "$TESTPASSWORD\r"
				exp_continue
			}
			"successfully" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: no success returned"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "init" $rtncode
}


function init-change () {
	echo "Testing init-change..."
	if [ "$1" == "1" ]; then
		user="$TESTUSER"
		password="$TESTPASSWORD"
		user2="$TESTUSER"_new
		password2="$TESTPASSWORD"_new
	else
		user2="$TESTUSER"
		password2="$TESTPASSWORD"
		user="$TESTUSER"_new
		password="$TESTPASSWORD"_new
	fi
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client init-change
		log_user 1

		expect {
			"*change session*? " {
				send -- "y\r"
				exp_continue
			}
			"IP: " {
				send -- "$server\r"
				exp_continue
			}
			"*CURRENT*username: " {
				send -- "$user\r"
				exp_continue
			}
			"*CURRENT*password: " {
				send -- "$password\r"
				exp_continue
			}
			"*CURRENT*password: " {
				send -- "$password\r"
				exp_continue
			}
			"*NEW*username: " {
				send -- "$user2\r"
				exp_continue
			}
			"*NEW*password: " {
				send -- "$password2\r"
				exp_continue
			}
			"*NEW*password: " {
				send -- "$password2\r"
				exp_continue
			}
			"successfully" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: no success returned"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "init-change" $rtncode
}


function generic_nointeraction () {
	cmd=$1
	echo "Testing $cmd..."
	if [ "$cmd" == "delete" ]; then
		cmd="delete testtitle"
	fi
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client $cmd
		log_user 1

		expect {
			"successful" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			"OK" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: no success returned"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "$(echo $cmd | cut -f 1 -d ' ')" $rtncode
}


function add () {
	echo "Testing add..."
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client add
		log_user 1

		expect {
			"title: " {
				send -- "testtitle\r"
				exp_continue
			}
			"username: " {
				send -- "recorduser\r"
				exp_continue
			}
			"password: " {
				send -- "recordpassword\r"
				exp_continue
			}
			"password: " {
				send -- "recordpassword\r"
				exp_continue
			}
			"Extra*: " {
				send -- "extra test\r"
				exp_continue

			}
			"*encryption password*: " {
				send -- "encryptionpassword\r"
				exp_continue

			}
			"*encryption password*: " {
				send -- "encryptionpassword\r"
				exp_continue

			}
			"successfully" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: no success returned"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "add" $rtncode
}


function update () {
	echo "Testing update..."
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client update
		log_user 1

		expect {
			"update: " {
				send -- "testtitle\r"
				exp_continue
			}
			"username: " {
				send -- "recordusernew\r"
				exp_continue
			}
			"password: " {
				send -- "recordpasswordnew\r"
				exp_continue
			}
			"password: " {
				send -- "recordpasswordnew\r"
				exp_continue
			}
			"Extra*: " {
				send -- "extra test new\r"
				exp_continue

			}
			"*encryption password*: " {
				send -- "encryptionpasswordnew\r"
				exp_continue

			}
			"*encryption password*: " {
				send -- "encryptionpasswordnew\r"
				exp_continue

			}
			"successfully" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: no success returned"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "update" $rtncode
}


function list () {
	echo "Testing list..."
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client list
		log_user 1

		expect {
			"list: " {
				send -- "test\r"
				exp_continue
			}
			"testtitle" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: title not found"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "list" $rtncode
}


function listall () {
	echo "Testing list all..."
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client list all
		log_user 1

		expect {
			"testtitle" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: title not found"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "listall" $rtncode
}


function getpart () {
	echo "Testing getting part of title..."
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client get
		log_user 1

		expect {
			"get: " {
				send -- "test\r"
				exp_continue
			}
			"testtitle" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: title not found"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "getpart" $rtncode
}


function get () {
	echo "Testing getting exact title..."
	if [ "$1" != "2" ]; then
		title="testtitle"
		user="recorduser"
		password="recordpassword"
		extra="extra test"
		encryptionpassword="encryptionpassword"
	else
		title="testtitle"
		user="recordusernew"
		password="recordpasswordnew"
		extra="extra test new"
		encryptionpassword="encryptionpasswordnew"
	fi
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		set values { "$title" "$user" "$password" "$extra" }
		spawn $client get --nomask
		log_user 1
		set output "" ;# initialize output variable

		expect {
			"get: " {
				send -- "$title\r"
				exp_continue
			}
			"encryption password: " {
				send -- "$encryptionpassword\r"
				exp_continue
			}
			eof {
				# Command finished, capture everything seen so far
				set output \$expect_out(buffer)
			}
			timeout {
				puts "Timeout waiting for prompt"
				exit 1
			}
		}



		# Split the output into lines
		set lines [split \$output "\n"]

		# list for detecting values fetched from server
		set found_values {}

		# Check each line for the fetched values
		foreach line \$lines {
			foreach value \$values {
				if {[string match "*\$value*" \$line]} {
					puts "Found value \$value"
					lappend found_values \$value
				}
			}
		}
		# Check if all values were returned
		set all_values_returned 1
		foreach value \$values {
			if {[lsearch -exact \$found_values \$value] < 0} {
				puts "Missing value: \$value"
				set all_values_returned 0
			}
		}

		if {\$all_values_returned} {
			puts "All values returned successfully."
			exit 0
		} else {
			puts "All values were not detected."
			exit 1
		}

		eof {
			# If you reach EOF, check the buffer
			set results \$expect_out(buffer)
			puts "init run FAIL: all expected data was not found"
			puts "Debug: \$results"
			exit 1
		}

EOF
	rtncode=$?
	log "get$1" $rtncode
}


function getpart () {
	echo "Testing getting part of title..."
	/usr/bin/expect <<EOF
		set timeout 5
		set send_slow {1 .5}
		spawn $client get
		log_user 1

		expect {
			"get: " {
				send -- "test\r"
				exp_continue
			}
			"testtitle" {
				# Capture output when the success message is received
				set results \$expect_out(buffer)
				puts "Success returned: init run pass"
				exit 0
			}
			eof {
				# If you reach EOF, check the buffer
				set results \$expect_out(buffer)
				puts "init run FAIL: title not found"
				puts "Debug: \$results"
				exit 1
			}
		}
EOF
	rtncode=$?
	log "getpart" $rtncode
}

function store_sessionfile () {
	# store existing session file temporarily during test
	if [ -f "$SESSIONPATH" ]; then
		mv "$SESSIONPATH" "$SESSIONPATH.testruntmp"
	fi
}


function restore_sessionfile () {
	# store existing session file temporarily during test
	if [ -f "$SESSIONPATH.testruntmp" ]; then
		mv "$SESSIONPATH.testruntmp" "$SESSIONPATH" 
	fi
}


# check expect availability
if [ -z "$(which expect 2>/dev/null)" ]; then
	echo "Please install expect first."
	exit 1
fi


# get IP/address
echo ; read -p "Server address/IP to run test againts: " server
if [ "$server" == '' ]; then
	echo -e "\nError: server address can't be empty.\n"; exit 1
fi


# get client path
echo ; read -p "Enter location of the client path: " client
if [ "$client" == '' ]; then
	echo -e "\nError: client path can't be empty.\n"; exit 1
fi


# test connectivity
nc -vz -w 5 "$server" $PORT
if [[ $? -ne 0 ]]; then
	echo -e "Error: Connection error. No server response.\n"; exit 1
fi

# store current session
store_sessionfile

# test sequence
init
generic_nointeraction "status"

add
list
listall
getpart
get "1"
update
get "2"
init-change "1"
get "2"
init-change "2"
get "2"
generic_nointeraction "backup"
generic_nointeraction "delete"

# store session
restore_sessionfile

# print results
tail -n 13 "$LOGFILE"
