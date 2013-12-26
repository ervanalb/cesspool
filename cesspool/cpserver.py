#!/usr/bin/python

from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import SharedDataMiddleware
import os
from werkzeug.wrappers import Request as RequestBase
from werkzeug.contrib.wrappers import JSONRequestMixin
from werkzeug.exceptions import BadRequest

from pool import Pool
try: from simplejson import dumps
except ImportError: from json import dumps

class Request(RequestBase, JSONRequestMixin):
	pass

class CPServer(object):
	def __init__(self):
		self.pool=Pool()

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

if __name__=='__main__':
	from twisted.web.server import Site
	from twisted.web.wsgi import WSGIResource
	from twisted.internet import reactor
	from twisted.web.static import File

	app=CPServer()

	local_root=os.path.join(os.path.dirname(__file__), '../')

	root = File(os.path.join(local_root,'www'))
	root.putChild("cmd", WSGIResource(reactor, reactor.getThreadPool(), app))
	root.putChild("downloads", File(os.path.join(local_root,'downloads')))

	reactor.listenTCP(9500, Site(root))
	reactor.run()

