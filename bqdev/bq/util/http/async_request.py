from threading import Thread, enumerate
from urllib import urlopen
from time import time



 
class URLThread(Thread):
    def __init__(self, **kw):
        super(URLThread, self).__init__()
        self.callback = kw.pop('callback', None)
        self.request_params  = kw
        self.setDaemon(True)
 
    def run(self):
        response_headers, content  = http_client.request (**self.request_params)

        if response_headers.status != 200:
            return
        if self.callback is not None:
            self.callback (content, response_headers)



def request(uri, method="GET", body=None, headers={}, callback=None, client= None, **kw):
    """ Make an aynchrounous request adding user credential if available"""
    prepare_credentials(headers)
    return URLThread (uri=uri,
                      method=method,
                      body=body,
                      headers=headers,
                      callback=callback,**kw)


def xmlrequest(url, op = 'GET', body='', headers={}, **kw):
    '''usage: headers, response = xmlrequest("http://aaa.com")
              headers, response = xmlrequest("http://aaa.com", "POST", "<xml>...")
    '''
    prepare_credentials(headers)
    headers['content-type'] = 'text/xml'
    return URLThread (uri=uri,
                      method=method,
                      body=body,
                      headers=headers,
                      callback=callback,**kw)

