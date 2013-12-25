# A simple bot framework

import requests
import json

class CPBot(object):
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.module_capabilities = None
        self.static_capabilities = None
        self.background_capabilities = None

    def doCommands(self, cmd_list):
        json_data = json.dumps(cmd_list)
        headers = {"Content-type": "text/json"}
        resp = requests.post(self.endpoint, data=json_data, headers=headers)
        return resp.json()

    def whoami(self):
        resp = requests.post(self.endpoint, data='[]', headers={"Content-type": "text/json"})
        return resp.headers['Client-ip']

    def doCommand(self,cmd):
        return self.doCommands([cmd])[0]

    def assert_success(self,result):
        if isinstance(result,dict):
            if result['success']:
                if 'result' in result:
                    return result['result']
                return None
            raise Exception(result['error'])
        
        if isinstance(result,list):
            for r in result:
                if not r['success']:
                    raise Exception(r['error'])
            return [r['result'] for r in result if 'result' in r]
        raise Exception('Bad response type from server')

