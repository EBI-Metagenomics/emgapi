#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018 EMBL - European Bioinformatics Institute
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


import logging

from rest_framework_json_api import serializers

from . import models as ena_models

logger = logging.getLogger(__name__)


class SubmitterSerializer(serializers.Serializer):

    first_name = serializers.CharField(max_length=30)
    surname = serializers.CharField(max_length=50)
    email_address = serializers.CharField(max_length=200)

    analysis = serializers.BooleanField(default=False)
    submitter = serializers.BooleanField(default=False)

    class Meta:
        model = ena_models.Submitter
        fields = '__all__'
