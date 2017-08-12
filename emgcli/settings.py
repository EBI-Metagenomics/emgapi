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


"""
Django settings for emg project.

Generated by 'django-admin startproject' using Django 1.11.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import sys
import os
import warnings
import logging
import binascii

from os.path import expanduser

try:
    from YamJam import yamjam, YAMLError
except ImportError:
    raise ImportError("Install yamjam. Run `pip install -r requirements.txt`")

logger = logging.getLogger(__name__)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAR_DIR = os.path.join(expanduser("~"), 'emgvar') 


LOGDIR = os.path.join(VAR_DIR, 'log')
if not os.path.exists(LOGDIR):
    os.makedirs(LOGDIR)

LOGGING_CLASS = 'cloghandler.ConcurrentRotatingFileHandler'
LOGGING_FORMATER = (
    '%(asctime)s %(levelname)5.5s [%(name)30.30s]'
    ' (proc.%(process)5.5d) %(funcName)s:%(lineno)d %(message)s')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'default': {
            'format': LOGGING_FORMATER
        },
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': LOGGING_CLASS,
            'filename': os.path.join(LOGDIR, 'emg.log').replace('\\', '/'),
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 10,
            'formatter': 'default',
        },
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'default',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {  # Stop SQL debug from logging to main logger
            'handlers': ['default', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': True
        },
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
try:
    SECRET_KEY
except NameError:
    dir_fd = os.open(VAR_DIR, os.O_RDONLY)

    def opener(path, flags, mode=0o600):
        return os.open(path, flags, mode, dir_fd=dir_fd)

    key_path = os.path.join(VAR_DIR, 'secret.key')
    if not os.path.exists(key_path):
        with open(key_path, 'w', opener=opener) as f:
            print(binascii.hexlify(os.urandom(50)).decode('ascii'), file=f)
    with open(key_path, 'r', opener=opener) as f:
        SECRET_KEY = f.read()
    os.close(dir_fd)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # 'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    # UI
    'emgui',
    # CORS
    'corsheaders',
    # rest framework
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'django_filters',
    'rest_auth',
    # apps
    'emgapi',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Simplified static file serving.
    # https://warehouse.python.org/project/whitenoise/
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Django CORS middleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'emgcli.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'emgcli.wsgi.application'

# Security
ALLOWED_HOSTS = ["*"]
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_SECURE = True
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r'^/api/.*$'
# CORS_URLS_ALLOW_ALL_REGEX = ()
CORS_ALLOW_METHODS = (
    'GET',
    'OPTIONS'
)


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(VAR_DIR, 'db.sqlite3'),
#     }
# }
try:
    DATABASES = yamjam()['emg']['databases']
except KeyError:
    raise KeyError("Config must container default database.")

try:
    SESSION_ENGINE = yamjam()['emg']['session_engine']
except KeyError:
    warnings.warn("SESSION_ENGINE not configured, using default",
                  RuntimeWarning)

try:
    CACHES = yamjam()['emg']['caches']
except KeyError:
    pass

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Django Rest Framewrk

REST_FRAMEWORK = {

    'PAGE_SIZE': 20,

    'EXCEPTION_HANDLER':
        'rest_framework_json_api.exceptions.exception_handler',

    'DEFAULT_PAGINATION_CLASS':
        # 'rest_framework.pagination.PageNumberPagination',
        'rest_framework_json_api.pagination.PageNumberPagination',

    'DEFAULT_PARSER_CLASSES': (
        'rest_framework_json_api.parsers.JSONParser',
        'rest_framework.parsers.JSONParser',
        # 'rest_framework_xml.parsers.XMLParser',
        # 'rest_framework_yaml.parsers.YAMLParser',
        # 'rest_framework.parsers.MultiPartParser'
    ),

    'DEFAULT_RENDERER_CLASSES': (
        'emgapi.renderers.DefaultJSONRenderer',
        'rest_framework_json_api.renderers.JSONRenderer',
        # 'rest_framework.renderers.JSONRenderer',
        # 'rest_framework_xml.renderers.XMLRenderer',
        # 'rest_framework_yaml.renderers.YAMLRenderer',
        # 'rest_framework_csv.renderers.CSVRenderer',
        # 'rest_framework.renderers.BrowsableAPIRenderer',
    ),

    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),

    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    'DEFAULT_METADATA_CLASS':
        'rest_framework_json_api.metadata.JSONAPIMetadata',

    'DEFAULT_AUTHENTICATION_CLASSES': (
        # 'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    # 'DEFAULT_CONTENT_NEGOTIATION_CLASS':
    #     'emgapi.negotiation.CustomContentNegotiation',

}

JSON_API_FORMAT_KEYS = 'dasherize'
JSON_API_FORMAT_TYPES = 'dasherize'
JSON_API_PLURALIZE_TYPES = True

# Swagger auth
# Toggles the use of Django Auth as an authentication mechanism.
# Note: The login/logout button relies on the LOGIN_URL and LOGOUT_URL
# settings These can either be configured under SWAGGER_SETTINGS or Django settings.
LOGIN_URL = 'rest_framework:login'
LOGOUT_URL = 'rest_framework:logout'

SWAGGER_SETTINGS = {
    'ENABLED_METHODS': [
        'get',
        'post',
    ],
    'SECURITY_DEFINITIONS': {
        # 'basic': {
        #     'type': 'basic'
        # }
    },
    'USE_SESSION_AUTH': True,
}

# Custom settings
try:
    EMG_DEFAULT_LIMIT = REST_FRAMEWORK['PAGE_SIZE']
except:
    EMG_DEFAULT_LIMIT = 20

# Authentication backends
AUTHENTICATION_BACKENDS = (
    'emgapi.backends.EMGBackend',
)

try:
    EMG_BACKEND_AUTH_URL = yamjam()['emg']['emg_backend_auth']
except KeyError:
    EMG_BACKEND_AUTH_URL = None


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
try:
    FORCE_SCRIPT_NAME = yamjam()['emg']['prefix']
except KeyError:
    FORCE_SCRIPT_NAME = ''

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '%s/static/' % FORCE_SCRIPT_NAME.rstrip('/')
