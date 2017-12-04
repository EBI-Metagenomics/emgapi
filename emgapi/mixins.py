#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import get_object_or_404
from django.http.response import StreamingHttpResponse

from rest_framework.response import Response

from emgapi.renderers import CSVStreamingRenderer


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


class ListModelMixin(object):
    """
    List a queryset.
    """

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if isinstance(request.accepted_renderer, CSVStreamingRenderer):
            response = StreamingHttpResponse(
                request.accepted_renderer.render({
                    'queryset': queryset,
                    'serializer': self.get_serializer_class(),
                    'context': {'request': request},
                }), content_type='text/csv')
            try:
                filename = queryset.model.__name__
            except AttributeError:
                try:
                    filename = queryset._name
                except AttributeError:
                    filename = queryset._document.__name__
            response['Content-Disposition'] = \
                'attachment; filename="{}.csv"'.format(filename)
            return response

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
