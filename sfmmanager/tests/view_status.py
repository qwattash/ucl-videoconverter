from django.test import TestCase

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from sfmmanager import views
from sfmmanager.models import *

from .base import *

# test status view
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
