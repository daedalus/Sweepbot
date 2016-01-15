#!/usr/bin/env python
from jsonrpc import ServiceProxy
import os,sys,time
from optparse import OptionParser

rpcuser=""
rpcpassword=""
savings=''
enabled = True

def getlastbalance():
	f = open('/tmp/Sweepbot.tmp','r')
	try:
		balance = float(f.read())
	except:
		balance = 0.0
	f.close
	return balance
 
def putbalance(balance):
	f = open('/tmp/Sweepbot.tmp','w')
	f.write(str(balance))
	f.close

access = ServiceProxy("http://{0!s}:{1!s}@127.0.0.1:8332".format(rpcuser, rpcpassword))

def proccess(force):
	access.settxfee(0)
	balance = float(access.getbalance())
	lastbalance = getlastbalance()

	if ((balance > lastbalance) or force):
		access.sendtoaddress(savings,balance)
		putbalance(balance)
	print "balance: {0!s},lastbalance: {1!s} ".format(balance, lastbalance)

def main():
      	parser = OptionParser()

        parser.add_option("--force", dest="force",
                help="force send")
	
	(options, args) = parser.parse_args()	
	
	force = bool(options.force)
	
	if force:
		t = 60
	else:
		t = 5

	for x in xrange(60/t):
		proccess(force)
		time.sleep(t)

if enabled:
	main()
