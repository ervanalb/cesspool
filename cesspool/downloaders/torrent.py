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

messages = Queue.Queue()

class TorrentDownloader(JSONParentPoller):
    def __init__(self):
        self.thread_stopped = False 
        self.state = None
        self.running = True
        self.update_lock = threading.Lock() # TODO I don't think this needs to exist
        super(TorrentDownloader, self).__init__()

    # TODO This shouldn't exist. (??? - copied from youtube.py)
    def safe_update(self):
        with self.update_lock:
            self.set_parameters(self.serialize())

    def cmd_init(self, magnet_url, fast_resume=None):
        self.state = "added"
        self.magnet_url = magnet_url
        self.fast_resume = fast_resume
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

        self.safe_update()
        messages.put("init")

    def startup(self):
        self.running = True
        self.state = "running"
        self.session = lt.session()

        if self.fast_resume is not None:
            fast_resume=base64.b64decode(fast_resume)
            try:
                self.add_torrent(fast_resume)
            except RuntimeError as e:
                self.state='error'
                self.error=str(e)
                return
        else:
            try:
                self.add_torrent()
            except RuntimeError as e:
                self.state='error'
                self.error=str(e)
                return

        self.run()

    def shutdown(self):
        self.running = False
        self.thread_stopped = True 
        self.state = "stopped"
        self.remove_torrent()

        with self.update_lock:
            self.rm()

    def add_torrent(self, fast_resume_data=None):
        params={'save_path': self.dlpath}
        if fast_resume_data is not None:
            params['resume_data']=fast_resume_data

        self.handle=lt.add_magnet_uri(self.session,str(self.magnet_url),params)

    def remove_torrent(self):
        self.session.remove_torrent(self.handle)

    def make_path(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        os.makedirs(path)

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
            if self.torrent_status=='seeding' and self.state=='running':
                if self.finished is None:
                    self.finished=time.time()
                self.state='complete'
            self.safe_update()
            time.sleep(1)
        
        self.shutdown()
        
    def cmd_rm(self):
        messages.put("rm")

    def cmd_play(self):
        #TODO
        pass

    def cmd_suspend(self):
        """
        fast_resume=None
        if self.state!='error':
            self.handle.save_resume_data()
            while True:
                if self.session.wait_for_alert(10) is None:
                    break
                a=self.session.pop_alert()
                if a is not None:
                    s=a.what()
                    if s=='save resume data complete':
                        fast_resume=a.resume_data
                    break
        if fast_resume is not None:
            fast_resume=base64.b64encode(lt.bencode(fast_resume))
        #TODO
        return {'url':self.url,'started':self.started,'finished':self.finished,'fast_resume':fast_resume}
        """
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

def serve_forever():
    while not mod.thread_stopped:
        try:
            mod.handle_one_command()
        except socket.error:
            break

t=threading.Thread(target=serve_forever)
t.daemon=True
t.start()

while True:
    msg = messages.get(block=True)
    messages.task_done()
    if msg == "init":
        mod.startup()
    elif msg == "rm":
        mod.shutdown()
    print "Done processing message"
    
mod.close()

