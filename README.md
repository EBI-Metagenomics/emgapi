[![Testing](https://github.com/EBI-Metagenomics/emgapi/actions/workflows/test.yml/badge.svg)](https://github.com/EBI-Metagenomics/emgapi/actions/workflows/test.yml)

EMG API
=======

Metagenomics service is a large-scale platform for analyzing and archiving metagenomic and metatranscriptome data. It provides a standardized analysis workflow, capable of producing rich taxonomic diversity and functional annotations, and allows analysis results to be compared within and across projects on a broad level, and across different data types (e.g. metagenomic and metatranscriptomic).

# Setup
## Local env.
For development, use the parent repo ["MGnify Web"](https://github.com/EBI-Metagenomics/mgnify-web) which includes this API repository, as well as the frontend web repository needed to develop/run the [MGnify website](https://www.ebi.ac.uk/metagenomics).

### MGnify Web parent repo
The parent repo uses docker-compose to configure a development environment and test data for the entire stack of the MGnify website.
It is the recommended development setup.
See: [MGnify Web](https://github.com/EBI-Metagenomics/mgnify-web) on GitHub for instructions.

**The Docker setup is just for local dev. at the moment.**

This API relies on a relational (SQLite or MySQL) and a document (Mongo) database.

This docker compose setup in the parent repo handles these.

### Helper scripts

There are some helper scripts that are meant to make running the project locally easier. 

- `manage.sh` wrapper for `manage.py` commands such as `runserver`.
- `gunicorn.sh` run the app using gunicorn with the `--reload` flag.

## Setup
Create/edit configuration file in `./config/<some config>.yaml` and set the env var `EMG_CONFIG` to point to that file.

### DB config file
The config file must specify the databases:
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
    
    ...
```
(see the example config yamls for full details).

If **not** using the mgnify-web docker compose setup for some reason: 

Install [virtualenv](https://virtualenv.pypa.io/en/latest/installation/).

Create a virtual environment or a conda env, e.g.: `virtualenv -p python3 venv`

Activate and install the dependencies `source venv/bin/activate && pip install .[dev,admin]`.

Run the migrations: `./manage.sh migrate`

Run the server: `./manage.sh runserver 8000`

**If using the mgnify-web setup, follow the instructions in the parents repo README, and use the Taskfile in it.**

---

**TODO: update the following**
## Production env.
### Install

Install application::

    conda create -q -n myenv python=3.6.8
    source activate myenv

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

### How to run the webuploader?

How to install the webuploader (one off)?

    conda create -q -n myenv python=3.6.8
    source activate myenv

    pip install -U -r https://raw.githubusercontent.com/EBI-Metagenomics/emgapi/webuploader/requirements-webuploader.txt
    pip install "git+git://github.com/EBI-Metagenomics/emgapi.git@webuploader"

    source activate myenv

    cd mycheckoutclone

    export PYTHONPATH="${PYTHONPATH}:$(pwd)/emgcli"
    export EMG_CONFIG=docker/local-config.yaml
    export ENA_API_PASSWORD=?
    export ENA_API_USER=?

    ./manage.sh import_analysis <rootpath>

### How to run a Django schema or data migration on dev?

    sync PRO/REL DB to DEV

    # Source virtual environment
    source activate myenv

    # export environment variables
    export EMG_CONFIG=docker/dev-config.yaml

    cd mycheckoutclone

    emgcli migrate --fake-initial


### Run in Docker

Start containers using::

    docker-compose -f docker/docker-compose.yml up --build --abort-on-container-exit


#### Tests

Tests are ran using `pytest <https://pytest.org>`_.

Set the env variable `EMG_CONFIG`.

To run tests::

    python setup.py test
    
    # or the simpler
    pytest # will use config/local-tests.yml as the config file

or use the wrapper script (will user docker/contig-test.yml)::

    ./run-tests.sh


Copyright (c) 2017-2022 EMBL - European Bioinformatics Institute
