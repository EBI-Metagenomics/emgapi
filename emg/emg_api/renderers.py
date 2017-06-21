# -*- coding: utf-8 -*-

# from rest_framework.renderers import JSONRenderer
from rest_framework_json_api.renderers import JSONRenderer


class VersionRenderer(JSONRenderer):
    media_type = 'application/vnd.api+json'


class DefaultRenderer(JSONRenderer):
    media_type = 'application/json'
