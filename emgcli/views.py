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

from django.middleware import csrf
from django.views.generic.base import TemplateView
from rest_framework.response import Response
from rest_framework.views import APIView


class ObtainCSRFToken(APIView):

    def get(self, request, *args, **kwargs):
        token = csrf.get_token(request)
        return Response(token)


obtain_csrf_token = ObtainCSRFToken.as_view()


class Handler500(TemplateView):
    template_name = "rest_framework/500.html"

    @classmethod
    def as_error_view(cls):
        v = cls.as_view()

        def view(request):
            return v(request).render()
        return view


handler500 = Handler500.as_error_view()
