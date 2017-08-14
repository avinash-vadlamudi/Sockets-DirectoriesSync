import socket
import os
import re
import time
import hashlib
import stat
import signal
import sys
import subprocess as sub

s1 = socket.socket()
s2 = socket.socket()

host = ""
port1 = 60000
port2 = 50000
try:
	s1.bind((host,port1))
except:
	port1 = 60005
	# print port1
	s1.bind((host,port1))
s1.listen(5)

r2_conn, addr = s1.accept()
s1_dir = os.path.dirname(os.path.realpath(__file__))
s2_dir = os.path.dirname(os.path.realpath(__file__))

try:
	s2.connect((host,port2))
except:
	port2 = 50005
	s2.connect((host,port2))

prev_checktime1 = time.time()
prev_checktime2 = time.time()
restart_time = time.time()
TIME = 1

start_flag = 1
flag_timebreak = 0

class TimedOutExc(Exception):
	pass

def handler(signum, frame):
	raise TimedOutExc()

def hash_file(filename):
	hash_md5 = hashlib.md5()

	with open(filename,"rb") as f:
		for chunk in iter(lambda: f.read(4096),b""):
			hash_md5.update(chunk)

	return hash_md5.hexdigest()

def send_hash(subdir):
	for [dirpath2,dirname,filenames] in os.walk(s1_dir+subdir):
		break
	for file in filenames:
		if file == "s1.py" or file == "file1.log":
			continue
		s2.recv(1024)
		hash_value = hash_file(s1_dir + subdir + "/"+ file)
		st = os.stat(s1_dir + subdir + "/"+ file)
		text = subdir + "/" +file + ';' + hash_value + ';' + str(st.st_mtime) 
		s2.send(text)
	for dirn in dirname:
		send_hash(subdir + "/" + dirn)
	return

def file_share(filename):
    f = open(filename,'rb')
    l = f.read(1024)
    while(l):
        r2_conn.send(l)
        r2_conn.recv(1024)
        l =f.read(1024)
    f.close()
    r2_conn.send("File Finished")
    r2_conn.recv(1024)
    return

def update_sharedfolders(subdir):
    for [dirpath2,dirname,filenames] in os.walk(s1_dir+subdir):
        break
    for file in filenames:
        r2_conn.send("1 "+subdir+"/"+file)
        reply = r2_conn.recv(1024)
        path2 = reply.split()
        if path2[0]=="1":
            hash_value = hash_file(path2[1])
            st = os.stat(path2[1])
            text = hash_value + ';' + str(st.st_mode)
            r2_conn.send(text)
            reply = r2_conn.recv(1024)
        if reply == "send":
        	flag = 0
        	if os.access(dirpath2+'/'+file,os.R_OK):
        		r2_conn.send("True")
        		val = r2_conn.recv(1024)
        		if val == "True":
        			flag =0
        		else:
        			flag = 1
        	else:
        		r2_conn.send("False")
        		flag = 1
        		r2_conn.recv(1024)
        	if flag == 1:
        		continue
        	file_share(dirpath2+'/'+file)

    for dirn in dirname:
        r2_conn.send("2 "+subdir+"/"+dirn)
        r2_conn.recv(1024)
        update_sharedfolders(subdir+"/"+dirn)
    return 

def download_file(message):
	messages = message.split(" ")
	path = s1_dir + messages[1]
	path2 = s2_dir + messages[1]
	s2.send("1 "+path2)
	value = s2.recv(1024)
	values = value.split(";")
	hash1 = values[0]
	mode = int(values[1])
	if os.path.exists(path):
		hash2 = hash_file(path)
		os.chmod(path, mode & 0777)
		if hash1 == hash2:
			s2.send("No Need")
		else:
			s2.send("send")
			flag = 0
			val = s2.recv(1024)
			if val == "True":
				if os.access(path,os.W_OK):
					s2.send("True")
				else:
					s2.send("False")
					flag = 1
			else:
				s2.send("False")
				flag = 1

			if flag == 1:
				print "permission denied"
				return
			print messages[1], "UPDATED"
			f = open(path,'wb')
			while True:
				data = s2.recv(1024)
				s2.send("OK")
				if data == "File Finished":
					break
				else:
					f.write(data)
			f.close()
	else:
		s2.send("send")
		flag = 0
		val = s2.recv(1024)
		if val == "True":
			s2.send("True")
			flag = 0
		else:
			s2.send("False")
			flag = 1

		if flag == 1:
			print "permission denied"
			return
		print messages[1], "UPDATED"
		f = open(path,'wb')
		while True:
			data = s2.recv(1024)
			s2.send("OK")
			if data == "File Finished":
				break
			else:
				f.write(data)
		f.close()
		os.chmod(path, mode & 0777)

	return


def update_sharedfolders_r():
	while True:
		message = s2.recv(1024)
		messages = message.split(" ")

		if message == "Over":
			s2.send("OK")
			break

		if messages[0]=="1":
			if messages[1] == "/s2.py" or messages[1] == "/file2.log":
				s2.send("yes")
				continue
			download_file(message)
		elif messages[0]=="2":
			path = s1_dir + messages[1]
			if not os.path.exists(path):
				os.makedirs(path)
				s2.send("no")
			else:
				s2.send("yes")

	return

signal.signal(signal.SIGALRM, handler)
while True:
	if start_flag == 1:
		r2_conn.send(s1_dir)
		r2_conn.recv(1024)

		s2_dir = s2.recv(1024)
		s2.send("OK")

		# print s1_dir
		# print s2_dir

		update_sharedfolders("")
		r2_conn.send("Over")
		r2_conn.recv(1024)
		prev_checktime1 = time.time()
		f = open(s1_dir+"/"+"file1.log","a+")
		f.write("AUTO UPDATE"+"   "+time.ctime(time.time()) + "\n")
		f.close()
		update_sharedfolders_r()
		prev_checktime2 = time.time()

		start_flag = 0
		continue

	if time.time() - prev_checktime1 >= 600:
		update_sharedfolders("")
		r2_conn.send("Over")
		r2_conn.recv(1024)
		prev_checktime1 = time.time()
		f = open(s1_dir+"/"+"file1.log","a+")
		f.write("AUTO UPDATE"+"   "+time.ctime(time.time())+"\n")
		f.close()
		update_sharedfolders_r()
		prev_checktime2 = time.time()
		continue		

	signal.alarm(TIME)

	try:
		if flag_timebreak == 0:
			command = raw_input("Prompt> ")
		else:
			flag_timebreak = 0 
			command = raw_input()
		signal.alarm(0)
		r2_conn.send(command)
		r2_conn.recv(1024)
		commands = command.split(" ")
		length = len(commands)
		if commands[0] == "close":
			break
		elif commands[0] == "index":
			if length == 1:
				print "invalid command"
				continue
			if commands[1] == "longlist" or commands[1] =="shortlist" or commands[1] == "regex":
				while True:
					r2_conn.send("OK")
					l = r2_conn.recv(1024)
					if l == "Over":
						break
					else:
						ls = l.split(";")
						size = int(ls[1])
						mode = int(ls[2])
						mtime = float(ls[3])
						if stat.S_ISREG(mode):
							file = "REG_FILE"
						elif stat.S_ISDIR(mode):
							file = "DIRECTORY"
						elif stat.S_ISLNK(mode):
							file = "SYM_LINK"
						elif stat.S_ISSOCK(mode):
							file = "SOCKET"
						else:
							file = "OTHERS"
						if commands[1] == "longlist":
							print "file-", ls[0], ", size-" , size , ", type-", file,", timestamp-", time.ctime(mtime)
			
						elif commands[1] == "shortlist":
							if length<4:
								print "invalid command"
								break
							time1 = float(commands[2])
							time2 = float(commands[3])
							if time1 <=mtime and mtime<=time2:
								print "file-", ls[0], ", size-" , size , ", type-", file,", timestamp-", time.ctime(mtime) 
			
						else:
							if length <3:
								print "invalid command"
								break
							string = commands[2]
							if re.search(string,ls[0]):
								print "file-", ls[0], ", size-" , size , ", type-", file,", timestamp-", time.ctime(mtime)
			else:
				print "invalid command"	
		elif commands[0] == "hash":
			if length == 1:
				print "invalid command"
				continue
			if commands[1] == "verify":
				if length ==2:
					print "invalid command"
					continue
				filename = commands[2]
				r2_conn.send("OK")
				value = r2_conn.recv(1024)

				if value == "FALSE":
					print "improper filename"
				else:
					values = value.split(";")
					hash_value = values[0]
					mtime = float(values[1])
					if os.path.exists(s1_dir+'/'+filename):
						hash_value2 = hash_file(s1_dir+'/'+filename)
						if hash_value == hash_value2:
							print "NOT UPDATED" , hash_value, "timestamp:", time.ctime(mtime)
						else:
							print "UPDATED", hash_value, "timestamp:", time.ctime(mtime)

					else:
						print "file doesn't exist in this folder",hash_value, time.ctime(mtime)

			elif commands[1] == "checkall":
				while True:
					r2_conn.send("Ok")
					value = r2_conn.recv(1024)
					if value == "Over":
						break
					else:
						values = value.split(";")
						hash_value = values[1]
						filename = values[0] 
						mtime = float(values[2])
						if os.path.exists(s1_dir+ filename):
							hash_value2 = hash_file(s1_dir+ filename)
							if hash_value == hash_value2:
								print "NOT UPDATED", filename, hash_value, time.ctime(mtime)
							else:
								print "UPDATED", filename, hash_value, time.ctime(mtime)
						else:
							print "file not there in this folder",filename, hash_value, time.ctime(mtime)

			else:
				print "invalid command"

		elif commands[0] == "download":
			if length == 1:
				print "invalid command"
				continue
			if commands[1] == "TCP":
				if length == 2:
					print "invalid command"
					continue
				filename = commands[2]
				r2_conn.send("OK")
				mess = r2_conn.recv(1024)
				if mess == "FALSE":
					print "improper filename"
				else:
					r2_conn.send("OK")
					value = r2_conn.recv(1024)
					values = value.split(";")
					hash_value = values[0]
					size = int(values[1])
					mtime = float(values[2])
					mode = int(values[3])

					if os.path.exists(s1_dir + '/' + filename):
						os.chmod(s1_dir + '/' + filename, mode & 0777)
						hash_value2 = hash_file(s1_dir + '/' + filename)
						if hash_value == hash_value2:
							r2_conn.send("NO NEED")
							r2_conn.recv(1024)
							print "FILE ALREADY UPDATED"
							print filename, size, time.ctime(mtime), hash_value
						else:
							r2_conn.send("SEND")
							r2_conn.recv(1024)
							f = open(s1_dir + '/' + filename,'wb')
							while True:
								r2_conn.send("OK")
								data = r2_conn.recv(1024)
								if data == "Over":
									break
								else:
									f.write(data)
							f.close()
							hash_value2 = hash_file(s1_dir + '/' + filename)
							if hash_value == hash_value2:
								print "hash checked"
								print filename, size, time.ctime(mtime),hash_value
							else:
								print "hash failed"
								print filename, size, time.ctime(mtime),hash_value



					else:
						r2_conn.send("SEND")
						r2_conn.recv(1024)
						f = open(s1_dir + '/' + filename,'wb')
						while True:
							r2_conn.send("OK")
							data = r2_conn.recv(1024)
							if data == "Over":
								break
							else:
								f.write(data)
						f.close()
						os.chmod(s1_dir + '/' + filename,mode & 0777)
						hash_value2 = hash_file(s1_dir + '/' + filename)
						if hash_value == hash_value2:
							print "hash checked"
							print filename, size, time.ctime(mtime), hash_value
						else:
							print "hash failed"
							print filename, size, time.ctime(mtime),hash_value


			elif commands[1] == "UDP":
				if length == 2:
					print "invalid command"
					continue
				filename = commands[2]
				r2_conn.send("OK")
				mess = r2_conn.recv(1024)
				if mess == "FALSE":
					print "improper filename"
				else:
					r2_conn.send("OK")
					value = r2_conn.recv(1024)
					values = value.split(";")
					hash_value = values[0]
					size = int(values[1])
					mtime = float(values[2])
					mode = int(values[3])

					if os.path.exists(s1_dir + '/' + filename):
						os.chmod(s1_dir + '/' + filename, mode & 0777)
						hash_value2 = hash_file(s1_dir + '/' + filename)
						if hash_value == hash_value2:
							r2_conn.send("NO NEED")
							r2_conn.recv(1024)
							print "FILE ALREADY UPDATED"
							print filename, size, time.ctime(mtime), hash_value
						else:
							r2_conn.send("SEND")
							r2_conn.recv(1024)

							sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
							sock1.bind((host,60002))
							f = open(s1_dir + '/' + filename,'wb')
							while 1:
								data , clientAddress = sock1.recvfrom(1024)
								# sock1.sendto("OK",clientAddress)
								if data == "Over":
									break
								else:
									f.write(data)
							f.close()
							sock1.close()


							hash_value2 = hash_file(s1_dir + '/' + filename)
							if hash_value == hash_value2:
								print "hash checked"
								print filename, size, time.ctime(mtime),hash_value
							else:
								print "hash failed"
								print filename, size, time.ctime(mtime),hash_value



					else:
						r2_conn.send("SEND")
						r2_conn.recv(1024)
						sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						sock1.bind((host,60002))
						f = open(s1_dir + '/' + filename,'wb')
						while 1:
							data , clientAddress = sock1.recvfrom(1024)
							# sock1.sendto("OK",clientAddress)
							if data == "Over":
								break
							else:
								f.write(data)
						f.close()
						sock1.close()
						os.chmod(s1_dir + '/' + filename,mode & 0777)
						hash_value2 = hash_file(s1_dir + '/' + filename)
						if hash_value == hash_value2:
							print "hash checked"
							print filename, size, time.ctime(mtime), hash_value
						else:
							print "hash failed"
							print filename, size, time.ctime(mtime),hash_value

			else:
				print "invalid command"

		else:
			print "invalid command"

	except TimedOutExc:
		signal.alarm(0)
		flag_timebreak = 1
		r2_conn.send("NO INPUT")
		r2_conn.recv(1024)

	message = s2.recv(1024)
	if message == "NO INPUT":
		s2.send("OK")
	else:
		s2.send("ok")
		f = open(s1_dir+"/"+"file1.log","a+")
		f.write(message+"   "+time.ctime(time.time())+"\n")
		f.close()
		messages = message.split(" ")
		length2 = len(messages)
		if messages[0] == "close":
			break
		elif messages[0] == "index":
			if length2 == 1:
				continue
			if messages[1] == "longlist" or messages[1] == "shortlist" or messages[1] == "regex":
				p = sub.Popen(['ls'],stdout=sub.PIPE,stderr=sub.PIPE)
				output, errors = p.communicate()
				output = output + "Over"
				lines = output.split("\n")
				count = 0
				for line in lines:
					if line !="Over" and line!="s1.py" and line!="file1.log":
						st = os.stat(s1_dir+'/'+line)
						line = line + ';' + str(st.st_size) + ';' + str(st.st_mode) + ';' + str(st.st_mtime)
						s2.recv(1024)
						s2.send(line)
						if messages[1] == "shortlist" and length2<4:
							break
						elif messages[1] == "regex" and length2<3:
							break
					elif line == "Over":
						s2.recv(1024)
						s2.send(line)

		elif messages[0] == "hash":
			if length2 == 1:
				continue
			if messages[1] == "verify":
				if length2 == 2:
					continue
				s2.recv(1024)
				filename = messages[2]
				if os.path.exists(s1_dir+'/'+filename):
					st=os.stat(s1_dir+'/'+filename)
					hash_value = hash_file(s1_dir+'/'+filename)
					s2.send(hash_value+';'+str(st.st_mtime))
				else:
					s2.send("FALSE")

			if messages[1] == "checkall":
				send_hash("")
				s2.recv(1024)
				s2.send("Over")

		elif messages[0] == "download":
			if length2 == 1:
				continue
			if messages[1] == "TCP":
				if length2 == 2:
					continue
				filename = messages[2]
				if os.path.exists(s1_dir + '/'+ filename):
					s2.recv(1024)
					s2.send("OK")

					s2.recv(1024)
					hash_value = hash_file(s1_dir + '/'+ filename)
					st = os.stat(s1_dir + '/'+ filename)
					text = hash_value + ';'+ str(st.st_size) + ';'+ str(st.st_mtime) + ';'+ str(st.st_mode)
					s2.send(text)

					mess = s2.recv(1024)
					s2.send("OK")
					if mess == "SEND":
						f = open(s1_dir + '/'+ filename,'rb')
						l = f.read(1024)
						while(l):
							s2.recv(1024)
							s2.send(l)
							l = f.read(1024)
						s2.recv(1024)
						s2.send("Over")

				else:
					s2.recv(1024)
					s2.send("FALSE")

			if messages[1] == "UDP":
				if length2 == 2:
					continue
				filename = messages[2]
				if os.path.exists(s1_dir + '/' + filename):
					s2.recv(1024)
					s2.send("OK")

					s2.recv(1024)
					hash_value = hash_file(s1_dir + '/'+ filename)
					st = os.stat(s1_dir + '/'+ filename)
					text = hash_value + ';' + str(st.st_size) + ';' + str(st.st_mtime) + ';' + str(st.st_mode)
					s2.send(text)

					mess = s2.recv(1024)
					s2.send("OK")
					if mess == "SEND":
						clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						f = open(s1_dir+'/'+filename,'rb')
						l = f.read(1024)
						while(l):
							clientSocket.sendto(l,(host,50002))
							# r = clientSocket.recvfrom(1024)
							l = f.read(1024)
						clientSocket.sendto("Over",(host,50002))
						# clientSocket.recvfrom(1024)
						clientSocket.close()


				else:
					s2.recv(1024)
					s2.send("FALSE")



