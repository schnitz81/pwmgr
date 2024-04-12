#!/bin/bash


# check if sqlite client is available
if [ -z "$(which openssl)" ] ; then
	echo "openssl not found."
	exit 1
fi

# check if sqlite client is available
if [ -z "$(which sqlite3)" ] ; then
	echo "sqlite3 not found."
	exit 1
fi

# check input parameter
if [ $# -lt 1 ]; then
	echo "Need path to sqlite file as input parameter."
	exit 1
fi

DB_PATH=$1
skips=0
errors=0

read -p "Enter number of old iterations: " old_iterations
read -p "Enter number of new iterations (to convert to): " new_iterations
read -s -p "Enter OLD encryption password (will be used for decryption): " old_encryption_pw
echo; read -s -p "Enter NEW encryption password (will be used for encryption, blank for reusing old pw): " new_encryption_pw

# resuse old pw if blank, repeat verifcation if new
if [ -z "$new_encryption_pw" ]; then
	new_encryption_pw=$old_encryption_pw
else
	echo; read -s -p "Repeat encryption password (or quit):" new_encryption_pw2
	if [ "$new_encryption_pw" != "$new_encryption_pw2" ]; then
		echo "Error: Encryption passwords don't match."
		exit 1
	fi
fi

mapfile -t arr_all_titles < <(sqlite3 "$DB_PATH" 'select title from records;')
for title in "${arr_all_titles[@]}"; do
	echo; echo "------------------"

	# get all encrypted values in record
	echo "Converting $title"

	sleep .3
	old_username=$(sqlite3 "$DB_PATH" "select username from records where title like '$title';" | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter "$old_iterations" -salt -pass pass:"$old_encryption_pw")
	sleep .3
	old_pw=$(sqlite3 "$DB_PATH" "select pw from records where title like '$title';" | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter "$old_iterations" -salt -pass pass:"$old_encryption_pw")
	sleep .3
	old_extra=$(sqlite3 "$DB_PATH" "select extra from records where title like '$title';" | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter "$old_iterations" -salt -pass pass:"$old_encryption_pw")
	sleep .3
	old_verification=$(sqlite3 "$DB_PATH" "select verification from records where title like '$title';" | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter "$old_iterations" -salt -pass pass:"$old_encryption_pw")
	sleep .3

	# verify old verification value - skip conversion of current record if invalid
	if [ "$old_verification" != "verification" ]; then
		echo "Warning: $title skipped due to invalid verification value."
		((skips=skips+1))
		continue
	fi

	# create new encrypted values
	new_username=$(echo -n "$old_username" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter "$new_iterations" -salt -pass pass:"$new_encryption_pw" | tr -d "\n")
	new_pw=$(echo -n "$old_pw" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter "$new_iterations" -salt -pass pass:"$new_encryption_pw" | tr -d "\n")
	new_extra=$(echo -n "$old_extra" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter "$new_iterations" -salt -pass pass:"$new_encryption_pw" | tr -d "\n")
	new_verification=$(echo -n "verification" | openssl enc -chacha20 -md sha3-512 -a -pbkdf2 -iter "$new_iterations" -salt -pass pass:"$new_encryption_pw" | tr -d "\n")

	# update DB record
	sql_new_username=$(sed 's/'\''/&&/g' <<< "$new_username")
	sql_new_pw=$(sed 's/'\''/&&/g' <<< "$new_pw")
	sql_new_extra=$(sed 's/'\''/&&/g' <<< "$new_extra")
	sql_new_verification=$(sed 's/'\''/&&/g' <<< "$new_verification")
	sqlite3 "$DB_PATH" "update records set username = '${sql_new_username}', pw = '${sql_new_pw}', extra = '${sql_new_extra}', verification = '${sql_new_verification}' where title like '$title'";
	sleep .3
	new_verification_check=$(sqlite3 "$DB_PATH" "select verification from records where title like '$title';" | openssl enc -chacha20 -md sha3-512 -a -d -pbkdf2 -iter "$new_iterations" -salt -pass pass:"$new_encryption_pw")
	if [ "$new_verification_check" == "verification" ]; then
		echo "$title record conversion success"
	else
		echo "Error: $title record conversion error"
		((errors=errors+1))
	fi
done

echo; echo "Done."
echo "Number of skipped records: $skips"
echo "Number of conversion errors: $errors"

