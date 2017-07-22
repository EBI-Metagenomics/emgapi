.. image:: https://travis-ci.org/ola-t/ebi-metagenomics-api.svg?branch=master
    :target: https://travis-ci.org/ola-t/ebi-metagenomics-api


EMG API
=======

Requirements:
-------------

 - Python 3.6
 - Django 1.11
 - MySQL 5.6 or 5.7

Installation::
--------------

# Install anaconda
wget https://repo.continuum.io/archive/Anaconda3-4.4.0-Linux-x86_64.sh 
bash Anaconda3-4.4.0-Linux-x86_64.sh 

conda -V
conda update conda
conda search "^python$"

# create venv
conda create -n venv python=3.6 anaconda
# activate
source activate venv

pip install "git+git://github.com/ola-t/ebi-metagenomics-api@master#egg=emgcli"
pip install "git+git://github.com/ola-t/django-rest-framework-json-api@develop#egg=djangorestframework-jsonapi"
emgunicorn

Uninstallation::
----------------

# deactivate
source deactivate

# remove
conda remove -n venv --all


Copyright (c) 2017 EMBL - European Bioinformatics Institute
