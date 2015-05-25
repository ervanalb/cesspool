from shmooze.modules import JSONParentPoller
import shmooze.lib.packet as packet
import shmooze.settings as settings

import libtorrent as lt
import Queue
import base64
import os
import shutil
import threading
import time
import uuid

class TorrentDownloader(JSONParentPoller, threading.Thread):
    def __init__(self):
        super(TorrentDownloader, self).__init__()
        self.daemon = True
        self.init_event = threading.Event()

        self.state = "added"
        self.stopped = False

        self.magnet_url = None
        self.fast_resume = None
        self.error=None
        self.running=False
        self.torrent_status=None
        self.progress=0.
        self.t_name=None
        self.started=time.time()
        self.finished=None
        self.uploaded=0
        self.downloaded=0
        self.handle = None

        self.prefix = str(uuid.uuid4())
        self.dlpath=os.path.join(settings.download_path, self.prefix)
        self.webpath=os.path.join(settings.web_path, self.prefix)
        print "Path:", self.dlpath

        self.safe_update()

    def safe_update(self):
        if not self.stopped:
            self.set_parameters(self.serialize())


    def set_error(self, err):
        self.state = "error"
        self.error = str(err)
        self.safe_update()

    def startup(self):
        self.running = True
        self.state = "running"
        self.session = lt.session()

        if self.fast_resume is not None:
            fast_resume=base64.b64decode(fast_resume)
            try:
                self.add_torrent(fast_resume)
            except RuntimeError as e:
                self.set_error(e)
                return
        else:
            try:
                self.add_torrent()
            except RuntimeError as e:
                self.set_error(e)
                return

    def shutdown(self):
        print "Shutting down"
        self.running = False
        self.stopped = True
        self.state = "stopped"
        self.remove_torrent()

        self.rm()

    def add_torrent(self, fast_resume_data=None):
        params={'save_path': self.dlpath}
        if fast_resume_data is not None:
            params['resume_data']=fast_resume_data

        self.handle=lt.add_magnet_uri(self.session,str(self.magnet_url),params)

    def remove_torrent(self):
        if self.handle is not None:
            try:
                self.session.remove_torrent(self.handle)
            except RuntimeError as e:
                self.state='error'
                self.error=str(e)
        self.delete_files()


    def delete_files(self):
        try:
            shutil.rmtree(self.dlpath)
        except OSError:
            # If we can't delete the files, nothing else to do
            print "Unable to delete folder:", self.dlpath

    def make_path(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.makedirs(path)

    def run(self):
        torrent_states=['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
        self.init_event.wait()
        self.startup()
        while self.running:
            if self.handle is not None:
                if self.handle.has_metadata():
                    self.t_name=self.handle.get_torrent_info().name()
                stat=self.handle.status()
                self.torrent_status=torrent_states[stat.state]
                self.progress=stat.progress
                self.uploaded=stat.total_payload_upload
                self.downloaded=stat.total_payload_download
                if self.torrent_status=='seeding' and self.state=='running':
                    if self.finished is None:
                        self.finished=time.time()
                    self.state='complete'
            self.safe_update()
            time.sleep(1)

        self.shutdown()

    def cmd_init(self, magnet_url, fast_resume=None):
        self.state = "initialized"
        self.magnet_url = magnet_url
        self.fast_resume = fast_resume

        self.safe_update()
        self.init_event.set()
        
    def cmd_rm(self):
        self.running = False

    def cmd_play(self):
        #TODO
        pass

    def cmd_suspend(self):
        #TODO
        pass

    def serialize(self):
        return {
            "magnet_url":self.magnet_url,
            "state":self.state,
            "error":self.error,
            "torrent_status":self.torrent_status,
            "progress":self.progress,
            "name":self.t_name,
            "started":self.started,
            "finished":self.finished,
            "upload":self.uploaded,
            "download":self.downloaded,
            "disk_path": self.dlpath,
            "web_path": self.webpath,
        }

    commands = {
        'init':cmd_init,
        'rm':cmd_rm,
        'play':cmd_play,
        'suspend':cmd_suspend,
    }


mod = TorrentDownloader()
mod.start()

while mod.isAlive():
    try:
        mod.handle_one_command()
    except socket.error:
        break

print "Graceful termination!"
