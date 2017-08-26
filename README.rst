.. image:: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api.svg?branch=master
    :target: https://travis-ci.org/ProteinsWebTeam/ebi-metagenomics-api


Introduction
============

What's metagenomics?
--------------------

The study of all genomes present in any given environment without the need for prior individual identification or amplification is termed metagenomics. For example, in its simplest form a metagenomic study might be the direct sequence results of DNA extracted from a bucket of sea water.

What is the EBI doing for metagenomic researchers?
--------------------------------------------------

The EBI resources of the European Nucleotide Archive (in particular Sequence Read Archive and EMBL-Bank), UniProt, InterPro, Ensembl Genomes and IntAct are all used for analysis by metagenomic researchers, but not in an integrated manner. We intend to provide a user friendly interface to these services, promoting their utility in the field of metagenomics. It will enable protein prediction, function analysis, comparison to complete reference genomes and metabolic pathway analysis.


EMG API
=======

Configure:
----------

Create configuration file in `~/.yamjam/config.yaml <docker/config.yaml>`_.


Install:
--------

Install Miniconda::

    wget https://repo.continuum.io/miniconda/Miniconda3-4.3.21-Linux-x86_64.sh
    bash Miniconda3-4.3.21-Linux-x86_64.sh

    export PATH=~/conda/bin:$PATH


Install application::

    pip install "git+git://github.com/ola-t/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
    pip install "git+git://github.com/ProteinsWebTeam/ebi-metagenomics-api@master#egg=emgcli"


Start application::

    emgcli check --deploy
    emgcli migrate --fake-initial
    emgcli collectstatic --noinput

    # start application server
    # for a TCP configuration use: --bind 127.0.0.1:8000
    # for UNIX domain socket use: --bind=unix:$SOCKFILE
    emgdeploy --daemon -p ~/emgvar/emg.pid --workers 5 --reload emgcli.wsgi:application

NOTE: `~/emgvar` is used as default directory to store logs, etc.


Tests:
------

To run tests::

    python setup.py tests


Copyright (c) 2017 EMBL - European Bioinformatics Institute
