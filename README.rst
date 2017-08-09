.. image:: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api.svg?branch=master
    :target: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api


EMG API
=======

Requirements:
-------------

 - Python 3.6
 - Django 1.11
 - MySQL 5.6 or 5.7

Install:
-------------

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
      session_engine: 'django.contrib.sessions.backends.cache'
      caches:
    ***REMOVED***
          BACKEND: "django_redis.cache.RedisCache"
          LOCATION: "redis://redis.host:6379/0"
          KEY_PREFIX: "some_key"
    ***REMOVED*** "https://backend"


Install anaconda::

    wget https://repo.continuum.io/archive/Anaconda3-4.4.0-Linux-x86_64.sh 
    bash Anaconda3-4.4.0-Linux-x86_64.sh 


Create conda environmnet::

    conda -V
    conda update conda
    conda search "^python$"


Create virtual environmnet::

    conda create -n venv python=3.6 anaconda


Activate::

    source activate venv

    pip install "git+git://github.com/ola-t/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
    pip install "git+git://github.com/ola-t/ebi-metagenomics-api@master#egg=emgcli"


Start up application server::

    gunicorn --daemon -p ~/emgvar/django.pid --bind 0.0.0.0:8000 --workers 5 --reload emgcli.wsgi:application

NOTE: `~/emgvar` is used as default directory to store logs, secret key, etc.


Uninstal:
----------------

Deactivate conda environment and remove::

    source deactivate
    conda remove -n venv --all


Copyright (c) 2017 EMBL - European Bioinformatics Institute
