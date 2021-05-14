# -*- coding: utf-8 -*-

# Copyright 2020 EMBL - European Bioinformatics Institute
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
