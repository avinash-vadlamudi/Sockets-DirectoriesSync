import time
import socket
import os
import re
import hashlib
import stat

s = socket.socket()
host = ""
port = 60000
start =1              
previous_checktime = time.time()

s.connect((host, port))
print "connected"
dir_client = os.path.dirname(os.path.realpath(__file__))
dir_server = os.path.dirname(os.path.realpath(__file__))
print dir_client

def hash_file(file_name):
    hash_md5 = hashlib.md5()
           # open file for reading in binary mode and reading chunks of 4 bytes
    with open(file_name,"rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()

def download_file(message):
	messages = message.split(" ")
	path = dir_client + messages[1] + '/' + messages[2]
	if os.path.exists(path):
		path2 = dir_server + messages[1] + '/' + messages[2]
		s.send("1 "+path2)
		hash1 = s.recv(1024)
		hash2 = hash_file(path)
		if hash1 == hash2:
			s.send("No Need")
		else:
			s.send("send")
			f = open(path,'wb')
			while True:
				data = s.recv(1024)
				if data == "File Finished":
					s.send("OK")
					break
				else:
					f.write(data)
			f.close()
	else:
		s.send("send")
		f = open(path,'wb')
		while True:
			data = s.recv(1024)
			if data == "File Finished":
				s.send("OK")
				break
			else:
				f.write(data)
		f.close()

	return


def update_sharedfolders():
	while True:
		message = s.recv(1024)
		print message
		messages = message.split(" ")

		if message == "Over":
			s.send("OK")
			break

		if messages[0]=="1":
			if messages[2] == "eg1.py":
				s.send("yes")
				continue
			path = dir_client + messages[1] + '/'+messages[2]
			st = os.stat(path)
			print st
			print "1"+path

			download_file(message)
		elif messages[0]=="2":
			path = dir_client+messages[1]
			print "2"+path
			if not os.path.exists(path):
				os.makedirs(path)
				s.send("no")
			else:
				s.send("yes")

	return

while True:
	if start == 1:
		s.send(dir_client)
		dir_server = s.recv(1024)
		print dir_server+'--'
		start = 0
		update_sharedfolders()
		continue

	if time.time() - previous_checktime >= 60:
		previous_checktime = time.time()
		update_sharedfolders()
		continue

	message = s.recv(1024)
	message_part = message.split(" ")

	print message
	if message_part[0] == "close":
		s.send("Hello server!")
		s.close()
		break
	elif message_part[0] == "download":
		filename = dir_client + '/' + message_part[1]
		if os.path.exists(filename):
			mtime = os.stat(filename).st_mtime
			if str(mtime) < message_part[2]:
				s.send("send")
				f = open(filename,'wb')
				while True:
					data = s.recv(1024)
					if data == "File Finished":
						s.send("OK")
						break
					else:
						f.write(data)
				f.close()
				file_hash = s.recv(1024)
				hash2 = hash_file(filename)
				if file_hash == hash2:
					print "yes"
				else:
					print "no"
			else:
				s.send("No Need")
		else:
			s.send("send")
			f = open(filename,'wb')
			while True:
				data = s.recv(1024)
				if data == "File Finished":
					s.send("OK")
					break
				else:
					f.write(data)

			f.close()
			file_hash = s.recv(1024)
			hash2 = hash_file(filename)
			if file_hash == hash2:
				print "yes"
				s.send("yes")
			else:
				s.send("no")
				print "no"
		time.sleep(0.1)
	else:
		s.send("ok")