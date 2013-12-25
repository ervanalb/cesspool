#!/usr/bin/env python
import hashlib
import hmac
import json
import sys
import os

from pool import Pool

from webserver import Webserver,HTTPException

HOST_NAME = ''
PORT_NUMBER = 9500

class CPServer(Webserver):
	def __init__(self,debug=False):
		self.debug=debug

		self.pool = Pool()

		Webserver.__init__(self,HOST_NAME, PORT_NUMBER)

	def get(self,form_data,path):
		if self.debug:
			p=path.path
			if p=='/' or p=='':
				p='/index.html'
			try:
				fn=os.path.join(os.path.dirname(os.path.realpath(__file__)),'../www',p[1:])
				return open(fn)
			except Exception:
				raise HTTPException(404,'File not found')
		else:
			raise NotImplementedError

	def json_transaction(self,json_data):
        	return self.pool.doMultipleCommandsAsync(json_data)

if __name__ == '__main__':
	debug=('--debug' in sys.argv)
	cps=CPServer(debug)
	cps.run()
