###############################################################################
##  Bisque                                                                   ##
##  Center for Bio-Image Informatics                                         ##
##  University of California at Santa Barbara                                ##
## ------------------------------------------------------------------------- ##
##                                                                           ##
##     Copyright (c) 2007,2008,2009,2010,2011,2012                           ##
##     by the Regents of the University of California                        ##
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
##                                                                           ##
## THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY         ##
## EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE         ##
## IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR        ##
## PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> OR           ##
## CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,     ##
## EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,       ##
## PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR        ##
## PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF    ##
## LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING      ##
## NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS        ##
## SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.              ##
##                                                                           ##
## The views and conclusions contained in the software and documentation     ##
## are those of the authors and should not be interpreted as representing    ##
## official policies, either expressed or implied, of <copyright holder>.    ##
###############################################################################
"""
SYNOPSIS
========
blob_service 
  

DESCRIPTION
===========
Micro webservice to store and retrieve blobs(untyped binary storage) on a variety 
of storage platforms: local, irods, s3
"""
import os
import logging
import hashlib
import urlparse
import itertools

from lxml import etree
from datetime import datetime
from datetime import timedelta


import tg
from tg import expose, flash, config, require, abort
from tg.controllers import RestController
#from paste.fileapp import FileApp
from bq.util.fileapp import BQFileApp
from pylons.controllers.util import forward
from repoze.what import predicates 

from bq.core.service import ServiceMixin
from bq.core.service import ServiceController
from bq.core import  identity
from bq.core.permission import perm2str
from bq.exceptions import IllegalOperation
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from bq.util.hash import make_uniq_hash, make_short_uuid
from bq.util.timer import Timer
from bq.util.sizeoffmt import sizeof_fmt

from bq import data_service
from bq.data_service.model import Taggable, DBSession



import blob_storage

log = logging.getLogger('bq.blobs')

try:
    # python 2.6 import
    from ordereddict import OrderedDict
except ImportError:
    try:
        # python 2.7 import
        from collections import OrderedDict
    except ImportError:
        log.error("can't import OrderedDict")


###########################################################################
# Hashing Utils
###########################################################################

import sys
import hashlib

def file_hash_SHA1( filename ):
    '''Takes a file path and returns a SHA-1 hash of its bits'''
    f = file(filename, 'rb')
    m = hashlib.sha1()
    readBytes = 1024 # use 1024 byte buffer
    while (readBytes):
        readString = f.read(readBytes)
        m.update(readString)
        readBytes = len(readString)
    f.close()
    return m.hexdigest()

def file_hash_MD5( filename ):
    '''Takes a file path and returns a MD5 hash of its bits'''
    f = file(filename, 'rb')
    m = hashlib.md5()
    readBytes = 1024 # use 1024 byte buffer
    while (readBytes):
        readString = f.read(readBytes)
        m.update(readString)
        readBytes = len(readString)
    f.close()
    return m.hexdigest()	  
   
#########################################################
# Utility functions
########################################################

def guess_type(filename):
    from bq import image_service 
    filename = filename.strip()
    filetype = image_service.guess_image_type (filename)
    if filetype:
        return 'image'
    return 'file'

def load_stores():
    stores = OrderedDict()
    store_list = [ x.strip() for x in config.get('bisque.blob_service.stores','').split(',') ] 
    log.debug ('requested stores = %s' % store_list)
    for store in store_list:
        params = dict ( (x[0].replace('bisque.stores.%s.' % store, ''), x[1]) 
                        for x in  config.items() if x[0].startswith('bisque.stores.%s.' % store))
        if 'path' not in params:
            log.error ('cannot configure %s with out path parameter' % store)
            continue
        log.debug("params = %s" % params)
        driver = blob_storage.make_storage_driver(params.pop('path'), **params)
        if driver is None: 
            log.error ("failed to configure %s.  Please check log for errors " % store)
            continue
        stores[store] = driver
    return stores

def transfer_msg(flocal, transfer_t):
    'return a human string for transfer time and size'
    fsize = os.path.getsize (flocal)
    name  = os.path.basename(flocal)
    if transfer_t == 0:
        return "transferred %s in 0 sec!" % fsize
    return "{name} transferred {size} in {time} ({speed}/sec)".format(name=name, size=sizeof_fmt(fsize),
                                                                      time=timedelta(seconds=transfer_t), 
                                                                      speed = sizeof_fmt(fsize/transfer_t))



class StorageManager(object):
    'Manage multiple stores'

    def __init__(self):
        self.stores = load_stores()
        log.info ('configured stores %s' % ','.join( str(x) for x in self.stores.keys()))

    def valid_blob(self, blob_id):
        "Determin if uripath is supported by configured blob_storage (without fetching)"
        for store in self.stores.values():
            if store.valid(blob_id):
                return True
        return False

    def fetch_blob(self, blob_id):
        path = None
        with Timer() as t:
            for store in self.stores.values():
                if store.valid(blob_id):
                    path =  store.localpath(blob_id)
                    break
        if log.isEnabledFor(logging.INFO):
            log.info (transfer_msg (path, t.interval))
        return path

    def save_blob(self, fileobj, filename, user_name, uniq):
        filename_safe = filename.encode('ascii', 'xmlcharrefreplace')
        for store_id, store in self.stores.items():
            try:
                # blob storage part
                if store.readonly:
                    log.debug("skipping %s: is readonly" % store_id)
                    continue
                return  store.write(fileobj, filename_safe, user_name = user_name, uniq=uniq)
            except Exception, e:
                log.exception('storing blob failed')
        return (None,None)

    def __str__(self):
        return "stores%s" % self.stores.keys()



###########################################################################
# BlobServer
###########################################################################

class BlobServer(RestController, ServiceMixin):
    '''Manage a set of blob files'''
    service_type = "blob_service"
    
    def __init__(self, url ):
        ServiceMixin.__init__(self, url)
        self.stores = StorageManager()

#################################
# service  functions 
################################
    def check_access(self, ident, action):
        from bq.data_service.controllers.resource_query import resource_permission
        query = DBSession.query(Taggable).filter_by (resource_uniq = ident)
        resource = resource_permission (query, action=action).first()
        if resource is None:
            if identity.not_anonymous():
                abort(403)
            else:
                abort(401)
        return resource

    @expose()
    def get_one(self, ident,  **kw):
        "Fetch a blob based on uniq ID"
        log.info("get_one() called %s" % kw)
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        #ident = args[0]
        self.check_access(ident, RESOURCE_READ)
        try:
            localpath = os.path.normpath(self.localpath(ident))
            filename = self.getBlobFileName(ident)
            if 'localpath' in kw:
                tg.response.headers['Content-Type']  = 'text/xml'
                resource = etree.Element ('resource', name=filename, value = localpath)
                return etree.tostring (resource)
            try:
                disposition = 'attachment; filename="%s"'%filename.encode('ascii')
            except UnicodeEncodeError:
                disposition = 'attachment; filename="%s"; filename*="%s"'%(filename.encode('utf8'), filename.encode('utf8'))

            return forward(BQFileApp(localpath,
                                   content_disposition=disposition,        
                                   ).cache_control (max_age=60*60*24*7*6)) # 6 weeks
        except IllegalOperation:
            abort(404)

    @expose(content_type='text/xml')
    @require(predicates.not_anonymous())
    def post(self, **transfers):
        "Create a blob based on unique ID"
        log.info("post() called %s" % kwargs)
        #log.info("post() body %s" % tg.request.body_file.read())

        def find_upload_resource(transfers, pname):
            log.debug ("transfers %s " % (transfers))
            
            resource = transfers.pop(pname+'_resource', None) #or transfers.pop(pname+'_tags', None)
            log.debug ("found %s _resource/_tags %s " % (pname, resource))
            if resource is not None:
                try:
                    if hasattr(resource, 'file'):
                        log.warn("XML Resource has file tag")
                        resource = f.file.read()
                    if isinstance(resource, basestring):
                        log.debug ("reading XML %s" % resource)
                        resource = etree.fromstring(resource)
                except:
                    log.exception("Couldn't read resource parameter %s" % resource)
                    resource = None
            return resource

        for k,f in dict(transfers).items():
            if k.endswith ('_resource') or k.endswith('_tags'): continue
            if hasattr(f, 'file'):
                resource = find_uploaded_resource(transfers, k)
                resource = self.store_blob(resource = resource, file_obj = f.file)

        return resource

    
    @expose()
    @require(predicates.not_anonymous())
    def delete(self, *args, **kwargs):
        ' Delete the resource  '
        ident = args[0]
        log.info("delete() called %s" % args)
        from bq.data_service.controllers.resource_query import resource_delete
        resource = self.getBlobInfo(ident)
        resource_delete(resource)

    @expose()
    @require(predicates.not_anonymous())
    def move(self, src, dst, *args,  **kwargs):
        ' Move a resource identified by path  '
        log.info("move() called %s" % args)
        from bq.data_service.controllers.resource_query import resource_permission
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        query = DBSession.query(Taggable).filter_by (resource_value=src,resource_parent=None)
        resource = resource_permission(query, RESOURCE_EDIT).first()
        if resource:
            resource.resource_value = dst
        return resource


########################################
# API functions
#######################################
    def create_resource(self, resource ):
        'create a resource from a blob and return new resource'
        # hashed filename + stuff

        perm     = resource.get('permission', 'private')
        filename = resource.get('name')
        resource.set('resource_type', resource.get('resource_type') or guess_type(filename))
        # KGK  
        # These are redundant (filename is the attribute name name upload is the ts
        resource.insert(0, etree.Element('tag', name="filename", value=filename, permission=perm))
        resource.insert(1, etree.Element('tag', 
                                         name="upload_datetime", 
                                         value=datetime.now().isoformat(' '), 
                                         type='datetime',
                                         permission=perm),
                        )

        log.info ("NEW RESOURCE <= %s" % (etree.tostring(resource)))
        return data_service.new_resource(resource = resource)


    def store_blob(self, resource, fileobj = None):
        'Store a resource in the DB must be a valid resource'
        fhash = resource.get ('resource_uniq')
        if fhash is None:
            fhash = make_short_uuid()
            resource.set('resource_uniq', fhash)
        if fileobj is not None:
            return self.store_fileobj(resource, fileobj)
        return self.store_reference(resource, resource.get('value') )
        

    def store_fileobj(self, resource, fileobj ):
        'Create a blob from a file'
        user_name = identity.current.user_name
        # dima: make sure local file name will be ascii, should be fixed later
        # dima: unix without LANG or LC_CTYPE will through error due to ascii while using sys.getfilesystemencoding()
        #filename_safe = filename.encode(sys.getfilesystemencoding()) 
        #filename_safe = filename.encode('ascii', 'xmlcharrefreplace')
        #filename_safe = filename.encode('ascii', 'replace')        
        filename = resource.get('name') or  getattr(fileobj, 'name') or ''
        uniq     = resource.get('resource_uniq')
        
        with Timer() as t:
            blob_id, flocal = self.stores.save_blob(fileobj, filename, user_name = user_name, uniq=uniq)

        if log.isEnabledFor(logging.INFO):
            log.info (transfer_msg (flocal, t.interval))

        resource.set('name', filename)
        resource.set('value', blob_id)
        resource.set('resouce_uniq', uniq)
        return self.create_resource(resource)

    def _make_url_local(self, urlref):
        'return a local file to the specified urlref'
        if urlref.startswith ('file:'):
            return urlref [5:]
        return None

    def store_reference(self, resource, urlref = None ):
        'create a blob from a blob_id'
        filename  = resource.get ('name') or urlref.rsplit('/',1)[1]
        if not self.stores.valid_blob(urlref):
            # We have a URLref that is not part of the sanctioned stores:
            # We will move it 
            localpath = self._make_url_local(urlref)
            if localpath:
                with open(localpath) as f:
                    return self.store_fileobj(resource, f)
            else:
                raise IllegalOperation("%s could not be moved to a valid store" % urlref)
        resource.set ('name' ,filename)
        resource.set ('value', urlref)

        return self.create_resource(resource)

    def localpath (self, uniq_ident):
        "Find  local path for the identified blob, using workdir for local copy if needed"
        resource = DBSession.query(Taggable).filter_by (resource_uniq = uniq_ident).first()
        path = None
        if resource is not None and resource.resource_value:
            blob_id  = resource.resource_value
            path = self.stores.fetch_blob(blob_id)
            log.debug('using %s full=%s localpath=%s' % (uniq_ident, blob_id, path))
            return path
        raise IllegalOperation("bad resource value %s" % uniq_ident)


    def getBlobInfo(self, ident): 
        resource = DBSession.query(Taggable).filter_by (resource_uniq = ident).first()
        return resource

    def getBlobFileName(self, ident): 
        fobj = self.getBlobInfo(ident)
        fname = str(id)
        if fobj != None and fobj.resource_name != None:
            fname =  fobj.resource_name 
        log.debug('Blobsrv - original name %s->%s ' % (ident, fname ))
        return fname   

    def blobsExist(self, fhashes):
        'search for files by content hash'
        blobsfound = []
        #for fhash in fhashes:
        #   if blobdb.find_image_id(fhash) != None:
        #       blobsfound.append(fhash)

        for fhash in fhashes:
            resource = DBSession.query(Taggable).filter_by (resource_uniq = fhash).first()
            if resource:
                blobsfound.append(fhash)
        log.warn("blobsExist not implemented")
        return blobsfound

    def originalFileName(self, ident): 
        log.debug ('originalFileName: deprecated %s', ident)
        return self.getBlobFileName(ident) 
        
    def fileExists(self, id):
        if id==None: return False      
        try:
            fileName = self.localpath(id)    
            return fileName and os.path.exists(fileName)
        except IllegalOperation,e:
            return False
        except Exception, e:
            log.exception('cannot load resource_uniq %s' % id)
            return False


    def move_resource_store(self, srcstore, dststore):
        """Find all resource on srcstore and move to dststore

        :param srcstore: Source store  ID
        :param dststore: Destination store ID
        """
        src_store = self.stores.get(srcstore)
        dst_store = self.stores.get(dststore)
        if src_store is None or dst_store is None:
            raise IllegalOperation("cannot access store %s, %s" % (srcstore, dststore))
        if src_store == dst_store:
            raise IllegalOperation("cannot move onto same store %s, %s" % (srcstore, dststore))

        for resource in DBSession.query(Taggable).filter_by(Taggable.resource_value.like (src_store.top)):
            localpath = self.localpath(resource.resource_uniq)

            filename = resource.resource_name
            user_name = resource.owner.resource_name
            try:
                with open(localpath) as f:
                    blob_id, flocal = dst_store.write(f, filename, user_name = user_name)
            except:
                log.error("move failed for resource_uniq %s" % resource.resource_uniq)
                continue
            old_blob_id = resource.resource_value 
            resource.resource_value = blob_id

    def geturi(self, id):
        return self.url + '/' + str(id)
            



def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  BlobServer(uri)
    #directory.register_service ('image_service', service)

    return service

#def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("bqserver")
#    package_path = pkg_resources.resource_filename(package,'bq')
#    return [(package_path, os.path.join(package_path, 'image_service', 'public'))]

#def get_model():
#    from bq.image_service import model
#    return model

__controller__ =  BlobServer

