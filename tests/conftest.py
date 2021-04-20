#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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


import os
import pytest

import mongoengine
import mongomock

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emgcli.settings')


def pytest_configure():
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["*"]
    settings.REST_FRAMEWORK['TEST_REQUEST_DEFAULT_FORMAT'] = 'vnd.api+json'
    settings.RT = {
        "url": "https://fake.helpdesk.ebi.ac.uk/REST/1.0/ticket/new",
        "user": "metagenomics-help-api-user",
        "pass": "secret-password",
        "emg_queue": "EMG_Q",
        "emg_email": "EMG@mail.com",
        "ena_queue": "ENA_Q"
    }
    # TODO: backend mock to replace FakeEMGBackend
    # settings.EMG_BACKEND_AUTH_URL = 'http://fake_backend/auth'
    settings.AUTHENTICATION_BACKENDS = ('test_utils.FakeEMGBackend',)
    # disconnect main database
    mongoengine.connection.disconnect()


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


# MongoDB connection
@pytest.fixture(scope='function')
def mongodb(request):
    """On the EMG_CONFIG use 'testdb' on the mongo configuration
    """
    if os.environ.get("JENKINS", False):
        # TEMP py3.4
        # patch to run a fake mongo db on
        # Jenkins, we don't have a running mongo
        # instance there yet.
        # This will be removed when we drop support for py3.4
        return mongomock.MongoClient()
    
    db = mongoengine.connect('testdb')

    def finalizer():
        db.drop_database('testdb')
        db.close()

    request.addfinalizer(finalizer)

    return db
