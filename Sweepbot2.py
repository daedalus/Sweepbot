#!/usr/bin/env python
from jsonrpc import ServiceProxy
import os,sys,time,random
from optparse import OptionParser
from bitcoin import *
import urllib2
import relay
import threading

rpcuser=""
rpcpassword=""
enabled = True
BTC = 100000000
fee = 10000
savings=''
myaddresses = [savings,'','']
sprivkey = ''

threads = list()
nodes = ""
addnodes = [("127.0.0.1",8333),("respends.thinlink.com",8333),("68.168.105.168",8333)]

txcache = {}
pkcache = {}

access = ServiceProxy("http://%s:%s@127.0.0.1:8332" % (rpcuser,rpcpassword))

def make_request(*args):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0'+str(random.randrange(1000000)))]
    try:
        return opener.open(*args).read().strip()
    except Exception,e:
        try: p = e.read().strip()
        except: p = e
        raise Exception(p)

def sendblockchain(priv,address,amount,fee):
	url =  "https://blockchain.info/merchant/%s/payment?to=%s&amount=%s&fee=%s" % (priv,address,amount,fee)

	#print url

	return make_request(url)

def findoutputs(txraw,address):
        tx = deserialize(txraw)
        outputs = []
        i = 0
        for out in tx['outs']:
                if address == script_to_address(out['script']):
                        output = {'output': txhash(txraw) +  ':' + str(i), 'value': out['value']}
                        outputs.append(output)
                i+=1
        return outputs

def newthread(target,args):
	t = threading.Thread(target=target,args=args)
        threads.append(t)
        t.start()

def maketx(txfrom,src,privkey,dest):
	ins = findoutputs(txfrom,src)	

	if ins:
		amount=0
	
		for input in ins:
			amount += input['value']

		global fee
		amount -= fee
	
		outs = [{'address': dest, 'value': amount}]

		tx = mktx(ins,outs)
		tx = signall(tx,privkey)

	return tx

def localsend(access,tx):
	try:
		ret = access.sendrawtransaction(tx)	
	except:
		ret = ""
	return ret

def push(tx):
	try:	
		ret = pushtx(tx)
	except:
		pass
	try:
		ret = blockr_pushtx(tx)
	except:
		pass
	try:
		ret = helloblock_pushtx(tx)
	except:
		pass
	try:
		ret = eligius_pushtx(tx)
	except:
		pass

	return ret


def getinfonodes(nodes):
	tmpnodes = []
	for node in nodes:
                addrport = node['addr'].split(':')
                
                if len(addrport) == 1:
                        port = 8333
                else:
                        port = int(addrport[1])
                addr = str(addrport[0])
                tmpnodes.append((addr,port))

	return tmpnodes

def broadcast(tx,nodes):
	for node in nodes:
		relay.relayTx(tx,node)
	#return ret

def puttxcache(txid):
	#print "putcache",txid
	if gettxcache(txid) == "":
		try:
			rawtx = access.getrawtransaction(txid)
        		txcache[txid] = rawtx
		except:
			return

def gettxcache(txid):
	try:
		ret = txcache[txid]
	except:
		ret = ""
	#print "getcache",txid,ret
	return ret

def putprivkeycache(address):
	if getprivkeycache(address) == "":
		try:
			pkcache[address] = access.dumpprivkey(address) 
		except:
			return

def getprivkeycache(address):
	try:
		ret =  pkcache[address]
	except:
		ret = ""
	return ret

def process():
	maxconf = 2
	txs = access.listtransactions()
	
	for tx in txs:
		src = tx['address']
		if (tx['category'] == "receive") and ((src not in myaddresses)) and (tx['confirmations'] <= maxconf):
			amount=int(tx['amount']*BTC)

			global fee
			print amount,fee
		
			while not (amount - fee > 0) and (amount > fee):
				fee = fee / 10
			
			if (amount >= fee):
				nodes = addnodes  + getinfonodes(access.getpeerinfo()) 

				print nodes
				#sys.exit(0)

				putprivkeycache(src)
				privkey = getprivkeycache(src)
				if privkey:
					puttxcache(tx['txid'])
					rawtx = gettxcache(tx['txid'])
					if rawtx:
						tx = maketx(rawtx,src,privkey,savings)
						#print tx
						newthread(target=broadcast,args=(tx,nodes,))
						newthread(target=localsend,args=(access,tx,))
						#newthread(target=pushtx,args=(tx,))

def main():
        parser = OptionParser()

        parser.add_option("--force", dest="force",
                help="force send")

        (options, args) = parser.parse_args()

        force = bool(options.force)

        for x in xrange(120):
                process()
                time.sleep(0.5)

if enabled:
	main()
