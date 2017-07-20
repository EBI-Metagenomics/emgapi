#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Content Negotiation
# http://www.django-rest-framework.org/api-guide/content-negotiation/

# Workaround for "Could not satisfy the request Accept header."
# Incompatibility with Django Rest Swagger
# https://github.com/django-json-api/django-rest-framework-json-api/issues/314

from rest_framework.negotiation import DefaultContentNegotiation


class CustomContentNegotiation(DefaultContentNegotiation):

    def get_accept_list(self, request):
        """
        Given the incoming request, return a tokenized list of media
        type strings.

        Note:
            This method is customized: it includes
            ['application/vnd.api+json'] at the end
            to allow django-rest-swagger to render
            django-rest-json-api style api's.
        """
        header = request.META.get('HTTP_ACCEPT', '*/*')
        accept = ['application/vnd.api+json']
        return [token.strip() for token in header.split(',')] + accept
