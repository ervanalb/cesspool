class Download:
	def __init__(self,parent,pool,uid,args):
		self.uid=uid
		self.parent=parent
		self.pool=pool
		self.add(**args)

	def _describe(self):
		return dict([('type',self.parent.TYPE_STRING),('uid',self.uid)]+self.describe().items())

class Downloader:
	TYPE_STRING='download'
	CHILD=Download

	def instantiate(self,pool,uid,args):
		return self.CHILD(self,pool,uid,args)

