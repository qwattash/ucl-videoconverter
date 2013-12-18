from django.db import models
from django.conf import settings

from django.contrib.auth.models import User

import tasks
from celery import chain

import os

class Video(models.Model):

    STATUS_RECONSTRUCTED = 1
    STATUS_PENDING = 2
    STATUS_ERROR = 3
    STATUS_FORBIDDEN = 4
    STATUS_UNKNOWN = 5
    STATUS_EXTRACT_FRAMES = 6
    STATUS_WORKING = 7
    STATUS_CONVERTING_OUTPUT = 8

    VIDEO_STATUS = (
        (STATUS_RECONSTRUCTED, "Reconstructed"),
        (STATUS_PENDING, "Pending"),
        (STATUS_WORKING, "Working"),
        (STATUS_ERROR, "Error"),
        (STATUS_FORBIDDEN, "Forbidden"),
        (STATUS_UNKNOWN, "Unknown"),
    )

    uid = models.ForeignKey(User)
    vname = models.CharField(max_length=256)
    #md5 video checksum
    vhash = models.CharField(max_length=64)
    #status informations
    status = models.CharField(max_length=1, choices=VIDEO_STATUS, default=STATUS_PENDING)
    #video data file
    data = models.FileField(upload_to=lambda instance, filename: Video.generate_file_name(instance, filename), null=True)

    """
    generate file name for given instance, self identifies the instance
    """
    def generate_file_name(self, filename):
        base = os.path.normpath(settings.MEDIA_ROOT)
        root, ext = os.path.splitext(filename)
        name = self.vhash + ext
        path = os.path.join(base, str(self.uid.id), name)
        return path
    
    """
    Process video
    processing is done usinga celery task chain
    priority and numberof runing tasks can be configured
    in the celery module
    """
    def process(self):
        #res = tasks.extractFrames.apply_async((self.id,))
        res = chain(tasks.extractFrames.s(self.id), 
                    tasks.processFrames.s(), 
                    tasks.processOutput.s())()
