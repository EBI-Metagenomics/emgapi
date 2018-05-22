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

from django.conf import settings

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


class NotifySerializer(serializers.Serializer):

    email = serializers.CharField(max_length=200)
    title = serializers.CharField(max_length=100)
    content = serializers.CharField(max_length=500)

    def create(self, validated_data):
        import requests
        n = ena_models.Notify(**validated_data)

        ticket = {
            "id": "ticket/new",
            "Queue": settings.RT['queue'],
            "Requestor": n.email,
            "Priority": "4",
            "Subject": n.title,
            "Text": n.content
        }

        content = [
            "{key}: {value}".format(
                key=key, value=value) for key, value in ticket.items()
        ]

        payload = {
            'user': settings.RT['user'],
            'pass': settings.RT['pass'],
            'content': "\n".join(content),
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        r = requests.post(settings.RT['url'], data=payload, headers=headers)
        return r.status_code

    class Meta:
        model = ena_models.Notify
        fields = '__all__'
