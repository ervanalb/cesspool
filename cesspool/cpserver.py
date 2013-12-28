#!/usr/bin/python

from werkzeug.wrappers import Response
from werkzeug.wrappers import Request as RequestBase
from werkzeug.contrib.wrappers import JSONRequestMixin
from werkzeug.exceptions import BadRequest
import os

from pool import Pool
try: from simplejson import dumps
except ImportError: from json import dumps
import sys

class Request(RequestBase, JSONRequestMixin):
	pass

class CPServer(object):
	def __init__(self,statefile=None,load=False):
		self.pool=Pool()
		self.statefile=statefile
		if self.statefile and load:
			self.pool.load_state(self.statefile)

	def dispatch_request(self,request):
		#if not request.json:
		#	return BadRequest('No JSON found!')
		result=self.pool.doMultipleCommandsAsync(request.json)
		return Response(dumps(result),content_type='text/json')

	def wsgi_app(self, environ, start_response):
		request = Request(environ)
		response = self.dispatch_request(request)
		return response(environ, start_response)

	def __call__(self, environ, start_response):
		return self.wsgi_app(environ,start_response)

	def close(self):
		if self.statefile:
			self.pool.save_state('state.json')

if __name__=='__main__':
	from twisted.web.server import Site
	from twisted.web.wsgi import WSGIResource
	from twisted.internet import reactor
	from twisted.web.static import File

	if len(sys.argv)>1:
		load=(sys.argv[1]!='noload')
	else:
		load='state.json'

	app=CPServer('state.json',load)

	local_root=os.path.join(os.path.dirname(__file__), '../')

	root = File(os.path.join(local_root,'www'))
	root.putChild("cmd", WSGIResource(reactor, reactor.getThreadPool(), app))
	root.putChild("downloads", File(os.path.join(local_root,'downloads')))

	reactor.listenTCP(9500, Site(root))
	reactor.run()
	app.close()

