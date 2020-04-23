.. image:: https://travis-ci.org/EBI-Metagenomics/emgapi.svg?branch=master
    :target: https://travis-ci.org/EBI-Metagenomics/emgapi

Introduction
============

Metagenomics service is a large-scale platform for analyzing and archiving metagenomic and metatranscriptome data. It provides a standardized analysis workflow, capable of producing rich taxonomic diversity and functional annotations, and allows analysis results to be compared within and across projects on a broad level, and across different data types (e.g. metagenomic and metatranscriptomic).


EMG API
=======

Local env. 
##########

For development there are 2 options: 

* Install the stack locally
* Use Docker for the database and mongo

On either case the webapp will be executed from a local virtual environment.

Stack locally
-------------

The app uses `MySQL` version `5.6` and `Mongo` version `3.4`.

TODO: write the instructions for MacOS and Linux.

Docker
------

There are 2 docker containers defined, one for `MySQL` and another one `MongoDB`.

The app will be executed from a python virtual environment.

**The Docker setup is just for local dev. at the moment.**

Setup
^^^^^

Create configuration file in `~/path/to/config.yaml <docker/config.yaml>`_.

### DB config file
An environment variable named *EMG_CONFIG* needs to be defined for the database config.
This should contain the path to yaml config file, which must contain the following fields:
```yaml
emg:
  databases:
    default:
      ENGINE: 'django.db.backends.mysql'
      HOST: 'host'
      PORT: 3306 (or other)
      DB: 'database_name'
      NAME: 'schema_name'
      USER: 'user'
      PASSWORD: 'password'
    dev:
        ....
    prod:
        ....
    era:
      ENGINE: 'django.db.backends.oracle'
      NAME: ?
      USER: ?
      PASSWORD: ?
      HOST: ?
      PORT: ?
```

Install `virtualenv <https://virtualenv.pypa.io/en/latest/installation//>`_

Create a virtual environment::
    
    `virtualenv -p python3 venv`

Activate and install the dependencies `source venv/bin/activate && pip install -r requirements-local-dev.txt`.

Start containers using::

    docker-compose -f docker/docker-compose.yml up --build -d

Run the migrations::

    ./manage.sh migrate

Run the server::

   ./manage.sh runserver 8000

Production env.
###############

Install
-------

Install application::

    conda create -q -n myenv python=3.6.8
    source activate myenv

    pip install -U git+git://github.com/EBI-Metagenomics/emg-backlog-schema.git;
    pip install -U git+git://github.com/EBI-Metagenomics/ena-api-handler.git
    pip install "git+git://github.com/EBI-Metagenomics/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
    pip install https://github.com/EBI-Metagenomics/emgapi/archive/$latestTag.tar.gz

Create database::

    mysql -e 'CREATE DATABASE emg;'
    mysql -u root --password="" --database=emg < travis/biomes.sql
    mysql -u root --password="" --database=emg < travis/variable_names.sql
    mysql -u root --password="" --database=emg < travis/experiment_type.sql
    mysql -u root --password="" --database=emg < travis/analysis_status.sql

Start application (API)::

    emgcli check --deploy
    emgcli migrate --fake-initial
    emgcli collectstatic --noinput

    # start application server
    # for a TCP configuration use: --bind 127.0.0.1:8000
    # for UNIX domain socket use: --bind=unix:$SOCKFILE
    emgdeploy --daemon -p ~/emgvar/emg.pid --workers 5 --reload emgcli.wsgi:application

NOTE: `~/emgvar` is used as default directory to store logs, etc.

How to run the webuploader?
---------------------------

How to install the webuploader (one off)?

    conda create -q -n myenv python=3.6.8
    source activate myenv

    pip install -U git+git://github.com/EBI-Metagenomics/emg-backlog-schema.git
    pip install -U git+git://github.com/EBI-Metagenomics/ena-api-handler.git
    pip install "git+git://github.com/EBI-Metagenomics/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"

    pip install -U -r https://raw.githubusercontent.com/EBI-Metagenomics/emgapi/webuploader/requirements-webuploader.txt
    pip install "git+git://github.com/EBI-Metagenomics/emgapi.git@webuploader"

    source activate myenv

    cd mycheckoutclone

    export PYTHONPATH="${PYTHONPATH}:$(pwd)/emgcli"
    export EMG_CONFIG=docker/local-config.yaml
    export ENA_API_PASSWORD=?
    export ENA_API_USER=?

    ./manage.sh import_analysis <rootpath>

How to run a Django schema or data migration on dev?
----------------------------------------------------

    sync PRO/REL DB to DEV

    # Source virtual environment
    source activate myenv

    # export environment variables
    export EMG_CONFIG=docker/dev-config.yaml

    cd mycheckoutclone

    emgcli migrate --fake-initial


Run in Docker
-------------

Start containers using::

    docker-compose -f docker/docker-compose.yml up --build --abort-on-container-exit


Tests
#####

Tests are ran using `pytest`.

Set the env variable `EMG_CONFIG`

To run tests::

    python setup.py test


Copyright (c) 2019 EMBL - European Bioinformatics Institute
