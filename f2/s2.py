import socket
import os
import stat
import re
import time
import hashlib
import signal
import sys
import subprocess as sub

s2 = socket.socket()
s1 = socket.socket()

host = ""
port1 = 60000
port2 = 50000

try:
	s2.bind((host,port2))
except:
	port2 = 50005
	# print port2
	s2.bind((host,port2))
s2.listen(5)

try:
	s1.connect((host,port1))
except:
	port1 = 60005
	s1.connect((host,port1))

r1_conn, addr = s2.accept()
s2_dir = os.path.dirname(os.path.realpath(__file__))
s1_dir = os.path.dirname(os.path.realpath(__file__))

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
	         #openfile for reading in binary mode and reading chunks of 4 bytes
	with open(filename,"rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)

	return hash_md5.hexdigest()

def send_hash(subdir):
	for [dirpath2,dirname,filenames] in os.walk(s2_dir+subdir):
		break
	for file in filenames:
		if file == "s2.py" or file == "file2.log":
			continue
		s1.recv(1024)
		hash_value = hash_file(s2_dir + subdir + "/"+ file)
		st = os.stat(s2_dir + subdir + "/"+ file)
		text = subdir + "/" +file + ';' + hash_value + ';' + str(st.st_mtime) 
		s1.send(text)
	for dirn in dirname:
		send_hash(subdir + "/" + dirn)
	return

def download_file(message):
	messages = message.split(" ")
	path = s2_dir + messages[1]
	path2 = s1_dir + messages[1]
	s1.send("1 "+path2)
	value = s1.recv(1024)
	values = value.split(";")
	hash1 = values[0]
	mode = int(values[1])
	if os.path.exists(path):
		hash2 = hash_file(path)
		os.chmod(path, mode & 0777)
		if hash1 == hash2:
			s1.send("No Need")
		else:
			s1.send("send")
			flag = 0
			val = s1.recv(1024)
			if val == "True":
				if os.access(path,os.W_OK):
					s1.send("True")
				else:
					s1.send("False")
					flag = 1
			else:
				s1.send("False")
				flag = 1

			if flag == 1:
				return
			print messages[1] , "UPDATED"
			f = open(path,'wb')
			while True:
				data = s1.recv(1024)
				s1.send("OK")
				if data == "File Finished":
					break
				else:
					f.write(data)
			f.close()
	else:
		s1.send("send")
		flag = 0
		val = s1.recv(1024)
		if val == "True":
			s1.send("True")
			flag = 0
		else:
			s1.send("False")
			flag = 1

		if flag == 1:
			return
		print messages[1] , "UPDATED"
		f = open(path,'wb')
		while True:
			data = s1.recv(1024)
			s1.send("OK")
			if data == "File Finished":
				break
			else:
				f.write(data)
		f.close()
		os.chmod(path, mode & 0777)

	return


def update_sharedfolders_r():
	while True:
		message = s1.recv(1024)
		messages = message.split(" ")

		if message == "Over":
			s1.send("OK")
			break

		if messages[0]=="1":
			if messages[1] == "/s1.py" or messages[1] == "/file1.log":
				s1.send("yes")
				continue
			download_file(message)
		elif messages[0]=="2":
			path = s2_dir + messages[1]
			if not os.path.exists(path):
				os.makedirs(path)
				s1.send("no")
			else:
				s1.send("yes")

	return

def file_share(filename):
    f = open(filename,'rb')
    l = f.read(1024)
    while(l):
        r1_conn.send(l)
        r1_conn.recv(1024)
        l =f.read(1024)
    f.close()
    r1_conn.send("File Finished")
    r1_conn.recv(1024)
    return

def update_sharedfolders(subdir):
    for [dirpath2,dirname,filenames] in os.walk(s2_dir+subdir):
        break
    for file in filenames:
        r1_conn.send("1 "+subdir+"/"+file)
        reply = r1_conn.recv(1024)
        path2 = reply.split()
        if path2[0]=="1":
            hash_value = hash_file(path2[1])
            st = os.stat(path2[1])
            text = hash_value + ';' + str(st.st_mode)
            r1_conn.send(text)
            reply = r1_conn.recv(1024)
        if reply == "send":
        	flag = 0
        	if os.access(dirpath2+'/'+file,os.R_OK):
        		r1_conn.send("True")
        		val = r1_conn.recv(1024)
        		if val == "True":
        			flag =0
        		else:
        			flag = 1
        	else:
        		r1_conn.send("False")
        		flag = 1
        		r1_conn.recv(1024)
        	if flag == 1:
        		continue
        	file_share(dirpath2+'/'+file)

    for dirn in dirname:
        r1_conn.send("2 "+subdir+"/"+dirn)
        r1_conn.recv(1024)
        update_sharedfolders(subdir+"/"+dirn)
    return 


signal.signal(signal.SIGALRM, handler)
while True:
	if start_flag == 1:
		s1_dir = s1.recv(1024)
		s1.send("OK")

		r1_conn.send(s2_dir)
		r1_conn.recv(1024)

		# print s1_dir
		# print s2_dir

		update_sharedfolders_r()
		prev_checktime1 = time.time()
		f = open(s2_dir+"/"+"file2.log","a+")
		f.write("AUTO UPDATE"+"   "+time.ctime(time.time())+"\n")
		f.close()
		update_sharedfolders("")
		r1_conn.send("Over")
		r1_conn.recv(1024)
		prev_checktime2 = time.time()

		start_flag = 0
		continue

	if time.time() - prev_checktime1 >=600:
		update_sharedfolders_r()
		prev_checktime1 = time.time()
		f = open(s2_dir+"/"+"file2.log","a+")
		f.write("AUTO UPDATE"+"   "+time.ctime(time.time())+"\n")
		f.close()
		update_sharedfolders("")
		r1_conn.send("Over")
		r1_conn.recv(1024)
		prev_checktime2 = time.time()
		continue		

	message = s1.recv(1024)
	if message == "NO INPUT":
		s1.send("OK")
	else:
		s1.send("ok")
		f = open(s2_dir+"/"+"file2.log","a+")
		f.write(message+"   "+time.ctime(time.time())+"\n")
		f.close()
		messages = message.split()
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
				for line in lines:
					if line !="Over" and line!="s2.py" and line!="file2.log":
						st = os.stat(s2_dir+'/'+line)
						line = line + ';' + str(st.st_size) + ';' + str(st.st_mode) + ';' + str(st.st_mtime)
						s1.recv(1024)
						s1.send(line)
						if messages[1] == "shortlist" and length2<4:
							break
						elif messages[1] == "regex" and length2<3:
							break
					elif line=="Over":
						s1.recv(1024)
						s1.send(line)

		elif messages[0] == "hash":
			if length2 == 1:
				continue
			if messages[1] == "verify":
				if length2 == 2:
					continue
				s1.recv(1024)
				filename = messages[2]
				if os.path.exists(s2_dir+'/'+filename):
					st = os.stat(s2_dir+'/'+filename)
					hash_value = hash_file(s2_dir + '/'+filename)
					s1.send(hash_value+';'+str(st.st_mtime))
				else:
					s1.send("FALSE")

			if messages[1] == "checkall":
				send_hash("")
				s1.recv(1024)
				s1.send("Over")

		elif messages[0] == "download":
			if length2 == 1:
				continue
			if messages[1] == "TCP":
				if length2 == 2:
					continue
				filename = messages[2]
				if os.path.exists(s2_dir + '/'+ filename):
					s1.recv(1024)
					s1.send("OK")

					s1.recv(1024)
					hash_value = hash_file(s2_dir + '/'+ filename)
					st = os.stat(s2_dir + '/'+ filename)
					text = hash_value + ';'+ str(st.st_size) + ';'+ str(st.st_mtime) + ';'+ str(st.st_mode)
					s1.send(text)

					mess = s1.recv(1024)
					s1.send("OK")
					if mess == "SEND":
						f = open(s2_dir + '/'+ filename,'rb')
						l = f.read(1024)
						while(l):
							s1.recv(1024)
							s1.send(l)
							l = f.read(1024)
						s1.recv(1024)
						s1.send("Over")



				else:
					s1.recv(1024)
					s1.send("FALSE")

			if messages[1] == "UDP":
				if length2 == 2:
					continue
				filename = messages[2]
				if os.path.exists(s2_dir + '/' + filename):
					s1.recv(1024)
					s1.send("OK")

					s1.recv(1024)
					hash_value = hash_file(s2_dir + '/'+ filename)
					st = os.stat(s2_dir + '/'+ filename)
					text = hash_value + ';' + str(st.st_size) + ';' + str(st.st_mtime) + ';' + str(st.st_mode)
					s1.send(text)

					mess = s1.recv(1024)
					s1.send("OK")
					if mess == "SEND":

						clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						f = open(s2_dir+'/'+filename,'rb')
						l = f.read(1024)
						while(l):
							clientSocket.sendto(l,(host,60002))
							# r = clientSocket.recvfrom(1024)
							l = f.read(1024)
						clientSocket.sendto("Over",(host,60002))
						# clientSocket.recvfrom(1024)
						clientSocket.close()


				else:
					s1.recv(1024)
					s1.send("FALSE")




	signal.alarm(TIME)

	try:
		if flag_timebreak == 0:
			command = raw_input("Prompt> ")
		else:
			command = raw_input()
			flag_timebreak = 0
		signal.alarm(0)
		r1_conn.send(command)
		r1_conn.recv(1024)

		commands = command.split(" ")
		length = len(commands)
		if commands[0] == "close":
			break
		elif commands[0] == "index":
			if length == 1:
				print "invalid command"
				continue
			if commands[1] == "longlist" or commands[1] == "shortlist" or commands[1] == "regex":
				while True:
					r1_conn.send("OK")
					l = r1_conn.recv(1024)
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
							print "file-", ls[0], ",size-" , size , ",type-", file,",timestamp-", time.ctime(mtime)

						elif commands[1] == "shortlist":
							if length<4:
								print "invalid command"
								break
							time1 = float(commands[2])
							time2 = float(commands[3])
							if time1<=mtime and mtime<=time2:
								print "file-", ls[0], ",size-" , size , ",type-", file,",timestamp-", time.ctime(mtime)

						else:
							if length <3:
								print "invalid command"
								break
							string = commands[2]
							if re.search(string,ls[0]):
								print "file-", ls[0], ",size-" , size , ",type-", file,",timestamp-", time.ctime(mtime)

		elif commands[0] == "hash":
			if length == 1:
				print "invalid command"
				continue
			if commands[1] == "verify":
				if length == 2:
					print "invalid command"
					continue
				filename = commands[2]
				r1_conn.send("OK")
				value = r1_conn.recv(1024)
				values = value.split(";")
				hash_value = values[0]
				mtime = float(values[1])

				if value == "FALSE":
					print "improper filename"
				else:
					if os.path.exists(s2_dir+'/'+filename):
						hash_value2 = hash_file(s2_dir+'/'+filename)
						if hash_value == hash_value2:
							print "NOT UPDATED" , hash_value, "timestamp:", time.ctime(mtime)
						else:
							print "UPDATED", hash_value, "timestamp:", time.ctime(mtime)

					else:
						print "file doesn't exist in this folder", hash_value, time.ctime(mtime)

			elif commands[1] == "checkall":
				while True:
					r1_conn.send("Ok")
					value = r1_conn.recv(1024)
					if value == "Over":
						break
					else:
						values = value.split(";")
						hash_value = values[1]
						filename = values[0] 
						mtime = float(values[2])
						if os.path.exists(s2_dir+ filename):
							hash_value2 = hash_file(s2_dir+ filename)
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
				r1_conn.send("OK")
				mess = r1_conn.recv(1024)
				if mess == "FALSE":
					print "improper filename"
				else:
					r1_conn.send("OK")
					value = r1_conn.recv(1024)
					values = value.split(";")
					hash_value = values[0]
					size = int(values[1])
					mtime = float(values[2])
					mode = int(values[3])

					if os.path.exists(s2_dir + '/' + filename):
						os.chmod(s2_dir + '/' + filename, mode & 0777)
						hash_value2 = hash_file(s2_dir + '/' + filename)
						if hash_value == hash_value2:
							r1_conn.send("NO NEED")
							r1_conn.recv(1024)
							print "FILE ALREADY UPDATED"
							print filename, size, time.ctime(mtime), hash_value
						else:
							r1_conn.send("SEND")
							r1_conn.recv(1024)
							f = open(s2_dir + '/' + filename,'wb')
							while True:
								r1_conn.send("OK")
								data = r1_conn.recv(1024)
								if data == "Over":
									break
								else:
									f.write(data)
							f.close()
							hash_value2 = hash_file(s2_dir + '/' + filename)
							if hash_value == hash_value2:
								print "hash checked"
								print filename, size, time.ctime(mtime),hash_value
							else:
								print "hash failed"
								print filename, size, time.ctime(mtime),hash_value



					else:
						r1_conn.send("SEND")
						r1_conn.recv(1024)
						f = open(s2_dir + '/' + filename,'wb')
						while True:
							r1_conn.send("OK")
							data = r1_conn.recv(1024)
							if data == "Over":
								break
							else:
								f.write(data)
						f.close()
						os.chmod(s2_dir + '/' + filename,mode & 0777)
						hash_value2 = hash_file(s2_dir + '/' + filename)
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
				r1_conn.send("OK")
				mess = r1_conn.recv(1024)
				if mess == "FALSE":
					print "improper filename"
				else:
					r1_conn.send("OK")
					value = r1_conn.recv(1024)
					values = value.split(";")
					hash_value = values[0]
					size = int(values[1])
					mtime = float(values[2])
					mode = int(values[3])

					if os.path.exists(s2_dir + '/' + filename):
						os.chmod(s2_dir + '/' + filename, mode & 0777)
						hash_value2 = hash_file(s2_dir + '/' + filename)
						if hash_value == hash_value2:
							r1_conn.send("NO NEED")
							r1_conn.recv(1024)
							print "FILE ALREADY UPDATED"
							print filename, size, time.ctime(mtime), hash_value
						else:
							r1_conn.send("SEND")
							r1_conn.recv(1024)

							sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
							sock1.bind((host,50002))
							f = open(s2_dir + '/' + filename,'wb')
							while 1:
								data , clientAddress = sock1.recvfrom(1024)
								# sock1.sendto("OK",clientAddress)
								if data == "Over":
									break
								else:
									f.write(data)
							f.close()
							sock1.close()

							hash_value2 = hash_file(s2_dir + '/' + filename)
							if hash_value == hash_value2:
								print "hash checked"
								print filename, size, time.ctime(mtime),hash_value
							else:
								print "hash failed"
								print filename, size, time.ctime(mtime),hash_value



					else:
						r1_conn.send("SEND")
						r1_conn.recv(1024)
						sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
						sock1.bind((host,50002))
						f = open(s2_dir + '/' + filename,'wb')
						while 1:
							data , clientAddress = sock1.recvfrom(1024)
							# sock1.sendto("OK",clientAddress)
							if data == "Over":
								break
							else:
								f.write(data)
						f.close()
						sock1.close()
						os.chmod(s2_dir + '/' + filename,mode & 0777)
						hash_value2 = hash_file(s2_dir + '/' + filename)
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
		flag_timebreak = 1
		signal.alarm(0)
		r1_conn.send("NO INPUT")
		r1_conn.recv(1024)


	

