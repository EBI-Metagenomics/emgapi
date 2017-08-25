.. image:: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api.svg?branch=master
    :target: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api


EMG API
=======

Requirements:
-------------

- Python 2.7, 3.5 or 3.6
- Django 1.11
- MySQL 5.6 or 5.7


Configure:
----------

Create configuration file in `~/.yamjam/config.yaml`::

    ***REMOVED***
    ***REMOVED***
    ***REMOVED***
    ***REMOVED***
          NAME: 'database_name'
          USER: 'database_user'
          PASSWORD: 'secret'
          HOST: 'mysql.host'
          PORT: 3306

      # Deploy under the custom prefix::
      prefix: "/metagenomics"

      admins:
        - ['admin', 'admin@example.com']
      email:
        host: localhost
        port: 25
        subject: "EMGAPI"

optional:

- Store HTTP session in redis (requires: `pip install django-redis>=4.4`)::

      session_engine: 'django.contrib.sessions.backends.cache'
      caches:
    ***REMOVED***
          BACKEND: "django_redis.cache.RedisCache"
          LOCATION: "redis://redis.host:6379/0"
          KEY_PREFIX: "some_key"
    ***REMOVED*** "https://backend"

- Customize statics location::

      static_root: /path/to/static/storage

- Documentation settings::

    ***REMOVED***
    ***REMOVED***
        # url: http://host
    ***REMOVED*** 'Is a free resource to visualise and discover metagenomic datasets. For more details go to http://www.ebi.ac.uk/metagenomics/'


Install:
--------

Install Miniconda::

    wget https://repo.continuum.io/miniconda/Miniconda3-4.3.21-Linux-x86_64.sh
    bash Miniconda3-4.3.21-Linux-x86_64.sh

    export PATH=~/conda/bin:$PATH


Install application::

    pip install "git+git://github.com/ola-t/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
    pip install "git+git://github.com/ola-t/ebi-metagenomics-api@master#egg=emgcli"


Start application::

    emgcli check --deploy
    emgcli migrate --fake-initial
    emgcli collectstatic --noinput

    # start application server
    # for a TCP configuration use: --bind 127.0.0.1:8000
    # for UNIX domain socket use: --bind=unix:$SOCKFILE
    emgdeploy --daemon -p ~/emgvar/django.pid --workers 5 --reload emgcli.wsgi:application

NOTE: `~/emgvar` is used as default directory to store logs, secret key, etc.


Tests:
------

To run tests::

    python setup.py tests


Copyright (c) 2017 EMBL - European Bioinformatics Institute
