[![CKAN](https://img.shields.io/badge/ckan-2.9-orange.svg?style=flat-square)](https://github.com/ckan/ckan/tree/2.9)

### Features

A Data Explorer app for CKAN built in React fetching data from the Data-API:

### Installation

**Important notice:** This extension requres the existance of an Data-API instance running, with Hasura running behind, all the resources that you want displayed also need to have a proper alias without any numbers at the start, the datastore table also needs to been tracked by the Hasura instance so that the graphql api works.

The React code repository is here - https://github.com/datopian/data-explorer-graphql.

To install ckanext-dataexplorer-graphql:

1. Activate your CKAN virtual environment, for example::

   . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-dataexplorer-react Python package into your virtual environment::
   `pip install -e git+https://github.com/datopian/ckanext-dataexplorer-graphql.git#egg=ckanext-dataexplorer-graphql`

3. Add `dataexplorer_view` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/production.ini`)

   - `dataexplorer_view`for multiview visualization table
   - Add `dataexplorer_table_view` for table view.

4. Add the `ckanext.data_explorer_react.data_api_url` setting to your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/production.ini`) this should have the the data-api instance url with the respective version Ex: `http://localhost:3000/v1/`

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

   sudo service apache2 reload

### Development Installation

To install ckanext-dataexplorer-react for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/datopian/ckanext-dataexplorer-graphql.git
    cd ckanext-dataexplorer-graphql
    python setup.py develop
    pip install -r dev-requirements.txt
