from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files.base import ContentFile

from sfmmanager import views
from sfmmanager.models import *
from sfmmanager.storage_utils import ResourceData, UserData
from .base import *

import shutil
import os

# test log download
class DumpLogTestCase(AuthUserTestCase):
    
    DEBUG_FILE_NAME = "37c4b87edffc5d198ff5a185cee7ee09"
    def setUp(self):
        super(DumpLogTestCase, self).setUp()
        self.udata = UserData(self.user)
        self.path = os.path.join(self.udata.getStorageDir(), DumpLogTestCase.DEBUG_FILE_NAME)
        self.data_path = self.path + "_data"
        os.mkdir(self.udata.getStorageDir())
        shutil.copytree(os.path.join(settings.MEDIA_ROOT, "testing/template_dir"), self.data_path)
        self.tempfile = ContentFile("The quick brown fox jumps over the lazy dog")
        self.tempfile.name = "dummy"
        self.video = Video()
        self.video.data = self.tempfile
        self.video.uid = self.user
        self.video.vname = "dummy"
        self.video.vhash = DumpLogTestCase.DEBUG_FILE_NAME
        self.video.status = Video.STATUS_RECONSTRUCTED
        self.video.save()
    
    def tearDown(self):
        Video.objects.filter(uid=self.user).delete()
        shutil.rmtree(self.udata.getStorageDir())
        super(DumpLogTestCase, self).tearDown()

    def test_unauth(self):
        self.deauth()
        response = self.client.get("/uclvr/log", {'name': 'dummy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_DOWNLOAD)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])

    def test_unexisting_video(self):
        self.auth()
        response = self.client.get("/uclvr/log", {'name': 'unexisting', 'type': 'ffmpeg'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_DOWNLOAD)
        self.assertEqual(response.context['payload'], ["Resource not existing or not yet ready"])

    def test_unexisting_log(self):
        self.auth()
        response = self.client.get("/uclvr/log", {'name': 'dummy', 'type': 'wrong'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_DOWNLOAD)
        self.assertEqual(response.context['payload'], ["Unexisting log file"])

    def test_success(self):
        self.auth()
        response = self.client.get("/uclvr/log", {'name': 'dummy', 'type': 'ffmpeg'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), "attachment; filename=ffmpeg.log")
        self.assertEqual(response.get('X-Sendfile'), os.path.join(self.data_path, "log/ffmpeg.log"))
