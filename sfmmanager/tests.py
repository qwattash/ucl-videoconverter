from django.test import TestCase

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.conf import settings
from django.core.files.base import ContentFile

from sfmmanager import views
from sfmmanager.models import Video
from sfmmanager.storage_utils import ResourceData, UserData, PlyHeader

import shutil
import os

# authentication test view
class AuthTestCase(TestCase):
    
    def setUp(self):
        #create dummy user
        User.objects.create_user("debug_user", "", "debug_user")

    def tearDown(self):
        #remove dummy user for security reasons
        user = User.objects.get(username="debug_user")
        user.delete()
    
    def test_auth_invalid_format(self):
        response = self.client.get("/uclvr/auth", {"wronguname": "debug_user", "wrongpwd": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["Invalid request format"])

    def test_auth_wrong_uname(self):
        response = self.client.get("/uclvr/auth", {"uname": "debug_wrong", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["Invalid username or password"])

    def test_auth_wrong_password(self):
        response = self.client.get("/uclvr/auth", {"uname": "debug_user", "password": "debug_wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["Invalid username or password"])

    def test_auth_success(self):
        response = self.client.get("/uclvr/auth", {"uname": "debug_user", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_AUTH)
        self.assertEqual(response.context['payload'], ["authentication succeded"])

class RegisterTestCase(TestCase):

    def setUp(self):
        #create dummy user
        User.objects.create_user("debug_user", "", "debug_user")
    
    def tearDown(self):
        #remove dummy user for security reasons
        try:
            user = User.objects.get(username="debug_user")
            user.delete()
            user = User.objects.get(username="debug_user1")
            user.delete()
        except:
            pass

    def test_register_invalid_format(self):
        response = self.client.get("/uclvr/register", {"wrong_uname": "", "email": "", "wrong_password": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_REG)
        self.assertEqual(response.context['payload'], ["Missing parameter"])

    def test_register_existing(self):
        response = self.client.get("/uclvr/register", {"uname": "debug_user", "email": "", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_REG)
        self.assertEqual(response.context['payload'], ["Account with same name already exists"])
    
    def test_register_success(self):
        response = self.client.get("/uclvr/register", {"uname": "debug_user1", "email": "mymail@mail.com", "password": "debug_user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user1')
        self.assertEqual(response.context['req'], views.REQ_REG)
        self.assertEqual(response.context['payload'], ["Registered"])

class AuthUserTestCase(TestCase):
    
    def setUp(self):
        #create dummy user
        self.user = User.objects.create_user("debug_user", "", "debug_user")
        self.user.save()

    def tearDown(self):
        #user = User.objects.get(username="debug_user")
        self.user.delete()

    def auth(self):
        self.client.login(username="debug_user", password="debug_user")

    def deauth(self):
        self.client.logout()

    def getUser(self):
        return self.user

class StatusTestCase(AuthUserTestCase):
    
    def setUp(self):
        super(StatusTestCase, self).setUp()
        #add dummy videos for the user at different progress levels
        # reconstructed video
        video = Video()
        video.data = None
        video.uid = self.user
        video.vname = "dummy_reconstructed"
        video.vhash = ""
        video.status = Video.STATUS_RECONSTRUCTED
        video.save()
        # working video
        video = Video()
        video.data = None
        video.uid = self.user
        video.vname = "dummy_working"
        video.vhash = ""
        video.status = Video.STATUS_WORKING
        video.save()
        # frame extraction video
        video = Video()
        video.data = None
        video.uid = self.user
        video.vname = "dummy_frames"
        video.vhash = ""
        video.status = Video.STATUS_EXTRACT_FRAMES
        video.save()
        # pending video
        video = Video()
        video.data = None
        video.uid = self.user
        video.vname = "dummy_pending"
        video.vhash = ""
        video.status = Video.STATUS_PENDING
        video.save()
        # converting output video
        video = Video()
        video.data = None
        video.uid = self.user
        video.vname = "dummy_converting"
        video.vhash = ""
        video.status = Video.STATUS_CONVERTING_OUTPUT
        video.save()
        # error video
        video = Video()
        video.data = None
        video.uid = self.user
        video.vname = "dummy_error"
        video.vhash = ""
        video.status = Video.STATUS_ERROR
        video.save()
        
    def tearDown(self):
        super(StatusTestCase, self).tearDown()
        Video.objects.filter(uid=self.user).delete()

    def checkPayload(self, payload_list, record):
        """
        check that the tuple record is inside the payload list
        """
        for item in payload_list:
            if item[0] == record[0] and item[1] == record[1]:
                return True
        return False

    def test_unauthenticated(self):
        self.deauth()
        response = self.client.get("/uclvr/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_STATUS)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])

    def test_user(self):
        self.auth()
        response = self.client.get("/uclvr/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_STATUS)
        self.assertTrue(self.checkPayload(response.context['list_payload'], 
                                          (views.STATUS[str(Video.STATUS_WORKING)], "dummy_working")))
        self.assertTrue(self.checkPayload(response.context['list_payload'], 
                                          (views.STATUS[str(Video.STATUS_ERROR)], "dummy_error")))
        self.assertTrue(self.checkPayload(response.context['list_payload'], 
                                          (views.STATUS[str(Video.STATUS_CONVERTING_OUTPUT)], "dummy_converting")))
        self.assertTrue(self.checkPayload(response.context['list_payload'], 
                                          (views.STATUS[str(Video.STATUS_EXTRACT_FRAMES)], "dummy_frames")))
        self.assertTrue(self.checkPayload(response.context['list_payload'], 
                                          (views.STATUS[str(Video.STATUS_PENDING)], "dummy_pending")))
        self.assertTrue(self.checkPayload(response.context['list_payload'], 
                                          (views.STATUS[str(Video.STATUS_RECONSTRUCTED)], "dummy_reconstructed")))

class DeleteTestCase(AuthUserTestCase):

    def setUp(self):
        super(DeleteTestCase, self).setUp()
        # error video
        video = Video()
        video.data = "DUMMYDATA"
        video.uid = self.user
        video.vname = "dummy"
        video.vhash = ""
        video.status = Video.STATUS_ERROR
        video.save()

    def tearDown(self):
        super(DeleteTestCase, self).tearDown()
        Video.objects.filter(uid=self.user).delete()

    def test_unauthenticated(self):
        self.deauth()
        response = self.client.get("/uclvr/delete")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_DEL)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])

    def test_invalid_format(self):
        self.auth()
        response = self.client.get("/uclvr/delete", {'wrong_label': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_DEL)
        self.assertEqual(response.context['payload'], ["No name given"])

    def test_unexisting(self):
        self.auth()
        response = self.client.get("/uclvr/delete", {'name': 'unexisting'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_DEL)
        self.assertEqual(response.context['payload'], ["Unexisting video"])

    def test_delete(self):
        self.auth()
        response = self.client.get("/uclvr/delete", {'name': 'dummy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_DEL)
        self.assertEqual(response.context['payload'], ["Deleted"])
        self.assertEqual(len(Video.objects.filter(uid=self.user)), 0, "Video record deleted")

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

    def test_unauth(self):
        self.deauth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])

    def test_upload_new(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Job submitted"])

    def test_upload_existing(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Job submitted"])
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Job already exists"])

    def test_invalid_form(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.post("/uclvr/upload", {'wrongparam': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Invalid form format"])

    def test_invalid_request(self):
        self.auth()
        target = open(os.path.join(settings.MEDIA_ROOT, "testing/debug_file"))
        response = self.client.get("/uclvr/upload", {'target': target})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_JOB)
        self.assertEqual(response.context['payload'], ["Invalid request"])
        
# test file download
class ResultDownloadTestCase(AuthUserTestCase):

    DEBUG_FILE_NAME = "37c4b87edffc5d198ff5a185cee7ee09"
    def setUp(self):
        super(ResultDownloadTestCase, self).setUp()
        self.udata = UserData(self.user)
        self.path = os.path.join(self.udata.getStorageDir(), ResultDownloadTestCase.DEBUG_FILE_NAME)
        self.data_path = self.path + "_data"
        os.mkdir(self.udata.getStorageDir())
        shutil.copytree(os.path.join(settings.MEDIA_ROOT, "testing/template_dir"), self.data_path)
        self.tempfile = ContentFile("The quick brown fox jumps over the lazy dog")
        self.tempfile.name = "dummy"
        self.video = Video()
        self.video.data = self.tempfile
        self.video.uid = self.user
        self.video.vname = "dummy"
        self.video.vhash = ResultDownloadTestCase.DEBUG_FILE_NAME
        self.video.status = Video.STATUS_RECONSTRUCTED
        self.video.save()
    
    def tearDown(self):
        Video.objects.filter(uid=self.user).delete()
        shutil.rmtree(self.udata.getStorageDir())
        super(ResultDownloadTestCase, self).tearDown()

    def test_unauth(self):
        self.deauth()
        response = self.client.get("/uclvr/download", {'name': 'dummy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_DOWNLOAD)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])

    def test_unexisting(self):
        self.auth()
        response = self.client.get("/uclvr/download", {'name': 'unexisting'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_DOWNLOAD)
        self.assertEqual(response.context['payload'], ["Resource not existing"])

    def test_success(self):
        self.auth()
        self.video.status = Video.STATUS_RECONSTRUCTED
        self.video.save()
        response = self.client.get("/uclvr/download", {'name': 'dummy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Disposition'), "attachment; filename=dummy.obj")
        self.assertEqual(response.get('X-Sendfile'), os.path.join(self.data_path, "result.obj"))

    def test_unfinished(self):
        self.auth()
        self.video.status = Video.STATUS_ERROR
        self.video.save()
        response = self.client.get("/uclvr/download", {'name': 'dummy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_DOWNLOAD)
        self.assertEqual(response.context['payload'], ["Output not ready or error occurred"])

# test log download
class DumpLogTestCase(AuthUserTestCase):
    
    DEBUG_FILE_NAME = "37c4b87edffc5d198ff5a185cee7ee09"
    def setUp(self):
        super(DumpLogTestCase, self).setUp()
        self.udata = UserData(self.user)
        self.path = os.path.join(self.udata.getStorageDir(), ResultDownloadTestCase.DEBUG_FILE_NAME)
        self.data_path = self.path + "_data"
        os.mkdir(self.udata.getStorageDir())
        shutil.copytree(os.path.join(settings.MEDIA_ROOT, "testing/template_dir"), self.data_path)
        self.tempfile = ContentFile("The quick brown fox jumps over the lazy dog")
        self.tempfile.name = "dummy"
        self.video = Video()
        self.video.data = self.tempfile
        self.video.uid = self.user
        self.video.vname = "dummy"
        self.video.vhash = ResultDownloadTestCase.DEBUG_FILE_NAME
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

# test UserData
class UserDataTestCase(AuthUserTestCase):

    def setUp(self):
        super(UserDataTestCase, self).setUp()
    
    def tearDown(self):
        super(UserDataTestCase, self).tearDown()

    def test_get_path(self):
        dummy_name = "dummy.tmp" # this never goes on filesystem, only testing path generation
        res = UserData(self.user)
        data_path = os.path.join(settings.MEDIA_ROOT, str(self.user.id) + "_" + self.user.username, dummy_name)
        self.assertEqual(res.joinPath(dummy_name), data_path)

# test ResourceData class
class ResourceDataTestCase(AuthUserTestCase):
    
    DEBUG_FILE_NAME = "37c4b87edffc5d198ff5a185cee7ee09"
    def setUp(self):
        super(ResourceDataTestCase, self).setUp()
        self.udata = UserData(self.user) # user data is assumed to work correctly
        self.auth()
        file_url = os.path.join(self.udata.getStorageDir(), ResourceDataTestCase.DEBUG_FILE_NAME)
        self.data_path = file_url + "_data"
        #setup user files in user directory from template testing dir
        shutil.copytree(os.path.join(settings.MEDIA_ROOT, "testing/template_dir"), self.data_path)
        self.resource = ResourceData(file_url)

    def tearDown(self):
        shutil.rmtree(self.udata.getStorageDir())
        super(ResourceDataTestCase, self).tearDown()

    def test_join_path(self):
        relpath = self.resource.joinPath("test/path/to/file.tmp")
        expected = self.udata.joinPath(ResourceDataTestCase.DEBUG_FILE_NAME + "_data/test/path/to/file.tmp")
        self.assertEqual(relpath, expected)

    def test_get_output_vsfm(self):
        ply = self.resource.getVsfmOutput()
        self.assertIn("result1.ply", ply)
        self.assertIn("result2.ply", ply)
        #remove result1, should output result 2
        os.remove(os.path.join(self.data_path, "result1.ply"))
        ply = self.resource.getVsfmOutput()
        self.assertIn("result2.ply", ply)
        self.assertNotIn("resutl1.ply", ply)
        #remove last ply
        os.remove(os.path.join(self.data_path, "result2.ply"))
        ply = self.resource.getVsfmOutput()
        self.assertEqual(ply, [])

    def test_get_unique_output(self):
        path = self.resource.getUniqueVsfmOutput()
        self.assertEqual(path, os.path.join(self.data_path, "result1.ply"))
        #remove result1, should output result 2
        os.remove(os.path.join(self.data_path, "result1.ply"))
        path = self.resource.getUniqueVsfmOutput()
        self.assertEqual(path, os.path.join(self.data_path, "result2.ply"))
        #remove last ply
        os.remove(os.path.join(self.data_path, "result2.ply"))
        path = self.resource.getUniqueVsfmOutput()
        self.assertEqual(path, None)

    def test_get_output_URL(self):
        url = self.resource.getFinalOutputFile()
        self.assertEqual(url, os.path.join(self.data_path, "result.obj"))
        #remove obj file, should return none
        os.remove(os.path.join(self.data_path, "result.obj"))
        url = self.resource.getFinalOutputFile()
        self.assertEqual(url, None)

    def test_get_log_path(self):
        #get log path for ffmpeg
        name, path = self.resource.getLogPath("ffmpeg")
        self.assertEqual(name, "ffmpeg.log")
        self.assertEqual(path, os.path.join(self.data_path, "log/ffmpeg.log"))
        #get log path for vsfm
        name, path = self.resource.getLogPath("vsfm")
        self.assertEqual(name, "vsfm.log")
        self.assertEqual(path, os.path.join(self.data_path, "log/vsfm.log"))
        #get log path for meshlab
        name, path = self.resource.getLogPath("meshlab")
        self.assertEqual(name, "meshlab.log")
        self.assertEqual(path, os.path.join(self.data_path, "log/meshlab.log"))
        #get unexisting
        name, path = self.resource.getLogPath("foo")
        self.assertIsNone(name)
        self.assertIsNone(path)

    def test_create_log(self):
        #create a log
        log = self.resource.getLogFile("mylog")
        self.assertIsNotNone(log)
        log.close()
        self.assertTrue(os.path.exists(os.path.join(self.data_path, "log/mylog.log")))
        #create other log
        log = self.resource.getLogFile("myotherlog")
        self.assertIsNotNone(log)
        log.close()
        self.assertTrue(os.path.exists(os.path.join(self.data_path, "log/myotherlog.log")))

    def test_clear_data(self):
        self.resource.removeProcessingData()
        self.assertEqual(os.listdir(self.data_path), [])

# test Ply parser
class PlyTestCase(TestCase):

    def test_missing_signature(self):
        data = open(os.path.join(settings.MEDIA_ROOT, "testing/ply/nosign.ply"))
        self.assertRaises(Exception, PlyHeader, data)

    def test_good(self):
        data = open(os.path.join(settings.MEDIA_ROOT, "testing/ply/result2.ply"))
        ply = PlyHeader(data)
        self.assertEqual(ply.elements["vertex"].number, 5729)
        self.assertEqual(ply.format, "binary_little_endian")
