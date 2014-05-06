import os
import shutil
import urllib
import poster
import time

from lxml import etree as ET
from xmldict import xml2d, d2xml
from bqclass import fromXml, toXml, BQMex


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError

    def __setattr__(self, name, value):
        self[name] = value
        return value

    def __getstate__(self):
        return self.items()

    def __setstate__(self, items):
        for key, val in items:
            self[key] = val


def safecopy (*largs):
    largs = list (largs)
    d = largs.pop()

    for f in largs:
        try:
            dest = d
            if os.path.isdir (d):
                dest = os.path.join (d, os.path.basename(f))
            print ("linking %s to %s"%(f,dest))
            if os.path.exists(dest):
                print ("Found existing file %s: removing .." % dest)
                os.unlink (dest)
            os.link(f, dest)
        except (OSError, AttributeError), e:
            print ("Problem in link %s .. trying copy" % e)
            shutil.copy2(f, dest)

def parse_qs(query):
    'parse a uri query string into a dict'
    pd = {}
    if '&' in query:
        for el in query.split('&'):
            nm, junk, vl = el.partition('=')
            pd.setdefault(nm, []).append(vl)
    return pd

def make_qs(pd):
    'convert back from dict to qs'
    query = []
    for k,vl in pd.items():
        for v in vl:
            pair = v and "%s=%s" % (k,v) or k
            query.append(pair)
    return "&".join(query)


def save_blob(session,  localfile, resource=None):
    """put a local image on the server and return the URL
    to the METADATA XML record

    @param session: the local session
    @param image: an BQImage object
    @param localfile:  a file-like object or name of a localfile
    @return XML content  when upload ok
    """
    url = session.service_url('import', 'transfer')
    if isinstance(localfile, basestring):
        localfile = open(localfile,'rb')

    with localfile:
        fields = { 'file' : localfile}
        if resource is not None:
            fields['file_resource'] = ET.tostring (resource)
        body, headers = poster.encode.multipart_encode(fields)
        content = session.c.post(url, headers=headers, content=body)
        try:
            rl = ET.XML (content)
            return rl[0]
        except ET.ParseError,e :
            pass

        return None


def fetch_blob(session, uri, dest=None, uselocalpath=False):
    """fetch original image locally as tif
    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server
    """
    image = session.load (uri)
    name = image.name or next_name ("blob")

    query = None
    if uselocalpath:
        # Skip 'file:'
        path = image.value
        if path.startswith('file:') :
            path =  path[5:]
        return { uri: path }

    uniq = image.get ('resource_uniq')
    url = session.service_url('blob_service', path = uniq,  )
    blobdata = session.c.fetch (url)
    if os.path.isdir(dest):
        outdest = os.path.join (dest, os.path.basename(name))
    else:
        outdest = os.path.join ('.', os.path.basename(name))
    f = open(outdest, 'wb')
    f.write(blobdata)
    f.close()
    return { uri : outdest }


def fetch_image_planes(session, uri, dest, uselocalpath=False):
    """fetch all the image planes of an image locally
    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server

    """
    image = session.load (uri, view='full')
    #x,y,z,t,ch = image.geometry()
    meta = image.pixels().meta().fetch()
    meta = ET.XML(meta)
    t  = meta.xpath('//tag[@name="image_num_t"]')
    t  = len(t) and t[0].get('value')
    z  = meta.xpath('//tag[@name="image_num_z"]')
    z  = len(z) and z[0].get('value')
    tplanes = int(t)
    zplanes = int(z)

    planes=[]
    for t in range(tplanes):
        for z in range(zplanes):
            ip = image.pixels().slice(z=z+1,t=t+1).format('tiff')
            if uselocalpath:
                ip = ip.localpath()
            planes.append (ip)

    files = []
    for i, p in enumerate(planes):
        slize = p.fetch()
        fname = os.path.join (dest, "%.5d.TIF" % i)
        if uselocalpath:
            path = ET.XML(slize).xpath('/resource/@src')[0]
            # Strip file:/ from path
            safecopy (path[5:], fname)
        else:
            f = open(fname, 'wb')
            f.write(slize)
            f.close()
        files.append(fname)

    return files


def next_name (name):
    count = 0
    while os.path.exists("%s-%.5d.TIF" % (name, count)):
        count = count + 1
    return "%s-%.5d.TIF" % (name, count)



def fetch_image_pixels(session, uri, dest, uselocalpath=False):
    """fetch original image locally as tif
    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server
    """
    image = session.load (uri)
    name = image.name or next_name ("image")
    ip = image.pixels().format('tiff')
    if uselocalpath:
        ip = ip.localpath()
    pixels = ip.fetch()
    if os.path.isdir(dest):
        dest = os.path.join (dest, os.path.basename(name))
    else:
        dest = os.path.join ('.', os.path.basename(name))


    if uselocalpath:
        path = ET.XML(pixels).xpath('/resource/@src')[0]
        #path = urllib.url2pathname(path[5:])
        path = path[5:]
        # Skip 'file:'
        safecopy (path, dest)
        return { uri : dest }
    f = open(dest, 'wb')
    f.write(pixels)
    f.close()
    return { uri : dest }


def fetch_dataset(session, uri, dest, uselocalpath=False):
    """fetch elemens of dataset locally as tif
    @param session: the bqsession
    @param uri: resource image uri
    @param dest: a destination directory
    @param uselocalpath: true when routine is run on same host as server
    """
    dataset = session.fetchxml (uri, view='deep')
    members = dataset.xpath('//value[@type="object"]')

    results = { }
    for i, imgxml in enumerate(members):
        uri =  imgxml.text   #imgxml.get('uri')
        print "FETCHING", uri
        #fname = os.path.join (dest, "%.5d.tif" % i)
        x = fetch_image_pixels (session, uri,
                            dest, uselocalpath=uselocalpath)
        results.update (x)
    return results


def fetchImage(session, uri, dest, uselocalpath=False):

    image = session.load(uri).pixels().getInfo()
    fileName = ET.XML(image.fetch()).xpath('//tag[@name="filename"]/@value')[0]

    ip = session.load(uri).pixels().format('tiff')

    if uselocalpath:
        ip = ip.localpath()

    pixels = ip.fetch()

    if os.path.isdir(dest):
        dest = os.path.join (dest, fileName)

    if uselocalpath:
        path = ET.XML(pixels).xpath('/resource/@src')[0]
        #path = urllib.url2pathname(path[5:])
        path = path[5:]

        # Skip 'file:'
        safecopy (path, dest)
        return { uri : dest }
    f = open(dest, 'wb')
    f.write(pixels)
    f.close()
    return { uri : dest }


def fetchDataset(session, uri, dest, uselocalpath=False):
    dataset = session.fetchxml(uri, view='deep')
    members = dataset.xpath('//value[@type="object"]')
    results = {}

    for i, imgxml in enumerate(members):
        uri = imgxml.text
        print "FETCHING: ", uri
        #fname = os.path.join (dest, "%.5d.tif" % i)
        result = fetchImage(session, uri, dest, uselocalpath=uselocalpath)
        results[uri] = result[uri]
    return results


# Post fields and files to an http host as multipart/form-data.
# fields is a sequence of (name, value) elements for regular form
# fields.  files is a sequence of (name, filename, value) elements
# for data to be uploaded as files
# Return the tuple (rsponse headers, server's response page)

# example:
#   post_files ('http://..',
#   fields = {'file1': open('file.jpg','rb'), 'name':'file' })
#   post_files ('http://..', fields = [('file1', 'file.jpg', buffer), ('f1', 'v1' )] )

def save_image_pixels(session,  localfile, image_tags=None):
    """put a local image on the server and return the URL
    to the METADATA XML record

    @param session: the local session
    @param image: an BQImage object
    @param localfile:  a file-like object or name of a localfile
    @return XML content  when upload ok
    """

    content = None
    url = session.service_url('import', 'transfer')
    if isinstance(localfile, basestring):
        with open(localfile,'rb') as f:
            fields = { 'file' : f }
            if image_tags:
                fields['file_tags'] = ET.tostring(toXml(image_tags))
            body, headers = poster.encode.multipart_encode(fields)
            content = session.c.post(url, headers=headers, content=body)
    return content


def as_flat_dict_tag_value(xmltree):
    def _xml2d(e, d, path=''):
        for child in e:
            name  = '%s%s'%(path, child.get('name', ''))
            value = child.get('value', None)
            if value is not None:
                if not name in d:
                    d[name] = value
                else:
                    if isinstance(d[name], list):
                        d[name].append(value)
                    else:
                        d[name] = [d[name], value]
            d = _xml2d(child, d, path='%s%s/'%(path, child.get('name', '')))
        return d

    return _xml2d(xmltree, {})

def as_flat_dicts_node(xmltree):
    def _xml2d(e, d, path=''):
        for child in e:
            name  = '%s%s'%(path, child.get('name', ''))
            #value = child.get('value', None)
            value = child
            #if value is not None:
            if not name in d:
                d[name] = value
            else:
                if isinstance(d[name], list):
                    d[name].append(value)
                else:
                    d[name] = [d[name], value]
            d = _xml2d(child, d, path='%s%s/'%(path, child.get('name', '')))
        return d

    return _xml2d(xmltree, {})
