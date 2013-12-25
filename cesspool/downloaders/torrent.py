from downloader import Downloader,Download

class Torrent(Download):

	def add(self,url):
		self.url=url

	def describe(self):
		return {"url":self.url}

class TorrentDownloader(Downloader):
	TYPE_STRING='torrent'
	CHILD=Torrent

	def __init__(self):
		pass
