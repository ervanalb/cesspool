import threading
import time

from downloadmanager import DownloadManager
from downloaders.torrent import TorrentDownloader


class Pool(object):
	PARAMS={'directory':'../downloads','web_path':'downloads'}
	DOWNLOADERS=[TorrentDownloader()]

	def __init__(self):
		self.dm=DownloadManager(self.DOWNLOADERS)
		self.pool=[]
		self.lock=threading.Semaphore()

	def save_state(self,filename):
		with open(filename,'w') as outfile:
			json.dump([dl.get_state() for dl in pool],outfile)

	def load_state(self,filename):
		with open(filename,'r') as infile:
			pool_state=json.load(infile)
			pool=[self.dm.restore_state(s) for s in pool_state]

	# pool command
	def get_pool(self):
		return [dl._describe() for dl in self.pool]

	# add command
	def add(self,type,args={}):
		dl_inst=self.dm.instantiate(self,type,args)
		self.pool.append(dl_inst)
		return {'uid':dl_inst.uid}

	def tell_download(self,uid,cmd,args={}):
		return self.dm.tell(self.find_dl(uid),cmd,args)

	def available_downloaders(self):
		return [dlr.TYPE_STRING for dlr in dm.downloaders]

	def describe_download(self,uid):
                return self.find_dl(uid)._describe()

	def rm(self,uid):
                return self.find_dl(uid).rm()

	def find_dl(self,uid):
		uid=int(uid)
		d=dict([(dl.uid,dl) for dl in self.pool])
		if uid not in d:
			raise Exception("Download identifier does not exist")
		return d[uid]

	# Runs a set of commands. Pool is guarenteed to not change during them.
	def doMultipleCommandsAsync(self,commands):
		return self.sync(lambda:[self.doCommand(cmd) for cmd in commands])

	# Acquires this object's lock and executes the given cmd
	def sync(self,cmd):
		try:
			self.lock.acquire()
			result=cmd()
		except Exception:
			self.lock.release()
			raise
		self.lock.release()
		return result

	# Removes a download asynchronously
	def removeMeAsync(self,uid):
		self.sync(lambda:self.removeMe(uid))

	def removeMe(self,uid):
		self.pool=[obj for obj in self.pool if obj.uid != uid]

	# Parse and run a command
	def doCommand(self,line):
		if not isinstance(line,dict):
			return errorPacket('Command not a dict.')

		try:
			cmd=line['cmd'] # Fails if no cmd given
		except KeyError:
			return errorPacket('No command given.')

		try:
			args=line['args']
		except KeyError:
			args={}

		if not isinstance(args,dict):
			return errorPacket('Argument list not a dict.')

		try:
			f=self.commands[cmd]
		except KeyError:	
			return errorPacket('Bad command.')

		try:
			result=f(self,**args)
		except Exception as e:
			raise
			return errorPacket(str(e))

		return goodPacket(result)

	commands={
		'rm':rm,
		'add':add,
		'pool':get_pool,
		'tell':tell_download,
		'describe':describe_download,
	}

# End class Pool

# Useful JSONification functions

def errorPacket(err):
	return {'success':False,'error':err}

def goodPacket(payload):
	if payload is not None:
		return {'success':True,'result':payload}
	return {'success':True}

