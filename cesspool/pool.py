import time
import os
import musicazoo.lib.cmdlog
import musicazoo.lib.database as database
import musicazoo.lib.service as service
import musicazoo.settings as settings

from downloaders.torrent import TorrentDownloader

import json

class Pool(service.JSONCommandProcessor, service.Service):
    port=settings.ports["pool"]
    download_path = settings.download_path # "../downloads"
    download_web_path = settings.download_web_path # "downloads"


class Pool(object):
    params={'directory':os.path.join(os.path.dirname(__file__),'../downloads'),'web_path':'downloads'}

    def __init__(self,downloaders,logfilename=None, debug=False):
        print "Queue started."
        # Create a UUID for this instance
        self.instance = str(uuid.uuid4())

        # Create lookup table of possible downloaders
        self.downloaders_available_dict = dict([(m.TYPE_STRING,m) for m in downloaders])

        # pool is the actual pool of downloaders
        self.pool = []
        # old_pool is used to diff the pool
        # Whenever pool is unlocked, it should equal pool
        self.old_pool = []

        # pool_lock is the sync object so that multiple clients don't edit the pool at the same time
        self.pool_lock=threading.Semaphore()

        # When debugging, uids are assigned sequentially
        self.debug = debug

        self.last_uid = -1
        self.log_namespace = "client-pool"
        if logfilename:
            self.logger = database.Database(log_table="pool_log")

        super(Pool, self).__init__()

#    def restore_state(self,state):
#        self.uid=state['uid']
#        dlrs=state['downloaders']
#        pool=state['pool']
#        d=dict([(dlr.TYPE_STRING,dlr) for dlr in self.downloaders])
#        for (name,dlr_state) in dlrs.iteritems():
#            if name in d:
#                d[name].restore_state(dlr_state)
#        self.pool=[self.reinstantiate(dl_state) for dl_state in pool]
#
#    def get_state(self):
#        dlrs=dict([(dlr.TYPE_STRING,dlr.get_state()) for dlr in self.downloaders])
#        pool=[dl._get_state() for dl in self.pool]
#        return {'uid':self.uid,'downloaders':dlrs,'pool':pool}
#
#    def save_state(self,filename):
#        with open(filename,'w') as outfile:
#            json.dump(self.get_state(),outfile)
#
#    def load_state(self,filename):
#        with open(filename,'r') as infile:
#            self.restore_state(json.load(infile))

    # pool command
    @service.coroutine
    def get_pool(self):
        raise service.Return( [dl._describe() for dl in self.pool])

    # add command
    @service.coroutine
    def add(self,type,args={}):
        dl_inst=self.instantiate(type,args)
        self.pool.append(dl_inst)
        raise service.Return({'uid':dl_inst.uid})

    @service.coroutine
    def tell_download(self,uid,cmd,args={}):
        result = yield self.dm.tell(self.find_dl(uid),cmd,args)
        raise service.Return(result)

    @service.coroutine
    def available_downloaders(self):
        raise service.Return([dlr.TYPE_STRING for dlr in self.downloaders])

    
    @service.coroutine
    def describe_download(self,uid):
        raise service.Return(serself.find_dl(uid)._describe())

    @service.coroutine
    def rm(self,uid):
        raise service.Return(self.find_dl(uid).rm())

    @service.coroutine
    def find_dl(self,uid):
        uid=int(uid)
        d=dict([(dl.uid,dl) for dl in self.pool])
        if uid not in d:
            raise Exception("Download identifier does not exist")
        raise service.Return(d[uid])

    def removeMe(self,uid):
        with (yield self.pool_lock.acquire()):
            self.pool=[obj for obj in self.pool if obj.uid != uid]

    def get_uid(self):
        if self.debug:
            u=self.uid
            self.uid+=1
        else:
            u = uuid.uuid4()
        return str(u)

    @service.coroutine
    def instantiate(self,type,args):
        if 'pool' in args or 'uid' in args:
            raise Exception('arg list cannot contain pool or uid')
        uid=self.get_uid()
        raise service.Return(self.downloaders_available_dict[type].instantiate(self,uid,args))

    @service.coroutine
    def reinstantiate(self,state):
        type=state['type']
        uid=state['uid']
        raise service.Return(self.downloaders_available_dict[type].reinstantiate(self,uid,state))

    commands={
        'rm':rm,
        'add':add,
        'pool':get_pool,
        'tell':tell_download,
        'describe':describe_download,
    }
