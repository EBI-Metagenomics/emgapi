#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http.response import StreamingHttpResponse
from rest_framework.exceptions import APIException

from rest_framework.response import Response

from emgapi.renderers import CSVStreamingRenderer, EMGBrowsableAPIRenderer
from rest_framework_json_api.renderers import JSONRenderer


class MultipleFieldLookupMixin(object):
    """
    Apply this mixin to any view or viewset to get multiple field filtering
    based on a `lookup_fields` attribute, instead of the default single field
    filtering.
    Source: http://www.django-rest-framework.org/api-guide/generic-views/
    """

    def get_object(self):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        filter = {}
        for field in self.lookup_fields:
            if self.kwargs[field]:
                filter[field] = self.kwargs[field]
        return get_object_or_404(queryset, **filter)


class ExcessiveCSVException(APIException):
    status_code = 413
    default_detail = 'The requested data is too long to be returned as a single CSV. ' \
                     'Please use the API to fetch paginated data. ' \
                     'E.g. https://gist.github.com/SandyRogers/5d9eff7f1f7b08cfa40265f5e2adf9cd'
    default_code = 'payload_too_large'


class ListModelMixin(object):
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if isinstance(request.accepted_renderer, CSVStreamingRenderer):

            if queryset.count() > 50 * settings.EMG_DEFAULT_LIMIT:
                # More than 50 pages of results will probably timeout
                # (for a complicated endpoint like Studies).
                # Return custom exception detailing use of paginated API.
                if request.accepts('text/html'):
                    request.accepted_renderer = EMGBrowsableAPIRenderer()
                else:
                    request.accepted_renderer = JSONRenderer()
                raise ExcessiveCSVException

            try:
                filename = queryset.model.__name__
            except AttributeError:
                try:
                    filename = queryset._name
                except AttributeError:
                    filename = queryset._document.__name__
            serializer = self.get_serializer(queryset, many=True)
            response = StreamingHttpResponse(request.accepted_renderer.render(serializer.data), content_type='text/csv')
            response['Content-Disposition'] = \
                'attachment; filename="{}.csv"'.format(filename)
            return response

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
