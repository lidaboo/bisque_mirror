# -*- mode: python -*-
"""Main server for image_service}
"""
import os
import logging
import pkg_resources
import tg
import urlparse
import re

from hashlib import md5
from datetime import datetime
from lxml import etree
from pylons.controllers.util import etag_cache
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash, config, abort
from repoze.what import predicates 
from bq.core.service import ServiceController
from paste.fileapp import FileApp
from pylons.controllers.util import forward
from bq.data_service.model import Taggable, DBSession

from bq.core import permission, identity
from bq.util.paths import data_path
from bq.util.mkdir import _mkdir
from imgsrv import ImageServer
from imgsrv import ProcessToken
import imgcnv
import bioformats

log = logging.getLogger("bq.image_service")


def get_image_id(url):
    path = urlparse.urlsplit(url)[2]
    if path[-1]=='/':
        path =path[:-1]

    id = path.split('/')[-1]
    return id

def get_format_map():
    bformats = ""
    if bioformats.installed() :
        bformats = bioformats.installed_formats() 
    xmlout='<response>%s%s</response>'  % (imgcnv.installed_formats(),bformats)
    format_tree = etree.XML(xmlout)
    formats = {}
    for ex in format_tree.xpath ('./format/codec/tag[@name="extensions"]'):
        codec = ex.getparent().get('name')
        for ext in ex.get('value').split('|'):
            formats.setdefault(ext, []).append(codec)
    for format in ('amiramesh', 'cfg', 'csv', 'dat', 'grey', 'htm', 'html', 'hx', 'inf', 'labels', 'log', 'lut', 'mdb', 'pst', 'pty', 'rec', 'tim', 'txt', 'xlog', 'xml', 'zip', 'zpo' ) :
        if format in formats:
            del formats[format] # some formats should not be accepted as an image format
    return formats


def cache_control (value):
    tg.response.headers.pop('Pragma', None)
    tg.response.headers['Cache-Control'] = value

class image_serviceController(ServiceController):
    #Uncomment this line if your controller requires an authenticated user
    #allow_only = predicates.not_anonymous()
    service_type = "image_service"

    def __init__(self, server_url):
        super(image_serviceController, self).__init__(server_url)
        imgdir = config.get('bisque.image_service.local_dir', data_path('imagedir'))
        workdir= config.get('bisque.image_service.work_dir', data_path('workdir'))

        _mkdir (workdir)
        log.info('ROOT=%s images=%s work=%s' % (config.get('bisque.root'), imgdir, workdir))
        self.format_map = None

        self.srv = ImageServer (image_dir=imgdir,
                                work_dir = workdir,
                                data_dir = data_path(),
                                server_url = server_url)


#    def store_blob(self, src, name):
#        log.info('storing blob %s' % name)
#        return self.srv.storeBlob(src,name)

#    def new_file(self, src, name, userPerm = permission.PRIVATE):
#        srv = self.srv
#        userId = identity.current.user_name
#        blob_id, path = srv.storeBlob (src=src, name=name, ownerId = userId, permission = userPerm)
#        url = self.makeurl(str(blob_id))
#        return dict(src=url)

#    def new_image(self, src, name, userPerm = permission.PRIVATE, **kw):
#        ''' place the image file in a local '''
#        srv = self.srv
#        userId = identity.current.user_name
#        image_id, path, x, y, ch, z, t = srv.addImage(src=src, name=name, ownerId = userId, permission = userPerm, **kw)
#        if image_id == None:
#            log.debug ("local_service FAILED to create image src=%s, name=%s, owner=%s" %(src,name,userId))
#            return dict()
#        log.debug("new_image %s, %s, %s, %s, %s, %s, %s [%s]"%(str(image_id), path, str(x), str(y), str(ch), str(z), str#(t), str(userPerm) ) )           
#        url = self.makeurl( str(image_id) )
#        return dict(src=url, x=x, y=y, ch=ch, z=z, t=t)

    def meta(self, imgsrc, **kw):
        id = get_image_id(imgsrc)
        userId = identity.current.user_name   
        log.debug('Meta: %s %s %s'%(imgsrc, id, userId ) )     
        doc = self.srv.execute('meta',  id, userId, None)
        log.debug('Meta doc: %s'%(doc ) )         
        return doc

    def info(self, imgsrc, **kw):
        id = get_image_id(imgsrc)
        userId = identity.current.user_name
        log.debug('Info: %s %s %s'%(imgsrc, id, userId ) )        
        doc = self.srv.execute('info',  id, userId, None)
        log.debug('Info doc: %s'%(doc ) )           
        return doc

    def local_file (self, url, **kw):
        ''' returns local path if it exists otherwise None'''
        userId = identity.current.user_name       
        
        m = re.search(r'(\/image_service\/image[s]?\/)(?P<id>[\w-]+)', url)
        id = m.group('id')         

        log.debug ("Checking %s" % id)
        # check for access permission
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        self.check_access(id, RESOURCE_READ)

        data_token = self.srv.process(url, id, userId)
        
        #first check if the output is an error
        if data_token.isHttpError():
            return None

        return data_token.data        
        

        
#    def files_exist(self, hashes, **kw):
#        #userId = identity.current.user_name  
#        return self.srv.blobsExist(hashes)

    def find_uris(self, hsh, **kw):
        #userId = identity.current.user_name  
        return self.srv.blobUris(hsh)

#    def local_path (self, src, **kw):
#        ''' return local path if it exists otherwise None'''
#        return self.srv.id2path(get_image_id(src))
        
#    def set_file_info( self, image_uri, **kw ):
#        self.srv.setBlobInfo(image_uri, **kw)

#    def set_file_credentials( self, image_uri, owner_name, permission ):
#        self.srv.setBlobCredentials(image_uri, owner_name, permission )

#    def set_file_acl( self, image_uri, owner_name, permission ):
#        self.srv.set_file_acl(image_uri, owner_name, permission )    

    def guess_image_type (self, filename):
        """guess whether the file is an image based on the filename
        and whether we think we can decode
        """
        if self.format_map is None:
            self.format_map = get_format_map()
        filename = filename.strip()
        ext = os.path.splitext(filename)[1][1:].lower()
        return self.format_map.get(ext)


    @expose()
    #@identity.require(identity.not_anonymous())    
    def _default(self, *path, **kw):
        #path = cherrypy.request.path+'?'+cherrypy.request.query_string
        id = path[0]
        return self.images(id, **kw)

    @expose(content_type='text/xml')
    def index(self, **kw):
           
        methods = {}
        methods['/ID'] = 'Returns a file for this ID'
        methods['/images/ID'] = 'same as /ID'   
        methods['/ID?SERVICE1=PAR1&SERVICE2=PAR2'] = 'Execute services for image ID and return result. Call /services to check available'        
        methods['/services'] = 'Returns XML list of supported services'
        methods['/formats'] = 'Returns XML list of supported formats' 
        methods['/upload_image'] = 'Upload image using HTTP upload form' 
        methods['/find?hash=HASH'] = 'Find all images with a given HASH' 
        methods['/update_image_permission'] = 'Changes file permissions using received XML'     
        
        response = etree.Element ('response')
        for m,d in methods.items():
            tag = etree.SubElement(response, 'method')
            tag.attrib['name'] = m
            tag.attrib['description'] = d           
        return etree.tostring(response)
        
    @expose()
    #@identity.require(identity.not_anonymous())
    def services(self, **kw):
        #request = cherrypy.request
        #response = cherrypy.response
        #path   = request.path+'?'+request.query_string
        #userId = identity.current.user_name
        
        data_token = ProcessToken()
        data_token = self.srv.request( 'services', None, data_token, None )
        tg.response.headers['Content-Type']  = data_token.contentType
        #tg.response.headers['Cache-Control'] = data_token.cacheInfo
        cache_control( data_token.cacheInfo )

        return data_token.data

    @expose(content_type="application/xml")
    #@identity.require(identity.not_anonymous())
    def formats(self, **kw):
        #request = cherrypy.request
        #response = cherrypy.response
        #path   = request.path+'?'+request.query_string
        #userId = identity.current.user_name
        
        data_token = ProcessToken()
        data_token = self.srv.request( 'formats', None, data_token, None )
        tg.response.headers['Content-Type']  = data_token.contentType
        #tg.response.content_type  = data_token.contentType
        #tg.response.headers['Cache-Control'] = data_token.cacheInfo
        cache_control( data_token.cacheInfo )
        return data_token.data

    @expose()
    #@identity.require(identity.not_anonymous())
    def remote(self, **kw):
        return self.images(-1, **kw)
    
    @expose()
    def blobs(self):
        pass

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
    def image(self, *path, **kw):
        id = path[0]
        return self.images(id, **kw)

    @expose()
    #@identity.require(identity.not_anonymous())
    def images(self, id, **kw):
        request = tg.request
        response = tg.response
        log.info ('Request: %s' % request.url)
      
        path   = request.path+'?'+request.query_string
        userId = identity.current.user_name

        # check for access permission
        from bq.data_service.controllers.resource_query import RESOURCE_READ, RESOURCE_EDIT
        self.check_access(id, RESOURCE_READ)
        
        
        # dima: patch for incorrect /auth requests for image service
        if path.find('/auth')>=0:
            tg.response.headers['Content-Type']  = 'text/xml'
            return '<resource />'
                            
        data_token = self.srv.process(path, id, userId, **kw)
        tg.response.headers['Content-Type']  = data_token.contentType
        #tg.response.content_type  = data_token.contentType
        #tg.response.headers['Cache-Control'] = ",".join ([data_token.cacheInfo, "public"])
        cache_control( ",".join ([data_token.cacheInfo, "public"]))
        
        #first check if the output is an error
        if data_token.isHttpError():
            log.error('Responce Code: %s : %s' % (data_token.httpResponseCode, data_token.data))
            tg.response.status_int = data_token.httpResponseCode             
            tg.response.content_type = data_token.contentType
            tg.response.charset = 'utf8'
            return data_token.data.encode('utf8')

        #second check if the output is TEXT/HTML/XML                  
        if data_token.isText():
            return data_token.data

        #third check if the output is actually a file
        if data_token.isFile():
            #modified =  datetime.fromtimestamp(os.stat(data_token.data).st_mtime)
            #etag_cache(md5(str(modified) + str(id)).hexdigest())

            fpath = data_token.data.split('/')
            fname = fpath[len(fpath)-1]

            if data_token.hasFileName():
               fname = data_token.outFileName
          
            #Content-Disposition: attachment; filename=genome.jpeg; 
            disposition = ''
            if data_token.isImage() is not True:
                disposition = 'attachment; '

            try:
                fname.encode('ascii')
                disposition = '%sfilename="%s"'%(disposition, fname)
            except UnicodeEncodeError:
                # dima: encode the filename in utf-8
                disposition = '%sfilename="%s"; filename*="%s"'%(disposition, fname.encode('utf8'), fname.encode('utf8'))
                #disposition = '%sfilename="%s"; filename*="%s"'%(disposition, fname.encode('ascii', errors='ignore'), fname.encode('utf8'))

                
            #tg.response.headers["Content-Disposition"] = disposition
            # this header is cleared when the streaming is used
            #cherrypy.response.headers["Content-Length"] = 10*1024*1024            


            # non streaming code           
            #ofs = open(data_token.data,'rb').read() 
            #log.debug('Returning file: ' + str(fname) )                       
            #return ofs            

            # fix for the cherrypy error 10055 "No buffer space available" on windows
            # by streaming the contents of the files as opposite to sendall the whole thing
            log.info ("returning %s type %s"%(data_token.data, data_token.contentType ))
            return forward(FileApp(data_token.data,
                                   content_type=data_token.contentType,
                                   content_disposition=disposition,
                                   ).cache_control (max_age=60*60*24*7*6)) # 6 weeks

        log.error ("unknown image issue")
        tg.response.status_int = 404             
        return "File not found"
       
#    @expose()
#    #@identity.require(identity.not_anonymous())    
#    def upload_file(self, file, **kw):
#        userId = identity.current.user_name
#        userPerm = 1
#        if ('permission' in kw): userPerm = kw['permission']
#        image_id, path = self.srv.storeBlob( file, None, ownerId = userId, permission = userPerm )
#        return '/imgsrv/images/'+str(image_id)  	
#    
#    @expose()
#    #@identity.require(identity.not_anonymous())    
#    def upload_image(self, file, **kw):
#        userId = identity.current.user_name
#        userPerm = 1
#        if ('permission' in kw): userPerm = kw['permission']
#        	    
#        image_id, path, x, y , ch, z ,t = self.srv.addImage( file, None, ownerId = userId, permission = userPerm, **kw )
#        #return turbogears.url('/imgsrv/images/'+str(image_id))
#        return '/imgsrv/images/'+str(image_id), x, y, ch, z, t

    @expose()
    def update_image_permission(self):

        # parse the request
        request = tg.request
        clen = int(request.headers.get('Content-Length') or 0 )
        if (clen<=0): return ""
        xmldata = request.body
        log.debug ("XML = " + xmldata)
        request = etree.XML(xmldata)
        image = request[0]
        src  = image.attrib['src']
        perm = image.attrib['perm']
        
        # check identity
        id = get_image_id(src)
        userId = identity.current.user_name
        if self.srv.changePermission( id, userId ) == False:
            tg.response.status_int = 401             
            return 'Permission denied...'
        
        # Deal w/request        
        log.debug ('permission: %s -> %s ' %( src, perm))
        self.set_file_info(src, perm=int(perm))
        return dict()
        
    @expose(content_type='text/xml')
    def find(self, hash=None):   
    
        # parse the request
        if not hash:
            request = tg.request
            clen = int(request.headers.get('Content-Length') or 0 )
            if (clen<=0): return "<response/>"
            xmldata = request.body
            
            log.debug ("XML = " + xmldata)
            request = etree.XML(xmldata)
            image = request[0]
            hash  = image.attrib['hash']
        
        uris = self.find_uris(hash)
        
        response = etree.Element ('response')
        for uri in uris:
            tag = etree.SubElement(response, 'image')
            tag.attrib['uri'] = str(uri)

        return etree.tostring(response)




def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  image_serviceController(uri)
    #directory.register_service ('image_service', service)

    return service

def get_static_dirs():
    """Return the static directories for this server"""
    package = pkg_resources.Requirement.parse ("bqserver")
    package_path = pkg_resources.resource_filename(package,'bq')
    return [(package_path, os.path.join(package_path, 'image_service', 'public'))]

#def get_model():
#    from bq.image_service import model
#    return model

__controller__ =  image_serviceController
