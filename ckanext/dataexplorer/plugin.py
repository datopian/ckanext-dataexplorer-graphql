
from six import text_type
from logging import getLogger

from ckan.common import json, config
import ckan.plugins as p
import ckan.plugins.toolkit as toolkit
from ckan.lib.helpers import url_for
log = getLogger(__name__)
ignore_empty = p.toolkit.get_validator('ignore_empty')
natural_number_validator = p.toolkit.get_validator('natural_number_validator')
Invalid = p.toolkit.Invalid
ckan_29_or_higher = p.toolkit.check_ckan_version(min_version='2.9.0')


def each_datastore_field_to_schema_type(dstore_type):
    # Adopted from https://github.com/frictionlessdata/datapackage-pipelines-ckan-driver/blob/master/tableschema_ckan_datastore/mapper.py
    '''
    For a given datastore type, return the corresponding schema type.
    datastore int and float may have a trailing digit, which is stripped.
    datastore arrays begin with an '_'.
    '''
    dstore_type = dstore_type.rstrip('0123456789')
    if dstore_type.startswith('_'):
        dstore_type = 'array'
    DATASTORE_TYPE_MAPPING = {
        'int': ('integer', None),
        'float': ('number', None),
        'smallint': ('integer', None),
        'bigint': ('integer', None),
        'integer': ('integer', None),
        'numeric': ('number', None),
        'money': ('number', None),
        'timestamp': ('datetime', 'any'),
        'date': ('date', 'any'),
        'time': ('time', 'any'),
        'interval': ('duration', None),
        'text': ('string', None),
        'varchar': ('string', None),
        'char': ('string', None),
        'uuid': ('string', 'uuid'),
        'boolean': ('boolean', None),
        'bool': ('boolean', None),
        'json': ('object', None),
        'jsonb': ('object', None),
        'array': ('array', None)
    }
    try:
        return DATASTORE_TYPE_MAPPING[dstore_type]
    except KeyError:
        log.warn('Unsupported DataStore type \'{}\'. Using \'string\'.'
                 .format(dstore_type))
        return ('string', None)


def datastore_fields_to_schema(resource):
    '''
    Return a table schema from a DataStore field types.
    :param resource: resource dict
    :type resource: dict
    '''
    data = {'resource_id': resource['id'], 'limit': 0}

    fields = toolkit.get_action('datastore_search')({}, data)['fields']
    ts_fields = []
    for f in fields:
        if f['id'] == '_id':
            continue
        datastore_type = f['type']
        datastore_id = f['id']
        ts_type, ts_format = each_datastore_field_to_schema_type(
            datastore_type)
        ts_field = {
            'name': datastore_id,
            'type': ts_type
        }
        if ts_format is not None:
            ts_field['format'] = ts_format
        ts_fields.append(ts_field)
    return ts_fields


def get_alias_of_resource(resource):
    '''
    Return an alias from a Datastore resource
    :param resource: resource dict
    :type resource: dict
    '''
    data = {'resource_id': '_table_metadata', 'limit': 3200}
    records = toolkit.get_action('datastore_search')({}, data)['records']
    for r in records:
        if r['alias_of'] != resource['id']:
            continue
        return r


def get_widget(view_dict, view_type, spec={}):
    '''
    Return a widges dict for a given view types.
    :param view_id: view id
    :type view_id: string
    :param view_type: datapackage view type.
    :type view_type: dict
    :param spec: datapackage view specs.
    :type spec: dict
    '''

    widgets = []

    for key, value in view_type:
        widgets.append({
            'name': value,
            'active': True,
            'datapackage': {
                'views': [{
                    'id': view_dict.get('id', ''),
                    'specType': key,
                    'spec': spec,
                    'view_type': view_dict.get('view_type', ''),
                }]
            }
        })
    return widgets


class DataExplorerViewBase(p.SingletonPlugin):
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IResourceView, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IConfigurable)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'dataexplorer')

    def can_view(self, data_dict):
        resource = data_dict['resource']
        return (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', ''))

    def get_helpers(self):
        return {
            'ckan_29_or_higher': ckan_29_or_higher
        }

    def configure(self, config):
        # Certain config options must exists for the plugin to work. Raise an
        # exception if they're missing.
        missing_config = "{0} is not configured. Please amend your .ini file."
        config_options = (
            'ckanext.data_explorer_graphql.data_api_url',
        )
        for option in config_options:
            if not config.get(option, None):
                raise RuntimeError(missing_config.format(option))

    def view_template(self, context, data_dict):
        return 'dataexplorer.html'


class DataExplorerTableView(DataExplorerViewBase):
    '''
        This extension provides table views using a v2 dataexplorer.
    '''

    def info(self):
        return {
            'name': 'dataexplorer_table_view',
            'title': 'Table',
            'filterable': False,
            'icon': 'table',
            'requires_datastore': True,
            'default_title': p.toolkit._('Table'),
        }

    def setup_template_variables(self, context, data_dict):

        view_type = view_type = [('table', 'Table')]

        widgets = get_widget(data_dict['resource_view'], view_type)
        schema = datastore_fields_to_schema(data_dict['resource'])
        filters = data_dict['resource_view'].get('filters', {})

        return {
            'widgets': widgets,
            'data_api_url': config.get('ckanext.data_explorer_graphql.data_api_url'),
            'data_dataset':  get_alias_of_resource(data_dict['resource'])['name'],
            'data_schema': {'fields': list(map(lambda x: {'type': x['type'], 'name': x['name'].replace(' ', '').replace('(', '_').replace(')', '_')}, schema))}
        }

    def can_view(self, data_dict):
        resource = data_dict['resource']

        if (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', '')):
            return True
        resource_format = resource.get('format', None)
        if resource_format:
            return resource_format.lower() in ['csv', 'xls', 'xlsx', 'tsv']
        else:
            return False
