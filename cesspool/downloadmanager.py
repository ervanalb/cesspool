class DownloadManager:
	def __init__(self,downloaders=[]):
		self.downloaders=downloaders
		self.uid=0

	def get_uid(self):
		u=self.uid
		self.uid+=1
		return u

	def instantiate(self,pool,type,args):
		if 'pool' in args or 'uid' in args:
			raise Exception('arg list cannot contain pool or uid')
		uid=self.get_uid()
		return dict([(dlr.TYPE_STRING,dlr) for dlr in self.downloaders])[type].instantiate(pool,uid,args)
