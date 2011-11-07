import os
import logging
import pkg_resources
from lxml import etree
from pylons.i18n import ugettext as _, lazy_ugettext as l_
from tg import expose, flash
from repoze.what import predicates 
from bq.core.service import ServiceController
from bq.dataset_service import model


from bq import data_service
from bq import module_service


log = logging.getLogger('bq.dataset')


class DatasetOp(object):
    def __init__(self, duri, dataset, members):
        self.duri = duri
        self.dataset = dataset
        self.members = members

    def __call__(self, **kw):
        return self.action(**kw)

    def action(self, member, **kw):
        'Null Op'
        return None
        
    
class IdemOp(DatasetOp):
    'An idempotent operation'
    def action(self, member, **kw):
        'return the members'
        log.debug ('idem action %s' % member)
        return member

class ModuleOp(DatasetOp):
    'Run a module on each member'
    def action(self, member, module, **kw):
        log.debug ('module action %s' % member)
        mex = module_service.execute (module_uri = module,
                                image_url = member.get('uri'),
                                **kw)
        return mex

class PermissionOp(DatasetOp):
    'change permission on member'
    def action(self, member, permission):
        log.debug('permission action %s' % member)
        resource = data_service.get_resource(member.get('uri'), view='short')
        log.debug('GOT %s' % etree.tostring (resource))
        resource.set('perm', permission)
        data_service.update(resource)
        return None

class DeleteOp(DatasetOp):
    'Delete each member'
    def action(self, member, **kw):
        log.debug ('Delete action %s' % member)
        data_service.del_resource (member.get('uri'))
        return None

class TagEditOp (DatasetOp):
    'Add/Remove/Modify Tags on each member'
    def action(self, member, action, tagdoc, **kw):
        """Modify the tags of the member 
        @param member: the memeber of the dataset
        @param action: a string :append, delete, edit_value, edit_name, change_name
        @poarag tagdoc
        """
        if isinstance(tagdoc, basestring):
            tagdoc = etree.XML(tagdoc)

        log.debug ('TagEdit (%s) %s with %s' % (action, member, etree.tostring(tagdoc)))
        # These update operation should be done in the database
        # However, I don't want to think about it now
        # so here's the brute-force way
        if action=="append":
            resource = data_service.get_resource(member.get('uri'), view='short')
            resource.append(tagdoc)
            data_service.update(resource)
        elif action=='delete':
            resource = data_service.get_resource(member.get('uri'), view='full')
            for tag in tagdoc.xpath('./tag'):
                resource_tags = resource.xpath('./tag[@name="%s"]' % tag.get('name'))
                for killtag in resource_tags:
                    data_service.del_resource(killtag.get('uri'))
        elif action=='edit_value':
            resource = data_service.get_resource(member.get('uri'), view='full')
            for tag in tagdoc.xpath('./tag'):
                resource_tags = resource.xpath('./tag[@name="%s"]' % tag.get('name'))
                for mtag in resource_tags:
                    mtag.set('value', tag.get('value'))
            data_service.update(resource)
        elif action=='edit_name':
            resource = data_service.get_resource(member.get('uri'), view='full')
            for tag in tagdoc.xpath('./tag'):
                resource_tags = resource.xpath('./tag[@value="%s"]' % tag.get('value'))
                for mtag in resource_tags:
                    mtag.set('name', tag.get('name'))
            data_service.update(resource)
        elif action=='change_name':
            resource = data_service.get_resource(member.get('uri'), view='full')
            for tag in tagdoc.xpath('./tag'):
                resource_tags = resource.xpath('./tag[@name="%s"]' % tag.get('name'))
                for mtag in resource_tags:
                    mtag.set('name', tag.get('value'))
            data_service.update(resource)

        return None


class DatasetServer(ServiceController):
    """Server side actions on datasets
    """
    service_type = "dataset_service"
    
    operations = {
        'idem' : IdemOp,
        'module' : ModuleOp,
        'permission' : PermissionOp,
        'delete' : DeleteOp,
        'tagedit' : TagEditOp
        }
    
    def __init__(self, server_url):
        super(DatasetServer, self).__init__(server_url)

    def _iterate_dataset(self, duri, operation):
        """Call operation on each dataset member"""
        results = []
        dataset = data_service.get_resource(duri)
        members = dataset.xpath('./tag[@name="members"]')
        for member in members:
            results.append (operation(member.get('uri')))
        return results
            
    @expose('bq.dataset_service.templates.datasets')
    def index(self, **kw):
        'list operations of dataset service'

        return dict(operations = self.operations, )

    @expose(content_type="text/xml")
    def add_query(self, duri, resource_tag, tag_query):
        """Append query results to a dataset

        @param duri: dataset uri of an existing dataset
        @param resource_tag:resource type tag i.e. images
        @param tag_query:  expression of tag search
        """

        dataset = data_service.get_resource(duri, view='deep')
        members = dataset.xpath('./tag[@name="members"]')[0]

        items = data_service.query (resource_tag, tag_query=tag_query)
        for resource in items:
            val = etree.Element('resource',
                                type=resource_tag,
                                uri=resource.get('uri'))
            members.append(val)

        log.debug ("members = %s" % etree.tostring(members))
        data_service.update(members)

    @expose(content_type="text/xml")
    def iterate(self, duri, operation='idem', **kw):
        """Iterate over a dataset executing an operation on each member

        @param  duri: dataset uri
        @param operation: an operation name (i.e. module, permisssion)
        @param kw : operation parameters by name
        """

        log.info('iterate op %s on  %s' % (operation, duri))
        dataset = data_service.get_resource(duri, view='deep')
        members = dataset.xpath('/dataset/tag[@name="members"]')[0]

        op_klass  = self.operations.get(operation, IdemOp)
        op = op_klass(duri, dataset=dataset, members = members)

        #mex = module_service.begin_internal_mex ("dataset_iterate")

        log.debug ("%s on %s with members %s" % (op, dataset.get('uri'), members))
        results = etree.Element('resource', uri=self.baseuri + '/iterate')
        for member in members:
            result =  op(member = member, **kw)
            log.debug ("acting on %s -> %s" % (member, result ))
            if result is not None:
                results.append (result)

        #module_service.end_internal_mex(mex.uri)

        return etree.tostring(results)





def initialize(uri):
    """ Initialize the top level server for this microapp"""
    # Add you checks and database initialize
    log.debug ("initialize " + uri)
    service =  DatasetServer(uri)
    #directory.register_service ('dataset_service', service)

    return service

__controller__ =  DatasetServer

