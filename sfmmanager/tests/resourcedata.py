from django.conf import settings

from sfmmanager.storage_utils import ResourceData, UserData
from .base import *

import shutil
import os

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
