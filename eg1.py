import socket
import os
import re
import time
import hashlib
import stat


port = 60000
s = socket.socket()
host=""
start=1
s.bind((host,port))
s.listen(10)
port_array = [60001,60002,60003]
previous_checktime = time.time()

print 'server listening ....'
client_conn, addr = s.accept()

dir_server = os.path.dirname(os.path.realpath(__file__))
print dir_server

def hash_file(file_name):
    hash_md5 = hashlib.md5()
           # open file for reading in binary mode and reading chunks of 4 bytes
    with open(file_name,"rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()

def file_share(filename):
#    os.chmod(filename, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    st = os.stat(filename)
    print st    
    f = open(filename,'rb')
    l = f.read(1024)
    while(l):
        client_conn.send(l)
        l =f.read(1024)
    f.close()
    client_conn.send("File Finished")
    client_conn.recv(1024)
    return

    
def update_sharedfolders(subdir):
    for [dirpath2,dirname,filenames] in os.walk(dir_server+subdir):
        break
    for file in filenames:
        client_conn.send("1 "+subdir+" "+file)
        reply = client_conn.recv(1024)
        path2 = reply.split()
        if path2[0]=="1":
            hash_req = hash_file(path2[1])
            client_conn.send(hash_req)
            reply = client_conn.recv(1024)
        if reply == "send":
            file_share(dirpath2+'/'+file)

    for dirn in dirname:
        client_conn.send("2 "+subdir+"/"+dirn)
        client_conn.recv(1024)
        update_sharedfolders(subdir+"/"+dirn)
    return 

while 1:
    if start ==1 :
        client_conn.send(dir_server)
        dir_client = client_conn.recv(1024)
        print dir_client
        start = 0
        update_sharedfolders("")
        client_conn.send("Over")
        client_conn.recv(1024)
        continue
    print previous_checktime,time.time()
    if time.time() - previous_checktime >= 60:
        previous_checktime = time.time()
        update_sharedfolders("")
        client_conn.send("Over")
        client_conn.recv(1024)
        continue
    command = raw_input("prompt> ")
    command_part = command.split(" ")

    if command_part[0] == "close":
#        client_conn.close()
        client_conn.send(command)
        recv_message = client_conn.recv(1024)
        break
    elif command_part[0] == "index":
        client_conn.send(command)
        recv_message = client_conn.recv(1024)
        print "index"
    elif command_part[0] == "download":
        file_name = dir_server + '/'+command_part[1]
        mtime = os.stat(file_name).st_mtime
        command = command + " " + str(mtime)
        client_conn.send(command)
        reply = client_conn.recv(1024)
        if reply == "send":
            f = open(file_name,'rb')
            l = f.read(1024)
            while(l):
                client_conn.send(l)
                l = f.read(1024)
            f.close()
            hash_value = hash_file(file_name)
            client_conn.send("File Finished")
            client_conn.recv(1024)
            client_conn.send(hash_value)
            client_conn.recv(1024)


        else:
            print reply
            print "latest file already present in that folder "

    else:
        client_conn.send(command)
        client_conn.recv(1024)