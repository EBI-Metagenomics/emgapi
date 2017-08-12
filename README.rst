.. image:: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api.svg?branch=master
    :target: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api


EMG API
=======

Requirements:
-------------

- Python 2.7, 3.5 or 3.6
- Django 1.11
- MySQL 5.6 or 5.7


Install:
--------

Create configuration file in `~/.yamjam/config.yaml`::

    emg:
      databases:
        default:
          ENGINE: 'django.db.backends.mysql'
          NAME: 'database_name'
          USER: 'database_user'
          PASSWORD: 'secret'
          HOST: 'mysql.host'
          PORT: 3306

      # Deploy under the custom prefix::
      prefix: "/metagenomics"


optional:

- Store HTTP session in redis (requires: `pip install django-redis>=4.4`)::

      session_engine: 'django.contrib.sessions.backends.cache'
      caches:
        default:
          BACKEND: "django_redis.cache.RedisCache"
          LOCATION: "redis://redis.host:6379/0"
          KEY_PREFIX: "some_key"
      emg_backend_auth: "https://backend"

- Customize statics location::

      static_root: /path/to/static/storage


Install Miniconda::

    wget https://repo.continuum.io/miniconda/Miniconda3-4.3.21-Linux-x86_64.sh
    bash Miniconda3-4.3.21-Linux-x86_64.sh

    export PATH=~/conda/bin:$PATH


Install application::

    pip install "git+git://github.com/ola-t/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
    pip install "git+git://github.com/ola-t/ebi-metagenomics-api@master#egg=emgcli"


Start up application server::

    emgcli check --deploy
    emgcli migrate --fake-initial
    emgcli collectstatic --noinput

    # start application server
    gunicorn --daemon -p ~/emgvar/django.pid --bind 0.0.0.0:8000 --workers 5 --reload emgcli.wsgi:application

NOTE: `~/emgvar` is used as default directory to store logs, secret key, etc.


Tests::

    python setup.py tests


Copyright (c) 2017 EMBL - European Bioinformatics Institute
