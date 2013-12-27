import os
import os.path
import shutil

class Download:
	def __init__(self,parent,pool,uid,args,reinstantiate):
		self.uid=uid
		self.parent=parent
		self.pool=pool

		self.dlpath=os.path.join(self.pool.params['directory'],str(self.uid))
		self.webpath=os.path.join(self.pool.params['web_path'],str(self.uid))

		if reinstantiate:
			self.reinstantiate(args)
		else:
			self.add(**args)

	def intrinsics(self):
		return {'type':self.parent.TYPE_STRING,'uid':self.uid}

	def _describe(self):
		return dict(self.intrinsics().items()+self.describe().items())

	def _get_state(self):
		return dict(self.intrinsics().items()+self.get_state().items())

	def _rm(self):
		self.rm()

	def mkdl(self):
		if os.path.isdir(self.dlpath):
			shutil.rmtree(self.dlpath)
		os.makedirs(self.dlpath)

	def rmdl(self):
		shutil.rmtree(self.dlpath)
		self.pool.removeMeAsync(self.uid)


class Downloader:
	TYPE_STRING='download'
	CHILD=Download

	def instantiate(self,pool,uid,args):
		return self.CHILD(self,pool,uid,args,False)

	def reinstantiate(self,pool,uid,args):
		return self.CHILD(self,pool,uid,args,True)

