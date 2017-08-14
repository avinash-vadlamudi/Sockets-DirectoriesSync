import os
import socket
import re
import time
import datetime
import hashlib

mypath = raw_input()
print mypath

def hash_file(file_name):
	hash_md5 = hashlib.md5()
		   # open file for reading in binary mode and reading chunks of 4 bytes
	with open(file_name,"rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)

	return hash_md5.hexdigest()

def find_updatetime(file_name):
	print file_name
	print "last modified time: %s" % time.ctime(os.path.getmtime(file_name))
#	print "last modified time: %s" % time.ctime(os.stat(file_name).st_mtime)
	return

def find_filename(dirpath2):
	for [dirpath2,dirname,filenames] in os.walk(dirpath2):
		break
	print filenames
	for file in filenames:
		find_updatetime(dirpath2+'/'+file)
	if dirname==[]:
		return
	else:
		print dirname
		for dirn in dirname:
			temp=dirpath2+'/'+dirn
			print '----'+temp
			find_filename(temp)
	return
print datetime.datetime.now()

find_filename(mypath)


