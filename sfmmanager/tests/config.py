from django.test import TestCase
from django.conf import settings

from sfmmanager.config import *

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
