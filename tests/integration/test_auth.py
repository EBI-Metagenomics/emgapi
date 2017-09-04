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
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from rest_framework import status
from rest_framework.test import APITestCase


class TestAuthAPI(APITestCase):

    def setUp(self):
        self.login_url = reverse('rest_auth_login')
        self.logout_url = reverse('rest_auth_logout')

    def tearDown(self):
        rsp = self.client.post(self.logout_url, format='json')
        assert rsp.status_code == status.HTTP_200_OK

    def test_default(self):
        data = {
            'username': 'username',
            'password': 'secret'
        }
        rsp = self.client.post(self.login_url, data=data, format='json')
        token = rsp.json()['data']['attributes']['key']
        assert rsp.status_code == status.HTTP_200_OK
        assert User.objects.count() == 1
        assert User.objects.get().username == 'username'
        assert Token.objects.get(user_id=User.objects.get().id).key == token

        rsp = self.client.post(
            self.logout_url,
            format='json'
        )
        assert rsp.status_code == status.HTTP_200_OK
        assert User.objects.count() == 1
        assert User.objects.get().username == 'username'
        with pytest.raises(Token.DoesNotExist):
            Token.objects.get(user_id=User.objects.get().id).key

    def test_bad_request(self):
        expected_rsp = [
            {
                'detail': 'This field is required.',
                'source': {
                    'pointer': '/data/attributes/password'
                },
                'status': '400'
            }
        ]
        rsp = self.client.post(self.login_url, data={}, format='json')
        assert rsp.status_code == status.HTTP_400_BAD_REQUEST
        assert rsp.json()['errors'] == expected_rsp
        assert User.objects.count() == 0
