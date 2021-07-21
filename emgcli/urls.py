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

from django.urls import include, path
from django.conf.urls import url
from django.conf import settings
from django.contrib.auth import views
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView

from rest_framework_jwt.views import obtain_jwt_token
from rest_framework_jwt.views import verify_jwt_token

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from emgapi.urls import router as emg_router
from emgapi.urls import mydata_router, utils_router, urlpatterns as emgapi_urlpatterns 
from emgapianns.urls import mongo_router, urlpatterns as mongo_urlpatterns
from emgapianns.urls import router as emg_ext_router


from . import routers
from .views import Handler500
from emgui.forms import CustomAuthenticationForm


handler500 = Handler500.as_error_view()


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
    path('http-auth/login_form', custom_login_view.as_view(
        template_name='rest_framework/login_form.html'), {}),

    path(r'http-auth/', include('rest_framework.urls',
                                namespace='rest_framework')),
]

# API authentication routing.
urlpatterns += [
    path(r'500/', TemplateView.as_view(template_name='500.html')),
]

# API URL routing.
urlpatterns += [

    path(r'', RedirectView.as_view(
        pattern_name='emgapi_v1:api-root', permanent=False)),

    path(r'v1/', include((router.urls, 'emgapi_v1'), namespace='emgapi_v1')),

    path(r'v1/utils/token/obtain', obtain_jwt_token,
        name='obtain_jwt_token_v1'),

    path(r'v1/utils/token/verify', verify_jwt_token,
        name='verify_jwt_token_v1'),
]

urlpatterns += mongo_urlpatterns
urlpatterns += emgapi_urlpatterns
urlpatterns += [
    path(r'schema/', SpectacularAPIView.as_view(), name='schema'),
    path(r'docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# admin
if settings.ADMIN:
    urlpatterns += [
        path('grappelli/', include('grappelli.urls')),
        path('admin/', admin.site.urls),
    ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path(r'__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
