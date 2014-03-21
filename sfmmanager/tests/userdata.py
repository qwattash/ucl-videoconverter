from django.conf import settings

from sfmmanager import views
from sfmmanager.storage_utils import UserData

from .base import *
import os

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
