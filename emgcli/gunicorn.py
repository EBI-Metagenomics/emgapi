#!/usr/bin/env python
# -*- coding: utf-8 -*-

# example http://docs.gunicorn.org/en/latest/custom.html


from __future__ import unicode_literals

import multiprocessing

import gunicorn.app.base

from gunicorn.six import iteritems

import os
from os.path import expanduser

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emgcli.settings")

application = get_wsgi_application()


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    options = {
        'pid': os.path.join(expanduser("~"), 'emgvar', 'django.pid'),
        'bind': '%s:%s' % ('0.0.0.0', '8000'),
        'workers': number_of_workers(),
        'timeout': '30',
        'max-requests': '0',
    }
    StandaloneApplication(application, options).run()


if __name__ == '__main__':
    main()
