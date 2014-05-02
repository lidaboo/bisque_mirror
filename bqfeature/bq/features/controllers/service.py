# -*- mode: python -*-
"""Main server for features
"""

__author__ = "Dmitry Fedorov, Kris Kvilekval, Carlos Torres and Chris Wheat"
__copyright__ = "Center for BioImage Informatics, University California, Santa Barbara"

import os
import logging
import pkg_resources
import tables
from PytablesMonkeyPatch import pytables_fix
import inspect
import pkgutil
import importlib
import uuid
import urllib2
import hashlib
import ntpath
from lxml import etree


from paste.fileapp import FileApp
from pylons.controllers.util import forward
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from pylons.controllers.util import abort
from tg import expose, flash, config, response, request

from bq.core.service import ServiceController
from bq.util.paths import data_path
from bq import data_service
from bq.image_service.controllers.locks import Locks
from bq.util.mkdir import _mkdir

from bq.features.controllers.ID import ID
from bq.features.controllers.Feature import BaseFeature, mex_validation
from bq.features.controllers.TablesInterface import Rows, IDRows, WorkDirRows, Tables, IDTables, WorkDirTable
from exceptions import FeatureServiceError,FeatureExtractionError
from .var import FEATURES_TABLES_FILE_DIR, FEATURES_TEMP_IMAGE_DIR, EXTRACTOR_DIR, FEATURES_TABLES_WORK_DIR, FEATURES_REQUEST_ERRORS_DIR

log = logging.getLogger("bq.features")


class Feature_Archive(dict):
    """
        List of included descriptors:
        SURF, ORB, SIFT, HTD, EHD, CLD, CSD, SCD, DCD
        FREAK, BRISK, TAS, PFTAS, ZM, HAR, ShCoD, FFTSD
        RSD, many more...
    """
    def __init__(self):
        """
            Looks into extractors/feature_module for extractor. Once found 
            it will import the library and parse the module for all classes
            inheriting FeatureBase
        """
        extractors = [name for module_loader, name, ispkg in pkgutil.iter_modules([EXTRACTOR_DIR]) if ispkg]
        for module in extractors:
            try:
                extractor = importlib.import_module('bq.features.controllers.extractors.' + module + '.extractor')  # the module needs to have a file named
                for n, item in inspect.getmembers(extractor):  # extractor.py to import correctly
                    if inspect.isclass(item) and issubclass(item, BaseFeature):
                        log.debug('Imported Feature: %s' % item.name)
                        item.library = module #for the list of features
                        self[item.name] = item
            except StandardError, err:  # need to pick a narrower error band but not quite sure right now
                log.exception('Failed Imported Feature: %s\n' % module)  # failed to import feature


FEATURE_ARCHIVE = Feature_Archive()


###############################################################
# Features Inputs
###############################################################

class ResourceList(object):
    """
        list of all unique elements and their hashes
        sorted by hashes
    """

    def __init__(self, feature_request_uri, feature_name, format_name , **kw):
        self.uri_hash_list = []  #list of the resource uris hashed
        self.error_hash_list = [] #list of hashes of all the lists
        self.element_dict = {} #a dictionary with keys as the hash of the resource uris and values as elements
        self.error_list = []

        try:
            self.format = FORMAT_DICT[format_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Format: %s  was not found'%format_name)

        try:
            self.feature = FEATURE_ARCHIVE[feature_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Feature: %s requested was not found'%feature_name)
            
        self.feature_request_uri = feature_request_uri
        
        if 'options' in kw:
            self.options=kw['options']
        else:
            self.options = {}
    
    def workdir_filename(self):
        """
            Returns resource name for the workdir which is an ordered
            list of all the element hashes 
        """
        return os.path.join(FEATURES_TABLES_WORK_DIR,self.feature.name, self.hash())     
    
    def hash(self):
        """
            Hashes the list of hashed ordered elements
        """
        hash = hashlib.md5()
        full_uri_hash_list = []
        full_uri_hash_list += self.uri_hash_list
        #full_uri_hash_list += self.error_hash_list
        full_uri_hash_list.sort()
        for e in full_uri_hash_list:
            hash.update(e)    
        return hash.hexdigest()

    def append(self, input_dict):
        """
            appends to element lists and orders the list by hash
            on the first append the types are checked

            @input_dict : dictionary where the keys are the input types and the values are the uris
        """
        # checking type
        if not self.uri_hash_list:  # check on the first entry
            input_dict, self.feature_name = input_resource_check(input_dict , self.feature.name)  # separates options from resources
            self.feature = FEATURE_ARCHIVE[self.feature_name]  # reassign new feature
        else:  # check if the types match the original feature
            input_dict, new_feature_name = input_resource_check(input_dict , self.feature.name)  # separates options from resources
            if new_feature_name != self.feature_name:
                log.debug('Argument Error: types are not consistance')
                raise FeatureServiceError(400, 'Argument Error: types are not consistance')

        #check if user has access to resource
        if mex_validation(**input_dict):
            uri_hash = self.feature().returnhash(**input_dict)
            if uri_hash not in self.element_dict:
                self.element_dict[uri_hash] = input_dict
                self.uri_hash_list.append(uri_hash)
                self.uri_hash_list.sort()
                
        #add it to a list of element with errors
        else:
            self.error_list.append(FeatureExtractionError(input_dict, 403, 'User is not authorized to read resource internally: %s'%input_dict))
            
        return  # returns options

    def remove(self, input_dict, exc):
        """
            Removes the given element from the uri hash list and the element dictionary 
            and place them in the error list
        """
        uri_hash = self.feature().returnhash(**input_dict)
        del self.element_dict[uri_hash]
        self.uri_hash_list.remove(uri_hash)
        self.error_hash_list.append(uri_hash)
        self.error_list.append(exc)
        

    def get(self,hash):
        """ get with hash name, if it doesnt find anything it returns nothing"""
        if hash in self.element_dict:
            return (hash, self.element_dict[hash])
        else:
            return

    def __getitem__(self, index):
        """ get with index, the list is always ordered """
        return (self.uri_hash_list[index], self.element_dict[self.uri_hash_list[index]])

    def __len__(self):
        return len(self.uri_hash_list)
    
    def __iter__(self): 
        #TODO: make a better iter function
        return iter(self.uri_hash_list)
    
    def error_list(self):
        return error_list


def input_resource_check( resources, feature_name):
    """
        Checks resource type of the input to make sure
        the correct resources have been used, if it can
        find an alternative feature with those inputs
        it will output the name of the new suggested feature
    """
    resource = {}
    feature = FEATURE_ARCHIVE[feature_name]
    if sorted(resources.keys()) == sorted(feature.resource):
        feature_name = feature.name
    else:
        for cf in feature.child_feature:
            if sorted(resources.keys()) == sorted(FEATURE_ARCHIVE[cf].resource):
                log.debug('Reassigning from %s to %s'%(feature_name,cf))
                feature_name = cf
                feature = FEATURE_ARCHIVE[feature_name]
                break
        else:
            log.debug('Excepted Feature Resource: %s'%str(feature.resource))
            log.debug('Input Resource: %s'%str(resources.keys()))
            log.debug('Argument Error: No resource type(s) that matched the feature')
            raise FeatureServiceError(400, 'Argument Error: No resource type(s) that match the feature')

    for resource_name in resources.keys():

        if resource_name not in feature.resource:

            log.debug('Argument Error: %s type was not found'%resource_name)
            raise FeatureServiceError(400, 'Argument Error: %s type was not found'%resource_name)

        elif type(resources[resource_name]) == list: #to take care of when elements have more then uri attached. not allowed in the features
              #server for now

            log.debug('Argument Error: %s type was found to have more then one URI'%resource_name)
            raise FeatureServiceError(400,'Argument Error: %s type was found to have more then one URI'%resource_name)
        else:

            resource[resource_name] = urllib2.unquote(resources[resource_name]) #decode url

    return resource ,feature_name


def parse_request(feature_request_uri, feature_name, format_name='xml', method='GET', **kw):
    """
        Parses request and returns a ResourceList
    """
    options = { #nothing in options works 
#                   'callback': None,
#                   'limit'   : None,
#                   # 'store'   : False,
#                   'recalc'  : False,
                }

    # check kw arg values
    for i in kw.keys():
        if i in options: 
            options[i] = kw[i]
            del kw[i] #removes options from the kw list to not interfere with error checking when reading in the resources
                      #kw is a dictionary where the keys are the input types and the values are the uris
    
    resource_list = ResourceList( feature_request_uri, feature_name, format_name, options=options )

    # validating request
    if method == 'POST' and 1 > request.headers['Content-type'].count('xml/text'):
        if not request.body:
            raise FeatureServiceError( 400, 'Document Error: No body attached to the POST')
        try:  # parse the resquest
            log.debug('request :%s' % request.body)
            body = etree.fromstring(request.body)
            if body.tag != 'dataset':
                raise FeatureServiceError( 400, 'Document Error: Only excepts datasets')


            # iterating through elements in the dataset parsing and adding to ElementList
            for value in body.xpath('value[@type="query"]'):
                query = value.text
                query = query.decode("utf8")
                log.debug('query: %s' % query)
                query = query.split('&')
                element = {}
                
                for q in query:
                    q = q.split('=')
                    element[q[0]] = q[1].replace('"', '')

                log.debug('Resource: %s' % element)
                resource_list.append(element)
        except:
            log.exception('Request Error: Xml document is malformed')
            raise FeatureServiceError(400, 'Xml document is malformed')

    elif method == 'GET':
        kw = resource_list.append(kw) #kw is a dictionary where the keys are the input types and the values are the uris
        
    else:
        log.debug('Request Error: http request was not formed correctly')
        raise FeatureServiceError(400, 'http request was not formed correctly')

    return resource_list


def operations(resource_list):
    """
        calculates features and stores them in the tables
    """
    # check work dir for the output
    workdir_filename = resource_list.workdir_filename()
    
    #initalizes workdir dir if it doesnt exist
    feature_workdir = os.path.join(FEATURES_TABLES_WORK_DIR, resource_list.feature.name)
    if not os.path.exists(feature_workdir):
        _mkdir(feature_workdir)
    
    #checking for cached output in the workdir, if not found starts to calculate features
    if not os.path.exists(workdir_filename):
        if resource_list.feature.cache: #checks if the feature caches

            # finding if features are in the tables
            feature_table = Tables(resource_list.feature())
            feature_rows = Rows(resource_list.feature())
            
            element_list_in_table = []
            for i, uri_hash in enumerate(resource_list):
                if feature_table.find(uri_hash):
                    log.debug("Returning Resource: %s from the feature table"%resource_list.element_dict[uri_hash])

                else:
                    log.debug("Resource: %s was not found in the feature table"%resource_list.element_dict[uri_hash])
                    resource_uris_dict = resource_list.get(uri_hash)[1]
                    
                    #checks to see if the feature calculation succeeded, if error
                    #then the resource is removed from the element list
                    try:
                        feature_rows.push(**resource_uris_dict)
                    except FeatureExtractionError as feature_extractor_error: #if error occured the element is moved for the resource list to the error list
                        resource_list.remove(resource_uris_dict,feature_extractor_error)
                        log.debug('Exception: Error Code %s : Error Message %s'%(resource_list.error_list[-1].code,resource_list.error_list[-1].message))

            # store features
            feature_table.store(feature_rows)

            # store in id table after just in case some features fail so their ids are not stored
            hash_table = IDTables()
            hash_row = IDRows(resource_list.feature())
            
            # finding hashes
            element_list_in_table = []
            for i, uri_hash in enumerate(resource_list):
                if hash_table.find(uri_hash):
                    log.debug("Returning Resource: %s from the uri table"%resource_list.element_dict[uri_hash])
                    
                else:
                    log.debug("Resource: %s was not found in the uri table"%resource_list.element_dict[uri_hash])
                    hash_row.push(**resource_list.get(uri_hash)[1])

            # store hashes
            hash_table.store(hash_row)

        else: #creating table for uncached features in the work dir
            log.debug('Calculating on uncached feature')

            if len(resource_list)>0: #if list is empty no table is created
                workdir_feature_table = WorkDirTable(resource_list.feature())


                # store features in an unindexed table in the workdir
                uncached_feature_rows = WorkDirRows(resource_list.feature())

                for i, uri_hash in enumerate(resource_list):
                    # pushes to the table list unless feature failed to be calculated
                    # then the element is removed from the element list
                    resource_uris_dict = resource_list.get(uri_hash)[1]
                    try:
                        uncached_feature_rows.push(**resource_uris_dict)
                    except FeatureExtractionError as feature_extractor_error: #if error occured the element is moved for the resource list to the error list
                        resource_list.remove(resource_uris_dict,feature_extractor_error)
                
                workdir_filename = resource_list.workdir_filename() #just in case some features failed
                workdir_feature_table.store(uncached_feature_rows, workdir_filename)
    else:
        log.debug('Getting request from the workdir at: %s'% workdir_filename)


def format_response(resource_list):
    """
        reads features from the tables and froms a response
    """
    workdir_filename = resource_list.workdir_filename()
    feature_init = resource_list.feature()
    request_uri = resource_list.feature_request_uri
    
    if resource_list.feature.cache and not os.path.exists(workdir_filename):  # queries for results in the feature tables

        feature_table = Tables( feature_init)
        format = resource_list.format( feature_init, request_uri)
        header = format.return_header( feature_table, resource_list)
        body = format.return_from_tables( feature_table, resource_list)
        return header, body

    else:  #returns unindexed table from the workdir

        uncached_feature_table = WorkDirTable( feature_init)
        format = resource_list.format( feature_init, request_uri)
        header = format.return_header( uncached_feature_table, resource_list)
        body = format.return_from_workdir( uncached_feature_table, resource_list)
        return header, body




###############################################################
# Features Outputs
###############################################################

class Format(object):
    """
        Base Class of formats for output
    """
    name = 'Format'
    #limit = 'Unlimited'
    description = 'Discription of the Format'
    content_type = 'text/xml'

    def __init__(self, feature, feature_request_uri, **kw):
        self.feature = feature
        self.feature_request_uri = feature_request_uri

    def return_header(self, table, resource_list, **kw):
        header = {'content-type': self.content_type}   
        return header

    def return_from_tables(self, table, resource_list, **kw):
        pass

    def return_from_workdir(self, table, resource_list, **kw):
        pass


#-------------------------------------------------------------
# Formatters - XML
# MIME types:
#   text/xml
#-------------------------------------------------------------
class Xml(Format):
    """
        returns in xml
    """
    name = 'XML'
    #limit = 1000  # nodes
    description = 'Extensible Markup Language'
    content_type = 'text/xml'

        
    def return_from_tables(self, table, resource_list, **kw):
        """Drafts the xml output"""
        
        #element = etree.Element('resource', uri=str(self.feature_request_uri))
        #element = etree.Element('resource')
        nodes = 0
        xml_doc = '<resource uri = "%s">'%str(self.feature_request_uri.replace('&','&amp;'))
        yield xml_doc

        for i, uri_hash in enumerate(resource_list):
            rows = table.get(uri_hash)
            if rows != None:  # a feature was found for the query
                resource = resource_list[i][1]

                for r in rows:
                    subelement = etree.Element( 'feature' , resource , type=str(self.feature.name))

                    if self.feature.parameter:
                        parameters = {}
                        # creates list of parameters to append to the xml
                        for parameter_name in self.feature.parameter:
                            parameters[parameter_name] = str(r[parameter_name])
                        etree.SubElement(subelement, 'parameters', parameters)

                    value = etree.SubElement(subelement, 'value')
                    value.text = " ".join('%g' % item for item in r['feature'])  # writes the feature vector to the xml
                    nodes += 1

                    xml_doc = etree.tostring(subelement)
                    yield xml_doc

            else:  # no feature was found from the query, adds an error message to the xml
                subelement = etree.Element(
                                                  'feature' ,
                                                  resource,
                                                  error_code = '404',
                                                  type=str(self.feature.name),
                                                  error='404 Not Found: The feature was not found in the table. Check feature logs for traceback'
                                           )
                xml_doc = etree.tostring(subelement)
                yield xml_doc
                
                
        #read through errors
        for i, error in enumerate(resource_list.error_list):
            subelement = etree.Element(
                                              'feature_error' ,
                                              error.resource,
                                              error_code = str(error.code),
                                              type=str(self.feature.name),
                                              error=error.message
                                          )
            xml_doc = etree.tostring(subelement)
            yield xml_doc
        xml_doc = '</resource>'
        yield xml_doc

    # not working
    def return_from_workdir(self, table, resource_list, **kw):
        """Drafts the xml output for uncached tables"""
        
        filename = resource_list.workdir_filename()
        
        yield '<resource uri = "%s">'%str(self.feature_request_uri.replace('&','&amp;'))
        
        
        
        with Locks(filename):
            log.debug('Reading from table path: %s'%filename)
            with tables.openFile(filename, 'r') as h5file:
            
                Table = h5file.root.values
    
                # reads through each line in the table and writes an xml node for it
                for i, r in enumerate(Table):
                    resource = {}  # creating a resource dictionary to story all the uris
                    for res in self.feature.resource:
                        resource[res] = r[res]
    
                    subelement = etree.Element( 'feature' , resource, type=str(self.feature.name))
    
                    if self.feature.parameter:
                        parameters = {}
    
                        # creates list of parameters to append to the xml node
                        for parameter_name in self.feature.parameter:
                            parameters[parameter_name] = str(r[parameter_name])
                        etree.SubElement(subelement, 'parameters', parameters)
    
                    value = etree.SubElement(subelement, 'value')
                    value.text = " ".join('%g' % item for item in r['feature'])  # writes the feature vector to the xml
                    
                    yield etree.tostring(subelement)


        for i, error in enumerate(resource_list.error_list):
            subelement = etree.Element(
                                              'feature_error' ,
                                              error.resource,
                                              error_code = str(error.code),
                                              type=str(self.feature.name),
                                              error=error.message
            )
            yield etree.tostring(subelement)

        yield '</resource>'

#-------------------------------------------------------------
# Formatters - CSV
# MIME types:
#   text/csv
#   text/comma-separated-values
#-------------------------------------------------------------
class Csv(Format):
    """
        returns in csv
    """
    name = 'CSV'
    description = 'Returns csv file format with columns as resource ... | feature | feature attributes...'
    content_type = 'text/csv'

    def return_header(self, table, resource_list, **kw):
        # creating a file name
        filename = 'feature.csv'  # think of how to name the files
        try:
            disposition = 'filename="%s"' % filename.encode('ascii')
        except UnicodeEncodeError:
            disposition = 'attachment; filename="%s"; filename*="%s"' % (filename.encode('utf8'), filename.encode('utf8'))

        
        header = {
                  'content-type': self.content_type,
                  'Content-Disposition':disposition
                  }
 
        return header

    def return_from_tables(self, table, resource_list, **kw):
        """Drafts the csv output"""
        # # plan to impliment for query and include parameters

        resource_names = self.feature.resource
        parameter_names = self.feature.parameter

        # creates a title row and writes it to the document
        titles = ",".join(['index', 'feature type'] + resource_names + ['descriptor'] + parameter_names + ['response code','error message'])
        yield titles+'\n'

        idx = 0
        for i, uri_hash in enumerate(resource_list.uri_hash_list):

            resource = resource_list[i][1]

            rows = table.get(uri_hash)
            
            if rows != None:  # check to see if nothing is return from the tables

                for r in rows:
                    value_string = ",".join('%g' % i for i in r['feature'])  # parses the table output and returns a string of the vector separated by commas
                    resource_uri = [resource[rn] for rn in resource_names]
                    parameter = []
                    parameter = ['%g'%r[pn] for pn in parameter_names]
                    line = ",".join([str(idx), self.feature.name] + resource_uri + ['"'+value_string+'"'] + parameter + ['200','none'])
                    yield line+'\n'
                    idx+=1

            else:  # if nothing is return from the tables enter Nan into each vector element
                value_string = ",".join(['Nan' for i in range(self.feature.length)])
                resource_uri = [resource[rn] for rn in resource_names]
                parameter = []
                parameter = ['Nan' for pn in parameter_names]
                line = ",".join([str(idx), self.feature.name] + resource_uri + ['"'+value_string+'"']  +  parameter + ['404','The feature was not found in the table. Check feature logs for traceback'])# appends all the row elements
                yield line+'\n'
                idx+=1
                
                     
        for i, error in enumerate(resource_list.error_list):
            value_string = ",".join(['Nan' for i in range(self.feature.length)])
            resource_uri = [error.resource[rn] for rn in resource_names]
            parameter = []
            parameter = ['Nan' for pn in parameter_names]
            line = ",",join([str(idx), self.feature.name] + resource_uri + [value_string]  +  parameter + [error.code,error.message])# appends all the row elements      
            yield line+'\n'
            idx+=1    

    def return_from_workdir(self, table, resource_list, **kw):
        """
            returns csv for features without cache
        """
        filename = resource_list.workdir_filename()
        resource_names = self.feature.resource
        parameter_names = self.feature.parameter

        # creates a title row and writes it to the document
        titles = ",".join(['index', 'feature type'] + resource_names + ['descriptor'] + parameter_names + ['response code','error message'])
        yield titles+'\n'

        with Locks(filename):
            log.debug('Reading from table path: %s'%filename)
            with tables.openFile(filename, 'r') as h5file:
                
                Table = h5file.root.values
                for idx, r in enumerate(Table):
    
                    resource = {}  # creating a resource dictionary to story all the uris
                    for res in self.feature.resource:
                        resource[res] = r[res]
    
                    value_string = ",".join('%g' % i for i in r['feature'])  # parses the table output and returns a string of the vector separated by commas
                    resource_uri = [resource[rn] for rn in resource_names]
                    parameter = [r[pn] for pn in parameter_names]
                    line = ",".join([str(idx), self.feature.name] + resource_uri + ['"'+value_string+'"'] + parameter + ['200','none']) # appends all the row elements
                    yield line+'\n' # writes line to the document            


        for i, error in enumerate(resource_list.error_list):
            value_string = ",".join(['Nan' for i in range(self.feature.length)])
            resource_uri = [error.resource[rn] for rn in resource_names]
            parameter = []
            parameter = ['Nan' for pn in parameter_names]
            line = ",",join([str(idx), self.feature.name] + resource_uri + ['"'+value_string+'"']  +  parameter + [error.code,error.message])# appends all the row elements
            yield line+'\n'  # write line to the document        
            idx+=1




#-------------------------------------------------------------
# Formatters - Hierarchical Data Format 5
# MIME types:
#   text
#-------------------------------------------------------------
class Hdf(Format):

    name = 'HDF'
    description = 'Returns HDF5 file with columns as resource ... | feature | feature attributes...'
    content_type = 'application/hdf5'
    
    def return_header(self, table, resource_list, **kw):

        
        path = resource_list.workdir_filename()
        filename = ntpath.basename(path)
        uuid.uuid1()
        m = hashlib.md5()
        m.update(filename+uuid.uuid1().hex)
        self.filename = m.hexdigest()
        try:
            self.disposition = 'filename="%s"' % (self.filename+'.h5').encode('ascii')
        except UnicodeEncodeError:
            self.disposition = 'attachment; filename="%s"; filename*="%s"' % ((self.filename+'.h5').encode('utf8'), (self.filename+'.h5').encode('utf8'))
            
        if len(resource_list)>0:
            header = {
                  'content-type': self.content_type,
                  'Content-Disposition':self.disposition    # sets the file name of the hdf file
            }
            
        else: #if no resources were found in the resource list
            header = {
                  'content-type': 'text/xml',
            }
                        
        return header

    def return_from_tables(self, table, resource_list, **kw):
        """
            Returns a newly formed hdf5 table
            All HDF files are saved in the work dir of the feature service
        """
            
        # creating a file name
        path = resource_list.workdir_filename()
        
        #writing the output to an uncached table
        workdir_feature_table = WorkDirTable(resource_list.feature())
        
        def func(h5file):
            #writing to table
            response_table = h5file.root.values
            for i, uri_hash in enumerate(resource_list.uri_hash_list):
                rows = table.get(uri_hash)
                for r in rows:  # taking rows out of one and placing them into the rows of the output table
                    row = ()
                    for e in self.feature.resource:  # adding input resource uris
                        row += tuple([resource_list[i][1][e]])
                    row += tuple([resource_list.feature.name])
                    row += tuple([r['feature']])
                    for p in self.feature.parameter:
                        row += tuple([r[p]])
                    response_table.append([row])
                response_table.flush()
        
        if len(resource_list)>0: #no table will be created it their are no elements
            workdir_feature_table.create_h5_file( path, func)
        
        return self.return_from_workdir(workdir_feature_table,resource_list)


    def return_from_workdir(self, table, resource_list, **kw):
        """
        
            Note: return header must be called first to establish a file name
        """
        # since the uncached table is already saved in the workdir the file is just
        # returned
        path = resource_list.workdir_filename() #path
        
        #if errors write error response xml
        if len(resource_list.error_list)>0:
            
            if self.filename:
            
                _mkdir(FEATURES_REQUEST_ERRORS_DIR)
                
                error_path = os.path.join(FEATURES_REQUEST_ERRORS_DIR,self.filename+'.xml')
                
                with Locks(None,error_path,failonexist=True) as l:
                    if not l.locked:
                        log.debug('Already initialized xml file path: %s'%self.filename)  
                    else:              
                        with open(error_path,'w') as f:
                            #read through errors
                            f.write('<resource uri = "%s">'%str(self.feature_request_uri))
                            for i, error in enumerate(resource_list.error_list):
                                subelement = etree.Element(
                                  'feature_error' ,
                                  error.resource,
                                  error_code = str(error.code),
                                  type=str(self.feature.name),
                                  error=error.message
                                )
                                f.write(etree.tostring(subelement))
                            f.write('</resource>')
            else:
                raise FeatureServiceError(error_code=500, error_message='return_header was not called before return_from_workdir')
            
        
        if len(resource_list)>0 and os.path.exists(path):
            #require read lock to stream
            with Locks(path):
                pass
            
            if not self.content_type or not self.disposition:
                raise FeatureServiceError(error_code=500, error_message='return_header was not called before return_from_workdir')
            request.method = 'GET' #hack to get the forward to work
            return forward(FileApp(path,
                           content_type = self.content_type,
                           content_disposition = self.disposition,
                           ).cache_control( max_age=60*60*24*7*6)) # 6 weeks

        else: 
            content = etree.Element('Error', uri = str(self.feature_request_uri), debug_uri = str("%s/features/debug/%s" % (request.host, self.filename)))
            content.text = "An error occurred in all the resources requested on, check %s/features/debug/%s for more details" % (request.host, self.filename)
            return etree.tostring(content)

            

#-------------------------------------------------------------
# Formatters - No Ouptut
# MIME types:
#   text/xml
#-------------------------------------------------------------
class NoOutput(Format):
    name = 'No Output'


#-------------------------------------------------------------
# Formatters - Numpy
# Only for internal use
#-------------------------------------------------------------
class ReturnNumpy(Format):
    """
    """
    name = 'numpy'
    description = 'Returns numpy arrays for features'
    content_type = ''    
    def return_from_tables(self, table, element_list, **kw):
        pass
    
    def return_from_workdir(self, table, filename, **kw):
        pass


FORMAT_DICT = {
    'xml'      : Xml,
    'csv'      : Csv,
    'hdf'      : Hdf,
    'none'     : NoOutput,
    #'localpath': LocalPath
}


###################################################################
# ##  Documentation
###################################################################

class FeatureDoc():
    """
    Feature Documentation Class is to organize the documention for
    the feature server
    (it will always output in xml)
    """
    def __init__(self):
        pass

    def feature_server(self):
        """
            Returns xml of the commands allowed on the feature server
        """
        #response.headers['Content-Type'] = 'text/xml'
        resource = etree.Element('resource', uri=str(request.url))
        command  = etree.SubElement(resource, 'command', name='/*feature name*', type='string', value='Documentation of specific feature')
        command  = etree.SubElement(resource, 'command', name='/list', type='string', value='List of features')
        command  = etree.SubElement(resource, 'command', name='/format', type='string', value='List of formats')
        command  = etree.SubElement(resource, 'command', name='/format/*format name*', type='string', value='Documentation of specific format')
        command  = etree.SubElement(resource, 'command', name='/*feature name*?uri=http://...', type='string', value='Returns feature in format set to xml')
        command  = etree.SubElement(resource, 'command', name='/*feature name*/*format name*?*resource type*=http://...(&*resource type*=http://...)', type='string', value='Returns feature in format specified')
        command  = etree.SubElement(resource, 'attribute', name='resource', value='The name of the resource depends on the requested feature')
        return etree.tostring(resource)


    def feature_list(self):
        """
            Returns xml of given feature
        """
        resource = etree.Element('resource', uri=str(request.url))  # self.baseurl+'/doc')
        resource.attrib['description'] = 'List of working feature extractors'
        feature_library = {}
        for featuretype in FEATURE_ARCHIVE.keys():
            feature_module = FEATURE_ARCHIVE[featuretype]

            if feature_module.library not in feature_library:
                feature_library[feature_module.library] = etree.SubElement(resource, 'library', name=feature_module.library)


            feature = etree.SubElement(
                                  feature_library[feature_module.library],
                                  'feature',
                                  name=featuretype,
                                  permission="Published",
                                  uri='features/list/' + featuretype
            )

        return etree.tostring(resource)


    def feature(self, feature_name):
        """
            Returns xml of information about the features
        """
        
        try:
            feature_module = FEATURE_ARCHIVE[feature_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Feature: %s requested was not found'%feature_name)
        
        feature_module = feature_module()
        Table = Tables(feature_module)


        xml_attributes = {
                          'description':str(feature_module.description),
                          'feature_length':str(feature_module.length),
                          'required_resources': ','.join(feature_module.resource),
                          'cache': str(feature_module.cache),
                          'confidence': str(feature_module.confidence)
                          #'table_length':str(len(Table)) this request takes a very long time in the current state
                         }
        if len(feature_module.parameter) > 0:
            xml_attributes['parameters'] = ','.join(feature_module.parameter)

        resource = etree.Element('resource', uri=str(request.url))
        feature = etree.SubElement(resource, 'feature', name=str(feature_module.name))
        for key, value in xml_attributes.iteritems():
            attrib = {key:value}
            info = etree.SubElement(feature, 'info', **attrib)
        return etree.tostring(resource)


        return etree.tostring(resource)

    def format_list(self):
        """
            Returns List of Formats
        """
        
        resource = etree.Element('resource', uri=str(request.url))
        resource.attrib['description'] = 'List of Return Formats'
        for format_name in FORMAT_DICT.keys():
            format = FORMAT_DICT[format_name]
            feature = etree.SubElement(resource,
                                      'format',
                                      name=format_name,
                                      permission="Published",
                                      uri='format/' + format_name)
        response.headers['Content-Type'] = 'text/xml'
        return etree.tostring(resource)

    def format(self, format_name):
        """
            Returns documentation about format
        """
        
        try:
            format = FORMAT_DICT[format_name]
        except KeyError:
            #through an exception to be picked up by the main try block
            raise FeatureServiceError(404, 'Format: %s  was not found'%format_name)        

        xml_attributes = {
                          'Name':str(format.name),
                          'Description':str(format.description),
                          'Limit':str(format.limit)
                          }

        resource = etree.Element('resource', uri=str(request.url))
        feature = etree.SubElement(resource, 'format', name=str(format.name))
        
        for key, value in xml_attributes.iteritems():
            attrib = {key:value}
            info = etree.SubElement(feature, 'info', attrib)
        return etree.tostring(resource)

###################################################################
# ## Feature Service Controller
###################################################################

class featuresController(ServiceController):

    service_type = "features"

    def __init__(self, server_url):
        super(featuresController, self).__init__(server_url)
        self.baseurl = server_url
        _mkdir(FEATURES_TABLES_FILE_DIR)
        _mkdir(FEATURES_TEMP_IMAGE_DIR)
        _mkdir(FEATURES_REQUEST_ERRORS_DIR)
        
        log.debug('importing features')
        self.docs = FeatureDoc()


    ###################################################################
    # ## Feature Service Entry Points
    ###################################################################
    @expose()
    def _default(self, *args, **kw):
        """
            Entry point for features calculation and command and feature documentation
        """
        # documentation
        log.info('%s : %s'%(request.method,request.url))

        if not args and request.method =='GET':
            body = self.docs.feature_server()  #print documentation
            header = {'content-type':'text/xml'}
            log.info('Content Type: %s  Returning Feature List'%(header['content-type'])) 
        elif len(args) == 1 and request.method =='GET' and not kw:
            try:
                body = self.docs.feature(args[0])
                header = {'content-type':'text/xml'}
                log.info('Content Type:%s  Returning Feature Info: %s'%(header['content-type'],args[0])) 
                                
            except FeatureServiceError as e:
                log.error('Error Code: %s - Error Message: %s'%(e.error_code,e.error_message))                
                abort(e.error_code, e.error_message)

        # calculating features
        elif len(args) == 2:
            try:
                resource_list = parse_request( request.url, args[0], args[1], request.method, **kw)
                operations( resource_list)
                header, body = format_response( resource_list)
                log.info( 'Content Type: %s  Returning Feature: %s'%(header['content-type'],args[0]))
                
            except FeatureServiceError as e:
                log.error('Error Code: %s - Error Message: %s'%(e.error_code,e.error_message))
                abort( e.error_code, e.error_message)

        else:
            log.error('Malformed Request: Not a valid features request')
            abort(400, 'Malformed Request: Not a valid features request')
        
        response.headers.update(header)
        return body

    @expose()
    def formats(self, *args):
        """
            entry point for format documentation
        """
        log.info('%s : %s'%(request.method,request.url))
        if request.method == 'GET':        
            if len(args) < 1: #returning list of useable formats
                body = self.docs.format_list()
                header = {'content-type':'text/xml'}
                log.info('Content Type: %s  Returning Format Type List'%(header['content-type']))          
                                    
            elif len(args) < 2: #returining info on specific format
                try:
                    body = self.docs.format(args[0])
                    header = {'Content-Type':'text/xml'}
                    log.info('Content Type: %s  Returning Format Type: %s'%(header['content-type'],args[0]))
                    
                except FeatureServiceError as e:
                    log.error('Error Cod:e %s - Error Message: %s'%(e.error_code,e.error_message))
                    abort(e.error_code, e.error_message)
            else:
                log.error('Malformed Request: Not a valid features request')
                abort(400, 'Malformed Request: Not a valid features request')
                
            response.headers.update(header)
            return body
        
        else:
            log.error('Malformed Request: Not a valid features request only excepts GET method')
            abort(400, 'Malformed Request: Not a valid features request only excepts GET method')         

    @expose()
    def list(self):
        """
            entry point for list of features
        """
        log.info('%s : %s'%(request.method,request.url))
        if request.method == 'GET':
            header = {'content-type':'text/xml'}
            response.headers.update(header)
            feature_list = self.docs.feature_list()
            log.info('Content Type:%s  Returning Feature List'%header['content-type'])
            return feature_list
        else:
            log.error('Malformed Request: Not a valid features request only excepts GET method')
            abort(400, 'Malformed Request: Not a valid features request only excepts GET method')            

    @expose()
    def debug(self, id):
        """
            returns status of failed requests
            
            id - a hash of the h5 file stored in the work dir and uuid base on time.
            This id is returned as the name of the h5 file. If no errors occured during
            the request no file is stored in the request_errors dir and a standard output
            is returned
        """
        log.info('%s : %s'%(request.method,request.url))
        if request.method == 'GET':
            #check dir
            path = os.path.join(FEATURES_REQUEST_ERRORS_DIR,id+'.xml')
            if os.path.exists(path):
                #if there return the xml file
                with Locks( path) as l:
                    pass
                
                header = {'content-type':'text/xml'}
                response.headers.update(header)
                return forward(FileApp(path,
                               content_type = 'text/xml',
                ).cache_control( max_age=60*60*24*7*6)) # 6 weeks
             
            else:    
                #else returns no errors in the calculation
                header = {'content-type':'text/xml'}
                response.headers.update(header)
                return '<resource>Did not find an error file</resource>'
            
        else:
            log.error('Malformed Request: Not a valid features request only excepts GET method')
            abort(400, 'Malformed Request: Not a valid features request only excepts GET method') 

#######################################################################
### Initializing Service
#######################################################################

def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.info ("initialize " + uri)
    service = featuresController(uri)
    # directory.register_service ('features', service)

    return service

# def get_static_dirs():
#    """Return the static directories for this server"""
#    package = pkg_resources.Requirement.parse ("features")
#    package_path = pkg_resources.resource_filename(package,'bq')
#    return [(package_path, os.path.join(package_path, 'features', 'public'))]

__controller__ = featuresController