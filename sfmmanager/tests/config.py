from django.test import TestCase
from django.conf import settings
from django.core.files.base import ContentFile

from sfmmanager.models import Video
from sfmmanager.config import *
from .base import *

import StringIO
import mock
import shutil
import os

import __builtin__

MOCK_DATA = """
# this is a comment
foo 5.4
# this is another commment

#other comment without leading space
bar --baz

multiple foo bar baz
#EOF
"""

class ConfigObjectTestCase(TestCase):
    
    TEST_CONF_PATH = "testing/template_config.conf"
    TEST_CONF_DEST = "testing/template_config.tmp"
    def setUp(self):
        self.src = os.path.join(settings.MEDIA_ROOT, ConfigObjectTestCase.TEST_CONF_PATH)
        self.dst = os.path.join(settings.MEDIA_ROOT, ConfigObjectTestCase.TEST_CONF_DEST)
        self.conf = Config(self.src, self.dst)

    def tearDown(self):
        if os.path.exists(self.dst):
            os.remove(self.dst)

    @mock.patch('__builtin__.open', mock.MagicMock())
    @mock.patch('StringIO.StringIO.close', mock.Mock())
    def test_read_conf(self):
        open_mock = __builtin__.open
        open_mock.return_value = StringIO.StringIO(MOCK_DATA)
        self.conf.load()
        self.assertEqual(self.conf, {'foo': '5.4', 'bar': '--baz', 'multiple': 'foo bar baz'})
        open_mock.assert_called_once_with(self.src, 'r')
        open_mock.return_value.close.assert_called_once_with()

    @mock.patch('__builtin__.open', mock.MagicMock())
    @mock.patch('StringIO.StringIO.write', mock.Mock())
    @mock.patch('StringIO.StringIO.close', mock.Mock())
    def test_save_conf(self):
        open_mock = __builtin__.open
        open_mock.return_value = StringIO.StringIO(MOCK_DATA)
        self.conf.load()
        open_mock.return_value.close.assert_called_once_with()
        self.conf['foo'] = 'modified_foo'
        self.conf.save()
        open_mock.assert_called_with(self.dst, 'w+')
        open_mock.return_value.write.assert_any_call("foo modified_foo\n")
        open_mock.return_value.write.assert_any_call("bar --baz\n")
        open_mock.return_value.write.assert_any_call("multiple foo bar baz\n")
        open_mock.return_value.close.assert_called_once_with()


class ConfigFactoryTestCase(AuthUserTestCase):
    
    TEST_CONF_PATH = "testing/template_config.conf"
    TEST_CONF_DEST = "testing/template_config.tmp"
    DATA_HASH = "016d9fe44dab3e71418995b5fb7fe5fd"
    def setUp(self):
        super(ConfigFactoryTestCase, self).setUp()
        self.udata = UserData(self.user)
        self.user_path = self.udata.getStorageDir()
        os.mkdir(self.user_path)
        # create video
        video = Video()
        tempfile = ContentFile("DUMMY_DATA")
        tempfile.name = "dummy"
        video.data = tempfile
        video.uid = self.user
        video.vname = "dummy"
        video.vhash = ConfigFactoryTestCase.DATA_HASH
        video.status = Video.STATUS_ERROR
        video.save()
        self.conf = ConfigFactory(video)

    def tearDown(self):
        shutil.rmtree(self.udata.getStorageDir())
        Video.objects.filter(uid=self.user).delete()
        super(ConfigFactoryTestCase, self).tearDown()

    @mock.patch('sfmmanager.config.Config')
    def test_gen_vsfm_config(self, mock_config):
        dst_path = os.path.join(self.user_path, ConfigFactoryTestCase.DATA_HASH + "_data", "conf/nv.ini")
        src_path = os.path.join(settings.MEDIA_ROOT, "conf/vsfm.skel")
        self.conf.buildVsfmConf()
        mock_config.assert_called_once_with(src_path, dst_path)
        mock_config.return_value.load.assert_called_once_with()
        mock_config.return_value.save.assert_called_once_with()
        mock_config.return_value.__setitem__.assert_any_call("frames", "1")

    @mock.patch('os.remove', mock.Mock())
    @mock.patch('shutil.copy', mock.Mock())
    def test_deploy_vsfm_config(self):
        src_path = os.path.join(self.user_path, ConfigFactoryTestCase.DATA_HASH + "_data", "conf/nv.ini")
        dst_path = ConfigFactory.VSFM_CONF_PATH
        self.conf.deployVsfmConf(src_path)
        os.remove.assert_called_once_with(dst_path)
        shutil.copy.assert_called_once_with(src_path, dst_path)
