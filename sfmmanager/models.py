from django.db import models
from django.conf import settings

from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from sfmmanager.storage_utils import *

import os

#constant for the maximum number of uploadable videos by an user
USER_MAX_FILES = 200

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
        (STATUS_CONVERTING_OUTPUT, "Converting"),
    )

    uid = models.ForeignKey(User)
    vname = models.CharField(max_length=256)
    #md5 video checksum
    vhash = models.CharField(max_length=64)
    #status informations
    status = models.CharField(max_length=1, choices=VIDEO_STATUS, default=STATUS_PENDING)
    #video data file
    data = models.FileField(upload_to=lambda instance, filename: Video.generate_file_name(instance, filename), null=True)
    #number of frames per second to extract from the video
    num_extract_fps = models.IntegerField(default=1)

    """
    generate file name for given instance, self identifies the instance
    """
    def generate_file_name(self, filename):
        res = UserData(self.uid)
        root, ext = os.path.splitext(filename)
        name = self.vhash + ext
        path = res.joinPath(name)
        return path
    
"""
handle Video creation signal to create the parameters for it
http://www.martin-geber.com/thought/2007/10/29/django-signals-vs-custom-save-method/
generate default parameters for the reconstruction of the video and attach them to this
video
"""
@receiver(post_save, sender=Video)
def onCreate(sender, instance, created, **kwargs):
    if created:
        # the video has been created for the first time
        # number of frames extracted per second
        paramFPS = Parameter(vid=instance, name=Parameter.PARAM_FPS)
        paramFPS.reset()

@receiver(post_delete, sender=Video)
def deleteHandler(sender, **kwargs):
    video = kwargs['instance']
    path = video.data.url
    resource = ResourceData(path)
    resource.clear()
    if os.path.exists(path):
        os.remove(path)

"""
model for configuration parameters
each parameter is of the form key->value and has a video associated
Currently it is not possible to
"""
class Parameter(models.Model):
    
    """
    parameter names
    """
    PARAM_FPS = 'frames'
    
    """
    map param names to their default value
    """
    DEFAULTS = {
        PARAM_FPS: '1'
        }

    name = models.CharField(max_length=256, null=False, default=None)
    value = models.CharField(max_length=256, null=False, default=None)
    vid = models.ForeignKey(Video)

    def reset(self):
        self.value = Parameter.DEFAULTS.get(self.name, None)
        self.save()

    def validate(self, param):
        if self.name == Parameter.PARAM_FPS:
            try:
                toInt = int(param)
                return True
            except ValueError:
                # account for non int values
                return False
            except TypeError:
                # account for NoneType param value
                return False
        else:
            return False
