import shmooze.pool
import shmooze.settings as settings
import shmooze.lib.service as service
from shmooze.modules import Module
import os
import signal

class TorrentDownloader(Module):
    TYPE_STRING='torrent'
    process = ['python','-m','cesspool.downloaders.torrent']

modules = [TorrentDownloader]

q= shmooze.pool.Pool(modules, settings.log_database)

def shutdown_handler(signum,frame):
    print
    print "Received signal, attempting graceful shutdown..."
    service.ioloop.add_callback_from_signal(q.shutdown)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

service.ioloop.start()
