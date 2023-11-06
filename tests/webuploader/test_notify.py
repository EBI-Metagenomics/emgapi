# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

import sys

from django.urls import reverse
from django.conf import settings

from rest_framework.test import APITestCase

import pytest
import responses
import json

from test_utils.emg_fixtures import *  # noqa


@pytest.mark.django_db
class TestNotify(APITestCase):

    def get_token(self):
        data = {
            'username': 'username',
            'password': 'secret',
        }

        rsp = self.client.post(
            reverse('obtain_jwt_token_v1'), data=data, format='json')
        token = rsp.json()['data']['token']
        return token

    @responses.activate
    @pytest.mark.skipif(sys.version_info < (3, 6), reason="requires python3.6 or higher")
    def test_notify_not_consent(self):
        """Test notify endpoint for non-consent requests
        """
        expected_body = {
            "Requestor": "fake@email.com",
            "Priority": "4",
            "Subject": "Test email subject",
            "Content": "Hi this is just an example",
            "Queue": settings.RT["emg_queue"]
        }

        responses.add(
            responses.POST,
            settings.RT["url"],
            status=200)
        post_data = {
            "from_email": "fake@email.com",
            "subject": "Test email subject",
            "message": "Hi this is just an example"
        }

        self.client.post(
            reverse('emgapi_v1:csrf-notify'),
            data=post_data, format='json',
            HTTP_AUTHORIZATION='Bearer {}'.format(self.get_token())
        )

        assert len(responses.calls) == 1
        call = responses.calls[0]
        assert call.request.url == settings.RT["url"]
        assert call.request.body == json.dumps(expected_body)