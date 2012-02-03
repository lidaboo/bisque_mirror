#!/usr/bin/env python
import os
import optparse 
import subprocess
import glob
import csv
import pickle
import logging
import itertools

from bq.api import BQSession
from bq.api.util import fetch_image_planes, AttrDict
from lxml.builder import E


logging.basicConfig(level=logging.DEBUG)

EXEC = "./araGT"

def gettag (el, tagname):
    for kid in el:
        if kid.get ('name') == tagname:
            return kid, kid.get('value')
    return None,None
            
class RootTip(object):

    def setup(self):
        #if not os.path.exists(self.images):
        #    os.makedirs(self.images)

        self.bq.update_mex('initializing')
        results = fetch_image_planes(self.bq, self.resource_url, '.', True) 
        

    def start(self):
        self.bq.update_mex('executing')
        # Matlab requires trailing slash
        subprocess.call([EXEC, './'])
        

    def teardown(self):
        # Post all submex for files and return xml list of results
        gobjects = self._read_results()
        tags = [{ 'name': 'outputs',
                  'tag' : [{'name': 'roots', 'type':'image', 'value':self.resource_url,
                            'gobject' : [{ 'name': 'root_tips', 'gobject' : gobjects }] }]
                  }]
        self.bq.finish_mex(tags = tags)

    def _read_results(self, ):
        results  = []
        image = self.bq.load(self.resource_url, view='full')
        xmax, ymax, zmax, tmax, ch = image.geometry()
        tips = csv.reader(open('tips.csv','rb'))
        angles = csv.reader(open('angle.csv','rb'))
        grates = csv.reader(open('gr.csv','rb'))
        for index, (tip, angle, gr)  in enumerate(itertools.izip(tips, angles, grates)):
            results.append({
                    'type' : 'tipangle',
                    'tag' : [{ 'name': 'angle', 'value': angle[0]},
                             { 'name': 'growth', 'value': gr[0]}, ],
                    'point' : { 
                        'vertex' : [ { 'x': str(xmax - int(tip[1])), 'y':tip[0], 't':index } ] ,
                        }
                    })
        return results



    def run(self):
        parser  = optparse.OptionParser()
        parser.add_option('-d','--debug', action="store_true")
        parser.add_option('-n','--dryrun', action="store_true")
        parser.add_option('--credentials')
        parser.add_option('--image_url')

        (options, args) = parser.parse_args()
        named = AttrDict (bisque_token=None, mex_url=None, staging_path=None)
        for arg in reversed(args):
            tag, sep, val = arg.partition('=')
            if sep != '=':
                break
            named[tag] = val

        if named.bisque_token:
            self.bq = BQSession().init_mex(named.mex_url, named.bisque_token)
            self.resource_url =  named.image_url
        elif options.credentials:
            user,pwd = options.credentials.split(':')
            self.bq = BQSession().init_local(user,pwd)
            self.resource_url =  options.image_url
        else:
            parser.error('need bisque_token or user credential')

        if self.resource_url is None:
            parser.error('Need a resource_url')



        self.setup()
        self.start()
        self.teardown()
        #command = args.pop(0)

        #if command not in ('setup','teardown', 'start'):
        #    parser.error('Command must be start, setup or teardown')

        # maltab code requires trailing slash..
        #self.images = os.path.join(options.staging_path, 'images') + os.sep
        #self.image_map_name = os.path.join(options.staging_path, IMAGE_MAP)
        #self.resource_url = options.resource_url
        #self.config = options
        #self.is_dataset = 'dataset' in self.resource_url

            
        #command = getattr(self, command)
        #command()

        



if __name__ == "__main__":
    RootTip().run()
    
