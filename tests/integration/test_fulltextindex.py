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

from rest_framework import status


def create_biomes(count):
    entries = []
    for pk in range(1, count+1):
        entries.append(
            mommy.prepare(
                "emg_api.Biome",
                pk=pk,
                biome_name="Biome findme",
                lineage="root:biome:findme"
            )
        )
    for pk in range(count+1, 2*count+1):
        entries.append(
            mommy.prepare(
                "emg_api.Biome",
                pk=pk,
                biome_name="Biome hideme",
                lineage="root:biome:hideme"
            )
        )
    return entries


def create_publications(count):
    entries = []
    for pk in range(1, count+1):
        entries.append(
            mommy.prepare(
                "emg_api.Publication",
                pk=pk,
                pub_title="Publication findme",
                pub_abstract="abcdefghijklmnoprstuvwxyz"
            )
        )
    for pk in range(count+1, 2*count+1):
        entries.append(
            mommy.prepare(
                "emg_api.Publication",
                pk=pk,
                pub_title="Publication hide",
                pub_abstract="abcdefghijklmnoprstuvwxyz"
            )
        )
    return entries


def create_studies(count):
    entries = []
    for pk in range(1, count+1):
        _biome = mommy.make('emg_api.Biome', pk=pk)
        entries.append(
            mommy.prepare(
                "emg_api.Study",
                pk=pk,
                biome=_biome,
                study_name="Study findme",
                study_abstract="abcdefghijklmnoprstuvwxyz",
                is_public=1
            )
        )
    for pk in range(count+1, 2*count+1):
        _biome = mommy.make('emg_api.Biome', pk=pk)
        entries.append(
            mommy.prepare(
                "emg_api.Study",
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
        _biome = mommy.make('emg_api.Biome', pk=pk)
        _study = mommy.make('emg_api.Study', pk=pk, biome=_biome, is_public=1)
        entries.append(
            mommy.prepare(
                "emg_api.Sample",
                pk=pk,
                biome=_biome,
                study=_study,
                sample_name="Sample findme",
                is_public=1
            )
        )
    for pk in range(count+1, 2*count+1):
        _biome = mommy.make('emg_api.Biome', pk=pk)
        _study = mommy.make('emg_api.Study', pk=pk, biome=_biome, is_public=1)
        entries.append(
            mommy.prepare(
                "emg_api.Sample",
                pk=pk,
                biome=_biome,
                study=_study,
                sample_name="Sample hideme",
                is_public=1
            )
        )
    return entries


class TestFullTextIndexAPI(object):

    @pytest.mark.parametrize(
        '_model, _view, search_term, search_attr, counts',
        [
            ('Biome', 'emg_api:biomes', 'findme', 'biome_name', 5),
            ('Study', 'emg_api:studies', 'findme', 'study_name', 5),
            ('Sample', 'emg_api:samples', 'findme', 'sample_name', 5),
            ('Publication', 'emg_api:publications', 'findme', 'pub_title', 5),
        ]
    )
    @pytest.mark.django_db
    def test_search(self, live_server, client,
                    _model, _view, search_term, search_attr, counts):
        view_name = _view.split(":")[1]
        klass = getattr(importlib.import_module("emg_api.models"), _model)
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
            assert d['type'] == _model
            assert d['attributes'][search_attr] == "%s findme" % _model
            assert not d['attributes'][search_attr] == "%s hideme" % _model
