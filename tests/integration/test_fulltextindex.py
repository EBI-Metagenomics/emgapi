#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2017 EMBL - European Bioinformatics Institute
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

import importlib
import pytest

from urllib.parse import urlencode

from model_mommy import mommy

from django.core.urlresolvers import reverse


@pytest.mark.skip(reason="zero results")
class TestFullTextIndexAPI(object):

    @pytest.mark.parametrize(
        '_model, _view, search_term, results',
        [
            ('Publication', 'publications', 'title', 4),
        ]
    )
    @pytest.mark.django_db
    def test_search(self, client, _model, _view, search_term, results):
        klass = getattr(importlib.import_module("emg_api.models"), _model)

        model_name = "emg_api.%s" % _model

        entries = []
        for pk in range(1, results+1):
            entries.append(
                mommy.prepare(
                    model_name,
                    pub_title="publication title foo bar",
                    pub_abstract="abcdefghijklmnoprstuvwxyz"
                )
            )
        klass.objects.bulk_create(entries)

        view_name = "%s-list" % _view
        qs = urlencode({'search': search_term})
        url = "%s?%s" % (reverse(view_name), qs)
        response = client.get(url)
        assert response.status_code == 200
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == results

        # Data
        assert len(rsp['data']) == results

        for d in rsp['data']:
            assert d['type'] == _model
            assert search_term in d['attributes']['pub_title']
