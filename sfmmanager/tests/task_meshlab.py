from django.conf import settings
from django.core.files import File

from sfmmanager.models import *
from sfmmanager.storage_utils import ResourceData, UserData
from sfmmanager.tasks import *
import sfmmanager #needed for mocking parts of it
from .base import *

import mock
import StringIO
import shutil
import os

import __builtin__

class MeshlabTestCase(CeleryTestCase):

    SAMPLE_FILE = "testing/samples/ffmpeg/c4ea9969cd299e73eccc37e918b59fa4.mp4"
    FILE_HASH = "c4ea9969cd299e73eccc37e918b59fa4"
    def setUp(self):
        super(MeshlabTestCase, self).setUp()
        # prepare directory tree
        self.path = os.path.join(self.udata.getStorageDir(), MeshlabTestCase.FILE_HASH)
        self.data_path = self.path + "_data"
        os.mkdir(self.udata.getStorageDir())
        os.mkdir(self.data_path)
        # create sample video
        self.tempfile = File(open(os.path.join(settings.MEDIA_ROOT, MeshlabTestCase.SAMPLE_FILE)))
        self.tempfile.name = "dummy.mp4"
        self.video = Video()
        self.video.data = self.tempfile
        self.video.uid = self.user
        self.video.vname = "dummy.mp4"
        self.video.vhash = MeshlabTestCase.FILE_HASH
        self.video.status = Video.STATUS_PENDING
        self.video.save()

    def tearDown(self):
        # remove everything
        Video.objects.filter(uid=self.user).delete()
        shutil.rmtree(self.udata.getStorageDir())
        super(MeshlabTestCase, self).tearDown()

    @mock.patch("sfmmanager.storage_utils.ResourceData.getLogFile", mock.Mock())
    @mock.patch("sfmmanager.storage_utils.ResourceData.getUniqueVsfmOutput", mock.Mock())
    @mock.patch("subprocess.Popen")
    def test_meshlab_call(self, mock_task):
        mock_log = sfmmanager.storage_utils.ResourceData.getLogFile
        mock_ply = sfmmanager.storage_utils.ResourceData.getUniqueVsfmOutput
        mock_log.return_value = StringIO.StringIO()
        mock_task.return_value.returncode = 0
        mock_ply.return_value = os.path.join(self.data_path, "vsfm.0.ply")
        result = processOutput(self.video.id)
        self.assertEqual(result, self.video.id)
        mock_task.assert_called_once_with(["meshlabserver", "-i", mock_ply.return_value, "-o", 
                                           os.path.join(self.data_path, "result.obj"), "-om", "vc", "vn"], 
                                          stdin=None, 
                                          stdout=mock_log.return_value, 
                                          stderr=mock_log.return_value)
        mock_log.assert_called_once_with("meshlab")
        self.assertEqual(Video.objects.get(pk=self.video.id).status, str(Video.STATUS_RECONSTRUCTED))
