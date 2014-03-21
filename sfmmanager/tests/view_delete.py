from django.core.urlresolvers import reverse

from sfmmanager import views
from sfmmanager.models import *

from .base import *

# test delete view
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
