from downloader import Downloader,Download

import libtorrent as lt
import threading
import time

class Torrent(Download,threading.Thread):
	def add(self,url):
		threading.Thread.__init__(self)
		self.daemon=True
		self.url=url
		self.status='added'
		self.error=None
		self.running=False
		self.torrent_status=None
		self.progress=0.
		self.t_name=None
		self.started=time.time()
		self.finished=None
		self.uploaded=0
		self.downloaded=0

		self.mkdl()

		try:
			self.parent.add_torrent(self)
			self.status='running'
			self.running=True
			self.start()
		except RuntimeError as e:
			self.status='error'
			self.error=str(e)

	def run(self):
		torrent_states=['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
		while self.running:
			if self.handle.has_metadata():
				self.t_name=self.handle.get_torrent_info().name()
			stat=self.handle.status()
			self.torrent_status=torrent_states[stat.state]
			self.progress=stat.progress
			self.uploaded=stat.total_payload_upload
			self.downloaded=stat.total_payload_download
			if self.torrent_status=='seeding' and self.finished is None:
				self.status='complete'
				self.finished=time.time()
			time.sleep(1)

		self.parent.remove_torrent(self)
		self.delete()

	def rm(self):
		if self.running:
			self.running=False
		else:
			self.delete()

	def delete(self):
		self.rmdl()

	def describe(self):
		return {
			"url":self.url,
			"status":self.status,
			"error":self.error,
			"torrent_status":self.torrent_status,
			"progress":self.progress,
			"name":self.t_name,
			"started":self.started,
			"finished":self.finished,
			"upload":self.uploaded,
			"download":self.downloaded,
		}

class TorrentDownloader(Downloader):
	TYPE_STRING='torrent'
	CHILD=Torrent

	def __init__(self):
		self.session=lt.session()

	def add_torrent(self,child):
		params={'save_path': child.dlpath}
		child.handle=lt.add_magnet_uri(self.session,str(child.url),params)

	def remove_torrent(self,child):
		self.session.remove_torrent(child.handle)
