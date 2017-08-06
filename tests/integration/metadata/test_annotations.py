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

import pytest

from django.core.urlresolvers import reverse

from rest_framework import status

from mongoengine.errors import NotUniqueError

from emgapimetadata import models as m_models


@pytest.mark.usefixtures('mongodb')
class TestAnnotations(object):

    def test_default(self, client):
        self.annotations = [
            {'accession': 'GO0001', 'run_accession': 'DRR066347',
             'description': 'abc', 'count': 123},
            {'accession': 'GO0001', 'run_accession': 'DRR066355',
             'description': 'abc', 'count': 345},
            {'accession': 'IPR0001', 'run_accession': 'DRR066347',
             'description': 'cde', 'count': 567},
            {'accession': 'IPR0001', 'run_accession': 'DRR066355',
             'description': 'efg', 'count': 789},
        ]
        anns = list()
        for a in self.annotations:
            anns.append(m_models.Annotation(
                accession=a['accession'],
                run_accession=a['run_accession'],
                description=a['description'],
                count=a['count']
            ))
        m_models.Annotation.objects.insert(anns)
        assert len(m_models.Annotation.objects.all()) == 4

        url = reverse("emgapimetadata:annotations-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        rsp = response.json()
        assert len(rsp['data']) == 4

    @pytest.mark.parametrize(
        'accession, run_accession, description, count',
        [
            pytest.mark.xfail(
                ('IPR0001', 'DRR066355', 'abc', 1),
                raises=NotUniqueError),
        ]
    )
    def test_unique(self, accession, run_accession,
                    description, count):
        m_models.Annotation.objects.create(
            accession=accession,
            run_accession=run_accession,
            description=description,
            count=count
        )
