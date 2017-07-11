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

from django.contrib import admin
from django.conf.urls import include, url

from rest_framework.schemas import get_schema_view
# from rest_framework.renderers import CoreJSONRenderer

from rest_framework_swagger.views import get_swagger_view


schema_view = get_schema_view(
    title='EBI metagenomics API',
    # renderer_classes=[CoreJSONRenderer]
)

docs_schema_view = get_swagger_view(title='EBI metagenomics API')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [

    url(r'^$', schema_view),

    url(r'^admin/', admin.site.urls),

    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),

    url(r'^api/', include('emg_api.urls',
                          namespace='emg_api')),

    url(r'^docs/$', docs_schema_view),

    # url(r'^rest-auth/', include('rest_auth.urls')),

]
