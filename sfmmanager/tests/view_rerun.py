from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from sfmmanager import views
from sfmmanager.models import *
from .base import *
import mock

# test rerun command
class RerunTestCase(AuthUserTestCase):
    
    def setUp(self):
        super(RerunTestCase, self).setUp()
        self.video = Video()
        self.video.data = None
        self.video.uid = self.user
        self.video.vname = "dummy"
        self.video.vhash = ""
        self.video.status = Video.STATUS_RECONSTRUCTED
        self.video.save()
    
    def tearDown(self):
        Video.objects.filter(uid=self.user).delete()
        super(RerunTestCase, self).tearDown()

    def test_rerun_unauth(self):
        self.deauth()
        response = self.client.get("/uclvr/rerun", {'name': 'dummy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], '')
        self.assertEqual(response.context['req'], views.REQ_RERUN)
        self.assertEqual(response.context['payload'], ["Unauthenticated"])

    def test_unexisting(self):
        self.auth()
        response = self.client.get("/uclvr/rerun", {'name': 'unexisting'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_RERUN)
        self.assertEqual(response.context['payload'], ["Unexisting video"])

    def test_no_name(self):
        self.auth()
        response = self.client.get("/uclvr/rerun")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_RERUN)
        self.assertEqual(response.context['payload'], ["No name given"])
    
    """
    see http://www.mattjmorrison.com/2011/09/mocking-django.html
    """
    @mock.patch("sfmmanager.models.Video.process", mock.Mock())
    def test_success(self):
        self.auth()
        response = self.client.get("/uclvr/rerun", {'name': 'dummy'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['uname'], 'debug_user')
        self.assertEqual(response.context['req'], views.REQ_RERUN)
        self.assertEqual(response.context['payload'], ["Rerunning"])
        self.assertEqual(Video.process.call_count, 1)
