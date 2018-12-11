.. image:: https://travis-ci.org/EBI-Metagenomics/emgapi.svg?branch=master
    :target: https://travis-ci.org/EBI-Metagenomics/emgapi


Introduction
============

Metagenomics service is a large-scale platform for analysing and archiving metagenomic and metatranscriptome data. It provides a standardised analysis workflow, capable of producing rich taxonomic diversity and functional annotations, and allows analysis results to be compared within and across projects on a broad level, and across different data types (e.g. metagenomic and metatranscriptomic).


EMG API
=======

Configure
---------

Create configuration file in `~/path/to/config.yaml <docker/config.yaml>`_.


Install
-------

Install application::

    pip install "git+git://github.com/olatarkowska/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
    pip install https://github.com/EBI-Metagenomics/emgapi/archive/$latestTag.tar.gz


Start application::

    emgcli check --deploy
    emgcli migrate --fake-initial
    emgcli collectstatic --noinput

    # start application server
    # for a TCP configuration use: --bind 127.0.0.1:8000
    # for UNIX domain socket use: --bind=unix:$SOCKFILE
    emgdeploy --daemon -p ~/emgvar/emg.pid --workers 5 --reload emgcli.wsgi:application

NOTE: `~/emgvar` is used as default directory to store logs, etc.


Run in Docker
-------------

Start containers using::

    docker-compose -f docker/docker-compose.yml up --build --abort-on-container-exit


Tests
-----

To run tests::

    python setup.py tests


Copyright (c) 2017 EMBL - European Bioinformatics Institute
