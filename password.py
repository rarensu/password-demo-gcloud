import hashlib
import random

def multihash64(password):
    hashes=multihash(password)
    while len(hashes)<64:
        ext_password=password+chr(len(hashes)+32)
        hash=hashlib.sha256(ext_password.encode()).hexdigest()
        hashes.append(hash)
    random.shuffle(hashes)
    return hashes

def multihash(password):
    passwords=multipass(password)
    hashes=[]
    for sub_password in passwords:
        hash=hashlib.sha256(sub_password.encode()).hexdigest()
        hashes.append(hash)
    return hashes

def multipass(password):
    passwords=[]
    if len(password):
        passwords.append(password)
    for i in range(len(password)):
        sub_password=password[:i]+password[i+1:]
        passwords.append(sub_password)
    return passwords

def match_vector(client_hashes, server_hashes):
    matches=[]
    for hash in client_hashes:
        if hash in server_hashes:
            matches.append(True)
        else:
            matches.append(False)
    return matches

def match_count(client_hashes, server_hashes):
    return sum(match_vector(client_hashes, server_hashes))

def match_stats(client_hashes, server_hashes):
    matches=match_count(client_hashes, server_hashes)
    long_match=client_hashes[0] in server_hashes
    if matches==0:
        return "no match"
    elif matches==len(client_hashes):
        return "exact match"
    elif long_match:
        return "likely deletion typo"
    else:
        return "likely other typo"
    return long_match, matches