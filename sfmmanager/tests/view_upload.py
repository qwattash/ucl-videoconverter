from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings

from sfmmanager import views
from sfmmanager.models import *
from sfmmanager.task_manager import *

from .base import *

import mock

import shutil
import os

# test file upload
class FileUploadTestCase(AuthUserTestCase):
    
    def setUp(self):
        super(FileUploadTestCase, self).setUp()

    def tearDown(self):
        Video.objects.filter(uid=self.user).delete()
        udata = UserData(self.user)
        if os.path.exists(udata.getStorageDir()):
            shutil.rmtree(udata.getStorageDir())
        super(FileUploadTestCase, self).tearDown()

    @mock.patch("sfmmanager.task_manager.TaskManager.run", mock.Mock())
    def test_unauth(self):
        self.deauth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])
        self.assertEqual(TaskManager.run.call_count, 0)

    @mock.patch("sfmmanager.task_manager.TaskManager.run", mock.Mock())
    def test_upload_new(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Job submitted"])
        self.assertEqual(TaskManager.run.call_count, 1)

    @mock.patch("sfmmanager.task_manager.TaskManager.run", mock.Mock())
    def test_upload_existing(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Job submitted"])
        TaskManager.run.reset_mock()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Job already exists"])
        self.assertEqual(TaskManager.run.call_count, 0)

    @mock.patch("sfmmanager.task_manager.TaskManager.run", mock.Mock())
    def test_invalid_form(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'wrongparam': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Invalid form format"])
        self.assertEqual(TaskManager.run.call_count, 0)

    @mock.patch("sfmmanager.task_manager.TaskManager.run", mock.Mock())
    def test_invalid_request(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.get("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Invalid request"])
        self.assertEqual(TaskManager.run.call_count, 0)
