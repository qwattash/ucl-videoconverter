#!/usr/bin/python

from __future__ import absolute_import

import os

from celery import Celery

from django.conf import settings

"""
@see http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django
"""

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vrserver.settings')

app = Celery('vrserver')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

@app.task(bind=True)
def debugTask(self):
    print('Request: {0!r}'.format(self.request))
