#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017-2022 EMBL - European Bioinformatics Institute
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import sys
import os
from importlib.util import find_spec 

import pytest

from mongoengine import connect

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emgcli.settings')


def pytest_configure():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if not os.getenv("EMG_CONFIG"):
        print("EMG_CONFIG not found on env, defaulting to config/local-tests.yml")
        os.environ["EMG_CONFIG"] = os.path.join(
            root, "config/local-tests.yml"
        )
    
    if find_spec("emgcli") is None:
        # Add emgcli to the path
        sys.path.insert(0, root)
        os.environ["PATH"] += ":" + os.path.join(root, "emgcli")

    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["*"]
    settings.REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'vnd.api+json'
    settings.RT = {
        "url": "https://fake.helpdesk.ebi.ac.uk/REST/1.0/ticket/new",
        "user": "metagenomics-help-api-user",
        "token": "<<TOKEN>>",
        "emg_queue": "EMG_Q",
        "emg_email": "EMG@mail.com",
        "ena_queue": "ENA_Q"
    }
    settings.RESULTS_PRODUCTION_DIR = "/dummy/path"
    # TODO: backend mock to replace FakeEMGBackend
    # settings.EMG_BACKEND_AUTH_URL = 'http://fake_backend/auth'
    settings.AUTHENTICATION_BACKENDS = ('test_utils.FakeEMGBackend',)


# List  of DB configs which should NOT be migrated by django-pytest
HIDE_DB_CONFIGS = ['ena', 'era', 'backlog_prod']


# Fixture to mask ena config from pytest-django to avoid migrating their database.
@pytest.fixture(scope='session')
def hide_ena_config():
    from django.conf import settings
    hidden_configs = {}
    for n in HIDE_DB_CONFIGS:
        if n in settings.DATABASES:
            ena_db_config = settings.DATABASES[n].copy()
            del settings.DATABASES[n]
            hidden_configs[n] = ena_db_config
    return hidden_configs


@pytest.fixture(scope='session')
def django_db_setup(hide_ena_config, django_db_setup):
    if hide_ena_config:
        settings.DATABASES.update(hide_ena_config)
    mongo_db = settings.MONGO_CONF["db"]
    if "test" not in mongo_db:
        raise ValueError(f"The mongo DB name is {mongo_db}... it should have the word 'test' somewhere.")
    mongo_connection = connect(**settings.MONGO_CONF)
    yield
    mongo_connection.drop_database(mongo_db)
