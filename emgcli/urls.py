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
from django.conf import settings
from django.contrib.auth import views
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

from rest_framework import status
from rest_framework.schemas import get_schema_view
from rest_framework.renderers import BaseRenderer, JSONRenderer

from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_jwt.views import verify_jwt_token

from emgapi.urls import router as emg_router
from emgapi.urls import mydata_router, utils_router, urlpatterns as emgapi_urlpatterns 
from emgapianns.urls import mongo_router, urlpatterns as mongo_urlpatterns
from emgapianns.urls import router as emg_ext_router

from openapi_codec import OpenAPICodec

from . import routers
from .views import Handler500
from emgui.forms import CustomAuthenticationForm


handler500 = Handler500.as_error_view()


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
    description=settings.EMG_DESC,
    renderer_classes=[OpenAPIRenderer]
)

# merge all routers
router = routers.DefaultRouter(trailing_slash=False)
router.extend(emg_router)
router.extend(emg_ext_router)
router.extend(mongo_router)
router.extend(mydata_router)
router.extend(utils_router)

custom_login_view = views.LoginView
custom_login_view.form_class = CustomAuthenticationForm

urlpatterns = [
    url(r'^http-auth/login_form$', custom_login_view.as_view(
        template_name='rest_framework/login_form.html'), {}),

    url(r'^http-auth/', include('rest_framework.urls',
                                namespace='rest_framework')),
]

# API authentication routing.
urlpatterns += [

    url(r'^schema/$', schema_view, name="schema_view"),

    url(r'^docs/',
        TemplateView.as_view(template_name='swagger-ui/index.html')),

    url(r'^500/$', TemplateView.as_view(template_name='500.html')),
]

# API URL routing.
urlpatterns += [

    url(r'^$', RedirectView.as_view(
        pattern_name='emgapi_v1:api-root', permanent=False)),

    url(r'^v1/', include((router.urls, 'emgapi_v1'), namespace='emgapi_v1')),

    url(r'^v1/utils/token/obtain', obtain_jwt_token,
        name='obtain_jwt_token_v1'),

    url(r'^v1/utils/token/verify', verify_jwt_token,
        name='verify_jwt_token_v1'),
]

urlpatterns += mongo_urlpatterns
urlpatterns += emgapi_urlpatterns

# admin
if settings.ADMIN:
    urlpatterns += [
        url('grappelli/', include('grappelli.urls')),
        url('admin/', admin.site.urls),
    ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
