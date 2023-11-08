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
import json

from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import validate_email
from rest_framework.exceptions import ValidationError

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


class EmailSerializer(serializers.Serializer):
    from_email = serializers.EmailField(required=True)
    subject = serializers.CharField(required=True)
    message = serializers.CharField(required=True)

    def create(self, validated_data):
        validated_data['recipient_list'] = (settings.EMAIL_HELPDESK,)
        logger.info("Email %r" % validated_data)
        send_mail(**validated_data)

    class Meta:
        model = ena_models.Notify
        fields = '__all__'


class NotifySerializer(serializers.Serializer):
    from_email = serializers.CharField(max_length=200, required=True)
    cc = serializers.CharField(max_length=200, allow_blank=True, required=False)
    subject = serializers.CharField(max_length=500, required=True)
    message = serializers.CharField(max_length=1000, required=True)
    is_consent = serializers.BooleanField(default=False, required=False)

    def is_valid(self):
        for field in ['from_email', 'cc']:
            if field not in self.initial_data:
                continue
            for email in self.initial_data[field].split(','):
                email = email.strip()
                if email == '':
                    continue
                try:
                    validate_email(email)
                except ValidationError as exc:
                    self.errors.append(exc.detail)
                    return False
        return super().is_valid()

    def create(self, validated_data):
        """Create an RT ticket in EMG queue
        Note: remember to setup valid credentials (i.e. url, user and token token) in the config.rt
        """
        import requests
        n = ena_models.Notify(**validated_data)

        emg_queue = settings.RT["emg_queue"]

        ticket = {
            "Requestor": n.from_email,
            "Priority": "4",
            "Subject": n.subject,
            "Content": n.message.replace("\n", ';')
        }
        if n.cc:
            ticket["Cc"] = n.cc

        if n.is_consent:
            return 404
        else:
            ticket["Queue"] = emg_queue

        logger.info("Ticket %r" % ticket)

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'token ' + settings.RT['token']
        }

        r = requests.post(
            settings.RT['url'],
            data=json.dumps(ticket),
            headers=headers
        )
        return r.status_code

    class Meta:
        model = ena_models.Notify
        fields = '__all__'
