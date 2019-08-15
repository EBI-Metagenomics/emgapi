#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2019 EMBL - European Bioinformatics Institute
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

from rest_framework_json_api import pagination
from django.core.paginator import Paginator
from django.utils.functional import cached_property


class DefaultPagination(pagination.PageNumberPagination):

    page_size = 25
    max_page_size = 250


class FasterDjangoPaginator(Paginator):
    """
    DjangoPaginator override.
    This class overrides the count method, selecting only the PK
    this makes the count faster as it doesn't need to fetch all
    the cols just to do a count.
    """

    @cached_property
    def count(self):
        # Only get the pk to make the pagination faster
        return self.object_list.values('pk').count()


class FasterCountPagination(pagination.PageNumberPagination):

    page_size = 25
    max_page_size = 250
    django_paginator_class = FasterDjangoPaginator
