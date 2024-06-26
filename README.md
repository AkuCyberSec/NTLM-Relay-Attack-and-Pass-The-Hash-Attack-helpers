# Scripts for NTLM Relay Attack and Pass-The-Hash Attack

## Description
During Internal Penetration Tests I usually perform NTLM Relay Attacks.  
It happened several times that I had to wait so long before a session was relayed, and I had to wait even more for the session of a user with high privileges on a specific machine.  
When a session is relayed, it could happen that the session expires and therefore we may lose the access we waited so long for.  
That's the reason behind these two simple scripts.

The script in Python (**autorun_crackmapexec_with_ntlmrelayx.py**) automatically checks for successfully relayed sessions and, if the session is marked as an "Admin session", it dumps the NTLM Hashes from the target system using **crackmapexec**. The script also performs a directory listing   
The script in Bash (**check_hash_against_smb.sh**) helps in performing a "Password Spraying Attack" (or maybe a "Hash Spraying Attack"?): for a given list of targets, usernames and hashes, it tries every combination.

## Why BASH and Python?
I just wrote these two scripts during different tests (BASH script first, Python script then).  
Feel free to translate the scripts in whatever programming language you like.

## Requirements
1. Responder
2. impacket-ntlmrelayx
3. crackmapexec
4. pth-smbclient
5. proxychains

## How the scripts work?
### autorun_crackmapexec_with_ntlmrelayx.py
To run this script we need Responder, impacket-ntlmrelayx, crackmapexec and proxychains.
First we need setup and run Responder for the poisoning:
1. Edit Responder.conf (default location on Kali: /etc/responder/Responder.conf)
2. Disable SMB Server by replacing the line "SMB = On" with "SMB = Off"
3. Run Responder

Then, we need to run impacket-ntlmrelayx for the NTLM Relay Attack.  
Remember to use the flag **-socks** to enable the SOCKS proxy for the relayed connections.  

The SOCKS proxy listens on port **1080**, so we need to setup **proxychains** to use it:
1. Edit /etc/proxychains4.conf
2. In the section [Proxylist] set: **socks4 127.0.0.1 1080**

Once the environment is setup, we can run the Python script (no arguments required).  
The script makes an HTTP GET request to **http://localhost:9090/ntlmrelayx/api/v1.0/relays**.  
This endpoint returns a 2D Array, and each array contains the following information:
0. Protocol (SMB)
1. Target (the IP Address of the target)
2. Username (Domain/Username)
3. AdminStatus (True if the relayed session is of an administrator)
4. Port (445)

The script runs **crackmapexec** to list all the directories:    
``proxychains -q crackmapexec smb {ipAddress} -d '{domain}' -u '{username}' -p '' --hashes > {filename}``

Then runs **crackmapexec** to dump the NTLM Hashes if the AdminStatus is True:  
``proxychains -q crackmapexec smb {ipAddress} -d '{domain}' -u '{username}' -p '' --sam > {filename}``

As you can see the password is empty: this is due to the fact that we're not actually authenticating to the target, but we're asking to ntlmrelayx.py to give us the relayed session, so the password is not necessary.

Everytime the script runs **crackmapexec**, it also saves the output to a folder, so that you don't miss anything.

### check_hash_against_smb.sh
This script is even simpler: all we need is **pth-smbclient**.  
For each given target, the script tries all the combinations of users and hashes.

First, we need to create 3 files:
1. A file that contains the IP Address of the targets (one per line). For example: targets.txt
2. A file that contains all the usernames we want to try (one per line). For example: usernames.txt
3. A file that contains all the hashes we want to try (one per line). For example: hashes.txt

Then, we need to decide a delay between each request. For example: 5 seconds.  
Finally, we need to decide the name of the output file. For example: output.txt

Run the command:  
``./check_hash_against_smb.sh ./targets.txt ./hashes.txt ./users.txt 5 ./output.txt``

This scripts uses **pth-smbclient** and, using **grep**, checks if the output contains the word "Share". If it does, it means that the hash works:  
``pth-smbclient -U <USERNAME> --pw-nt-hash --password=<HASH> -L //<TARGET> 2>/dev/null | grep -i Share``

**Note: if the SMB Server allows Guest Session or Null Sessions, the script may generate false positives.**

## Some tips for ntlmrelayx.py
If, for any reason, ntlmrelayx.py doesn't allow you to relay multiple session for a single targets by giving you the message "Connection controlled, but there are no more targets left!", there's a simple workaround:
1. Find the file called targetsutils.py (usually under the folder of impacket/examples/ntlmrelayx/utils)
2. Find the method getTarget(self, identity=None, multiRelay=True)
3. On the line before the first instruction (if identity is not [...]) add: **multiRelay=True**

You may wonder why:
Imagine you've relayed the session of the user "John" to the target 10.1.1.1, and AdminStatus is False.  
Now imagine you see that ntlmrelayx.py controlled a connection for the user "Administrator" but didn't try to relay the session because "there are no more targets left".  
If this happens, you may lose your chance to relay the session of an administrator.  

Back in the past, I didn't need to use this workaround.  
Now, I don't know why, but this is the only way it works for me.
