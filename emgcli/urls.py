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
from django.views.generic import TemplateView

from rest_framework import status
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import BaseRenderer, JSONRenderer

from rest_auth import views as rest_auth_views

from emgapi.urls import router as emg_router
from emgapi.urls import mydata_router
from emgapianns.urls import mongo_router
from emgapianns.urls import router as emg_ext_router

from openapi_codec import OpenAPICodec

from . import routers


api_version = settings.REST_FRAMEWORK['DEFAULT_VERSION']


# merge all routers
router = routers.DefaultRouter(trailing_slash=False)
router.extend(emg_router)
router.extend(emg_ext_router)
router.extend(mongo_router)
router.extend(mydata_router)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [

    # url(r'^admin/', admin.site.urls),

    url(r'^$', RedirectView.as_view(
        pattern_name='emgapi:api-root', permanent=False)),

    url(r'^500$', TemplateView.as_view(template_name='500.html')),

    url(r'^http-auth/', include('rest_framework.urls',
                                namespace='rest_framework')),

    url(
        r'^v%s/auth/login' % api_version,
        rest_auth_views.LoginView.as_view(),
        name='rest_auth_login'
    ),

    url(
        r'^v%s/auth/logout' % api_version,
        rest_auth_views.LogoutView.as_view(),
        name='rest_auth_logout'
    ),

    url(r'^v%s/' % api_version, include(router.urls,
                                        namespace='emgapi')),

]


class OpenAPIRenderer(BaseRenderer):
    media_type = 'application/openapi+json'
    charset = None
    format = 'openapi'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context['response'].status_code != status.HTTP_200_OK:
            return JSONRenderer().render(data)
        return OpenAPICodec().encode(data)


schema_view = get_schema_view(
    title=settings.EMG_TITLE, url=settings.EMG_URL,
    description=settings.EMG_DESC, renderer_classes=[OpenAPIRenderer]
)


urlpatterns += [

    url(r'^schema/$', schema_view, name="schema_view"),

    url(r'^docs/',
        TemplateView.as_view(template_name='swagger-ui/index.html')),

]
