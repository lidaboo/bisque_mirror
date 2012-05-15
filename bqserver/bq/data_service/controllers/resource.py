###############################################################################
##  Bisquik                                                                  ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007 by the Regents of the University of California     ##
##                            All rights reserved                            ##
##                                                                           ##
## Redistribution and use in source and binary forms, with or without        ##
## modification, are permitted provided that the following conditions are    ##
## met:                                                                      ##
##                                                                           ##
##     1. Redistributions of source code must retain the above copyright     ##
##        notice, this list of conditions, and the following disclaimer.     ##
##                                                                           ##
##     2. Redistributions in binary form must reproduce the above copyright  ##
##        notice, this list of conditions, and the following disclaimer in   ##
##        the documentation and/or other materials provided with the         ##
##        distribution.                                                      ##
##                                                                           ##
##     3. All advertising materials mentioning features or use of this       ##
##        software must display the following acknowledgement: This product  ##
##        includes software developed by the Center for Bio-Image Informatics##
##        University of California at Santa Barbara, and its contributors.   ##
##                                                                           ##
##     4. Neither the name of the University nor the names of its            ##
##        contributors may be used to endorse or promote products derived    ##
##        from this software without specific prior written permission.      ##
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS "AS IS" AND ANY ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED ##
## WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE, ARE   ##
## DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR  ##
## ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL    ##
## DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS   ##
## OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)     ##
## HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,       ##
## STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN  ##
## ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE           ##
## POSSIBILITY OF SUCH DAMAGE.                                               ##
##                                                                           ##
###############################################################################
"""
SYNOPSIS
========


DESCRIPTION
===========

    RESTful resource with caching

"""
from __future__ import with_statement
import string
import os
import re
#import md5
import hashlib
import logging

from urlparse import urlparse
from datetime import datetime
from time import gmtime, strptime

import pylons
from pylons.controllers.util import abort

import tg
from tg import redirect, expose, request
from tg.util import Bunch
from tg.configuration import  config
#from tg.controllers import CUSTOM_CONTENT_TYPE

from bq.core import identity
from bq.core.service import ServiceController
from bq.exceptions import RequestError
from bq.util.paths import data_path

log = logging.getLogger("bq.data_service.resource")

CACHING  = bool(config.get ('bisque.data_service.caching', True))
SERVER_CACHE = bool(config.get('bisque.data_service.server_cache', True))
CACHEDIR = config.get ('bisque.data_service.server_cache', data_path('server_cache'))

URI = re.compile(r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")

def parse_uri(uri):
    """Parses a URI using the regex given in Appendix B of RFC 3986.

        (scheme, authority, path, query, fragment) = parse_uri(uri)
    """
    groups = URI.match(uri).groups()
    return (groups[1], groups[3], groups[4], groups[6], groups[8])

def urlnorm(uri):
    
    (scheme, authority, path, params, query, fragment) = urlparse(uri)
    #(scheme, authority, path, query, fragment) = parse_uri(uri)
    #if not scheme or not authority:
    #    raise RequestError("Only absolute URIs are allowed. uri = %s" % uri)
    authority = authority and authority.lower() or ""
    scheme = scheme and scheme.lower() or ""
    path = path or "/"
    # Could do syntax based normalization of the URI before
    # computing the digest. See Section 6.2.2 of Std 66.
    request_uri = query and "?".join([path, query]) or path
    #request_uri = path
    scheme = scheme.lower()
    #defrag_uri = scheme + "://" + authority + request_uri
    defrag_uri = request_uri
    return scheme, authority, request_uri, defrag_uri


# Cache filename construction (original borrowed from Venus http://intertwingly.net/code/venus/)
re_url_scheme    = re.compile(r'^\w+://')
#re_slash         = re.compile(r'[?/:|]+')
re_slash         = re.compile(r'[/\:|]+')
re_reserved      = re.compile(r'[<>"*]+')

def safename(filename, user):
    """Return a filename suitable for the cache.

    Strips dangerous and common characters to create a filename we
    can use to store the cache in.
    """

    try:
        if re_url_scheme.match(filename):
            if isinstance(filename,str):
                filename = filename.decode('utf-8')
                filename = filename.encode('idna')
            else:
                filename = filename.encode('idna')
    except UnicodeError:
        pass
    if isinstance(filename,unicode):
        filename=filename.encode('utf-8')
    #filemd5 = md5.new(filename).hexdigest()
    filename = re_url_scheme.sub("", filename)
    filename = re_slash.sub(",", filename)
    filename = re_reserved.sub('-', filename)
    # This one is special to create cachenames that args can be seperate from requested path
    filename = filename.replace('?', '#')

    # limit length of filename
    if len(filename)>200:
        filename=filename[:200]
    if user is None: user = 0
    #return ",".join((str(user), filename, filemd5))
    return ",".join((str(user), filename))

class BaseCache(object):
    def fetch(self, url, user):
        return None, None
    def save(self, url, header, value, user):
        pass
    def invalidate(self, url, user, files=None):
        pass
    def modified(self, url, user):
        return None
    def etag (self, url, user):
        return None
    
class ResponseCache(object):
    known_headers = [ 'Content-Length', 'Content-Type' ] 
    
    def __init__(self, cachepath):
        "create the local cache"
        self.cachepath  = cachepath
        if not os.path.exists(cachepath):
            os.makedirs (cachepath)

    def _cache_name (self, url, user):
        scheme, authority, request_uri, defrag_uri = urlnorm(url)
        return safename ( defrag_uri, user )
     
    def save(self, url, headers, value,user):
        cachename = os.path.join(self.cachepath, self._cache_name(url, user))
        headers = dict ([ (k,v) for k,v in headers.items() if k in self.known_headers])
        log.debug ('cache write %s to %s' % (url, cachename) )
        with  open (cachename, 'w') as f:
            f.write (str (headers))
            f.write ('\n\n')
            f.write (value)
             
    def fetch(self, url,user):
        #log.debug ('cache fetch %s' % url) 
        cachename = os.path.join(self.cachepath, self._cache_name(url, user))
        if os.path.exists (cachename):
            with open(cachename) as f:
                headers, cached = f.read().split ('\n\n', 1)
                log.info ('cache fetch serviced %s' % url) 
                headers = eval (headers)
                return headers, cached
        return None, None
    
    def invalidate(self, url, user, files = None, exact=False):
        if not files:
            files = os.listdir(self.cachepath)
        # Skip parameters in invalidate
        if '?' in url: 
            url = url.split('?',1)[0]
        cachename = self._cache_name(url, user)
        log.info ('cache invalidate ( %s' % cachename )
        if exact:
            # current cache names file-system safe versions of urls
            # /data_service/images/1?view=deep
            #   =>  ,data_service/images,1#view=deep
            # ',' can be troublesome at ends so we remove them 
            #     ,data_service/images,1#view=deep == ,data_service/images,1,#view=deep 
            cachename = cachename.split('#',1)[0].split(',',1)[1].strip(',')
            for mn, cf in [ (fn.split('#',1)[0].split(',',1)[1].strip(','), fn) for fn in files ] :
                #log.debug('exact %s <> %s' % (cachename, mn))

                if mn == cachename:
                    try:
                        os.unlink (os.path.join(self.cachepath, cf))
                    except OSError:
                        # File was removed by other process
                        pass
                    files.remove (cf)
                    log.debug ('cache exact remove %s' % cf)
            return 
        for cf in files[:]:
            #log.debug ("checking %s" % cf)
            if cachename.startswith('*')\
               and cf.split(',',1)[1].startswith(cachename.split(',',1)[1])\
               or cf.startswith (cachename):
                try:
                    os.unlink (os.path.join(self.cachepath, cf))
                except OSError:
                    # File was removed by other process
                    pass
                files.remove (cf)
                log.debug ('cache remove %s' % cf)

    def modified(self, url, user):
        cachename = os.path.join(self.cachepath, self._cache_name(url, user))
        if os.path.exists(cachename):
            return datetime.fromtimestamp(os.stat(cachename).st_mtime)
        return None
        
    def etag (self, url, user):
        mtime =  self.modified(url, user)
        if mtime:
            cachename = os.path.join(self.cachepath, self._cache_name(url, user))
            return hashlib.md5 (str(mtime) + cachename).hexdigest()
        return None
        
        

class HierarchicalCache(ResponseCache):
    """Specialized Cache that auto-invalidates parent elements of URL
    """
    def invalidate(self, url, user, files=None):
        """Invalidate the URL element and all above it until you hit a collection
        for example:
           invalidate /ds/images/1/gobjects/2  will invalidate both
           /ds/images/1/gobjects/2 and /ds/images/1/gobjects

           This is overkill as we do not need to invalidate
             /ds/images/1/gobjects/3
        """
        log.info ("CACHE invalidate %s for %s " % (url , user))
        files = os.listdir(self.cachepath)
        (scheme, authority, path, query, fragment) = parse_uri(url)
        splitpath = path.split('/')
        # Delete the special queries that may change at any time
        # Will not work for public images used by other users
        # Should probably delete all users cached values but seems
        # like overkill
        scheme = scheme or 'http'
        authority = authority or 'localhost'
        for special in ('tag_names', 'tag_values'):
            super(HierarchicalCache, self).invalidate(''.join([scheme, "://",
                                                               authority,
                                                               '/data_service/images/',
                                                               special]),
                                         '*',files)
        object_found = False
        #  Delete all cached for the URL 
        #  Delete exact matches if URL url is 
        #  
        path = '/'.join(splitpath[:4])
        request_uri = query and "?".join([path, query]) or path
        super(HierarchicalCache, self).invalidate (
            ''.join([scheme, "://" , authority , request_uri]),
            '*', files,exact= False )

        # Delete all top level caches without regard to parameter
        # but not recursively (would be alot )
        path = '/'.join(splitpath[:3])
        request_uri = query and "?".join([path, query]) or path
        super(HierarchicalCache, self).invalidate (
            ''.join([scheme, "://" , authority , request_uri]),
            '*', files,exact=True )
        

        # while splitpath:
        #     path = '/'.join(splitpath)
        #     request_uri = query and "?".join([path, query]) or path
        #     super(HierarchicalCache, self).invalidate (''.join([scheme, "://" , authority , request_uri]),
        #                                                user, files)
        #     pid = splitpath.pop()
        #     # Specifically for /ds/dataset/XX/tag/XX/values that apear
        #     # to act like full queries..
        #     if pid == 'values': continue
        #     # Not an integer token..so stop
        #     # Has the effect of stopping on the next highest container.
        #     #if pid and pid[0] in string.ascii_letters:
        #     #    break
        #     # The above was had error when modifing tags or gobjects 
        #     # and then fetching a view deep on a top level object i.e
        #     # POST /data_service/images/2/gobjects/
        #     # then GET /data_service/images/2?view=deep
        #     # we are seeing a container
            
        #     # if numeric then break
        #     if pid and pid[0] not in string.ascii_letters:
        #         break

        #     # Current code just deletes all up until the top level object.
        #     # Could be made better by deletes all view=deeps ?
        #     #if len(splitpath) <=3:
        #     #    break


def parse_http_date(timestamp_string):
    if timestamp_string is None: return None
    test = timestamp_string[3]
    if test == ',':
        format = "%a, %d %b %Y %H:%M:%S GMT"
    elif test == ' ':
        format = "%a %d %b %H:%M:%S %Y"
    else:
        format = "%A, %d-%b-%y %H:%M:%S GMT"
    return datetime(*strptime(timestamp_string, format)[:6])


class Resource(ServiceController):
    '''
    Base class to create a REST like resource for turbogears:

    Addresses are of the form::

      /Resource
      /Resource/#ID
      /Resource/#ID[/ChildResource/#ID]*

    Operations::

      Target    METHOD: Descritption  method on resource object
      ../Resource : Collection
                GET   : list elements -> dir
                POST  : add an element to resource -> new(factory, doc)
                PUT   : replace all elements given -> replace_all(resource, doc)
                DELETE: delete all elements denoted -> delete_all(resource)

      Examples::
             /ds/images
                  GET : list all element of images
                  POST: create a new image
                        <request>
                          <image x='100' y='100' />
                          ...
             /ds/images/1/tags
                  PUT : replace tag collection of image 1 with
                        <request>
                           <tag name="param" />
                           ...
                  DELETE : delete collection of tags
                  
      ../Resource/#ID : Element ::
                GET   : get value     -> get (resource)
                POST  : add element to resource -> append(resource, doc)
                /ds/images/1
                       <request>
                          <tag name = "" />
                          ...
                      or update the image element permission attribute
                       <request >
                         <image uri="/ds/images/1" perm="0" />
                       
                PUT   : modify value  -> modify (resource, doc)
                DELETE: delete resource -> delete(resource)

      kw['xml_body'] will have the xml_body if available.

    '''
    service_type = "resource"
    cache = False
    children = {}
    server_cache = BaseCache()
    hier_cache   = HierarchicalCache(CACHEDIR)

    def __init__(self, cache=True, **kw):
        super(Resource,self).__init__(**kw)

#         error_function = getattr(self.__class__, 'error', None)
#         if error_function is not None:
#             #If this class defines an error handling method (self.error),
#             #then we should decorate our methods with the TG error_handler.
#             self.get = error_handler(error_function)(self.get)
        log.debug ("Resource()")
        if cache and self.cache == True:
            log.debug ("using CACHE")
            self.server_cache = self.hier_cache
            
#             self.modify = error_handler(error_function)(self.modify)
#             self.new = error_handler(error_function)(self.new)
#             self.append = error_handler(error_function)(self.append)
#             self.delete = error_handler(error_function)(self.delete)

    @classmethod
    def get_child_resource(cls, token):
        return cls.children.get(token, None)


    def check_cache_header(self, resource):
        if not CACHING: return
        etag_check = tg.request.headers.get('If-None-Match', None)
        if etag_check:
            etag = self.get_entity_tag(resource)
            if etag:
                if etag_check == etag:
                    abort(304)

        if not etag_check or not etag:
            modified_check = tg.request.headers.get('If-Modified-Since', None)
            modified_check = parse_http_date(modified_check)
            if modified_check is not None:
                last_modified = self.get_last_modified_date(resource)
                if last_modified is not None:
                    if last_modified <= modified_check:
                        abort(304)

    def add_cache_header(self, resource):
        if not CACHING: return
        tg.response.headers['Cache-Control'] = 'public'
        etag = self.get_entity_tag(resource)
        if etag:
            tg.response.headers['ETag'] = etag
            return
       
        last_modified = self.get_last_modified_date(resource)
        #logger.debug('response: ' + str(last_modified))
        if last_modified is None:
            last_modified = datetime(*gmtime()[:6])

            tg.response.headers['Last-Modified'] = ( 
                datetime.strftime(last_modified, "%a, %d %b %Y %H:%M:%S GMT"))

    def invalidate(self, url):
        self.user_id = None
        if identity.not_anonymous():
            self.user_id = identity.current.get_bq_user().id
        self.server_cache.invalidate(url, user=self.user_id)

    @expose()
    def _default(self, *path, **kw):
        request = tg.request
        response = tg.response
        path = list(path)
        resource = None
        user_id = None
        if not hasattr(request, 'bisque'):
            bisque = Bunch()
            request.bisque = bisque
        bisque = request.bisque 
        if not hasattr(bisque, 'user_id'):
            if identity.not_anonymous():
                user_id = identity.current.get_bq_user().id
            bisque.user_id = user_id
        user_id = bisque.user_id 


        http_method = request.method.lower()
        log.info ('Request "%s" with %s?%s'%(http_method,str(request.path),str(kw)))
        log.debug ('Request "%s" '%(path))

        #check the http method is supported.
        try:
            method_name = dict(get='get', head='head', post='append',
                               put='modify', delete='delete')[http_method]
        except KeyError:
            abort(501)


        if not path: #If the request path is to a collection.
            self.check_cache_header(resource)
            if http_method == 'post':
                #If the method is a post, we call self.create which returns
                #a class which is passed into the self.new method.
                resource = self.create(**kw)
                assert resource is not None
                method_name = 'new'
            elif http_method == 'get':
                #If the method is a get, call the self.index method, which
                #should list the contents of the collection.
                headers, value = self.server_cache.fetch(request.url, user=user_id)
                if value:
                    response.headers.update(headers) # cherrypy.response.headers.update (headers)
                else:
                    #self.add_cache_header(None)
                    value =  self.dir(**kw)
                    self.server_cache.save (request.url,
                                            response.headers,
                                            value, user=user_id)
                self.add_cache_header(resource)
                return value
            elif http_method == 'put':
                resource = bisque.parent
                method_name = 'replace_all'
            elif http_method == 'delete':
                resource = bisque.parent
                method_name = 'delete_all'
            elif http_method == 'head':
                # Determine whether the collection has changed
                self.add_cache_header(None)
                return dict()
            else:
                #Any other methods get rejected.
                abort(501)

        if resource is None:
            #if we don't have a resource by now, (it wasn't created)
            #then try and load one.
            token = path.pop(0)
            resource = self.load(token)
            if resource is None:
                #No resource found?
                if user_id is None:
                    abort(401)
                abort(404)

        #if we have a path, check if the first token matches this 
        #classes children.
        if path:
            token = path.pop(0)
            #log.debug('Token: ' + str(token))
            child = self.get_child_resource(token)
            if child is not None:
                bisque.parent = resource
                #log.debug ("parent = %s" % resource)
                #call down into the child resource.
                return child._default(*path, **kw)


#        if http_method == 'get':
#            #if this resource has children, make sure it has a '/'
#            #on the end of the URL
#            if getattr(self, 'children', None) is not None:
#                if request.path[-1:] != '/':
#                    redirect(request.path + "/")

        self.check_cache_header(resource)

        method = getattr(self, method_name)
        #pylons.response.headers['Content-Type'] = 'text/xml' 
        log.debug ("Dispatch for %s", method_name)
        try:
            if http_method in ('post', 'put'):
                clen = int(request.headers.get('Content-Length', 0))
                content = request.headers.get('Content-Type')
                if content.startswith('text/xml') or \
                       content.startswith('application/xml'):
                    data = request.body_file.read(clen)
                    #log.debug('POST '+ data)
                    #kw['xml_text'] = data
                    value = method(resource, xml=data, **kw)
                else:
                    #response = method(resource, doc = None, **kw)
                    # Raise illegal operation (you should provide XML)
                    log.debug ("Bad media type in post/put:" + content)
                    redirect("", 415)
                self.server_cache.invalidate(request.url, user=user_id)
            elif http_method == 'delete':
                value = method(resource, **kw)
                self.server_cache.invalidate(request.url, user=user_id)
            else:  # http_method is in ('get', 'head')
                headers, value = self.server_cache.fetch(request.url, user=user_id)
                if value:
                    response.headers.update (headers)
                else:
                    #run the requested method, passing it the resource
                    value = method(resource, **kw)
                    self.server_cache.save (request.url,
                                            response.headers,
                                            value, user=user_id)
                    
            #set the last modified date header for the response
            self.add_cache_header(resource)
            return value
        except identity.BQIdentityException:
            response.status_int = 401    
            return "<response>FAIL</response>"


    def get_entity_tag(self, resource):
        """
        returns the Etag for the collection (resource=None) or the resource
        """
        log.debug ("ETAG: %s " %tg.request.url)
        if self.cache:
            return self.server_cache.etag (tg.request.url,
                                           tg.request.bisque.user_id)
        return None
    def get_last_modified_date(self, resource):
        """
        returns the last modified date of the resource.
        """
        log.debug ("CHECK MODFIED: %s " %tg.request.url)

        if self.cache:
            return self.server_cache.modified (tg.request.url,
                                               tg.request.bisque.user_id)
        return None

    def dir(self, **kw):
        """
        returns the representation of a collection of resources.
        """
        raise abort(403)

    def load(self, token):
        """
        loads and returns a resource identified by the token.
        """
        return None

    def create(self, **kw):
        """
        returns a class or function which will be passed into the self.new 
        method. 
        """
        raise abort(501)

    def new(self, resource_factory, xml, **kw):
        """
        uses resources factory to create a resource, commit it to the 
        database.
        """
        raise abort(501)

    def modify(self, resource, xml, **kw):
        """
        Modify the resource in place replace the value
        uses kw to modifiy the resource.
        """
        raise abort(501)

    def get(self, resource, **kw):
        """
        fetches the resource, and returns a representation of the resource.
        """
        raise abort(501)
    def append(self, resource, xml, **kw):
        """
        Append value to resource 
        """
        raise abort(501)
    def delete(self, resource,  **kw):
        """
        Delete the resource from the database
        """
        raise abort(501)

    
