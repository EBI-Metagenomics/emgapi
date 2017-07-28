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

from emgapimetadata import serializers as m_serializers

from emgapimetadata import models as m_models


@pytest.mark.usefixtures('mongodb')
class TestAnnotations(object):

    @pytest.mark.parametrize(
        'accession, run_accession, pipeline_version',
        [
            ('GO0001', 'DRR066347', '3.0'),
            ('IPR0001', 'DRR066347', '3.0'),
        ]
    )
    def test_serializer(self, accession, run_accession, pipeline_version):
        instance = m_models.Annotation.objects.create(
            accession=accession,
            run_accession=run_accession,
            pipeline_version=pipeline_version,
        )

        serializer = m_serializers.AnnotationSerializer(instance)
        expected = {
            'id': accession,
            'accession': accession,
        }
        assert serializer.data == expected
