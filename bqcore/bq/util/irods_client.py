import os
import re
import urlparse
import shutil
import atexit
import logging
import irods
import posixpath

import subprocess
import urllib

from bq.util.mkdir import _mkdir
from bq.util.paths import data_path

from irods.exception import (DataObjectDoesNotExist, CollectionDoesNotExist)
from irods.session import iRODSSession
IRODS_CACHE = data_path('irods_cache')

CONNECTION_POOL = {}


class IrodsError(Exception):
    pass

log = logging.getLogger('bq.irods')
log.setLevel (logging.DEBUG)

parse_net = re.compile('^((?P<user>[^:]+):(?P<password>[\w.#^!;]+)?@)?(?P<host>[^:]+)(?P<port>:\d+)?')

if not os.path.exists(IRODS_CACHE):
    _mkdir (IRODS_CACHE)

class IrodsConnection():
    def __init__(self, url, user=None, host=None, port=None, password = None, zone=None):
        irods_url = urlparse.urlparse(url)
        assert irods_url.scheme == 'irods'
        env = parse_net.match(irods_url.netloc).groupdict()
        args = dict(
            user = user or env['user'], #or irods_env.getRodsUserName()
            host  = host or env['host'], #or irods_env.getRodsHost()
            port  = port or env['port'] or 1247, #or irods_env.getRodsPort() or 1247
            zone = zone or 'iplant',
            password = password or env['password'])

        log.debug ("irods_connection env %s ->%s" , env, args)

        path = ''
        zone = ''
        if irods_url.path:
            path = urllib.unquote(irods_url.path).split('/')
            if len(path):
                zone = path[1]
            path = '/'.join(path)

        self.irods_url = irods_url
        self.path = path
        self.zone = zone

        # Ensure all parameters are not None
        if not all (args.values()):
            raise IrodsError("missing parameter %s", ",".join ( k for k,v in args.items() if v is None))

        self.session = iRODSSession(**args)

    def open(self):
        pass
        #conn, err = irods.rcConnect(self.host, self.port, self.user, self.zone)
        #if conn is None:
        #    raise IrodsError("Can't create connection to %s " % self.host)
        #if self.password:
        #    irods.clientLoginWithPassword(conn, self.password)
        #else:
        #    irods.clientLogin(conn)

        #coll = self.session.collections.get (
        #nm = coll.getCollName()

        #self.irods_url = urlparse.urlunparse(list(self.irods_url)[:2] + ['']*4)
        #if self.path in ['', '/']:
        #    self.path = nm

        #self.conn = conn
        #self.base_dir = nm
        #return self

    def close(self):
        if self.session:
            self.session.cleanup()
        self.session = None

    def __enter__(self):
        if self.session is None:
            self.open()
        return self

    def __exit__(self, ty, val, tb):
        self.close()
        return False


BLOCK_SZ=512*1024
def copyfile(f1, *dest):
    'copy a file to multiple destinations'
    while True:
        buf = f1.read(BLOCK_SZ)
        if not buf:
            break
        for fw in dest:
            fw.write(buf)
        if len(buf) < BLOCK_SZ:
            break
#####################
# iRods CACHE
def irods_cache_name(path):
    cache_filename = os.path.join(IRODS_CACHE, path[1:])
    return cache_filename
def irods_cache_fetch(path):
    cache_filename = os.path.join(IRODS_CACHE, path[1:])
    if os.path.exists(cache_filename):
        return cache_filename
    return None

def irods_cache_save(f, path, *dest):
    cache_filename = os.path.join(IRODS_CACHE, path[1:])
    _mkdir(os.path.dirname(cache_filename))
    with open(cache_filename, 'wb') as fw:
        copyfile(f, fw, *dest)

    return cache_filename

def irods_fetch_file(url, **kw):
    try:
        ic = IrodsConnection(url, **kw)
        log.debug( "irods_fetching %s -> %s" , url, ic.path)
        localname = irods_cache_fetch(ic.path)
        if localname is None:
            obj = ic.session.data_objects.get (ic.path)
            with obj.open ('r') as f:
                localname = irods_cache_save(f, ic.path)
        return localname
    except IrodsError:
        raise
    except Exception, e:
        log.exception ("fetch of %s", url)
        raise IrodsError("can't read irods url %s" % url)


def irods_push_file(fileobj, url, savelocal=True, **kw):
    try:
        with IrodsConnection(url, **kw) as ic:
            # Hmm .. if an irodsEnv exists then it is used over our login name provided above,
            # meaning even though we have logged in as user X we may be the homedir of user Y (in .irodsEnv)
            # irods.mkCollR(conn, basedir, os.path.dirname(path))
            #retcode = irods.mkCollR(ic.conn, '/', os.path.dirname(ic.path))
            #ic.makedirs (os.path.dirname (ic.path))
            compdirs = posixpath.dirname(ic.path).split ('/')
            for pos in range(3, len (compdirs)+1):
                try:
                    coll = ic.session.collections.get ("/".join(compdirs[:pos]))
                except CollectionDoesNotExist:
                    break
            if pos < len(compdirs):
                for  pos in range (pos,  len(compdirs)+1):
                    coll = ic.session.collections.create ("/".join(compdirs[:pos]))

            log.debug( "irods-path %s" %  ic.path)
            obj = ic.session.data_objects.create (ic.path)
            with obj.open('w') as f:
                localname = irods_cache_save(fileobj, ic.path, f)
            return localname
    except IrodsError:
        raise
    except Exception, e:
        log.exception ("during push %s", url)
        raise IrodsError("can't write irods url %s" % url)

def irods_delete_file(url, **kw):
    try:
        with IrodsConnection(url, **kw) as ic:
            log.debug( "irods-path %s" %  ic.path)
            localname = irods_cache_fetch(ic.path)
            if localname is not None:
                os.remove (localname)
            log.debug( "irods_delete %s -> %s" % (url, ic.path))
            ic.session.data_objects.unlink (ic.path)
    except IrodsError:
        raise
    except Exception, e:
        log.exception ("during delete %s", url)
        raise IrodsError("can't delete %s" % url)

def irods_isfile (url, **kw):
    try:
        with IrodsConnection(url, **kw) as ic:
            log.debug( "irods_isfile %s -> %s" % (url, ic.path))
            obj = ic.session.data_objects.get (ic.path)
            return hasattr (obj, 'path')
    except DataObjectDoesNotExist:
        pass
    except IrodsError:
        raise
    except Exception:
        log.exception ("isfile %s", url)
    return False

def irods_isdir (url, **kw):
    try:
        with IrodsConnection(url, **kw) as ic:
            ic.session.collections.get (ic.path)
            return True
    except CollectionDoesNotExist:
        pass
    except IrodsError:
        raise
    except Exception:
        log.exception("isdir %s", url)
    return False


def irods_fetch_dir(url, **kw):
    try:
        result = []
        with IrodsConnection(url, **kw) as ic:
            coll = ic.session.collections.get (ic.path)
            for nm in coll.subcollections:
                result.append('/'.join([ic.base_url, ic.path[1:], nm, '']))

            for nm, resource in  coll.data_objects:
                result.append( '/'.join([ic.base_url, ic.path[1:], nm]))
        return result
    except Exception:
        log.exception ('fetch_dir %s', url)
        return result