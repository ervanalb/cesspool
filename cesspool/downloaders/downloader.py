import os
import os.path
import shutil

class Download:
	def __init__(self,parent,pool,uid,args):
		self.uid=uid
		self.parent=parent
		self.pool=pool
		self.add(**args)

	def _describe(self):
		return dict([('type',self.parent.TYPE_STRING),('uid',self.uid)]+self.describe().items())

	def _rm(self):
		self.rm()

	def mkdl(self):
		self.dlpath=os.path.join(self.pool.PARAMS['directory'],str(self.uid))
		self.webpath=os.path.join(self.pool.PARAMS['web_path'],str(self.uid))
		if os.path.isdir(self.dlpath):
			shutil.rmtree(self.dlpath)
		os.mkdir(self.dlpath)

	def rmdl(self):
		shutil.rmtree(self.dlpath)
		self.pool.removeMeAsync(self.uid)


class Downloader:
	TYPE_STRING='download'
	CHILD=Download

	def instantiate(self,pool,uid,args):
		return self.CHILD(self,pool,uid,args)

