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

"""
import operator
from datetime import datetime
from lxml import etree
from tg import expose, controllers, flash, url
import logging
from repoze.what.predicates import is_user
from repoze.what.predicates import not_anonymous

import bq
from bq.core.service import ServiceController
from bq.core import identity
from bq.core.model import   User #, Visit
from bq.core.model import DBSession as session
from bq.data_service.model import  BQUser, Image, TaggableAcl
#from bq.image_service.model import  FileAcl
from tg import redirect
from tg import request

log = logging.getLogger('bq.admin')


    

class AdminController(ServiceController):
    """The admin controller is a central point for
    adminstrative tasks such as monitoring, data, user management, etc.
    """
    service_type = "admin"


    #require = identity.in_group("admin")
    allow_only = is_user('admin')

    @expose('bq.client_service.templates.admin.index')
    def index(self, **kw):
        log.info ("ADMIN")
        query = kw.pop('query', '')
        wpublic = kw.pop('wpublic', not bq.core.identity.not_anonymous())
        return dict(query = query, wpublic = wpublic, analysis = None, search = None)

    @expose ('bq.client_service.templates.admin.users')
    def users(self, order = "id", **kw):
        ordering = { 'id' : BQUser.id,
                     'user_name' : BQUser.user_name,
                     'display_name' : BQUser.display_name,
                     'email_address' : BQUser.email_address,
                     'images': BQUser.id
                     }
        order_with = ordering.get (order, BQUser.id)
        users = session.query(BQUser).order_by(order_with).all()
        results  = []
        for u in users:
            count = session.query(Image).filter (Image.owner_id == u.id).count()
            results.append ( [u, count] )

        if order == "images":
            results.sort (key = operator.itemgetter (1) )
            results.reverse()
            
        query = kw.pop('query', '')
        wpublic = kw.pop('wpublic', not bq.core.identity.not_anonymous())
        return dict(users = results, query = query, wpublic = wpublic, analysis = None, search = None)

    @expose ('bq.client_service.templates.admin.edituser')
    def edituser(self, username=None, **kw):
        options = {}
        
        #Grab passed args
        if options.has_key('page'):
            options['page'] = int(kw.pop('page'))
        else:
            options['page'] = 1
        
        if not options['page'] > 0:
            options['page'] = 1
        options['perpage'] = 20

        #Grab the user passed from url
        user = BQUser.query.filter(BQUser.user_name == username).first()
        
        #If we got a handle on the user
        if user:
            #Find all his images
            results = session.query(Image).filter(Image.owner_id == user.id).all()
        else:
            flash('No user was found with name of ' + username + '. Perhaps something odd happened?')
            redirect(url('/admin/error'))
        options['totalimages'] = len(results)
    
        #Calculate paging ranges
        myrange = range(0, len(results), options['perpage'])
        
        #Bounds checking
        if options['page'] <= len(myrange):
            x = myrange[options['page']-1]
            images = results[x:x+options['perpage']]
        else:
            images = []

        return dict(user=user, images=images, query=None, wpublic =kw.pop('wpublic', not bq.core.identity.not_anonymous()), search=None, analysis = None, options = options)

    @expose ()
    def deleteimage(self, imageid=None, **kw):
        log.debug("image: " + str(imageid) )
        image = session.query(Image).filter(Image.id == imageid).first()
        session.delete(image)
        session.flush()
        redirect(request.headers.get("Referer", "/"))

    @expose ('bq.client_service.templates.admin.confirmdeleteuser')
    def confirmdeleteuser(self, username=None, **kw):
        flash("Caution. You are deleting " + username + " from the system. All of their images will also be deleted. Are you sure you want to continue?")
        return dict(username = username, query=None, wpublic=None, search=None, analysis=None)
    
    @expose ()
    def deleteuser(self, username=None,  **kw):
        #session.autoflush = False


        # Remove the user from the system for most purposes, but
        # leave the id for statistics purposes.
        user = session.query(User).filter (User.display_name == username).first()
        log.debug ("Renaming internal user %s" % user)
        if user:
            user.display_name = ("(R)" + user.display_name)[:255]
            user.email_address = ("(R)" + user.email_address)[:255]
            user.user_name = ("(R)" + user.user_name)[:16]
        


        user = session.query(BQUser).filter(BQUser.user_name == username).first()
        log.debug("ADMIN: Deleting user: " + str(user) )
        # delete the access permission
        #for p in session.query(FileAcl).filter_by(user = user.user_name):
        #    log.debug ("KILL FILEACL %s" % p)
        #    session.delete(p)
        for p in session.query(TaggableAcl).filter_by(user_id=user.id):
            log.debug ("KILL ACL %s" % p)
            session.delete(p)
        session.flush()
        
        self.deleteimages(username, will_redirect=False)
        session.delete(user)

        session.flush()
        redirect('/admin/users')

    @expose ('bq.client_service.templates.admin.confirmdeleteimages')
    def confirmdeleteimages(self, username=None, **kw):
        flash("Caution. This will delete all images of " + username + " from the system. Are you sure you want to continue?")
        return dict(username = username, query=None, wpublic=None, search=None, analysis=None)

    @expose ()
    def deleteimages(self, username=None,  will_redirect=True, **kw):
        user = session.query(BQUser).filter(BQUser.user_name == username).first()
        log.debug("ADMIN: Deleting all images of: " + str(user) )
        images = session.query(Image).filter( Image.owner_id == user.id).all()
        for i in images:
            log.debug("ADMIN: Deleting image: " + str(i) )
            session.delete(i)
        if will_redirect:
            session.flush()
            redirect('/admin/users')
        return dict()
    
    @expose ()
    def adduser(self, **kw):
        user_name = unicode( kw['user_name'] )
        password = unicode( kw['user_password'] )
        email_address = unicode( kw['email'] )
        display_name = unicode( kw['display_name'] )
                                
        log.debug("ADMIN: Adding user: " + str(user_name) )
       
        user = User(user_name=user_name, password=password, email_address=email_address, display_name=display_name)
        
        session.flush()        
        redirect('/admin/users')    
    
    @expose ()
    def updateuser(self, **kw):
        user_name = unicode( kw.get('user_name', '') )
        password = unicode( kw.get('user_password', '') )
        email_address = unicode( kw.get('email', '') )
        display_name = unicode( kw.get('display_name', '') )
                                
        log.debug("ADMIN: Updating user: " + str(user_name) )
        #Grab the user passed from url
        user = BQUser.query.filter(BQUser.user_name == user_name).first()
        
        #If we haven't got a handle on the user
        if not user:
            log.debug('No user was found with name of ' + user_name + '. Perhaps something odd happened?')
            redirect(url('/admin/'))
        
        user.password = password
        user.email_address = email_address
        user.display_name = display_name

        tg_user = User.query.filter (User.user_name == user_name).first()
        if not tg_user:
            log.debug('No user was found with name of ' + user_name + '. Please check core tables?')
            redirect(url('/admin/'))

        tg_user.email_address = email_address
        tg_user.password = password
        tg_user.display_name = display_name


        log.debug("ADMIN: Updated user: " + str(user_name) )
        
        session.flush()
        #flash ('User Updated')
        #return ""
        redirect( '/admin/edituser?username='+ str(user_name) )


    @expose('bq.client_service.templates.admin.error')
    def default (*l, **kw):
        log.debug ("got " + str(l) + str(kw))
        return dict(query=None, wpublic=None, search=None, analysis=None)


def initialize(url):
    return AdminController(url)
    
        
__controller__ = AdminController
__staticdir__ = None
__model__ = None
