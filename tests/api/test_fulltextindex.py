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

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from model_bakery import baker

from django.core.urlresolvers import reverse

from rest_framework import status


def create_publications(count):
    entries = []
    for pk in range(1, count+1):
        entries.append(
            baker.prepare(
                "emgapi.Publication",
                pk=pk,
                pubmed_id=pk,
                pub_title="Publication findme",
                pub_abstract="abcdefghijklmnoprstuvwxyz"
            )
        )
    for pk in range(count+1, 2*count+1):
        entries.append(
            baker.prepare(
                "emgapi.Publication",
                pk=pk,
                pubmed_id=pk,
                pub_title="Publication hide",
                pub_abstract="abcdefghijklmnoprstuvwxyz"
            )
        )
    return entries


def create_studies(count):
    entries = []
    for pk in range(1, count+1):
        _biome = baker.make('emgapi.Biome', pk=pk)
        entries.append(
            baker.prepare(
                "emgapi.Study",
                pk=pk,
                biome=_biome,
                study_name="Study findme",
                study_abstract="abcdefghijklmnoprstuvwxyz",
                is_public=1
            )
        )
    for pk in range(count+1, 2*count+1):
        _biome = baker.make('emgapi.Biome', pk=pk)
        entries.append(
            baker.prepare(
                "emgapi.Study",
                pk=pk,
                biome=_biome,
                study_name="Study hide",
                study_abstract="abcdefghijklmnoprstuvwxyz",
                is_public=1
            )
        )
    return entries


def create_samples(count):
    entries = []
    for pk in range(1, count+1):
        _biome = baker.make('emgapi.Biome', pk=pk)
        _study = baker.make('emgapi.Study', pk=pk, biome=_biome, is_public=1)
        entries.append(
            baker.prepare(
                "emgapi.Sample",
                pk=pk,
                biome=_biome,
                studies=[_study],
                sample_name="Sample findme",
                is_public=1
            )
        )
    for pk in range(count+1, 2*count+1):
        _biome = baker.make('emgapi.Biome', pk=pk)
        _study = baker.make('emgapi.Study', pk=pk, biome=_biome, is_public=1)
        entries.append(
            baker.prepare(
                "emgapi.Sample",
                pk=pk,
                biome=_biome,
                studies=[_study],
                sample_name="Sample hideme",
                is_public=1
            )
        )
    return entries


class TestFullTextIndexAPI(object):

    @pytest.mark.parametrize(
        '_model, _dashed, _view, search_term, search_attr, counts',
        [
            ('Study', 'studies', 'emgapi_v1:studies',
             'findme', 'study-name', 5),
            ('Sample', 'samples', 'emgapi_v1:samples',
             'findme', 'sample-name', 5),
            ('Publication', 'publications', 'emgapi_v1:publications',
             'findme', 'pub-title', 5),
        ]
    )
    @pytest.mark.django_db
    def test_search(self, live_server, client,
                    _model, _dashed, _view,
                    search_term, search_attr, counts):
        view_name = _view.split(":")[1]
        klass = getattr(importlib.import_module("emgapi.models"), _model)
        entries = globals()["create_%s" % view_name](counts)
        klass.objects.bulk_create(entries)
        assert len(klass.objects.all()) == 2*counts

        view_name = "%s-list" % _view
        qs = urlencode({'search': search_term})
        url = "%s%s?%s" % (live_server.url, reverse(view_name), qs)
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()

        # Meta
        assert rsp['meta']['pagination']['page'] == 1
        assert rsp['meta']['pagination']['pages'] == 1
        assert rsp['meta']['pagination']['count'] == counts

        # Data
        assert len(rsp['data']) == counts

        for d in rsp['data']:
            assert d['type'] == _dashed
            assert d['attributes'][search_attr] == "%s findme" % _model
            assert not d['attributes'][search_attr] == "%s hideme" % _model
