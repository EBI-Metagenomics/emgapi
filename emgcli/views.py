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

from django.views.generic.base import TemplateView


class Handler500(TemplateView):
    template_name = "rest_framework/500.html"

    @classmethod
    def as_error_view(cls):
        v = cls.as_view()

        def view(request):
            return v(request).render()
        return view

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return super(TemplateView, self) \
            .render_to_response(context, status=500)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return super(TemplateView, self) \
            .render_to_response(context, status=500)
