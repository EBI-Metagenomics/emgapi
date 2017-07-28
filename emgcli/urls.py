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

# from django.contrib import admin
from django.conf.urls import include, url
from django.conf import settings
from django.views.generic import RedirectView

from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view


# schema_prefix
schema_view = get_schema_view(
    title=settings.EMG_TITLE, url=settings.EMG_URL,
    description=settings.EMG_DESC)

docs_schema_view = get_swagger_view(
    title=settings.EMG_TITLE, url=settings.EMG_URL)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [

    # url(r'^admin/', admin.site.urls),

    url(r'^$', RedirectView.as_view(
        pattern_name='emgapi:api-root', permanent=False)),

    url(r'^http-auth/', include('rest_framework.urls',
                                namespace='rest_framework')),

    url(r'^schema/', schema_view),

    url(r'^docs/', docs_schema_view),

    url(r'^v0.2/', include('emgapi.urls',
                           namespace='emgapi')),

    url(r'^api/', include('emgapimetadata.urls',
                          namespace='emgapimetadata')),

]
