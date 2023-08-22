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

import urllib

from rest_framework import serializers
from rest_framework.reverse import reverse


class DownloadHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        if obj.pk is None:
            return None
        kwargs = {}
        # if study
        if hasattr(obj, 'study') and hasattr(obj, 'pipeline'):
            kwargs = {
                'accession': obj.study.accession,
                'release_version': obj.pipeline.release_version,
            }
        # if analysis
        elif hasattr(obj, 'job'):
            kwargs = {
                'accession': obj.job.accession,
            }
        elif hasattr(obj, 'genome'):
            kwargs = {
                'accession': obj.genome.accession
            }
        elif hasattr(obj, 'genome_catalogue'):
            kwargs = {
                'catalogue_id': obj.genome_catalogue.catalogue_id,
            }
        elif hasattr(obj, 'assembly'):
            kwargs = {
                'accession': obj.assembly.accession
            }

        elif hasattr(obj, 'run'):
            kwargs = {
                'accession': obj.run.accession
            }
        kwargs['alias'] = obj.alias

        return reverse(
            view_name, kwargs=kwargs, request=request, format=format)


class IdentifierField(serializers.Field):

    def get_attribute(self, obj):
        return obj['var__var_name']

    def to_representation(self, obj):
        return obj.__class__.__name__


class PipelineToolHyperlinkedField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        kwargs = {
            'tool_name': obj.tool_name,
            'version': obj.version
        }
        return reverse(
            view_name, kwargs=kwargs, request=request, format=format)


class AnalysisJobHyperlinkedField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        kwargs = {
            'accession': obj.accession,
            'release_version': obj.pipeline.release_version
        }
        return reverse(
            view_name, kwargs=kwargs, request=request, format=format)


class AnalysisJobHyperlinkedRelatedField(serializers.HyperlinkedRelatedField):

    def get_url(self, obj, view_name, request, format):
        kwargs = {
            'accession': obj.accession,
            'release_version': obj.pipeline.release_version
        }
        return reverse(
            view_name, kwargs=kwargs, request=request, format=format)


class OrganismHyperlinkedIdentityField(serializers.HyperlinkedIdentityField):

    def get_url(self, obj, view_name, request, format):
        if hasattr(obj, 'pk') and obj.pk in (None, ''):
            return None

        lookup_value = urllib.parse.quote_plus(
            getattr(obj, self.lookup_field), safe='')
        kwargs = {self.lookup_url_kwarg: lookup_value}
        return reverse(
            view_name, kwargs=kwargs, request=request, format=format)
