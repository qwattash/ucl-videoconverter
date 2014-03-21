from django.test import TestCase

from django.conf import settings
from django.test.utils import override_settings

from sfmmanager.models import *
from sfmmanager.storage_utils import ResourceData, UserData, PlyHeader
from sfmmanager.tasks import *

import mock

import shutil
import os
########## celery tasks are tested

#override celery production settings
"""
@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')

class CeleryTestCase(TestCase):
    
    def setUp(self):
        #create dummy user
        self.user = User.objects.create_user("debug_user", "", "debug_user")
        self.user.save()
        self.udata = UserData(self.user)
    
    def tearDown(self):
        self.user.delete()

@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class ExtractFramesTestCase(CeleryTestCase):

    SAMPLE_FILE = "testing/samples/ffmpeg/c4ea9969cd299e73eccc37e918b59fa4.mp4"
    FILE_HASH = "c4ea9969cd299e73eccc37e918b59fa4"
    def setUp(self):
        super(ExtractFramesTestCase, self).setUp()
        self.path = os.path.join(self.udata.getStorageDir(), ExtractFramesTestCase.FILE_HASH)
        self.data_path = self.path + "_data"
        os.mkdir(self.udata.getStorageDir())
        os.mkdir(self.data_path)
        #shutil.copytree(os.path.join(settings.MEDIA_ROOT, "testing/template_dir"), self.data_path)
        self.tempfile = File(open(os.path.join(settings.MEDIA_ROOT, ExtractFramesTestCase.SAMPLE_FILE)))
        self.tempfile.name = "dummy.mp4"
        self.video = Video()
        self.video.data = self.tempfile
        self.video.uid = self.user
        self.video.vname = "dummy.mp4"
        self.video.vhash = ExtractFramesTestCase.FILE_HASH
        self.video.status = Video.STATUS_PENDING
        self.video.save()

    def tearDown(self):
        Video.objects.filter(uid=self.user).delete()
        shutil.rmtree(self.udata.getStorageDir())
        super(ExtractFramesTestCase, self).tearDown()

    def test_extract_frames(self):
        from celery import Celery
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vrserver.settings')
        
        app = Celery('vrserver')
        app.config_from_object('django.conf:settings')
        app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

        result = extractFrames(self.video.id)
        print result.status
        print os.listdir(self.data_path)
        
"""
