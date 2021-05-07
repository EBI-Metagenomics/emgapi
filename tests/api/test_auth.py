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

from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase


class TestTokenAuthAPI(APITestCase):

    def test_default_token(self):
        data = {
            'username': 'username',
            'password': 'secret',
        }

        rsp = self.client.post(
            reverse('obtain_jwt_token_v1'), data=data, format='json')
        token = rsp.json()['data']['token']
        assert rsp.status_code == status.HTTP_200_OK

        data = {
            'token': token,
        }

        rsp = self.client.post(
            reverse('verify_jwt_token_v1'), format='json', data=data)
        assert rsp.status_code == status.HTTP_200_OK

        rsp = self.client.get(
            reverse('emgapi_v1:mydata-list'),
            HTTP_AUTHORIZATION='Bearer {}'.format(token)
        )
        assert rsp.status_code == status.HTTP_200_OK

    def test_invalid_credentials(self):
        error = {
            'non_field_errors':
                ['Unable to log in with provided credentials.']
        }
        data = {
            'username': 'abc',
            'password': '123',
        }

        rsp = self.client.post(
            reverse('obtain_jwt_token_v1'), data=data, format='json')
        assert rsp.json()['errors'] == error
        assert rsp.status_code == status.HTTP_400_BAD_REQUEST

    def test_unauthorized(self):
        error = [
            {
                'detail': 'Error decoding signature.',
                'source': {
                    'pointer': '/data'
                },
                'status': '401',
                'code': 'authentication_failed',
            }
        ]

        rsp = self.client.get(
            reverse('emgapi_v1:mydata-list'),
            HTTP_AUTHORIZATION='Bearer 12345'
        )
        assert rsp.status_code == status.HTTP_401_UNAUTHORIZED
        assert rsp.json()['errors'] == error
        assert User.objects.count() == 0
